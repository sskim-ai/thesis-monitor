"""One local run ledger over existing OperatorApproval, not a new consent token.

It counts intents before I/O. Source quality, account STOP/Lane and original
Worker/Stage owners remain separate mandatory checks at their original ports.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path

import httpx

from app.services import prospective_class_c_owner as registration
from app.services.unified_snapshot_contract import digest, encoded

STATES = ('NO_APPROVAL', 'APPROVED_FROZEN_RUN', 'REGISTRATION_CAPTURED',
          'SOURCE_CAPTURED', 'SOURCE_OWNED', 'MODEL_BUDGETED', 'RENDERED_NO_SEND', 'STOPPED_NO_SEND')


class SelectedRunLedger:
    def __init__(self, *, path, approval, master_id, children, provider_caps,
                 max_http, max_models, database_identity, onboarding=False, database_budget=None,
                 wallclock_seconds_max=None, runtime_cap=None):
        decision = registration._approval(approval)
        if (not master_id or set(children) != {'us', 'kr'}
                or len({c['generation'] for c in children.values()}) != 2
                or any(c['generation'] == master_id for c in children.values())
                or any(not c['subjects'] or len(set(c['subjects'])) != len(c['subjects']) for c in children.values())
                or sorted(t for c in children.values() for t in c['subjects']) != sorted(decision.subjects)
                or any(type(n) is not int or n < 0 for n in (*provider_caps.values(), max_http, max_models))
                or (runtime_cap is None and sum(provider_caps.values()) > max_http)):
            raise ValueError('selected_frozen_run_scope_invalid')
        self.approval = approval
        self.path = Path(path)
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError('selected_run_ledger_symlink')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.identity = dict(contract='selected-run-budget-ledger-v1', master_id=master_id,
            approval_event=decision.event_id, approval_sha256=digest(decision.model_dump(mode='json')),
            authorized_at=decision.effective_at.isoformat(), expires_at=decision.expires_at.isoformat(),
            children=deepcopy(children), provider_caps=dict(provider_caps), max_http=max_http,
            max_models=max_models, database_identity=database_identity, retry=0, send=False)
        if onboarding:
            from app.services.vnext_execution_profile import SOL_HIGH_V1
            slots = {m: {t: ['CORE', 'DECISION'] for t in c['subjects']} for m,c in children.items()}
            maximum = 2 * sum(len(c['subjects']) for c in children.values())
            if maximum > max_models:
                raise ValueError('selected_onboarding_model_reserve_exceeds_cap')
            self.identity['onboarding'] = dict(slots=slots, max_models=maximum,
                profile=SOL_HIGH_V1.contract, model=SOL_HIGH_V1.model, effort=SOL_HIGH_V1.effort)
        if database_budget is not None:
            if (not onboarding or not database_budget or (runtime_cap is None and sum(provider_caps.values()) != max_http) or any(
                    type(n) is not int or n < 0 for n in database_budget.values())):
                raise ValueError('selected_finite_database_budget_required')
            self.identity['database_budget'] = dict(database_budget)
        if wallclock_seconds_max is not None:
            if type(wallclock_seconds_max) is not int or not 1 <= wallclock_seconds_max <= 86400:
                raise ValueError('selected_finite_wallclock_max_required')
            self.identity['wallclock_seconds_max'] = wallclock_seconds_max
        if runtime_cap is not None:
            if not runtime_cap.get('endpoints') or max_models>14:
                raise ValueError('runtime_cap_endpoints_and_fourteen_model_max_required')
            self.identity['runtime_cap'] = deepcopy(runtime_cap)
        self._event('OPEN')
        registration.bind_run_stop(approval,self.stop)

    def _external(self):
        now = datetime.now(timezone.utc)
        maximum = self.identity.get('wallclock_seconds_max')
        if maximum is not None and now >= datetime.fromisoformat(self.identity['authorized_at'])+timedelta(seconds=maximum):
            raise ValueError('selected_campaign_wallclock_exhausted')
        if self.approval is None:
            if not datetime.fromisoformat(self.identity['authorized_at'])<=now<datetime.fromisoformat(self.identity['expires_at']):
                raise ValueError('selected_worker_frozen_approval_expired')
            return
        decision = registration._approval(self.approval)
        if digest(decision.model_dump(mode='json')) != self.identity['approval_sha256']:
            raise ValueError('selected_run_approval_changed')

    def worker_binding(self):
        self._external()
        if self.state()['state']=='STOPPED_NO_SEND':raise ValueError('selected_run_stopped')
        return dict(path=str(self.path.absolute()),identity_sha256=digest(self.identity))

    @classmethod
    def attach_worker(cls, binding):
        """Existing trusted worker frame pins this budget file; no new token.

        Backend revoke appends STOP to this same locked file before completing.
        The worker cannot issue approvals, refreeze plans or refill counters.
        """
        path=Path(binding['path'])
        if not path.is_absolute() or any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file():
            raise ValueError('selected_worker_existing_budget_required')
        with path.open('rb') as f:first=json.loads(f.readline())
        if digest(first['identity'])!=binding['identity_sha256']:
            raise ValueError('selected_worker_budget_identity_changed')
        instance=object.__new__(cls)
        instance.path,instance.identity,instance.approval=path,first['identity'],None
        instance._external()
        instance._event('OPEN')
        return instance

    def _event(self, event, **value):
        with os.fdopen(os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600), 'r+b') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            raw = f.read()
            if raw and not raw.endswith(b'\n'):
                raise ValueError('selected_run_torn_intent_no_replay')
            state = dict(state='APPROVED_FROZEN_RUN', registration=None, registration_receipt=None, db_intent=False,
                db_connection_attempts=0, preopen_corrections=0, reserved_connection_unentered=False,
                reserved_connection_continued=False,
                plans={}, sources={}, captures=[], models={}, used={}, pending=None, completed=[],
                http={}, http_total=0, source_http_total=0, model_total=0, db_select_reserved=0, db_select_actual=0,
                onboarding_http_plans={}, onboarding_model_total=0, monitoring_model_total=0,
                onboarding_accepted={}, onboarding_failed={}, database_used={}, wire_fingerprints=[],runtime=None)
            previous, count = None, 0
            for line in raw.splitlines():
                row = json.loads(line)
                pin = row.pop('sha256')
                if (row['identity'] != self.identity or row['previous'] != previous
                        or row['sequence'] != count or digest(row) != pin):
                    raise ValueError('selected_run_ledger_identity_or_chain_drift')
                self._apply(state, row['event'], row['value'])
                previous, count = pin, count + 1
            if event != 'OPEN' or not raw:
                self._apply(state, event, value)
                row = dict(identity=self.identity, sequence=count, previous=previous, event=event, value=value,
                    recorded_at=datetime.now(timezone.utc).isoformat())
                row['sha256'] = digest(row)
                f.write(encoded(row) + b'\n')
                f.flush()
                os.fsync(f.fileno())
            return state

    def _apply(self, s, event, v):
        children = self.identity['children']
        if event == 'OPEN': return
        if event.startswith('PHYSICAL_'):
            from app.services.campaign_runtime_cap import runtime_state,apply_runtime_event
            if not self.identity.get('runtime_cap'):
                raise ValueError('runtime_cap_not_enabled')
            if s['runtime'] is None:s['runtime']=runtime_state()
            apply_runtime_event(s['runtime'],event,v,self.identity)
            s['http_total']=s['runtime']['total']
            s['http']=dict(s['runtime']['providers'])
            return
        if event == 'DB_AUDIT':
            if (not s['db_connection_attempts'] or v['connections'] != s['db_connection_attempts']
                    or not 0 <= v['completed'] <= v['attempted'] <= s['db_select_reserved']):
                raise ValueError('selected_database_usage_audit_gap')
            s['db_select_actual'] = v['attempted']
            return
        if event == 'STOP':
            s['state'] = 'STOPPED_NO_SEND'
            return
        if event == 'PREOPEN_CORRECTION':
            if (s['state'] != 'STOPPED_NO_SEND' or not s['db_intent'] or s['registration'] is not None
                    or s['db_connection_attempts'] > int(v.get('reserved_argument_failure') is True) or s['preopen_corrections']
                    or v['observed_connections'] != 0 or v['observed_selects'] != 0):
                raise ValueError('selected_cannot_repair_consumed_database_attempt')
            # No counter or intent is cleared. A local Python argument error
            # before connect is not a second physical database attempt.
            s.update(state='APPROVED_FROZEN_RUN', preopen_corrections=1,
                reserved_connection_unentered=bool(s['db_connection_attempts']))
            return
        if s['state'] in ('STOPPED_NO_SEND', 'RENDERED_NO_SEND'):
            raise ValueError('selected_run_terminal_no_new_work')
        if event == 'ONBOARDING_HTTP_PLAN':
            m = v['market']
            if (not self.identity.get('onboarding') or m not in children
                    or m in s['onboarding_http_plans'] or s['http_total']
                    or not v['logical_ids'] or len(set(v['logical_ids'])) != len(v['logical_ids'])):
                raise ValueError('selected_onboarding_http_plan_not_frozen')
            s['onboarding_http_plans'][m] = v
        elif event == 'ONBOARDING_DB':
            operation = v['operation']
            maximum = self.identity.get('database_budget', {}).get(operation, 0)
            used = s['database_used'].get(operation, 0)
            if type(v['units']) is not int or v['units'] < 1 or used+v['units'] > maximum:
                raise ValueError('selected_database_operation_budget_exhausted')
            s['database_used'][operation] = used+v['units']
        elif event == 'ONBOARDING_INTENT':
            config = self.identity.get('onboarding', {})
            m, ticker, stage, key = (v[k] for k in ('market', 'ticker', 'stage', 'key'))
            subject = m+':'+ticker
            slots = config.get('slots', {}).get(m, {}).get(ticker, ())
            if (s['pending'] or key in s['used'] or stage not in slots
                    or subject in s['onboarding_failed']
                    or s['state'] not in ('APPROVED_FROZEN_RUN', 'REGISTRATION_CAPTURED')
                    or s['onboarding_model_total'] >= config.get('max_models', 0)
                    or s['model_total'] >= self.identity['max_models']
                    or (stage == 'DECISION' and 'CORE' not in s['onboarding_accepted'].get(subject, {}))):
                raise ValueError('selected_onboarding_duplicate_dependency_or_budget')
            s['model_total'] += 1
            s['onboarding_model_total'] += 1
            s['used'][key] = v
            s['pending'] = key
        elif event == 'ONBOARDING_RESULT':
            key = v['key']
            call = s['used'].get(key, {})
            if s['pending'] != key or not key.startswith('ONBOARDING:'):
                raise ValueError('selected_onboarding_result_without_intent')
            s['pending'] = None
            s['completed'].append(key)
            subject = call['market']+':'+call['ticker']
            if v['ok']:
                s['onboarding_accepted'].setdefault(subject, {})[call['stage']] = v['output_sha256']
            else:
                # Validation failure is subject-local; consumed slots never refill.
                s['onboarding_failed'][subject] = v
        elif event == 'ONBOARDING_SUBJECT_FAILED':
            m, ticker = v['market'], v['ticker']
            if (not self.identity.get('onboarding') or m not in children
                    or ticker not in children[m]['subjects'] or s['pending']):
                raise ValueError('selected_onboarding_failure_scope_invalid')
            s['onboarding_failed'][m+':'+ticker] = v
        elif event == 'DB_INTENT':
            if s['db_intent']: raise ValueError('selected_registration_already_attempted')
            s.update(db_intent=True, db_select_reserved=5)
        elif event == 'DB_OPEN':
            if not s['db_intent'] or s['db_connection_attempts'] or s['registration'] is not None:
                raise ValueError('selected_database_connection_already_attempted')
            s['db_connection_attempts'] = 1
        elif event == 'DB_OPEN_RESERVED_CONTINUATION':
            if (s['state']!='APPROVED_FROZEN_RUN' or not s['reserved_connection_unentered']
                    or s['reserved_connection_continued'] or s['registration'] is not None
                    or s['db_connection_attempts']!=1):
                raise ValueError('selected_reserved_connection_not_available')
            s['reserved_connection_continued']=True
        elif event == 'REGISTRATION':
            if not s['db_intent'] or s['registration'] is not None or not 1 <= v['selects'] <= 5:
                raise ValueError('selected_registration_receipt_gap')
            if digest(v['receipt']) != v['sha256']:
                raise ValueError('selected_registration_receipt_hash_drift')
            s.update(registration=v['sha256'], registration_receipt=v['receipt'],
                db_select_actual=v['selects'], state='REGISTRATION_CAPTURED')
        elif event == 'PLAN':
            m = v['market']
            if s['registration'] is None or m not in children or m in s['plans'] or s['source_http_total']:
                raise ValueError('selected_plan_must_freeze_once_before_http')
            s['plans'][m] = v['sha256']
        elif event == 'CAPTURE':
            m = v['market']
            if set(s['plans']) != set(children) or m in s['captures'] or s['pending']:
                raise ValueError('selected_source_capture_gap')
            s['captures'].append(m)
            if set(s['captures']) == set(children): s['state'] = 'SOURCE_CAPTURED'
        elif event == 'SOURCE':
            m = v['market']
            if m not in s['captures'] or m in s['sources']:
                raise ValueError('selected_source_admission_gap')
            s['sources'][m] = v['sha256']
            if set(s['sources']) == set(children): s['state'] = 'SOURCE_OWNED'
        elif event == 'MODEL_PLAN':
            m = v['market']
            if set(s['sources']) != set(children) or m in s['models'] or s['monitoring_model_total']:
                raise ValueError('selected_model_source_or_freeze_gap')
            s['models'][m] = v
            if sum(r['slots'] for r in s['models'].values()) + self.identity.get('onboarding', {}).get('max_models', 0) > self.identity['max_models']:
                raise ValueError('selected_model_plan_over_cap')
            if set(s['models']) == set(children): s['state'] = 'MODEL_BUDGETED'
        elif event == 'INTENT':
            key, kind, m = v['key'], v['kind'], v['market']
            if s['pending'] or key in s['used'] or m not in children:
                raise ValueError('selected_run_duplicate_or_parallel_intent')
            if kind == 'HTTP':
                p = v['provider']
                if v.get('phase') == 'ONBOARDING':
                    plan = s['onboarding_http_plans'].get(m, {})
                    scope_ok = (v['plan'] == plan.get('sha256') and v['logical_id'] in plan.get('logical_ids', ())
                        and s['state'] in ('APPROVED_FROZEN_RUN', 'REGISTRATION_CAPTURED'))
                else:
                    scope_ok = (set(s['plans']) == set(children) and m not in s['captures']
                        and v['plan'] == s['plans'][m])
                if (not scope_ok or (not self.identity.get('runtime_cap') and (
                        s['http_total'] >= self.identity['max_http']
                        or s['http'].get(p, 0) >= self.identity['provider_caps'].get(p, 0)))):
                    raise ValueError('selected_physical_http_scope_or_budget')
                fingerprint = v.get('request_sha256')
                if fingerprint and (m, fingerprint) in s['wire_fingerprints']:
                    raise ValueError('selected_physical_request_already_attempted')
                if fingerprint:
                    s['wire_fingerprints'].append((m, fingerprint))
                if not self.identity.get('runtime_cap'):
                    s['http'][p] = s['http'].get(p, 0) + 1
                    s['http_total'] += 1
                if v.get('phase') != 'ONBOARDING':
                    s['source_http_total'] += 1
            elif kind == 'MODEL':
                if (s['state'] != 'MODEL_BUDGETED' or v['plan'] != s['models'][m]['sha256']
                        or v['slot'] not in s['models'][m]['slot_ids']
                        or s['model_total'] >= self.identity['max_models']):
                    raise ValueError('selected_model_scope_or_budget')
                s['model_total'] += 1
                s['monitoring_model_total'] += 1
            else: raise ValueError('selected_external_kind')
            s['used'][key] = v
            s['pending'] = key
        elif event == 'RESULT':
            if s['pending'] != v['key']: raise ValueError('selected_result_without_intent')
            s['pending'] = None
            s['completed'].append(v['key'])
            if not v['ok']: s['state'] = 'STOPPED_NO_SEND'
        elif event == 'RENDER':
            if (s['state'] != 'MODEL_BUDGETED' or s['pending']
                        or s['monitoring_model_total'] != sum(r['slots'] for r in s['models'].values())):
                raise ValueError('selected_render_incomplete')
            s['state'] = 'RENDERED_NO_SEND'
        else: raise ValueError('selected_unknown_run_event')

    def state(self):
        return self._event('OPEN')

    def stop(self, reason):
        return self._event('STOP', reason=reason)

    def before_registration(self, *, approval, permission, generations):
        self._external()
        if (approval is not self.approval or permission.event_id != self.identity['approval_event']
                or set(permission.subjects) != {t for c in self.identity['children'].values() for t in c['subjects']}
                or generations != {m:c['generation'] for m,c in self.identity['children'].items()}
                or dict(path=str(permission.database), device=permission.device, inode=permission.inode) != self.identity['database_identity']):
            raise ValueError('selected_database_frozen_scope_changed')
        permission.require()
        state = self.state()
        if state['preopen_corrections'] and state['state']=='APPROVED_FROZEN_RUN':
            return
        self._event('DB_INTENT')

    def before_database_open(self):
        self._external()
        state=self.state()
        self._event('DB_OPEN_RESERVED_CONTINUATION' if state['reserved_connection_unentered'] else 'DB_OPEN')

    def correct_preopen_wiring(self, *, evidence_sha256, observed_connections, observed_selects,
                              reserved_argument_failure=False):
        self._external()
        self._event('PREOPEN_CORRECTION', evidence_sha256=evidence_sha256,
            observed_connections=observed_connections, observed_selects=observed_selects,
            reserved_argument_failure=reserved_argument_failure is True)

    def registration_captured(self, receipt):
        selects = sum(r['operation'] == 'SELECT' for r in receipt['query_trace'])
        if (receipt['permission_event'] != self.identity['approval_event'] or receipt['total_changes'] != 0
                or receipt['sqlite_mode'] != 'ro' or receipt['query_only'] is not True):
            raise ValueError('selected_original_readonly_receipt_required')
        self._event('REGISTRATION', sha256=digest(receipt), selects=selects, receipt=receipt)

    def bind_source_plan(self, market, plan):
        c = self.identity['children'][market]
        if (plan.market != market or plan.generation_id != c['generation'] or tuple(plan.subjects) != tuple(c['subjects'])
                or any(d.transient_retry_max != 0 for d in plan.descriptors)):
            raise ValueError('selected_request_scope_changed')
        self._event('PLAN', market=market, sha256=plan.plan_sha256)

    def source_captured(self, market):
        self._event('CAPTURE', market=market)

    def source_owned(self, child):
        child.verify()
        c = self.identity['children'][child.market]
        a = child.owner.acceptance()
        state = self.state()
        if (a['generation_id'] != c['generation'] or a['subjects'] != list(c['subjects'])
                or a['registration_capture_receipt_sha256'] != state['registration']
                or a['request_plan_sha256'] != state['plans'].get(child.market)):
            raise ValueError('selected_admitted_child_scope_changed')
        self._event('SOURCE', market=child.market, sha256=digest(a))

    def bind_model_plan(self, child):
        child.verify()
        if digest(child.owner.acceptance()) != self.state()['sources'].get(child.market):
            raise ValueError('selected_model_admitted_source_changed')
        self._event('MODEL_PLAN', market=child.market, sha256=child.plan.sha256, slots=len(child.plan.slots),
            slot_ids=[s.slot_id for s in child.plan.slots])

    def before_http(self, *, market, provider, logical_id, plan_sha256):
        self._external_http(require_registration=True)
        key = f'HTTP:{market}:{logical_id}'
        self._event('INTENT', key=key, kind='HTTP', market=market, provider=provider, plan=plan_sha256)
        return key

    def before_model(self, plan, slot):
        self._external()
        if (self.state().get('runtime') or {}).get('first_external_failure') is not None:
            raise ValueError('selected_external_failure_blocks_model')
        key = f'MODEL:{plan.cohort.run_id}:{slot["slot_id"]}'
        self._event('INTENT', key=key, kind='MODEL', market=slot['market'], slot=slot['slot_id'], plan=plan.sha256)
        return key

    def before_onboarding_model(self, *, market, ticker, stage, payload_sha256):
        self._external()
        if (self.state().get('runtime') or {}).get('first_external_failure') is not None:
            raise ValueError('selected_external_failure_blocks_model')
        key = f'ONBOARDING:{self.identity["children"][market]["generation"]}:{ticker}:{stage}'
        self._event('ONBOARDING_INTENT', key=key, market=market, ticker=ticker,
            stage=stage, payload_sha256=payload_sha256)
        return key

    def onboarding_model_result(self, key, *, ok, output_sha256, error_type=None):
        self._event('ONBOARDING_RESULT', key=key, ok=ok is True,
            output_sha256=output_sha256, error_type=error_type)

    def fail_onboarding_subject(self, *, market, ticker, error_type):
        self._event('ONBOARDING_SUBJECT_FAILED', market=market, ticker=ticker, error_type=error_type)

    def bind_onboarding_http_plan(self, *, market, plan_sha256, logical_ids):
        self._external()
        self._event('ONBOARDING_HTTP_PLAN', market=market, sha256=plan_sha256, logical_ids=list(logical_ids))

    def _external_http(self, *, require_registration):
        self._external()
        receipt = self.state()['registration_receipt']
        if ((require_registration and receipt is None) or (receipt is not None and
                datetime.now(timezone.utc) >= datetime.fromisoformat(receipt['cutoff'])+timedelta(hours=1))):
            raise ValueError('selected_original_registration_http_window_expired')

    def before_onboarding_database(self, operation, *, units=1):
        self._external()
        return self._event('ONBOARDING_DB', operation=operation, units=units)

    def before_onboarding_http(self, *, market, provider, logical_id, plan_sha256, request_sha256=None):
        self._external_http(require_registration=False)
        key = f'HTTP:ONBOARDING:{market}:{logical_id}'
        self._event('INTENT', key=key, kind='HTTP', phase='ONBOARDING', market=market,
            provider=provider, plan=plan_sha256, logical_id=logical_id, request_sha256=request_sha256)
        return key

    def result(self, key, *, ok):
        self._event('RESULT', key=key, ok=ok is True)

    def rendered(self, master, results):
        result = master.combine(results)
        self._event('RENDER', messages_sha256=result['messages_sha256'])
        return result


class OnboardingCampaignTransport(httpx.AsyncBaseTransport):
    """Count onboarding wires through existing provider transport-injection ports."""
    def __init__(self, *, ledger, market, plan_sha256, routes, inner):
        frozen = ledger.state()['onboarding_http_plans'].get(market, {})
        route_ids = [identity for r in routes for identity in self._ids(r)]
        if (frozen.get('sha256') != plan_sha256
                or set(route_ids) != set(frozen.get('logical_ids', []))
                or len(route_ids) != len(frozen.get('logical_ids', []))):
            raise ValueError('onboarding_http_exact_frozen_routes_required')
        self.ledger, self.market, self.plan = ledger, market, plan_sha256
        self.routes, self.inner = deepcopy(routes), inner

    @staticmethod
    def _ids(route):
        maximum = route.get('maximum_attempts', 1)
        if type(maximum) is not int or not 1 <= maximum <= 1000:
            raise ValueError('onboarding_http_finite_route_cap_required')
        return [route['logical_id'] if maximum == 1 else route['logical_id']+':'+str(i)
                for i in range(maximum)]

    async def handle_async_request(self, request):
        matches = [route for route in self.routes if
            (request.method, request.url.host) == (route['method'], route['host'])
            and (request.url.path == route.get('path') or (
                route.get('path_prefix') and request.url.path.startswith(route['path_prefix'])))
            and all(request.url.params.get(key) == value for key,value in route.get('public_params', {}).items())]
        if len(matches) != 1:
            raise ValueError('onboarding_http_outside_frozen_plan')
        route = matches[0]
        used = self.ledger.state()['used']
        identity = next((i for i in self._ids(route)
            if f'HTTP:ONBOARDING:{self.market}:{i}' not in used), None)
        if identity is None:
            raise ValueError('onboarding_http_finite_route_exhausted')
        # Persist public request identity, never credentials, headers or auth body.
        from app.services.unified_run_artifacts import SECRET_KEY
        public = sorted((k,v) for k,v in request.url.params.multi_items() if not SECRET_KEY.search(k))
        fingerprint = digest((request.method,request.url.host,request.url.path,public))
        key = self.ledger.before_onboarding_http(market=self.market, provider=route['provider'],
            logical_id=identity, plan_sha256=self.plan, request_sha256=fingerprint)
        try:
            response = await self.inner.handle_async_request(request)
        except BaseException:
            self.ledger.result(key, ok=False)
            raise
        self.ledger.result(key, ok=200 <= response.status_code < 300)
        return response

    async def aclose(self):
        # Existing short-lived provider clients do not own the campaign wire.
        pass
