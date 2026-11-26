"""Append-only local invocation accounting. An interrupted intent is never retried."""
import fcntl
import json
import os
from pathlib import Path

from app.services.unified_snapshot_contract import digest, encoded
from app.services.model_timeout_retry import (
    validate_timeout, validate_b2_retry_binding, market_timeout_retry_cap, b2_retry_budget_bounds, stock_slot_retry,
)


def _empty():
    return dict(bound={}, used=set(), accepted={}, inherited={}, stopped=False,
                attempts={}, timeouts={}, exhausted=set(), retry_used=0, physical_calls=0)


def read_invocation_journal(raw, identity=None):
    if not raw or not raw.endswith(b'\n'):
        raise ValueError('model_journal_torn_write_no_replay')
    rows = [json.loads(line) for line in raw.splitlines()]
    identity = identity if identity is not None else rows[0]['identity']
    state = _empty()
    previous = None
    for index, row in enumerate(rows):
        pin = row.pop('sha256')
        if (digest(row) != pin or row['previous'] != previous or row['sequence'] != index
                or row['identity'] != identity or (index == 0) != (row['event'] == 'OPEN')):
            raise ValueError('model_journal_identity_or_chain_drift')
        _apply(state, row['event'], row['value'], identity)
        previous = pin
    return dict(state, _previous=previous, _count=len(rows))


class ModelInvocationJournal:
    def __init__(self, path, *, plan_sha256, maximum, inherited_market_slot=None, retry_cap=0, b2_retry_policy=None,
                 retry_market='us'):
        self.path = Path(path)
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError('model_journal_symlink')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.identity = dict(contract='model-invocation-journal-v1', plan_sha256=plan_sha256, maximum=maximum)
        if inherited_market_slot is not None:
            self.identity['inherited_market_slot'] = inherited_market_slot
        if type(retry_cap) is not int or retry_cap not in (0, 1, 2) or (retry_cap and inherited_market_slot):
            raise ValueError('model_timeout_retry_cap_invalid')
        if retry_cap:
            self.identity['timeout_retry_cap'] = retry_cap
        if retry_market not in ('us','kr') or retry_market=='kr' and (
                retry_cap not in (0,1) or not (retry_cap or b2_retry_policy)
                or inherited_market_slot or not b2_retry_policy and maximum<2):
            raise ValueError('model_kr_market_retry_journal_scope')
        if retry_market=='kr':
            self.identity['timeout_retry_market']='kr'
        if b2_retry_policy is not None:
            validate_b2_retry_binding(b2_retry_policy)
            minimum, full_maximum = b2_retry_budget_bounds(b2_retry_policy,
                retry_cap=retry_cap, retry_market=retry_market)
            if (retry_cap not in (0,1) or inherited_market_slot
                    or type(maximum) is not int or not minimum <= maximum <= full_maximum
                    or b2_retry_policy['plan_sha256'] != plan_sha256):
                raise ValueError('model_b2_retry_journal_scope')
            market_timeout_retry_cap(b2_retry_policy,retry_cap=retry_cap,retry_market=retry_market)
            self.identity['b2_retry_policy'] = b2_retry_policy
        self.transact('OPEN')

    def transact(self, event, **value):
        flags = os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
        with os.fdopen(os.open(self.path, flags, 0o600), 'r+b') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            raw = f.read()
            state = read_invocation_journal(raw, self.identity) if raw else dict(
                _empty(), _previous=None, _count=0)
            previous, count = state.pop('_previous'), state.pop('_count')
            if event != 'OPEN' or not raw:
                _apply(state, event, value, self.identity)
                row = dict(identity=self.identity, sequence=count, previous=previous, event=event, value=value)
                row['sha256'] = digest(row)
                content = encoded(row)+b'\n'
                from app.services.research_artifact_budget import active_budget
                if (budget := active_budget()) is not None:
                    budget.before_write(self.path, len(content), role='result')
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            return state

