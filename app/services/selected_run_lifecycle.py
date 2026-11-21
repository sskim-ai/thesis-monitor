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
                 wallclock_seconds_max=None, runtime_cap=None, onboarding_subjects=None,
                 staged_markets=False, capture_max_private_export_bytes=None, timeout_retry_cap=0, b2_retry_policy=None):
        decision = registration._approval(approval)
        from app.services.unified_stock_acquisition import UNIVERSE
        single_us = (staged_markets is True and set(children) == {'us'}
                     and tuple(children['us']['subjects']) == UNIVERSE['us'])
        if (not master_id or not (set(children) == {'us', 'kr'} or single_us)
                or len({c['generation'] for c in children.values()}) != len(children)
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
        if decision.routine_us_no_send_source_seconds is not None:
            if set(children) != {'us'} or onboarding or wallclock_seconds_max is None:
                raise ValueError('selected_routine_us_no_send_source_scope')
            self.identity['routine_us_no_send_source_seconds'] = decision.routine_us_no_send_source_seconds
        if type(staged_markets) is not bool or (staged_markets and runtime_cap is None):
            raise ValueError('selected_staged_runtime_cap_required')
        if staged_markets:
            self.identity['staged_markets'] = True
        if (type(timeout_retry_cap) is not int or timeout_retry_cap not in (0,1,2)
                or timeout_retry_cap and (not staged_markets or onboarding
                    or wallclock_seconds_max is None)):
            raise ValueError('selected_timeout_retry_requires_finite_research_only_run')
        if timeout_retry_cap:
            self.identity['timeout_retry_cap'] = timeout_retry_cap
            if max_http:
                if not provider_caps or not any(provider_caps.values()):
                    raise ValueError('selected_fresh_timeout_retry_provider_caps_required')
                self.identity['fresh_timeout_retry_market'] = 'us'
        if b2_retry_policy is not None:
            from app.services.model_timeout_retry import retry_policy_limits
            _,retry_reserves,retry_maximum = retry_policy_limits(b2_retry_policy)
            if (timeout_retry_cap
                    or not staged_markets or onboarding or set(children) != {'us'}
                    or wallclock_seconds_max is None or max_models != retry_maximum):
                raise ValueError('selected_b2_retry_new_us_campaign_required')
            self.identity['b2_retry_policy'] = b2_retry_policy
            if max_http:
                if not provider_caps or not any(provider_caps.values()):
                    raise ValueError('selected_fresh_timeout_retry_provider_caps_required')
                self.identity['fresh_timeout_retry_market'] = 'us'
        if capture_max_private_export_bytes is not None:
            from app.services.minimal_class_c_export import validate_export_limit
            self.identity['capture_max_private_export_bytes'] = validate_export_limit(capture_max_private_export_bytes)
        if onboarding:
            from app.services.vnext_execution_profile import SOL_HIGH_V1
            selected = {m:list(c['subjects']) for m,c in children.items()} if onboarding_subjects is None else onboarding_subjects
            if (set(selected) != set(children) or any(len(set(ts)) != len(ts)
                    or not set(ts) <= set(children[m]['subjects']) for m,ts in selected.items())):
                raise ValueError('selected_onboarding_subject_subset_required')
            slots = {m: {t: ['CORE', 'DECISION'] for t in ts} for m,ts in selected.items()}
            maximum = 2 * sum(len(ts) for ts in selected.values())
            if maximum > max_models:
                raise ValueError('selected_onboarding_model_reserve_exceeds_cap')
            self.identity['onboarding'] = dict(slots=slots, max_models=maximum,
                profile=SOL_HIGH_V1.contract, model=SOL_HIGH_V1.model, effort=SOL_HIGH_V1.effort)
        elif onboarding_subjects is not None:
            raise ValueError('selected_onboarding_configuration_required')
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
            maximum = 14
            if staged_markets:
                from app.services.unified_stock_acquisition import UNIVERSE
                if any(not set(c['subjects']) <= set(UNIVERSE[m]) for m,c in children.items()):
                    raise ValueError('selected_staged_original_roster_required')
                monitoring = sum(1+3*((len(c['subjects'])+2)//3)+len(c['subjects']) for c in children.values())
                maximum = min(88, monitoring+self.identity.get('onboarding',{}).get('max_models',0)) + (retry_reserves if b2_retry_policy else timeout_retry_cap)
            if not runtime_cap.get('endpoints') or max_models>maximum:
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
            state.update(active_markets=list(self.identity['children']), registrations={},
                registration_pending=False, registration_markets=[], selected_subjects={}, rendered_markets={}, failed_markets={},
                registration_revalidations={}, timeout_attempts={}, timed_out={}, timeout_exhausted=[], retry_used=0)
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
                content = encoded(row) + b'\n'
                from app.services.research_artifact_budget import active_budget
                if (budget := active_budget()) is not None:
                    budget.before_write(self.path, len(content), role='result')
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            return state

    def _apply(self, s, event, v):
        children = self.identity['children']
        staged = self.identity.get('staged_markets', False)
        required = set(s['active_markets']) if staged else set(children)
        if event == 'OPEN': return
        if event.startswith('PHYSICAL_'):
            from app.services.campaign_runtime_cap import runtime_state,apply_runtime_event
            if not self.identity.get('runtime_cap'):
                raise ValueError('runtime_cap_not_enabled')
            if s['runtime'] is None:s['runtime']=runtime_state()
            if event == 'PHYSICAL_INTENT' and v.get('optional_news'):
                pending = s['used'].get(s['pending'], {})
                if (v['optional_news']['plan_sha256'] != s['plans'].get(v['market'])
                        or pending.get('key') != 'HTTP:us:' + v['optional_news']['logical_id']
                        or pending.get('provider') != v['provider']):
                    raise ValueError('selected_optional_news_pending_plan_mismatch')
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
            markets = v.get('markets', list(children))
            if (market := self.identity.get('fresh_timeout_retry_market')) and markets != [market]:
                raise ValueError('selected_fresh_timeout_retry_market_scope')
            if staged:
                if (len(markets)!=1 or not set(markets)<=set(children) or s['registration_pending'] or s['pending']
                        or any(m in s['registrations'] for m in markets)
                        or any(m not in s['rendered_markets'] and m not in s['failed_markets'] for m in s['registrations'])):
                    raise ValueError('selected_registration_already_attempted')
                s.update(active_markets=list(markets), registration_markets=list(markets),
                    registration_pending=True, db_intent=True, registration=None, registration_receipt=None,
                    db_select_reserved=s['db_select_reserved']+5, state='APPROVED_FROZEN_RUN')
            else:
                if s['db_intent']: raise ValueError('selected_registration_already_attempted')
                s.update(db_intent=True, db_select_reserved=5)
        elif event == 'DB_REVALIDATE':
            m=v['market']
            if (self.identity.get('fresh_timeout_retry_market') or not staged
                    or m not in s['failed_markets'] or m not in s['registrations']
                    or m in s['registration_revalidations'] or m in s['sources'] or m in s['models']
                    or s['registration_pending'] or s['pending']
                    or v['previous_capture_sha256']!=s['registrations'][m]['sha256']
                    or not isinstance(v['requested_work_order_sha256'],str)
                    or len(v['requested_work_order_sha256'])!=64):
                raise ValueError('selected_explicit_single_registration_revalidation_required')
            s['registration_revalidations'][m]=dict(previous=s['registrations'][m],**v)
            s.update(active_markets=[m],registration_markets=[m],registration_pending=True,
                db_intent=True,registration=None,registration_receipt=None,
                db_select_reserved=s['db_select_reserved']+5,state='APPROVED_FROZEN_RUN')
        elif event == 'DB_OPEN':
            if (not s['db_intent'] or s['registration'] is not None or
                    (s['db_connection_attempts'] >= len(s['registrations'])+1+len(s['registration_revalidations'])
                     if staged else s['db_connection_attempts'])):
                raise ValueError('selected_database_connection_already_attempted')
            s['db_connection_attempts'] += 1
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
                db_select_actual=s['db_select_actual']+v['selects'] if staged else v['selects'], state='REGISTRATION_CAPTURED')
            if staged:
                for market in s['registration_markets']:
                    s['registrations'][market] = dict(sha256=v['sha256'],receipt=v['receipt'])
                s['registration_pending'] = False
        elif event == 'REGISTERED_SUBJECTS':
            market, subjects = v['market'], v['subjects']
            if (not staged or market not in required or market not in s['registrations']
                    or market in s['selected_subjects'] or not subjects or len(set(subjects))!=len(subjects)
                    or not set(subjects)<=set(children[market]['subjects'])
                    or v['capture_sha256']!=s['registrations'][market]['sha256']):
                raise ValueError('selected_current_registered_subset_required')
            s['selected_subjects'][market] = list(subjects)
        elif event == 'PLAN':
            m = v['market']
            if (s['registration'] is None or m not in required or m in s['plans']
                    or (staged and m not in s['selected_subjects']) or (not staged and s['source_http_total'])):
                raise ValueError('selected_plan_must_freeze_once_before_http')
            s['plans'][m] = v['sha256']
        elif event == 'CAPTURE':
            m = v['market']
            if (not required<=set(s['plans']) or m not in required or m in s['captures'] or s['pending']
                    or (self.identity.get('fresh_timeout_retry_market') and (s['runtime'] or {}).get('pending'))):
                raise ValueError('selected_source_capture_gap')
            s['captures'].append(m)
            if required<=set(s['captures']): s['state'] = 'SOURCE_CAPTURED'
        elif event == 'SOURCE':
            m = v['market']
            if m not in s['captures'] or m in s['sources']:
                raise ValueError('selected_source_admission_gap')
            s['sources'][m] = v['sha256']
            if required<=set(s['sources']): s['state'] = 'SOURCE_OWNED'
        elif event == 'MODEL_PLAN':
            m = v['market']
            if (not required<=set(s['sources']) or m not in required or m in s['models']
                    or (not staged and s['monitoring_model_total'])):
                raise ValueError('selected_model_source_or_freeze_gap')
            if self.identity.get('timeout_retry_cap') and (m!='us' or v.get('inherited_market_slot')
                    or v['slots']+self.identity['timeout_retry_cap'] != self.identity['max_models']
                    or set(v.get('slot_stages',{})) != set(v['slot_ids'])):
                raise ValueError('selected_model_retry_plan_scope')
            if self.identity.get('b2_retry_policy'):
                from app.services.model_timeout_retry import validate_b2_retry_binding
                retry = validate_b2_retry_binding(v['b2_retry_binding'])
                if (m != 'us' or retry['policy'] != self.identity['b2_retry_policy'] or v.get('inherited_market_slot') or retry['plan_sha256'] != v['sha256']
                        or v['slots'] != retry['base_slots'] or self.identity['max_models'] != retry['maximum']
                        or v['slot_stages'] != retry['slot_stages'] or set(v['slot_ids']) != set(retry['slot_stages'])):
                    raise ValueError('selected_model_per_ticker_plan_scope')
            s['models'][m] = v
            if (sum(r['slots'] for r in s['models'].values()) + self.identity.get('onboarding', {}).get('max_models', 0)
                    + (len(v['b2_retry_binding']['b2_slots']) if self.identity.get('b2_retry_policy') else self.identity.get('timeout_retry_cap', 0)) > self.identity['max_models']):
                raise ValueError('selected_model_plan_over_cap')
            if required<=set(s['models']): s['state'] = 'MODEL_BUDGETED'
        elif event == 'MODEL_INHERIT_MARKET':
            m = v['market']
            plan = s['models'].get(m, {})
            if (m != 'kr' or s['state'] != 'MODEL_BUDGETED' or s['pending'] or v['plan'] != plan.get('sha256')
                    or not plan.get('inherited_market_slot') or v['slot'] != plan['inherited_market_slot']
                    or plan.get('market_lineage') is not None or v['lineage']['new_model_invocations'] != 0
                    or v['lineage']['source_generation'] != children[m]['generation']):
                raise ValueError('selected_market_inheritance_scope')
            s['models'][m] = dict(plan, market_lineage=v['lineage'])
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
                    scope_ok = (required<=set(s['plans']) and m in required and m not in s['captures']
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
                        or (s['models'][m].get('inherited_market_slot') and not s['models'][m].get('market_lineage'))
                        or s['model_total'] >= self.identity['max_models']):
                    raise ValueError('selected_model_scope_or_budget')
                cap = self.identity.get('timeout_retry_cap',0)
                per_ticker = s['models'][m].get('b2_retry_binding')
                if cap or per_ticker:
                    from app.services.model_timeout_retry import market_timeout_retry_cap
                    market_retry = v['stage'] == 'MARKET' and market_timeout_retry_cap(per_ticker)
                    attempt = v['attempt']
                    bound = s['timeout_attempts'].get(v['slot'], [])
                    if (not isinstance(attempt,dict)
                            or v['stage'] != s['models'][m]['slot_stages'].get(v['slot'])
                            or v['slot'] in s['timeout_exhausted']
                            or any(key not in s['timeout_exhausted'] and old[-1] in s['timed_out']
                                for key,old in s['timeout_attempts'].items() if key != v['slot'])
                            or key != 'MODEL:'+v['attempt']['attempt_id']
                            or attempt['ordinal'] != len(bound)+1 or len(bound)>1
                            or bound and (bound[0] not in s['timed_out']
                                or (v['slot'] not in per_ticker['b2_slots'] and not market_retry
                                    if per_ticker else s['retry_used']>=cap)
                                or (self.identity.get('fresh_timeout_retry_market') and v['stage']!='B2' and not market_retry)
                                or s['used'][bound[0]]['stage']!=v['stage']
                                or any(s['used'][bound[0]]['attempt'][k]!=attempt[k]
                                    for k in ('prompt_sha256','schema_sha256')))):
                        raise ValueError('selected_model_retry_scope_or_budget')
                    s['retry_used'] += bool(bound)
                    s['timeout_attempts'][v['slot']] = [*bound,key]
                s['model_total'] += 1
                s['monitoring_model_total'] += 1
            else: raise ValueError('selected_external_kind')
            s['used'][key] = v
            s['pending'] = key
        elif event == 'RESULT':
            if s['pending'] != v['key']: raise ValueError('selected_result_without_intent')
            optional = v.get('optional_unavailable')
            if optional is not None:
                from app.services.campaign_runtime_cap import optional_news_result
                attempt = (s.get('runtime') or {}).get('attempts', {}).get(optional, {})
                if (v['ok'] is not False or not optional_news_result(attempt, self.identity)
                        or v['key'] != 'HTTP:us:' + attempt['optional_news']['logical_id']):
                    raise ValueError('selected_optional_news_result_not_original_429')
            s['pending'] = None
            s['completed'].append(v['key'])
            if not v['ok'] and optional is None:
                s['state'] = 'STOPPED_NO_SEND'
        elif event == 'MODEL_CONFIRMED_TIMEOUT':
            from app.services.model_timeout_retry import validate_timeout

            key, proof = v['key'], v['proof']
            call = s['used'].get(key,{})
            validate_timeout(proof)
            if (not (self.identity.get('timeout_retry_cap') or self.identity.get('b2_retry_policy')) or s['state']!='MODEL_BUDGETED'
                    or s['pending']!=key or call.get('kind')!='MODEL'
                    or any(call['attempt'][k]!=proof[k] for k in ('attempt_id','prompt_sha256','schema_sha256'))):
                raise ValueError('selected_model_timeout_not_pending')
            s['timed_out'][key]=proof
            s['pending']=None
        elif event == 'MODEL_B2_TIMEOUT_EXHAUSTED':
            slot = v['slot']
            scope = s['models'].get(v['market'],{})
            calls = s['timeout_attempts'].get(slot,())
            cap = self.identity.get('timeout_retry_cap',0)
            per_ticker = scope.get('b2_retry_binding')
            if (not (cap or per_ticker) or s['pending'] or s['state'] != 'MODEL_BUDGETED'
                    or scope.get('slot_stages',{}).get(slot) != 'B2' or slot in s['timeout_exhausted']
                    or not calls or any(key not in s['timed_out'] for key in calls)
                    or (len(calls)!=2 if per_ticker else len(calls)==1 and s['retry_used']<cap)):
                raise ValueError('selected_model_b2_timeout_not_exhausted')
            s['timeout_exhausted'].append(slot)
        elif event == 'MODEL_OUTPUT_REJECTED':
            key=v['key'];call=s['used'].get(key,{})
            if (not staged or s['pending']!=key or call.get('kind')!='MODEL'
                    or v['reason']!='CANONICAL_OUTPUT_VALIDATION_REJECTED'
                    or (s['runtime'] or {}).get('pending')
                    or (s['runtime'] or {}).get('first_external_failure') is not None):
                raise ValueError('selected_local_model_output_rejection_not_admissible')
            s['pending']=None
            s['completed'].append(key)
            s['failed_markets'].setdefault(call['market'],dict(market=call['market'],reason=v['reason']))
            s['state']=('STOPPED_NO_SEND' if set(s['failed_markets'])|set(s['rendered_markets'])==set(children)
                else 'APPROVED_FROZEN_RUN')
        elif event == 'RENDER':
            if (s['state'] != 'MODEL_BUDGETED' or s['pending']
                        or any(p.get('inherited_market_slot') and not p.get('market_lineage') for p in s['models'].values())
                        or s['monitoring_model_total'] != sum(r['slots'] for r in s['models'].values())):
                raise ValueError('selected_render_incomplete')
            s['state'] = 'RENDERED_NO_SEND'
        elif event == 'RENDER_MARKET':
            m = v['market']
            completed = [call['slot'] for key,call in s['used'].items() if key in s['completed']
                         and call.get('kind')=='MODEL' and call.get('market')==m]
            required_slots = set(s['models'].get(m,{}).get('slot_ids',()))
            omitted = set(v.get('timeout_slots',()))
            if (omitted != set(s['timeout_exhausted']) or not omitted<=required_slots):
                raise ValueError('selected_partial_render_timeout_binding')
            if (not staged or m not in required or m in s['rendered_markets'] or s['pending']
                    or s['state']!='MODEL_BUDGETED' or m not in s['models']
                    or (s['models'][m].get('inherited_market_slot') and not s['models'][m].get('market_lineage'))
                    or len(completed) != len(set(completed)) or set(completed) != required_slots-omitted):
                raise ValueError('selected_market_render_incomplete')
            s['rendered_markets'][m] = v['result_sha256']
            accounted=set(s['rendered_markets'])|set(s['failed_markets'])
            s['state'] = ('STOPPED_NO_SEND' if s['failed_markets'] else 'RENDERED_NO_SEND') if accounted==set(children) else 'APPROVED_FROZEN_RUN'
        elif event == 'MARKET_FAILED':
            m=v['market']
            runtime=s['runtime'] or {}
            if (not staged or m not in required or m not in s['registrations']
                    or m in s['failed_markets'] or m in s['rendered_markets'] or s['pending']
                    or runtime.get('pending') or runtime.get('first_external_failure') is not None
                    or not isinstance(v['reason'],str) or not v['reason']):
                raise ValueError('selected_local_market_failure_not_admissible')
            s['failed_markets'][m]=v
            s['state']='STOPPED_NO_SEND' if set(s['failed_markets'])|set(s['rendered_markets'])==set(children) else 'APPROVED_FROZEN_RUN'
        else: raise ValueError('selected_unknown_run_event')

    def state(self):
        return self._event('OPEN')

    def stop(self, reason):
        return self._event('STOP', reason=reason)

    def before_registration(self, *, approval, permission, generations,revalidation_work_order_sha256=None):
        self._external()
        expected = {m:c['generation'] for m,c in self.identity['children'].items()}
        matches = (bool(generations) and set(generations)<=set(expected)
                   and all(expected[m]==g for m,g in generations.items())) if self.identity.get('staged_markets') else generations==expected
        if (approval is not self.approval or permission.event_id != self.identity['approval_event']
                or set(permission.subjects) != {t for c in self.identity['children'].values() for t in c['subjects']}
                or not matches
                or permission.max_private_export_bytes != self.identity.get('capture_max_private_export_bytes',8*1024*1024)
                or dict(path=str(permission.database), device=permission.device, inode=permission.inode) != self.identity['database_identity']):
            raise ValueError('selected_database_frozen_scope_changed')
        permission.require()
        state = self.state()
        if state['preopen_corrections'] and state['state']=='APPROVED_FROZEN_RUN':
            return
        if revalidation_work_order_sha256 is not None:
            if len(generations)!=1:raise ValueError('selected_single_revalidation_market_required')
            m=next(iter(generations))
            self._event('DB_REVALIDATE',market=m,
                previous_capture_sha256=state['registrations'].get(m,{}).get('sha256'),
                requested_work_order_sha256=revalidation_work_order_sha256)
            return
        self._event('DB_INTENT', **(dict(markets=list(generations)) if self.identity.get('staged_markets') else {}))

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
                or receipt['sqlite_mode'] != 'ro' or receipt['query_only'] is not True
                or receipt.get('private_export',{}).get('max_private_export_bytes',8*1024*1024)
                    != self.identity.get('capture_max_private_export_bytes',8*1024*1024)):
            raise ValueError('selected_original_readonly_receipt_required')
        self._event('REGISTRATION', sha256=digest(receipt), selects=selects, receipt=receipt)

    def bind_source_plan(self, market, plan):
        self._external()
        c = self.selected_child(market)
        if (plan.market != market or plan.generation_id != c['generation'] or tuple(plan.subjects) != tuple(c['subjects'])
                or any(d.transient_retry_max != 0 for d in plan.descriptors)):
            raise ValueError('selected_request_scope_changed')
        seconds = self.identity.get('routine_us_no_send_source_seconds')
        if (getattr(plan, 'routine_us_no_send_source_seconds', None) != seconds
                or seconds is not None and (market != 'us' or plan.purpose != registration.ROUTINE_SCOPE)):
            raise ValueError('selected_routine_source_plan_approval_mismatch')
        self._event('PLAN', market=market, sha256=plan.plan_sha256)

    def source_captured(self, market):
        self._event('CAPTURE', market=market)


    def source_owned(self, child):
        child.verify()
        c = self.selected_child(child.market)
        a = child.owner.acceptance()
        state = self.state()
        if (a['generation_id'] != c.get('execution_generation',c['generation'])
                or a['source_generation_id'] != c['generation'] or a['subjects'] != list(c['subjects'])
                or a['registration_capture_receipt_sha256'] != (state['registrations'][child.market]['sha256']
                    if self.identity.get('staged_markets') else state['registration'])
                or a['request_plan_sha256'] != state['plans'].get(child.market)):
            raise ValueError('selected_admitted_child_scope_changed')
        self._event('SOURCE', market=child.market, sha256=digest(a))

    def bind_model_plan(self, child, *, inherited_market=False):
        child.verify()
        if digest(child.owner.acceptance()) != self.state()['sources'].get(child.market):
            raise ValueError('selected_model_admitted_source_changed')
        slots = [s.slot_id for s in child.plan.slots]
        extra = {}
        if self.identity.get('timeout_retry_cap') or self.identity.get('b2_retry_policy'):
            extra['slot_stages'] = {s.slot_id:s.stage for s in child.plan.slots}
        if self.identity.get('b2_retry_policy'):
            from app.services.model_timeout_retry import b2_retry_binding
            extra['b2_retry_binding'] = b2_retry_binding(child.plan,self.identity['b2_retry_policy'])
        if inherited_market:
            markets = [s.slot_id for s in child.plan.slots if s.stage == 'MARKET']
            if child.market != 'kr' or len(markets) != 1:
                raise ValueError('selected_inherited_market_requires_single_kr_slot')
            slots.remove(markets[0])
            extra['inherited_market_slot'] = markets[0]
        self._event('MODEL_PLAN', market=child.market, sha256=child.plan.sha256, slots=len(slots),
            slot_ids=slots, **extra)

    def inherit_market(self, plan, slot, lineage):
        self._external()
        self._event('MODEL_INHERIT_MARKET', market=slot['market'], plan=plan.sha256,
            slot=slot['slot_id'], lineage=lineage)

    def before_http(self, *, market, provider, logical_id, plan_sha256):
        self._external_http(require_registration=True)
        key = f'HTTP:{market}:{logical_id}'
        self._event('INTENT', key=key, kind='HTTP', market=market, provider=provider, plan=plan_sha256)
        return key

    def before_model(self, plan, slot, *, attempt=None):
        self._external()
        runtime = self.state().get('runtime') or {}
        if (runtime.get('first_external_failure') is not None
                or (self.identity.get('staged_markets') and runtime.get('pending'))):
            raise ValueError('selected_external_failure_blocks_model')
        key = f'MODEL:{plan.cohort.run_id}:{slot["slot_id"]}'
        extra={}
        if attempt is not None:
            if not (self.identity.get('timeout_retry_cap') or self.identity.get('b2_retry_policy')):
                raise ValueError('selected_model_attempt_not_approved')
            key='MODEL:'+attempt['attempt_id']
            extra=dict(attempt=attempt,stage=slot['stage'])
        self._event('INTENT', key=key, kind='MODEL', market=slot['market'], slot=slot['slot_id'], plan=plan.sha256, **extra)
        return key

    def model_confirmed_timeout(self, key, proof):
        self._external()
        self._event('MODEL_CONFIRMED_TIMEOUT',key=key,proof=proof)

    def model_b2_timeout_exhausted(self, slot):
        self._external()
        self._event('MODEL_B2_TIMEOUT_EXHAUSTED',market=slot['market'],slot=slot['slot_id'])

    def before_onboarding_model(self, *, market, ticker, stage, payload_sha256):
        self._external()
        runtime = self.state().get('runtime') or {}
        if (runtime.get('first_external_failure') is not None
                or (self.identity.get('staged_markets') and runtime.get('pending'))):
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
                (require_registration or not self.identity.get('staged_markets')) and
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

    def result(self, key, *, ok, optional_unavailable=None):
        self._event('RESULT', key=key, ok=ok is True, **(
            {'optional_unavailable': optional_unavailable} if optional_unavailable is not None else {}))

    def reject_model_output(self,key):
        return self._event('MODEL_OUTPUT_REJECTED',key=key,reason='CANONICAL_OUTPUT_VALIDATION_REJECTED')

    def rendered(self, master, results):
        result = master.combine(results)
        self._event('RENDER', messages_sha256=result['messages_sha256'])
        return result

    def select_registered_subjects(self, market, owner):
        """Bind only the original current Owner's subset; never activate a row."""
        self._external()
        _, receipt = registration._state(owner)
        registration.require_generation(owner,self.identity['children'][market]['generation'],
            purpose=registration.ROUTINE_SCOPE if self.identity.get('routine_us_no_send_source_seconds') is not None else registration.SCOPE)
        if receipt.get('routine_us_no_send_source_seconds') != self.identity.get('routine_us_no_send_source_seconds'):
            raise ValueError('selected_routine_registration_approval_mismatch')
        state = self.state()
        if (receipt['market']!=market or receipt['approval_event']!=self.identity['approval_event']
                or receipt['capture_receipt_sha256']!=state['registrations'].get(market,{}).get('sha256')):
            raise ValueError('selected_registered_subset_owner_mismatch')
        if market in state['selected_subjects']:
            if (market not in state['registration_revalidations']
                    or state['selected_subjects'][market]!=sorted(receipt['bindings'])):
                raise ValueError('selected_revalidation_subjects_changed')
            return
        self._event('REGISTERED_SUBJECTS',market=market,subjects=sorted(receipt['bindings']),
            capture_sha256=receipt['capture_receipt_sha256'])

    def selected_child(self, market):
        child = deepcopy(self.identity['children'][market])
        if self.identity.get('staged_markets'):
            subjects = self.state()['selected_subjects'].get(market)
            if not subjects:
                raise ValueError('selected_current_registered_subset_required')
            child['subjects'] = subjects
        return child

    def rendered_market(self, child, result):
        """Original per-market terminal, without pretending the other window ran."""
        from app.services.research_no_send_run import PARTIAL, TERMINAL, RESEARCH_STAGES, MarketResearchChild
        if not isinstance(child,MarketResearchChild):
            raise ValueError('selected_original_market_child_required')
        binding = child.binding()
        messages = result.get('messages',[])
        if child.plan.cohort.limitation_subjects:
            from app.services.model_execution_plan import verify_mixed_render

            if result.get('status') != TERMINAL:
                raise ValueError('selected_mixed_limitation_terminal_required')
            verify_mixed_render(child.plan, messages, result.get('limitation_receipts',{}))
        partial = result.get('status') == PARTIAL
        omissions = result.get('unissued',{}) if partial else {}
        b2_slots = {s.subjects[0]:s.slot_id for s in child.plan.slots if s.stage=='B2'}
        if (partial and (not (self.identity.get('timeout_retry_cap') or self.identity.get('b2_retry_policy')) or not omissions
                or not set(omissions)<=set(b2_slots)
                or result.get('expected_message_count')!=len(binding['message_ids'])
                or any(row.get('slot_id')!=b2_slots[t] or row.get('status')!='B2_UNISSUED_TIMEOUT'
                       for t,row in omissions.items()))):
            raise ValueError('selected_partial_market_terminal_scope')
        if (result.get('status') not in {TERMINAL,PARTIAL} or result.get('child_binding')!=binding
                or result.get('normal_messages_sent') is not False
                or result.get('messages_sha256')!=digest(messages)
                or sorted(r['message_id'] for r in messages)!=sorted(set(binding['message_ids'])-set(omissions))
                or any(r.get('NO_SEND') is not True for r in messages)
                or [r.get('stage') for r in result.get('stage_receipts',[])]!=list(RESEARCH_STAGES)
                or any(r.get('status')!='PASS' for r in result['stage_receipts'])):
            raise ValueError('selected_original_market_terminal_required')
        extra = dict(timeout_slots=sorted(b2_slots[t] for t in omissions)) if omissions else {}
        self._event('RENDER_MARKET',market=child.market,result_sha256=digest(result), **extra)
        return result

    def market_failed(self, market, reason):
        """Record a local data/contract failure without clearing a hard STOP."""
        self._external()
        return self._event('MARKET_FAILED',market=market,reason=reason)


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
