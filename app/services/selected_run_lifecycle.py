"""One local run ledger over existing OperatorApproval, not a new consent token.

It counts intents before I/O. Source quality, account STOP/Lane and original
Worker/Stage owners remain separate mandatory checks at their original ports.
"""
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path

from app.services import prospective_class_c_owner as registration
from app.services.unified_snapshot_contract import digest, encoded

STATES = ('NO_APPROVAL', 'APPROVED_FROZEN_RUN', 'REGISTRATION_CAPTURED',
          'SOURCE_CAPTURED', 'SOURCE_OWNED', 'MODEL_BUDGETED', 'RENDERED_NO_SEND', 'STOPPED_NO_SEND')


class SelectedRunLedger:
    def __init__(self, *, path, approval, master_id, children, provider_caps,
                 max_http, max_models, database_identity):
        decision = registration._approval(approval)
        if (not master_id or set(children) != {'us', 'kr'}
                or len({c['generation'] for c in children.values()}) != 2
                or any(c['generation'] == master_id for c in children.values())
                or any(not c['subjects'] or len(set(c['subjects'])) != len(c['subjects']) for c in children.values())
                or sorted(t for c in children.values() for t in c['subjects']) != sorted(decision.subjects)
                or any(type(n) is not int or n < 0 for n in (*provider_caps.values(), max_http, max_models))
                or sum(provider_caps.values()) > max_http):
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
        self._event('OPEN')

    def _external(self):
        decision = registration._approval(self.approval)
        if digest(decision.model_dump(mode='json')) != self.identity['approval_sha256']:
            raise ValueError('selected_run_approval_changed')

    def _event(self, event, **value):
        with os.fdopen(os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600), 'r+b') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            raw = f.read()
            if raw and not raw.endswith(b'\n'):
                raise ValueError('selected_run_torn_intent_no_replay')
            state = dict(state='APPROVED_FROZEN_RUN', registration=None, registration_receipt=None, db_intent=False,
                db_connection_attempts=0, preopen_corrections=0,
                plans={}, sources={}, captures=[], models={}, used={}, pending=None, completed=[],
                http={}, http_total=0, model_total=0, db_select_reserved=0, db_select_actual=0)
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
                    or s['db_connection_attempts'] or s['preopen_corrections']
                    or v['observed_connections'] != 0 or v['observed_selects'] != 0):
                raise ValueError('selected_cannot_repair_consumed_database_attempt')
            # No counter or intent is cleared. A local Python argument error
            # before connect is not a second physical database attempt.
            s.update(state='APPROVED_FROZEN_RUN', preopen_corrections=1)
            return
        if s['state'] in ('STOPPED_NO_SEND', 'RENDERED_NO_SEND'):
            raise ValueError('selected_run_terminal_no_new_work')
        if event == 'DB_INTENT':
            if s['db_intent']: raise ValueError('selected_registration_already_attempted')
            s.update(db_intent=True, db_select_reserved=5)
        elif event == 'DB_OPEN':
            if not s['db_intent'] or s['db_connection_attempts'] or s['registration'] is not None:
                raise ValueError('selected_database_connection_already_attempted')
            s['db_connection_attempts'] = 1
        elif event == 'REGISTRATION':
            if not s['db_intent'] or s['registration'] is not None or not 1 <= v['selects'] <= 5:
                raise ValueError('selected_registration_receipt_gap')
            if digest(v['receipt']) != v['sha256']:
                raise ValueError('selected_registration_receipt_hash_drift')
            s.update(registration=v['sha256'], registration_receipt=v['receipt'],
                db_select_actual=v['selects'], state='REGISTRATION_CAPTURED')
        elif event == 'PLAN':
            m = v['market']
            if s['registration'] is None or m not in children or m in s['plans'] or s['http_total']:
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
            if set(s['sources']) != set(children) or m in s['models'] or s['model_total']:
                raise ValueError('selected_model_source_or_freeze_gap')
            s['models'][m] = v
            if sum(r['slots'] for r in s['models'].values()) > self.identity['max_models']:
                raise ValueError('selected_model_plan_over_cap')
            if set(s['models']) == set(children): s['state'] = 'MODEL_BUDGETED'
        elif event == 'INTENT':
            key, kind, m = v['key'], v['kind'], v['market']
            if s['pending'] or key in s['used'] or m not in children:
                raise ValueError('selected_run_duplicate_or_parallel_intent')
            if kind == 'HTTP':
                p = v['provider']
                if (set(s['plans']) != set(children) or m in s['captures']
                        or v['plan'] != s['plans'][m]
                        or s['http_total'] >= self.identity['max_http']
                        or s['http'].get(p, 0) >= self.identity['provider_caps'].get(p, 0)):
                    raise ValueError('selected_physical_http_scope_or_budget')
                s['http'][p] = s['http'].get(p, 0) + 1
                s['http_total'] += 1
            elif kind == 'MODEL':
                if (s['state'] != 'MODEL_BUDGETED' or v['plan'] != s['models'][m]['sha256']
                        or v['slot'] not in s['models'][m]['slot_ids']
                        or s['model_total'] >= self.identity['max_models']):
                    raise ValueError('selected_model_scope_or_budget')
                s['model_total'] += 1
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
                    or s['model_total'] != sum(r['slots'] for r in s['models'].values())):
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
        if state['preopen_corrections'] and state['state']=='APPROVED_FROZEN_RUN' and not state['db_connection_attempts']:
            return
        self._event('DB_INTENT')

    def before_database_open(self):
        self._external()
        self._event('DB_OPEN')

    def correct_preopen_wiring(self, *, evidence_sha256, observed_connections, observed_selects):
        self._external()
        self._event('PREOPEN_CORRECTION', evidence_sha256=evidence_sha256,
            observed_connections=observed_connections, observed_selects=observed_selects)

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
        self._external()
        key = f'HTTP:{market}:{logical_id}'
        self._event('INTENT', key=key, kind='HTTP', market=market, provider=provider, plan=plan_sha256)
        return key

    def before_model(self, plan, slot):
        self._external()
        key = f'MODEL:{plan.cohort.run_id}:{slot["slot_id"]}'
        self._event('INTENT', key=key, kind='MODEL', market=slot['market'], slot=slot['slot_id'], plan=plan.sha256)
        return key

    def result(self, key, *, ok):
        self._event('RESULT', key=key, ok=ok is True)

    def rendered(self, master, results):
        result = master.combine(results)
        self._event('RENDER', messages_sha256=result['messages_sha256'])
        return result
