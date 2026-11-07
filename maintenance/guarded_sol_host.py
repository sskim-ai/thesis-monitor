"""Task-local exact Sol profile binding for the original public-analysis broker.

This is not a scheduler, a source authority, or a replacement Stage Owner.
All paths and helper bytes are supplied by a local, pinned launch manifest.
"""
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import re
import sys
import time
import types

from app.services.vnext_execution_profile import SOL_HIGH_V1

TASK = 'C21G_SOL_HIGH_GUARDED_HOST_COMPATIBILITY_AND_SINGLE_NO_SEND_CANARY'
VERSION = 'UNIFIED_JUDGMENT_V3_AI_OWNED_SOL_HIGH_PROMPT_V1'


def digest(data):
    if not isinstance(data, bytes):
        data = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def plain(path):
    path = Path(path)
    if not path.is_absolute() or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('plain_absolute_path_required')
    if path.is_file() and path.stat().st_nlink != 1:
        raise ValueError('unique_file_required')
    return path


def write_once(path, value, mode=0o600):
    path = Path(path)
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    path.chmod(mode)


@dataclass(frozen=True)
class Binding:
    binary: Path
    binary_sha256: str
    catalog: Path
    catalog_sha256: str
    legacy: Path
    helper_pins: dict
    root: Path
    scope: Path
    scope_sha256: str

    def verify(self):
        for path, expected in [(self.binary, self.binary_sha256), (self.catalog, self.catalog_sha256), (self.scope, self.scope_sha256)]:
            if digest(plain(path).read_bytes()) != expected:
                raise ValueError('runtime_asset_pin')
        plain(self.root)
        if self.root.resolve() != self.root:
            raise ValueError('canonical_root_required')
        for name, expected in self.helper_pins.items():
            if digest(plain(self.legacy.parent / name).read_bytes()) != expected:
                raise ValueError('original_helper_changed')
        models = json.loads(self.catalog.read_bytes())['models']
        if len(models) != 1 or models[0]['slug'] != SOL_HIGH_V1.model:
            raise ValueError('exact_catalog_model')
        if SOL_HIGH_V1.effort not in [x['effort'] for x in models[0]['supported_reasoning_levels']]:
            raise ValueError('catalog_effort')
        scope = json.loads(self.scope.read_bytes())
        if (scope['task'], scope['execution_profile'], scope['root'], scope['ledger']) != (
            TASK, SOL_HIGH_V1.contract, str(self.root), str(self.root / 'inference-ledger.json')):
            raise ValueError('exact_scope_required')
        if self.scope.stat().st_mode & 0o222:
            raise ValueError('scope_must_be_read_only')
        return scope


def require_request(request, prompt, schema, packet, scope):
    expected = dict(model=SOL_HIGH_V1.model, effort=SOL_HIGH_V1.effort,
                    execution_profile=SOL_HIGH_V1.contract, prompt_version=VERSION,
                    contract='UNIFIED_STAGE_REVIEW_V3_SOL_61_HIGH_V1',
                    timeout_seconds=600, input_bytes=393216, output_bytes=131072, retries=0, send=False)
    if any(request.get(k) != v for k, v in expected.items()):
        raise ValueError('exact_sol_stage_contract')
    if request['stage'] not in ('BLIND', 'ADJUDICATION') or not request['invocation_id']:
        raise ValueError('fresh_stage_identity')
    if len(prompt.encode()) > 393216 or request['prompt_sha'] != digest(prompt.encode()) or request['schema_sha'] != digest(schema):
        raise ValueError('prompt_schema_binding')
    if request['source_sha'] != digest(packet) or scope['owner_sha256'] != digest(packet):
        raise ValueError('packet_binding')
    if request['account'] != scope['account'] or request['security']['canonical_security_id'] != scope['security']:
        raise ValueError('subject_account_binding')
    if request['source_as_of'] != scope['source_generation']:
        raise ValueError('source_generation_binding')
    if (request['stage'] == 'BLIND') != (request['prior_stage_sha'] is None):
        raise ValueError('accepted_prior_binding_required')


