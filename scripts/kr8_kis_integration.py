"""Opt-in KR8 source integration. No production consumer or model imports.

Current values are acquired anew; accepted protocol controls establish semantics
only. Each conditional price/action request is bounded by the frozen KR8 scope.
"""
from datetime import date, datetime
from hashlib import sha256
import json
import shutil
import time

import httpx

from app.services.unified_run_artifacts import durable_bytes
from scripts import kis_current_fy1_owner as price
from scripts import kis_estimate_capability_probe as base
from scripts import kis_exact_action_guard as action
from scripts import kis_output3_protocol_owner as protocol
from scripts.kis_eps_wire_calibration import digest, sealed
from scripts.kis_exact_action_probe import ExactActionProbe
from scripts.kis_fy1_semantic_owner import Documentation, Evidence, SemanticGap
from scripts.kis_protocol_stage_b_probe import IDENTITY_PATH, IDENTITY_TR

CONTRACT = 'kr8-fresh-kis-source-integration-v1'
SUBJECTS = tuple(sorted(base.KR8))


def build_plan(*, generation, as_of, securities, static_hashes):
    if set(securities) != set(SUBJECTS):
        raise ValueError('KR8_EXACT_SECURITY_SET_REQUIRED')
    for code, security in securities.items():
        if (security['ticker'] != code or security['exchange'] != 'KRX'
                or security['currency'] != 'KRW' or not security['canonical_security_id']
                or not security.get('corp_code')):
            raise ValueError('KR8_SECURITY_IDENTITY_GAP')
    return sealed(dict(contract=CONTRACT, generation_id=generation, scope='KR8_ONLY',
        securities=securities, as_of=as_of, calendar=price.calendar_receipt(as_of),
        static_hashes=static_hashes, subjects=list(SUBJECTS), auth_max=1,
        estimate_max=8, identity_max=8, price_max=8, action_initial_max=48,
        action_data_max=60, action_continuation_max=18, data_max=84,
        minimum_spacing_seconds=1.101, timeout_seconds=45, retries=0,
        estimate_identity_continuation='DENY', action_policy=action.POLICY,
        action_variants=list(action.VARIANTS),
        conditional_price_action='FRESH_QUALIFIED_POSITIVE_FY1_EPS_ONLY',
        overall_direction_use=False, delivery_disabled=True, us_calls=0))


def evidence(path):
    raw = path.read_bytes()
    return Evidence(raw, sha256(raw).hexdigest())


def normalized_inventory(source, receipt, *, code, corp_code):
    """Lossless date projection from the freshly receipt-bound DART inventory."""
    payload = source.payload()
    request = receipt['request']
    if (receipt['raw_sha256'] != source.sha256 or receipt['http_status'] != 200
            or request['path'] != '/api/list.json' or request['params']['corp_code'] != corp_code
            or payload.get('status') != '000' or payload.get('page_no') != 1
            or payload.get('total_page') != 1
            or payload.get('total_count') != len(payload.get('list', []))):
        raise SemanticGap('FRESH_DART_INVENTORY_RECEIPT_GAP')
    rows = []
    for raw in payload['list']:
        if raw.get('stock_code') != code or raw.get('corp_code') != corp_code:
            raise SemanticGap('FRESH_DART_INVENTORY_IDENTITY_GAP')
        day = datetime.strptime(raw['rcept_dt'], '%Y%m%d').date().isoformat()
        rows.append(dict(raw, rcept_dt=day))
    body = json.dumps(dict(payload, list=rows), ensure_ascii=False, sort_keys=True).encode()
    return Evidence(body, sha256(body).hexdigest()), sealed(dict(
        contract='kis-fiscal-inventory-date-projection-v1', security_code=code,
        raw_sha256=source.sha256, receipt_sha256=digest(receipt),
        projected_sha256=sha256(body).hexdigest(), transformation='RCEPT_DT_YYYYMMDD_TO_ISO_ONLY'))


