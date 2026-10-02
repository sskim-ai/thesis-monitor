"""Opt-in REV38 read-only exact-security KSD probe; no price/estimate refresh."""
import argparse
from hashlib import sha256
import json
import logging
from pathlib import Path
import time

import httpx

from app.services.unified_run_artifacts import durable_bytes
from scripts import kis_estimate_capability_probe as base
from scripts import kis_exact_action_guard as g
from scripts import kis_current_fy1_owner as p
from scripts.kis_eps_wire_calibration import digest, verified
from scripts.kis_fy1_semantic_owner import SemanticGap


def build_plan(rows, documentation):
    if len(rows) != 8 or {r['security_code'] for r in rows} != set(base.KR8):
        raise base.ProbeStop('COHORT_GAP')
    indexed = {r['security_code']: r for r in rows}
    requests, identities = [], {}
    for code in base.KR8:
        row = indexed[code]
        eps, price = row['eps'], row['price']
        if eps['state'] != 'KIS_FY1_EPS_ESTIMATE_SNAPSHOT' or not price:
            continue
        p.eps_receipt(eps)
        verified(price, p.PRICE)
        # The old owner validates security/currency/calendar before refusing missing actions.
        assert p.current_fper(eps, price, None)['state'] == 'UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE'
        if eps['security_code'] != code:
            raise base.ProbeStop('EPS_ROW_IDENTITY_GAP')
        window = g.envelope(eps['estdate'], price['session_date'])
        identities[code] = {'eps_sha256': eps['receipt_sha256'], 'price_sha256': price['receipt_sha256'],
            'estimate_date': eps['estdate'], 'price_date': price['session_date'], 'guard_envelope': window}
        for variant in g.VARIANTS:
            route = g.route_contract(variant, documentation)
            requests.append({'subject': code, 'variant': variant, 'path': route['path'],
                'tr_id': route['tr_id'], 'params': g.action_params(variant, code, window)})
    if len(requests) > 42:
        raise base.ProbeStop('SCOPE_GAP')
    return {'contract': 'REV38ExactSecurityActionPlan', 'policy': g.POLICY,
        'requests': requests, 'inputs': identities, 'documentation_sha256': digest(documentation),
        'maximum_data_calls': 60, 'maximum_initial_calls': 42, 'maximum_continuation_calls': 18,
        'minimum_spacing_seconds': 1.1, 'timeout_seconds': 45, 'retries': 0,
        'price_refresh': 0, 'estimate_refresh': 0, 'models': 0, 'messages': 0,
        'continuation_policy': 'SOURCE_OWNED_CHANGED_CURSOR_AND_OFFICIAL_BINDING_OR_STOP_FAMILY'}


