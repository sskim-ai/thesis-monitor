"""Explicit opt-in REV37 read-only KIS scope; no estimate refresh or production imports."""
import argparse
from hashlib import sha256
import json
import logging
from pathlib import Path
import time

import httpx

from app.services.unified_run_artifacts import durable_bytes
from scripts import kis_estimate_capability_probe as base
from scripts.kis_current_fy1_owner import (
    PRICE_PATH, PRICE_TR, ROUTES, action_params, calendar_receipt, eps_receipt, price_params,
)
from scripts.kis_eps_wire_calibration import digest


def build_plan(rows, documentation, as_of):
    calendar = calendar_receipt(as_of)
    qualified = [row['eps'] for row in rows if row['eps']['state'] == 'KIS_FY1_EPS_ESTIMATE_SNAPSHOT']
    codes = [e['security_code'] for e in qualified]
    if len(rows) != 8 or set(r['security_code'] for r in rows) != set(base.KR8):
        raise base.ProbeStop('COHORT_GAP')
    if len(codes) != 7 or len(set(codes)) != 7 or '003690' in codes:
        raise base.ProbeStop('QUALIFIED_EPS_SCOPE_GAP')
    for eps in qualified:
        eps_receipt(eps)
    start, end = min(e['estdate'] for e in qualified), calendar['latest_completed_session']
    requests = []
    for family, (path, tr_id, _) in ROUTES.items():
        if documentation['actions'][family]['path'] != '/uapi/domestic-stock/v1/ksdinfo/' + path:
            raise base.ProbeStop('DOCUMENTATION_ROUTE_GAP')
        requests.append({'kind': 'action', 'subject': family, 'path': '/uapi/domestic-stock/v1/ksdinfo/' + path,
            'tr_id': tr_id, 'params': action_params(family, start, end)})
    requests += [{'kind': 'price', 'subject': code, 'path': PRICE_PATH, 'tr_id': PRICE_TR,
                 'params': price_params(code)} for code in codes]
    return {'contract': 'REV37BoundedKISRequestPlan', 'calendar': calendar, 'window_start': start,
        'window_end': end, 'requests': requests, 'eps_receipt_hashes': {e['security_code']: e['receipt_sha256'] for e in qualified},
        'documentation_sha256': digest(documentation), 'maximum_data_calls': 20,
        'price_max': 7, 'initial_action_max': 5, 'extra_action_pages_max': 8,
        'maximum_pages_per_family': 3, 'minimum_spacing_seconds': 1.1,
        'continuation': 'OFFICIAL_M_TO_N_SAME_PARAMS_NO_INVENTED_CURSOR',
        'estimate_refresh': 0, 'retries': 0, 'timeout_seconds': 45}