def _apply(state, event, value, identity):
        if identity.get('timeout_retry_market') is not None and (
                identity['timeout_retry_market']!='kr' or identity.get('timeout_retry_cap',0) not in (0,1)
                or not (identity.get('timeout_retry_cap') or identity.get('b2_retry_policy'))
                or identity.get('inherited_market_slot')):
            raise ValueError('model_kr_market_retry_journal_scope')
        policy = identity.get('b2_retry_policy')
        if policy is not None:
            validate_b2_retry_binding(policy)
            cap=identity.get('timeout_retry_cap',0)
            minimum, full_maximum = b2_retry_budget_bounds(policy, retry_cap=cap,
                retry_market=identity.get('timeout_retry_market','us'))
            if (cap not in (0,1) or identity.get('inherited_market_slot')
                    or type(identity['maximum']) is not int or not minimum <= identity['maximum'] <= full_maximum
                    or identity['plan_sha256'] != policy['plan_sha256']):
                raise ValueError('model_b2_retry_journal_identity')
            market_timeout_retry_cap(policy,retry_cap=cap,retry_market=identity.get('timeout_retry_market','us'))
        if event == 'OPEN':
            return
        if event == 'STOP':
            state['stopped'] = True
            return
        if state['stopped']:
            raise ValueError('model_journal_failed_cycle_no_more_calls')
        slot = value['slot_id']
        cap = identity.get('timeout_retry_cap', 0)
        retry_enabled = bool(cap or policy)
        unresolved = state['used'] - state['accepted'].keys() - state['exhausted']
        if event == 'BIND':
            scope = value['scope']
            if (slot in state['bound'] or slot != scope['slot_id']
                    or identity.get('timeout_retry_market')=='kr' and scope.get('market')!='kr'
                    or policy and (scope['stage'] != policy['slot_stages'].get(slot)
                        or scope.get('market')!=identity.get('timeout_retry_market','us')
                        or scope['stage'] == 'B2' and scope.get('subjects') != [policy['b2_slots'][slot]])
                    or any(state['accepted'].get(k) != v for k,v in scope['dependency_outputs'].items())):
                raise ValueError('model_journal_binding_or_dependency_gap')
            state['bound'][slot] = scope
        elif event == 'INHERIT_MARKET':
            scope = state['bound'].get(slot, {})
            lineage = value['lineage']
            if (slot != identity.get('inherited_market_slot') or scope.get('stage') != 'MARKET'
                    or state['used'] or state['accepted'] or lineage['payload_sha256'] != scope['payload_sha256']
                    or lineage['source_generation'] != scope['source_generation'] or lineage['new_model_invocations'] != 0):
                raise ValueError('model_journal_market_inheritance_gap')
            state['inherited'][slot] = lineage
            state['accepted'][slot] = lineage['output_sha256']
        elif event == 'CONSUME':
            if (slot not in state['bound'] or slot in state['used']
                    or slot == identity.get('inherited_market_slot')
                    or unresolved or len(state['used']) >= (policy['base_slots'] if policy else identity['maximum'] - cap)
                    or state['physical_calls'] >= identity['maximum']):
                raise ValueError('model_journal_used_parallel_or_exhausted')
            if retry_enabled:
                _model_attempt(state, slot, value, expected=1)
            state['used'].add(slot)
            state['physical_calls'] += 1
        elif event == 'TIMEOUT_CONFIRMED':
            proof = value['proof']
            validate_timeout(proof)
            attempt = state['attempts'].get(slot, ())
            existing = state['timeouts'].get(slot, [])
            if (not retry_enabled or unresolved != {slot} or not attempt or len(existing) != len(attempt)-1
                    or any(proof[k] != attempt[-1][k] for k in ('attempt_id','prompt_sha256','schema_sha256'))):
                raise ValueError('model_journal_timeout_binding')
            state['timeouts'][slot] = [*existing, proof]
        elif event == 'RETRY_ATTEMPT':
            stock_retry = stock_slot_retry(policy, slot)
            market_retry = state['bound'][slot]['stage']=='MARKET' and market_timeout_retry_cap(
                policy,retry_cap=cap,retry_market=identity.get('timeout_retry_market','us'))
            if (not retry_enabled or unresolved != {slot} or len(state['attempts'].get(slot, ())) != 1
                    or len(state['timeouts'].get(slot, ())) != 1
                    or (not (stock_retry or market_retry) if policy else state['retry_used'] >= cap)
                    or policy and state['retry_used'] >= identity['maximum']-policy['base_slots']
                    or identity.get('timeout_retry_market')=='kr' and not (market_retry or stock_retry)
                    or state['physical_calls'] >= identity['maximum']):
                raise ValueError('model_journal_retry_unavailable')
            _model_attempt(state, slot, value, expected=2)
            state['retry_used'] += 1
            state['physical_calls'] += 1
        elif event == 'RETRY_EXHAUSTED':
            attempts = state['attempts'].get(slot, ())
            if (not retry_enabled or unresolved != {slot} or state['bound'][slot]['stage'] != 'B2'
                    or identity.get('timeout_retry_market')=='kr'
                    or policy and cap
                    or not attempts or len(state['timeouts'].get(slot, ())) != len(attempts)
                    or (len(attempts) != 2 if policy else len(attempts) == 1 and state['retry_used'] < cap)):
                raise ValueError('model_journal_b2_exhaustion_unproven')
            state['exhausted'].add(slot)
        elif event == 'ACCEPT':
            if (slot not in unresolved or retry_enabled and (
                    len(state['timeouts'].get(slot, ())) == len(state['attempts'][slot])
                    or value.get('attempt_id') != state['attempts'][slot][-1]['attempt_id'])):
                raise ValueError('model_journal_acceptance_gap')
            state['accepted'][slot] = value['output_sha256']
        else:
            raise ValueError('model_journal_unknown_event')


def _model_attempt(state, slot, value, *, expected):
    import re

    attempt = value['attempt']
    previous = state['attempts'].get(slot, [])
    pins = ('prompt_sha256','schema_sha256')
    if (set(attempt) != {'attempt_id','ordinal',*pins} or attempt['ordinal'] != expected
            or not re.fullmatch(r'[A-Za-z0-9_.:-]+-[a-f0-9]{32}', attempt['attempt_id'])
            or any(not re.fullmatch('[a-f0-9]{64}', attempt[k]) for k in pins)
            or any(attempt['attempt_id'] == old['attempt_id']
                   for rows in state['attempts'].values() for old in rows)
            or previous and any(attempt[k] != previous[0][k] for k in pins)):
        raise ValueError('model_journal_attempt_identity_changed')
    state['attempts'][slot] = [*previous, attempt]