class ExactActionProbe(base.Probe):
    def __init__(self, *args, plan, documentation, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan, self.documentation = plan, documentation
        self.calls, self.chain, self.failed = [], {}, set()
        self.last_finished = None
        self.extra_pages = 0

    def authenticate(self):
        super().authenticate()
        self.last_finished = time.monotonic()
        self.save('auth-pacing-origin.json', {'completed_at': base.now(),
            'monotonic_after_auth': self.last_finished, 'minimum_spacing_seconds': 1.1})

    def fetch(self, request, cursor='', page=1):
        key = (request['subject'], request['variant'])
        previous = self.chain.get(key)
        if (request not in self.plan['requests'] or not self.token or self.last_finished is None
                or key in self.failed or self.data_count >= 60
                or page != self.pages.get(key, 0) + 1
                or (page == 1 and cursor != '')
                or (page > 1 and (not previous or previous['next_cursor'] is None
                    or cursor != previous['next_cursor'] or self.extra_pages >= 18))):
            raise base.ProbeStop('REQUEST_SCOPE_GAP')
        self.disk_guard()
        time.sleep(max(0, 1.101 - (time.monotonic() - self.last_finished)))
        self.data_count += 1
        self.extra_pages += int(page > 1)
        self.pages[key] = page
        self.calls.append({'subject': key[0], 'variant': key[1], 'page': page})
        stem = f'action/{key[0]}/{key[1]}-{page}'
        headers = {'authorization': 'Bearer ' + self.token, 'appkey': self.credentials.app_key,
            'appsecret': self.credentials.app_secret, 'tr_id': request['tr_id'], 'custtype': 'P',
            'tr_cont': '' if page == 1 else 'N', 'user-agent': 'ThesisMonitor/1.0',
            'accept': 'application/json', 'content-type': 'application/json'}
        params = {**request['params'], 'CTS': cursor}
        owned = {**request, 'params': params, 'method': 'GET', 'tr_cont': headers['tr_cont'],
            'page': page, 'ordinal': self.data_count, 'started_at': base.now(),
            'started_monotonic': time.monotonic(), 'previous_completed_monotonic': self.last_finished,
            'redirects': False, 'retries': 0, 'plan_sha256': digest(self.plan)}
        self.save(stem + '-request.json', owned)
        try:
            response = self.client.get(base.ORIGIN + request['path'], params=params, headers=headers)
        except httpx.HTTPError:
            self.save(stem + '-receipt.json', {'state': 'TRANSPORT_FAILURE', 'request': owned, 'ended_at': base.now()})
            raise base.ProbeStop('TRANSPORT_FAILURE') from None
        raw = response.content
        base.scan(raw, self.secrets, auth_fields=True)
        response_headers = {k: response.headers.get(k) for k in ('tr_cont', 'content-type', 'date', 'tr_id')}
        base.scan(json.dumps(response_headers).encode(), self.secrets)
        durable_bytes(self.output / (stem + '.body'), raw, exclusive=True)
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        state = 'COMPLETE_RESPONSE' if response.status_code == 200 and payload.get('rt_cd') == '0' else 'SOURCE_INCOMPLETE'
        rate = response.status_code == 429 or payload.get('msg_cd') == 'EGW00201'
        if rate:
            state = 'KIS_RATE_LIMIT_GAP'
        next_value, chain_error = None, None
        seen = set(previous['seen_cursors']) if previous else set()
        hashes = list(previous['hashes']) if previous else []
        row_hash = digest(payload.get('output1'))
        if state == 'COMPLETE_RESPONSE':
            try:
                if row_hash in hashes:
                    raise SemanticGap('DUPLICATE_PAGE_LOOP')
                rows = payload.get('output1')
                if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
                    raise SemanticGap('ACTION_ROWS_GAP')
                if any(g.row_identity(r, key[0]) != 'EXACT' for r in rows):
                    raise SemanticGap('ACTION_IDENTITY_GAP')
                next_value = g.next_cursor(payload, response_headers, cursor, seen,
                    g.route_contract(key[1], self.documentation))
            except SemanticGap as exc:
                chain_error = str(exc)
                self.failed.add(key)
        else:
            self.failed.add(key)
        seen.add(cursor)
        hashes.append(row_hash)
        self.chain[key] = {'next_cursor': next_value, 'seen_cursors': sorted(seen), 'hashes': hashes}
        receipt = {'state': state, 'request': owned, 'http_status': response.status_code,
            'raw_sha256': sha256(raw).hexdigest(), 'bytes': len(raw), 'ended_at': base.now(),
            'response_headers': response_headers, 'rt_cd': payload.get('rt_cd'), 'msg_cd': payload.get('msg_cd'),
            'next_cursor': next_value, 'chain_error': chain_error, 'secret_scan': 'PASS'}
        self.save(stem + '-receipt.json', receipt)
        self.last_finished = time.monotonic()
        if rate:
            raise base.ProbeStop('KIS_RATE_LIMIT_GAP')
        if response.status_code != 200:
            raise base.ProbeStop('TRANSPORT_FAILURE')
        return receipt

    def counters(self):
        return {'auth': self.auth_count, 'action_data_calls': self.data_count,
            'initial_calls': self.data_count - self.extra_pages, 'continuation_calls': self.extra_pages,
            'calls': self.calls, 'estimate_calls': 0, 'price_calls': 0, 'retries': 0,
            'models': 0, 'messages': 0, 'telegram': 0, 'orders': 0, 'production_mutations': 0}


def run(output, env_file, rows_file, documentation_file, plan_file):
    rows, docs, plan = [json.loads(f.read_bytes()) for f in (rows_file, documentation_file, plan_file)]
    if plan != build_plan(rows, docs):
        raise base.ProbeStop('FROZEN_PLAN_PARITY_GAP')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in ('httpx', 'httpcore'):
        logging.getLogger(name).disabled = True
    with httpx.Client(timeout=45, follow_redirects=False) as client:
        probe = ExactActionProbe(output, base.load_credentials(env_file), client, plan=plan, documentation=docs)
        probe.save('request-freeze.json', plan)
        terminal = 'BOUNDED_ACQUISITION_COMPLETE_OFFLINE_QUALIFICATION_REQUIRED'
        try:
            probe.authenticate()
            for request in plan['requests']:
                cursor, page = '', 1
                while True:
                    receipt = probe.fetch(request, cursor, page)
                    print('ACTION_RECEIPT', request['subject'], request['variant'], page, receipt['state'], flush=True)
                    cursor = receipt['next_cursor']
                    if cursor is None or probe.extra_pages >= 18:
                        break
                    page += 1
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