def original(binding):
    binding.verify()
    saved = dict(sys.modules)
    sys.path.insert(0, str(binding.legacy))
    for name in ('task', 'host_preflight', 'executor_stream', 'flexible_output', 'wire_schema'):
        sys.modules.pop(name, None)
    try:
        spec = importlib.util.spec_from_file_location('c21g_original_transport', binding.legacy / 'live_transport.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        seen = set()
        def check_closure(current):
            if id(current) in seen:
                return
            seen.add(id(current))
            path = getattr(current, '__file__', None)
            if not path or not Path(path).is_relative_to(binding.legacy.parent):
                return
            path = Path(path)
            key = str(path.relative_to(binding.legacy.parent))
            if path.suffix != '.py' or binding.helper_pins.get(key) != digest(plain(path).read_bytes()):
                raise ValueError('unapproved_original_helper_dependency')
            for value in vars(current).values():
                if isinstance(value, types.ModuleType):
                    check_closure(value)
        check_closure(module)
        module.t.BASE = binding.root
        module.t.TASK_ID = TASK
        return module
    finally:
        sys.path.pop(0)
        for name in set(sys.modules) - set(saved):
            sys.modules.pop(name, None)
        sys.modules.update(saved)


def config_args(binding, stage_root):
    values = dict(model=SOL_HIGH_V1.model, model_reasoning_effort=SOL_HIGH_V1.effort,
                  approval_policy='never', sandbox_mode='read-only', web_search='disabled',
                  model_catalog_json=str(binding.catalog), sqlite_home=str(stage_root / 'state'),
                  log_dir=str(stage_root / 'logs'))
    values.update({'analytics.enabled': False, 'agents.enabled': False, 'orchestrator.skills.enabled': False})
    values.update({'features.' + n: False for n in ('shell_tool', 'unified_exec', 'code_mode', 'multi_agent',
                  'multi_agent_v2', 'apps', 'plugins', 'request_permissions', 'js_repl', 'realtime_conversation', 'image_generation')})
    return [item for key, value in values.items() for item in ('-c', key + '=' + json.dumps(value))]


def host_profile(binding, stage_root, *, authenticated=False):
    home = Path.home()
    shared = [binding.root / 'inference-ledger.json', binding.root / 'host-control-ledger.json']
    allowed = [binding.binary, binding.catalog, binding.scope, *shared]
    if authenticated:
        allowed += [home / '.codex/auth.json']
        rules = home / '.codex/rules'
        if rules.is_dir():
            allowed += [rules, *[plain(p) for p in rules.iterdir() if p.suffix == '.rules']]
    exceptions = '\n'.join('(require-not (literal ' + json.dumps(str(p)) + '))' for p in allowed)
    # Seatbelt's regex reader is not Python's; avoid escaped hyphens and counts.
    response_pattern = '^' + re.escape(str(binding.root)).replace(r'\-', '-') + '/response-' + '[a-f0-9]' * 64 + '[.]json$'
    response_exception = '(require-not (regex #' + json.dumps(response_pattern) + '))'
    shared_writes = '\n'.join('(require-not (literal ' + json.dumps(str(p)) + '))' for p in shared)
    root = json.dumps(str(stage_root))
    network = '''(allow network-outbound (remote tcp "*:443"))
(allow network-outbound (remote udp "*:53"))
(allow network-outbound (remote unix-socket (literal "/private/var/run/mDNSResponder")))''' if authenticated else ''
    return f'''(version 1)
(allow default)
(deny network*)
{network}
(deny file-read-data (require-all (subpath {json.dumps(str(home))})
 (require-not (subpath {root})) {exceptions} {response_exception}))
(deny file-write* (require-all (subpath {json.dumps(str(home))}) (require-not (subpath {root})) {shared_writes} {response_exception}))
(deny file-write* (literal {json.dumps(str(stage_root / 'policy.json'))})
 (literal {json.dumps(str(stage_root / 'policy.sha256'))}) (literal {json.dumps(str(binding.scope))}))
'''


def execute(binding, *, request, prompt, schema, packet, owner_check, deadline, out):
    """Original broker/guard receipts; the caller still uses the original StageController."""
    scope = binding.verify()
    require_request(request, prompt, schema, packet, scope)
    if not callable(owner_check) or not owner_check() or not 0 < deadline - time.time() <= 600:
        raise ValueError('live_owner_deadline_required')
    original_module = original(binding)
    t = original_module.t
    wire_schema, schema_binding = original_module.adapt(schema)
    stage = 'BLIND' if request['stage'] == 'BLIND' else 'ADJ'
    root = binding.root / stage
    root.mkdir(mode=0o700)
    for name in ('input', 'scratch', 'state', 'logs', 'tmp'):
        (root / name).mkdir()
    write_once(root / 'input/public_packet.json', packet)
    write_once(root / 'input/original_prompt.txt', prompt.encode())
    files = {p.name: t.pin(p) for p in (root / 'input').iterdir()}
    broker = original_module.PublicBroker(root, files=files, deadline=deadline, budget=binding.root / 'tool-budget.json',
        security=scope['security'], generation=scope['source_generation'], owner_ref=digest(packet),
        session=request['invocation_id'], owner_check=owner_check, request_identity=request)
    write_once(root / 'host.sb', host_profile(binding, root, authenticated=True).encode())
    env = dict(PATH='/usr/bin:/bin', HOME=str(Path.home()), CODEX_HOME=str(Path.home() / '.codex'),
               TMPDIR=str(root / 'tmp'), RUST_LOG='off', CODEX_DISABLE_REMOTE_CONTROL='1',
               TM_P1_DISPATCH_POLICY=str(root / 'policy.json'), TM_P1_DISPATCH_POLICY_PIN_FILE=str(root / 'policy.sha256'),
               TM_SOL_TASK_SCOPE=str(binding.scope), TM_SOL_TASK_SCOPE_SHA256=binding.scope_sha256, TM_P1_POLICY_AUDIT='1')
    args = ['/usr/bin/sandbox-exec', '-f', str(root / 'host.sb'), str(binding.binary), '--listen', 'stdio://'] + config_args(binding, root)
    client = None
    runtime = dict(verified=False, model=SOL_HIGH_V1.model, effort=SOL_HIGH_V1.effort,
                   execution_profile=SOL_HIGH_V1.contract, guard_binary_sha256=binding.binary_sha256)
    try:
        broker.start()
        client = original_module.load_transport()(args, cwd=root / 'input', env=env, stderr=root / 'host.stderr.log')
        client.rpc('initialize', dict(clientInfo=dict(name='tm_guarded_sol', version='1'), capabilities=dict(experimentalApi=True)))
        client.send(dict(method='initialized', params={}))
        account = client.rpc('account/read', dict(refreshToken=False))
        if account.get('account', {}).get('type') != 'chatgpt':
            raise ValueError('signed_in_chatgpt_required')
        del account
        client.events.clear(); client.pending.clear()
        thread = client.rpc('thread/start', dict(model=SOL_HIGH_V1.model, ephemeral=True, approvalPolicy='never', environments=[],
            dynamicTools=[original_module.SPEC], cwd=str(root / 'input'), runtimeWorkspaceRoots=[], experimentalRawEvents=False,
            baseInstructions='Follow the supplied versioned public research contract. Only bounded tm_analysis computations are permitted. Tool outputs are not source authority. Return the required JSON.',
            developerInstructions='The two public files are exact prompt and packet copies. Preserve all source-use restrictions.'))
        tid = thread['thread']['id']
        if thread['model'] != SOL_HIGH_V1.model:
            raise ValueError('returned_thread_model')
        policy = dict(task=TASK, execution_profile=SOL_HIGH_V1.contract, account=request['account'], stage=stage,
            security=scope['security'], owner_sha256=digest(packet), prompt_sha256=digest(prompt.encode()), request_sha256=digest(request),
            thread_id=tid, source_generation=scope['source_generation'], schema=wire_schema,
            schema_binding={k: schema_binding[k] for k in ('adapter_version', 'canonical_schema_sha256', 'wire_schema_sha256', 'changed_paths')},
            started_unix=int(time.time()), deadline_unix=int(deadline - 5), ledger=scope['ledger'])
        write_once(root / 'policy.json', policy, 0o400)
        write_once(root / 'policy.sha256', digest((root / 'policy.json').read_bytes()).encode(), 0o400)
        turn = client.rpc('turn/start', dict(threadId=tid, environments=[], input=[dict(type='text', text=prompt)],
                          effort=SOL_HIGH_V1.effort, outputSchema=wire_schema), seconds=min(30, deadline-time.time()-10))
        turn_id = turn['turn']['id']; broker.bind(tid, turn_id)
        pending = list(client.pending); client.pending.clear(); completion = None
        while time.time() < deadline - 10:
            try:
                message = pending.pop(0) if pending else client.receive(min(5, max(.01, deadline-time.time()-10)))
            except queue.Empty:
                continue
            method = message.get('method')
            if method == 'item/tool/call':
                reply = broker.dispatch(message['params']); client.send(dict(id=message['id'], result=reply))
            elif 'id' in message and method:
                raise ValueError('unexpected_server_request')
            elif method == 'turn/completed':
                if message['params']['threadId'] != tid or message['params']['turn']['id'] != turn_id:
                    raise ValueError('completion_binding')
                completion = message['params']['turn']; break
        if not completion or completion['status'] != 'completed':
            raise ValueError('turn_not_completed_no_retry')
        items = [e['message']['params']['item'] for e in client.events if e['direction'] == 'receive'
                 and e['message'].get('method') == 'item/completed' and e['message']['params']['item'].get('type') == 'agentMessage']
        raw = items[-1]['text'].encode()
        write_once(out / 'MODEL_RAW.txt', raw)
        if len(raw) > 131072:
            raise ValueError('output_limit_no_truncation')
        value = json.loads(raw)
        rows = t.load(binding.root / 'inference-ledger.json')
        rows = [r for r in rows if r['thread_id'] == tid]
        if not rows or any(r['request_sha256'] != digest(request) or r['model'] != SOL_HIGH_V1.model or r['effort'] != SOL_HIGH_V1.effort for r in rows):
            raise ValueError('guard_receipt_binding')
        responses = [t.load(binding.root / ('response-' + r['wire_sha256'] + '.json')) for r in rows]
        if not all(r['response_status'] == 200 and r['response_headers_received'] for r in responses) or not owner_check():
            raise ValueError('authentic_response_and_live_owner_required')
        runtime.update(verified=True, session=tid, guard_requests=rows, response_receipts=responses)
        return value, runtime
    finally:
        if client:
            runtime['host_shutdown'] = client.close()
        runtime['executor_shutdown'] = broker.close()
        runtime['broker_receipts'] = broker.receipts
        write_once(out / 'HOST_TRANSPORT.json', runtime)
