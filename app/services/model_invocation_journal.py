"""Append-only local invocation accounting. An interrupted intent is never retried."""
import fcntl
import json
import os
from pathlib import Path

from app.services.unified_snapshot_contract import digest, encoded


class ModelInvocationJournal:
    def __init__(self, path, *, plan_sha256, maximum):
        self.path = Path(path)
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise ValueError('model_journal_symlink')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.identity = dict(contract='model-invocation-journal-v1', plan_sha256=plan_sha256, maximum=maximum)
        self.transact('OPEN')

    def transact(self, event, **value):
        flags = os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW
        with os.fdopen(os.open(self.path, flags, 0o600), 'r+b') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            raw = f.read()
            if raw and not raw.endswith(b'\n'):
                raise ValueError('model_journal_torn_write_no_replay')
            state = dict(bound={}, used=set(), accepted={}, stopped=False)
            previous, count = None, 0
            for line in raw.splitlines():
                row = json.loads(line)
                pin = row.pop('sha256')
                if (digest(row) != pin or row['previous'] != previous or row['sequence'] != count
                        or row['identity'] != self.identity):
                    raise ValueError('model_journal_identity_or_chain_drift')
                self._apply(state, row['event'], row['value'])
                previous, count = pin, count+1
            if event != 'OPEN' or not raw:
                self._apply(state, event, value)
                row = dict(identity=self.identity, sequence=count, previous=previous, event=event, value=value)
                row['sha256'] = digest(row)
                f.write(encoded(row)+b'\n')
                f.flush()
                os.fsync(f.fileno())
            return state

    def _apply(self, state, event, value):
        if event == 'OPEN':
            return
        if event == 'STOP':
            state['stopped'] = True
            return
        if state['stopped']:
            raise ValueError('model_journal_failed_cycle_no_more_calls')
        slot = value['slot_id']
        if event == 'BIND':
            scope = value['scope']
            if (slot in state['bound'] or slot != scope['slot_id']
                    or any(state['accepted'].get(k) != v for k,v in scope['dependency_outputs'].items())):
                raise ValueError('model_journal_binding_or_dependency_gap')
            state['bound'][slot] = scope
        elif event == 'CONSUME':
            if (slot not in state['bound'] or slot in state['used']
                    or state['used'] - state['accepted'].keys()
                    or len(state['used']) >= self.identity['maximum']):
                raise ValueError('model_journal_used_parallel_or_exhausted')
            state['used'].add(slot)
        elif event == 'ACCEPT':
            if slot not in state['used'] or slot in state['accepted']:
                raise ValueError('model_journal_acceptance_gap')
            state['accepted'][slot] = value['output_sha256']
        else:
            raise ValueError('model_journal_unknown_event')
