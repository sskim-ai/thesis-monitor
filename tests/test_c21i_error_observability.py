import json
import time
from types import SimpleNamespace
import pytest

from maintenance import guarded_sol_host as host
from test_guarded_sol_host import subject


def events(error_info='badRequest'):
    error = dict(message='SYNTHETIC_SECRET https://private.invalid Bearer hidden',
                 additionalDetails='PRIVATE_INPUT_ECHO', codexErrorInfo=error_info)
    return [dict(direction='receive', message=dict(method='error', params=dict(
        threadId='SYNTHETIC_THREAD', turnId='SYNTHETIC_TURN', error=error, willRetry=False))),
        dict(direction='receive', message=dict(method='turn/completed', params=dict(
            threadId='SYNTHETIC_THREAD', turn=dict(id='SYNTHETIC_TURN', status='failed', error=error))))]


def inspect(tmp_path, values, completion=None):
    if completion is None and values:
        completion = values[-1]['message']['params'].get('turn')
    return host.error_observability(completion, values, thread_id='SYNTHETIC_THREAD',
        turn_id='SYNTHETIC_TURN', receipt_root=tmp_path, observed_unix=123.5)


def test_both_error_sources_preserved_without_raw_text_or_identifiers(tmp_path):
    values = events()
    result = inspect(tmp_path, values)
    encoded = json.dumps(result)
    assert [r['method'] for r in result['events']] == ['error', 'turn/completed']
    assert result['event_count'] == 2 and not result['multiple_sources_disagree']
    assert all(r['scope_match'] and r['message_present'] and r['additional_details_present'] for r in result['events'])
    assert all(s not in encoded for s in ('SYNTHETIC_SECRET','PRIVATE_INPUT_ECHO','private.invalid','SYNTHETIC_THREAD','SYNTHETIC_TURN'))


def test_exact_enums_and_http_status_only_not_identifier_shaped_secrets(tmp_path):
    for info in ('SecretTokenLookingLikeAnIdentifier', {'SecretKey': {'httpStatusCode': 401}},
                 {'httpConnectionFailed': {'httpStatusCode': True, 'token': 'SECRET'}}):
        result = inspect(tmp_path, events(info))
        assert 'SecretToken' not in json.dumps(result) and 'SecretKey' not in json.dumps(result)
        assert not any('httpStatusCode' in str(r['error_info']) for r in result['events'])
    result = inspect(tmp_path, events({'httpConnectionFailed': {'httpStatusCode': 400, 'secret': 'PRIVATE'}}))
    assert result['events'][0]['error_info'] == {'httpConnectionFailed': {'httpStatusCode': 400}}
    assert 'PRIVATE' not in json.dumps(result)


def test_disagreement_missing_and_foreign_events_are_not_resolved_by_guessing(tmp_path):
    values = events()
    values[-1]['message']['params']['turn']['error']['codexErrorInfo'] = 'other'
    # Use independent payloads: notifications and terminal may legitimately differ.
    values[0]['message']['params']['error'] = dict(message='hidden', codexErrorInfo='badRequest')
    assert inspect(tmp_path, values)['multiple_sources_disagree']
    missing = inspect(tmp_path, [], completion={})
    assert missing['error_evidence_missing'] and missing['terminal']['status'] == 'unknown'
    values = events()
    values[0]['message']['params']['threadId'] = 'FOREIGN'
    result = inspect(tmp_path, values)
    assert result['events'][0]['scope_match'] is False


def test_receipt_hash_status_conflict_and_event_cap(tmp_path):
    path = tmp_path/('response-'+'a'*64+'.json')
    raw = b'{"response_status":400,"response_headers_received":true}'
    path.write_bytes(raw)
    result = inspect(tmp_path, events({'httpConnectionFailed': {'httpStatusCode':503}}))
    assert result['multiple_sources_disagree']
    assert result['receipt_references'] == [dict(file=path.name, sha256=host.digest(raw), response_status=400)]
    capped = inspect(tmp_path, events()*40)
    assert len(capped['events']) == 64 and capped['omitted_events'] == 16


def test_failed_execute_persists_both_sources_and_closes_host_and_executor(monkeypatch, tmp_path):
    request, prompt, schema, packet, scope = subject()
    runtime, out = tmp_path/'runtime', tmp_path/'out'
    runtime.mkdir(); out.mkdir()
    scope.update(root=str(runtime), ledger=str(runtime/'inference-ledger.json'))
    binding = SimpleNamespace(root=runtime, execution_profile='SOL_61_HIGH_EXECUTION_V1',
        binary=tmp_path/'NEVER_EXECUTED', binary_sha256='a'*64, catalog=tmp_path/'SYNTHETIC',
        scope=tmp_path/'scope', scope_sha256='b'*64, verify=lambda:scope)
    calls = []
    class Client:
        def __init__(self):
            self.events = []; self.pending = []
        def rpc(self, method, params, **kwargs):
            if method == 'account/read': return dict(account=dict(type='chatgpt'))
            if method == 'thread/start': return dict(thread=dict(id='SYNTHETIC_THREAD'), model='gpt-6.1-sol')
            if method == 'turn/start':
                self.events = events()
                self.pending = [e['message'] for e in self.events]
                return dict(turn=dict(id='SYNTHETIC_TURN'))
            return {}
        def send(self, value): pass
        def close(self):
            calls.append('host_closed'); return dict(exit=0, reader_joined=True)
    class Broker:
        receipts = []
        def __init__(self, *args, **kwargs): pass
        def start(self): calls.append('executor_started')
        def bind(self, *args): pass
        def close(self):
            calls.append('executor_closed'); return dict(exit=0, reader_joined=True)
    adapted = dict(adapter_version='SYNTHETIC', canonical_schema_sha256='c'*64, wire_schema_sha256='d'*64, changed_paths=[])
    module = SimpleNamespace(t=SimpleNamespace(pin=lambda p:host.digest(p.read_bytes())),
        adapt=lambda s:(s,adapted), PublicBroker=Broker, load_transport=lambda:(lambda *a,**k:Client()), SPEC={})
    monkeypatch.setattr(host, 'original', lambda b:module)
    with pytest.raises(ValueError, match='turn_not_completed_no_retry'):
        host.execute(binding, request=request, prompt=prompt, schema=schema, packet=packet,
            owner_check=lambda:True, deadline=time.time()+30, out=out)
    result = json.loads((out/'ERROR_OBSERVABILITY.json').read_bytes())
    assert result['event_count'] == 2 and calls == ['executor_started','host_closed','executor_closed']
    assert not json.loads((out/'HOST_TRANSPORT.json').read_bytes())['verified']