class FreshProbe(base.Probe):
    def __init__(self, *args, plan, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan, self.calls, self.last_finished = plan, [], None

    def disk_guard(self):
        if shutil.disk_usage(self.output).free < 12 * 1024**3:
            raise base.ProbeStop('DISK_GAP')

    def authenticate(self):
        super().authenticate()
        self.last_finished = time.monotonic()

    def fetch(self, code, kind, *, eps=None):
        key = code, kind
        if (code not in SUBJECTS or kind not in {'estimate','identity','price'}
                or key in self.calls or not self.token or self.data_count >= 24):
            raise base.ProbeStop('REQUEST_SCOPE_GAP')
        if kind == 'price' and (eps is None or eps.get('security_code') != code
                               or price.eps_receipt(eps) <= 0):
            raise base.ProbeStop('PRICE_EPS_ADMISSION_GAP')
        if price.calendar_receipt(base.now())['latest_completed_session'] != self.plan['calendar']['latest_completed_session']:
            raise base.ProbeStop('FROZEN_SESSION_CHANGED')
        self.disk_guard()
        time.sleep(max(0, 1.101 - (time.monotonic() - self.last_finished)))
        path, tr, params = {
            'estimate': (base.DATA_PATH, base.TR_ID, {'SHT_CD':code}),
            'identity': (IDENTITY_PATH, IDENTITY_TR, {'PDNO':code,'PRDT_TYPE_CD':'300'}),
            'price': (price.PRICE_PATH, price.PRICE_TR, price.price_params(code)),
        }[kind]
        self.calls.append(key)
        self.data_count += 1
        stem = kind + '/' + code
        request = dict(method='GET', path=path, tr_id=tr, params=params,
            security_code=code, started_at=base.now(), ordinal=self.data_count,
            redirects=False, retries=0, plan_sha256=self.plan['receipt_sha256'])
        self.save(stem+'-request.json', request)
        try:
            response = self.client.get(base.ORIGIN+path, params=params, headers={
                'authorization':'Bearer '+self.token, 'appkey':self.credentials.app_key,
                'appsecret':self.credentials.app_secret, 'tr_id':tr, 'custtype':'P',
                'tr_cont':'', 'accept':'application/json', 'content-type':'application/json',
                'user-agent':'ThesisMonitor/1.0'})
        except httpx.HTTPError:
            self.save(stem+'-receipt.json', dict(state='TRANSPORT_FAILURE', request=request, ended_at=base.now()))
            raise base.ProbeStop('TRANSPORT_FAILURE') from None
        finally:
            self.last_finished = time.monotonic()
        raw = response.content
        base.scan(raw, self.secrets, auth_fields=True)
        headers = {k:response.headers.get(k) for k in ('tr_cont','content-type','date','tr_id')}
        base.scan(json.dumps(headers).encode(), self.secrets)
        durable_bytes(self.output/(stem+'.body'), raw, exclusive=True)
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        state = 'COMPLETE'
        if response.status_code == 429 or payload.get('msg_cd') == 'EGW00201':
            state = 'KIS_RATE_LIMIT_GAP'
        elif response.status_code != 200:
            state = 'TRANSPORT_FAILURE'
        elif payload.get('rt_cd') != '0':
            state = 'PROVIDER_RETURN_ERROR'
        elif headers.get('tr_cont') not in {'','D','E'}:
            state = 'UNAVAILABLE_CONTINUATION_CONTRACT'
        receipt = dict(state=state, request=request, http_status=response.status_code,
            raw_sha256=sha256(raw).hexdigest(), bytes=len(raw), ended_at=base.now(),
            response_headers=headers, rt_cd=payload.get('rt_cd'), msg_cd=payload.get('msg_cd'), secret_scan='PASS')
        self.save(stem+'-receipt.json', receipt)
        if state != 'COMPLETE':
            raise base.ProbeStop(state)
        return Evidence(raw, receipt['raw_sha256']), receipt


def action_plan(rows, documentation):
    requests, inputs = [], {}
    if len(rows) != 8 or {r['security_code'] for r in rows} != set(SUBJECTS):
        raise ValueError('KR8_EXACT_ROW_SET_REQUIRED')
    for row in rows:
        eps, close = row['eps'], row.get('price')
        if eps['state'] != 'KIS_FY1_EPS_ESTIMATE_SNAPSHOT' or price.eps_receipt(eps) <= 0:
            continue
        if close is None:
            raise ValueError('ELIGIBLE_PRICE_MISSING')
        code = row['security_code']
        if eps['security_code'] != code:
            raise ValueError('EPS_ROW_IDENTITY_GAP')
        if price.current_fper(eps, close, None)['state'] != 'UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE':
            raise ValueError('PRICE_EPS_COMPATIBILITY_GAP')
        window = action.envelope(eps['estdate'], close['session_date'])
        inputs[code] = dict(eps_sha256=eps['receipt_sha256'], price_sha256=close['receipt_sha256'], guard_envelope=window)
        for variant in action.VARIANTS:
            route = action.route_contract(variant, documentation)
            requests.append(dict(subject=code, variant=variant, path=route['path'], tr_id=route['tr_id'],
                params=action.action_params(variant, code, window)))
    return dict(contract='kr8-fresh-exact-action-plan-v1', requests=requests, inputs=inputs,
        policy=action.POLICY, maximum_initial_calls=48, maximum_data_calls=60,
        maximum_continuation_calls=18, documentation_sha256=digest(documentation), retries=0)


def qualify_estimates(root, plan, *, inventories, docs, controls, scale):
    if plan != build_plan(generation=plan['generation_id'], as_of=plan['as_of'],
            securities=plan['securities'], static_hashes=plan['static_hashes']):
        raise ValueError('KIS_PLAN_REPRODUCTION_GAP')
    def read(name):
        return json.loads((root/name).read_bytes())
    rows = []
    for code in SUBJECTS:
        est, identity = evidence(root/f'estimate/{code}.body'), evidence(root/f'identity/{code}.body')
        receipt = read(f'estimate/{code}-receipt.json')
        for kind, ev, path, tr, params in (
            ('estimate', est, base.DATA_PATH, base.TR_ID, {'SHT_CD':code}),
            ('identity', identity, IDENTITY_PATH, IDENTITY_TR, {'PDNO':code,'PRDT_TYPE_CD':'300'}),
        ):
            sr = read(f'{kind}/{code}-receipt.json')
            price._source(ev, sr, path, tr, params)
            if (sr['request']['plan_sha256'] != plan['receipt_sha256']
                    or datetime.fromisoformat(sr['request']['started_at']) < datetime.fromisoformat(plan['as_of'])
                    or sr['response_headers']['tr_cont'] not in {'','D','E'}):
                raise ValueError('KIS_FRESH_RECEIPT_BINDING_GAP')
        inventory, projection = inventories[code]
        row = protocol.qualify(code, est, identity, inventory, plan['securities'][code]['corp_code'],
            date.fromisoformat(plan['as_of'][:10]), docs, controls, scale,
            receipt['ended_at'], date.fromisoformat(receipt['ended_at'][:10]))
        row['fiscal_projection'] = projection
        rows.append(row)
    return rows


def replay(root, plan, *, inventories, docs, controls, scale, price_docs, action_docs):
    rows = qualify_estimates(root, plan, inventories=inventories, docs=docs, controls=controls, scale=scale)
    def read(name):
        return json.loads((root/name).read_bytes())
    for row in rows:
        code = row['security_code']
        row['price'], row['action'] = None, None
        eps = row['eps']
        if eps['state'] == 'KIS_FY1_EPS_ESTIMATE_SNAPSHOT' and price.eps_receipt(eps) > 0:
            security = dict(plan['securities'][code], standard_code=eps['security']['standard_code'])
            if read(f'price/{code}-receipt.json')['request']['plan_sha256'] != plan['receipt_sha256']:
                raise ValueError('PRICE_FRESH_GENERATION_GAP')
            row['price'] = price.price_receipt(eps, security, evidence(root/f'price/{code}.body'),
                read(f'price/{code}-receipt.json'), plan['calendar'], price_docs)
    expected = action_plan(rows, action_docs)
    if read('action-plan.json') != expected:
        raise ValueError('ACTION_PLAN_REPRODUCTION_GAP')
    for row in rows:
        code, eps = row['security_code'], row['eps']
        if row['price'] is not None:
            families = {}
            for variant in action.VARIANTS:
                pages = []
                for i in range(1, 20):
                    p = root/f'actions/action/{code}/{variant}-{i}.body'
                    if not p.exists():
                        break
                    sr = read(f'actions/action/{code}/{variant}-{i}-receipt.json')
                    if (sr['request']['plan_sha256'] != digest(expected)
                            or datetime.fromisoformat(sr['request']['started_at']) < datetime.fromisoformat(plan['as_of'])):
                        raise ValueError('ACTION_FRESH_GENERATION_GAP')
                    pages.append((evidence(p), sr))
                families[variant] = action.family_receipt(variant, code,
                    eps['estdate'], row['price']['session_date'], pages, action_docs)
            row['action'] = action.compatibility_receipt(eps, row['price'], families)
        row['current_fper'] = price.current_fper(eps, row['price'], row['action'])
    return dict(contract=CONTRACT, generation_id=plan['generation_id'], scope='KR8_ONLY',
        rows=rows, rows_sha256=digest(rows), overall_direction_use=False)


class FreshActions(ExactActionProbe):
    def disk_guard(self):
        if shutil.disk_usage(self.output).free < 12 * 1024**3:
            raise base.ProbeStop('DISK_GAP')


def semantic_inputs(static, hashes):
    if {p.name: sha256(p.read_bytes()).hexdigest() for p in static.iterdir() if p.is_file()} != hashes:
        raise ValueError('KIS_STATIC_CONTRACT_HASH_GAP')
    return dict(docs=Documentation(evidence(static/'estimate-docs.json')),
        controls=[evidence(static/(code+'.body')) for code in base.STAGE_A],
        scale=json.loads((static/'protocol.json').read_bytes()),
        price_docs=json.loads((static/'price-docs.json').read_bytes()),
        action_docs=json.loads((static/'action-docs.json').read_bytes()))


def acquire(root, *, plan, credentials, inventories, static, guard):
    """One fresh acquisition. Transport failures terminate; no fallback/retry."""
    if plan != build_plan(generation=plan['generation_id'], as_of=plan['as_of'],
            securities=plan['securities'], static_hashes=plan['static_hashes']):
        raise ValueError('KIS_PLAN_REPRODUCTION_GAP')
    inputs = semantic_inputs(static, plan['static_hashes'])
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    class Guarded(httpx.HTTPTransport):
        def handle_request(self, request):
            guard()
            return super().handle_request(request)
    with httpx.Client(timeout=45, follow_redirects=False, transport=Guarded(retries=0)) as client:
        probe = FreshProbe(root, credentials, client, plan=plan)
        actions = None
        terminal = 'KIS_FRESH_ACQUISITION_COMPLETE_REPLAY_REQUIRED'
        try:
            guard()
            probe.save('plan.json', plan)
            probe.authenticate()
            for code in SUBJECTS:
                probe.fetch(code, 'estimate')
                probe.fetch(code, 'identity')
            rows = qualify_estimates(root, plan, inventories=inventories,
                **{k:inputs[k] for k in ('docs','controls','scale')})
            probe.save('estimate-qualification.json', rows)
            for row in rows:
                row['price'] = None
                eps, code = row['eps'], row['security_code']
                if eps['state'] == 'KIS_FY1_EPS_ESTIMATE_SNAPSHOT' and price.eps_receipt(eps) > 0:
                    ev, sr = probe.fetch(code, 'price', eps=eps)
                    security = dict(plan['securities'][code], standard_code=eps['security']['standard_code'])
                    row['price'] = price.price_receipt(eps, security, ev, sr, plan['calendar'], inputs['price_docs'])
            ap = action_plan(rows, inputs['action_docs'])
            probe.save('action-plan.json', ap)
            (root/'actions').mkdir()
            actions = FreshActions(root/'actions', credentials, client, plan=ap, documentation=inputs['action_docs'])
            # Reuse the same in-memory token; neither credentials nor token are archived.
            actions.token, actions.secrets = probe.token, probe.secrets
            actions.last_finished = probe.last_finished
            for request in ap['requests']:
                cursor, page = '', 1
                while True:
                    guard()
                    sr = actions.fetch(request, cursor, page)
                    if sr['next_cursor'] is None or actions.extra_pages >= 18:
                        break
                    cursor, page = sr['next_cursor'], page + 1
            probe.save('acquired-rows.json', rows)
        except (base.ProbeStop, SemanticGap, ValueError) as exc:
            terminal = str(exc)
        except Exception as exc:
            terminal = 'INTERNAL_GAP_' + type(exc).__name__
        finally:
            counters = dict(authentication=probe.auth_count, basic_data=probe.data_count,
                estimates=sum(k=='estimate' for _,k in probe.calls), identities=sum(k=='identity' for _,k in probe.calls),
                prices=sum(k=='price' for _,k in probe.calls), actions=actions.counters() if actions else None,
                total_data=probe.data_count+(actions.data_count if actions else 0),
                retries=0, us_calls=0, models=0, telegram=0, production_mutations=0)
            probe.save('counters.json', counters)
            probe.save('terminal.json', dict(state=terminal, ended_at=base.now()))
            probe.token = None
            if actions:
                actions.token = None
    return terminal