class CurrentProbe(base.Probe):
    def __init__(self, *args, plan, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = plan
        self.calls = []
        self.last_finished = time.monotonic()
        self.extra_pages = 0
        self.last_status = {}

    def fetch(self, request, page=1):
        key = (request['kind'], request['subject'])
        if (request not in self.plan['requests'] or not self.token or self.data_count >= 20
                or page != 1 + self.pages.get(key, 0)
                or (page > 1 and (key[0] != 'action' or self.last_status.get(key) != 'M'
                                 or self.extra_pages >= 8 or page > 3))):
            raise base.ProbeStop('REQUEST_SCOPE_GAP')
        self.disk_guard()
        time.sleep(max(0, 1.1 - (time.monotonic() - self.last_finished)))
        self.pages[key] = page
        self.data_count += 1
        self.extra_pages += int(page > 1)
        self.calls.append({'kind': key[0], 'subject': key[1], 'page': page})
        stem = f'{key[0]}/{key[1]}-{page}'
        headers = {'authorization': 'Bearer ' + self.token, 'appkey': self.credentials.app_key,
            'appsecret': self.credentials.app_secret, 'tr_id': request['tr_id'], 'custtype': 'P',
            'tr_cont': '' if page == 1 else 'N', 'user-agent': 'ThesisMonitor/1.0', 'accept': 'application/json'}
        owned = {**request, 'method': 'GET', 'tr_cont': headers['tr_cont'], 'page': page,
            'ordinal': self.data_count, 'started_at': base.now(), 'redirects': False, 'retries': 0,
            'plan_sha256': digest(self.plan)}
        self.save(stem + '-request.json', owned)
        try:
            response = self.client.get(base.ORIGIN + request['path'], params=request['params'], headers=headers)
        except httpx.HTTPError:
            self.save(stem + '-receipt.json', {'state': 'TRANSPORT_FAILURE', 'request': owned, 'ended_at': base.now()})
            raise base.ProbeStop('TRANSPORT_FAILURE') from None
        finally:
            self.last_finished = time.monotonic()
        raw = response.content
        base.scan(raw, self.secrets, auth_fields=True)
        durable_bytes(self.output / (stem + '.body'), raw, exclusive=True)
        response_headers = {k: response.headers.get(k) for k in ('tr_cont', 'content-type', 'date', 'tr_id')}
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        state = 'COMPLETE' if response.status_code == 200 and payload.get('rt_cd') == '0' else 'SOURCE_INCOMPLETE'
        if payload.get('msg_cd') == 'EGW00201':
            state = 'KIS_RATE_LIMIT_GAP'
        receipt = {'state': state, 'request': owned, 'http_status': response.status_code,
            'raw_sha256': sha256(raw).hexdigest(), 'bytes': len(raw), 'ended_at': base.now(),
            'response_headers': response_headers, 'rt_cd': payload.get('rt_cd'), 'msg_cd': payload.get('msg_cd'),
            'secret_scan': 'PASS'}
        self.save(stem + '-receipt.json', receipt)
        self.results[stem] = receipt
        self.last_status[key] = response_headers['tr_cont']
        if state == 'KIS_RATE_LIMIT_GAP':
            raise base.ProbeStop(state)
        return receipt

    def counters(self):
        return {'auth': self.auth_count, 'data_total': self.data_count, 'calls': self.calls,
            'prices': sum(c['kind'] == 'price' for c in self.calls),
            'actions': sum(c['kind'] == 'action' for c in self.calls), 'extra_pages': self.extra_pages,
            'estimate_refresh': 0, 'retries': 0, 'models': 0, 'messages': 0, 'telegram': 0,
            'orders': 0, 'production_mutations': 0}


def run(output, env_file, rows_file, documentation_file, plan_file):
    rows, docs, plan = [json.loads(p.read_bytes()) for p in (rows_file, documentation_file, plan_file)]
    if plan != build_plan(rows, docs, plan['calendar']['as_of']):
        raise base.ProbeStop('FROZEN_PLAN_PARITY_GAP')
    # Freeze may precede calls slightly; crossing a completed-session boundary is not allowed.
    if calendar_receipt(base.now())['latest_completed_session'] != plan['window_end']:
        raise base.ProbeStop('FROZEN_SESSION_CHANGED')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in ('httpx', 'httpcore'):
        logging.getLogger(name).disabled = True
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        probe = CurrentProbe(output, base.load_credentials(env_file), client, plan=plan)
        probe.save('request-freeze.json', plan)
        terminal = 'BOUNDED_ACQUISITION_COMPLETE_OFFLINE_OWNERSHIP_REVIEW_REQUIRED'
        try:
            probe.authenticate()
            for request in plan['requests']:
                hashes = set()
                for page in range(1, 4 if request['kind'] == 'action' else 2):
                    if page > 1 and probe.extra_pages >= 8:
                        break
                    receipt = probe.fetch(request, page)
                    repeated = receipt['raw_sha256'] in hashes
                    hashes.add(receipt['raw_sha256'])
                    if (receipt['state'] != 'COMPLETE' or repeated
                            or receipt['response_headers']['tr_cont'] != 'M'):
                        break
        except base.ProbeStop as exc:
            terminal = str(exc)
        except Exception as exc:
            terminal = 'INTERNAL_GAP_' + type(exc).__name__
        finally:
            probe.save('counters.json', probe.counters())
            probe.save('terminal.json', {'state': terminal, 'ended_at': base.now(), 'token_storage': 'MEMORY_ONLY'})
            probe.token = None
        print(terminal, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('output', 'env-file', 'rows-file', 'documentation-file', 'plan-file'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.output, args.env_file, args.rows_file, args.documentation_file, args.plan_file)
