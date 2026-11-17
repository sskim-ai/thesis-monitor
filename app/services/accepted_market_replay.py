"""Verify a sealed MARKET response against the rebuilt canonical MARKET input."""
from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from app.services.model_invocation_journal import read_invocation_journal
from app.services.production_model_profile import SolHighWirePolicy
from app.services.research_artifact_budget import plain_path
from app.services.research_request_storage import load_stage_request, load_stage_response
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded


@dataclass(frozen=True)
class AcceptedMarketOrigin:
    seal: Path
    seal_sha256: str
    stage_directory: Path
    invocation_journal: Path


def _require(condition, code):
    if not condition:
        raise ValueError('market_replay_' + code)


def _market_content(market):
    display = market['views']['display']
    # These two pins include the whole Source graph, including stock custody.
    origin = {k:v for k,v in display['origin'].items() if k not in {'authority_sha256','source_packet_sha256'}}
    return {k:market[k] for k in ('packet','context','schema')} | {
        'directional': market['views']['directional'], 'display': dict(display, origin=origin)}


def verify_market_replay(origin, *, snapshot, session, item):
    from dataclasses import asdict
    from app.services import canonical_monitoring_domain as domain
    from app.services.new_buyer_base_contract import validate_json_schema
    from app.services.official_codex_shadow_transport_service import command_prefix
    from app.services.vnext_execution_profile import SOL_HIGH_V1

    _require(type(origin) is AcceptedMarketOrigin, 'explicit_origin_required')
    archive = plain_path(origin.seal).read_bytes()
    _require(sha256_bytes(archive) == origin.seal_sha256, 'seal_hash_drift')
    with ZipFile(BytesIO(archive)) as z:
        _require(len(z.namelist()) == len(set(z.namelist())), 'duplicate_sealed_member')
        manifest = json.loads(z.read('MANIFEST.json'))['files']

        def member(name):
            raw = z.read(name)
            _require(manifest.get(name) == dict(bytes=len(raw), sha256=sha256_bytes(raw)), 'manifest_member_drift')
            return raw

        sealed_response = member('model/KR_MARKET_response.json')
        raw = member('model/raw-output.json')
        transport = json.loads(member('model/transport-receipt.json'))
        authorization = json.loads(member('model/production-authorization.json'))
        parent_exit = json.loads(member('model/parent-exit.json'))
        journal = member('model/invocation-events.jsonl')
        pins = json.loads(member('evidence/recovery1/OS_PLAN.json'))['binding']['code_pins']
        runtime = json.loads(member('evidence/prior_same_C22AQ/CURRENT_RUNTIME_BINDING.json'))

    # The original acceptance policy is not replaced by a matching response hash.
    repo = Path(__file__).resolve().parents[2]
    for name in ('app/services/production_monitoring_session.py', 'app/services/canonical_monitoring_domain.py',
                 'app/services/market_numeric_claim_service.py', 'app/services/canonical_monitoring_owner.py',
                 'app/services/official_night_market_eligibility_service.py',
                 'scripts/m12ds_r4_r4_market.py', 'scripts/m12ds_r4_r1_market.py', 'scripts/m12ds_r3_market.py',
                 'scripts/m12ds_r2_market.py', 'scripts/m12ds_r2_judgment_policy.py'):
        path = repo / name
        _require(sha256_bytes(path.read_bytes()) == pins.get(str(path)), 'market_policy_drift')

    directory = plain_path(origin.stage_directory)
    _require(plain_path(origin.invocation_journal).read_bytes() == journal, 'origin_journal_drift')
    response_path = plain_path(directory / 'response.json')
    _require(response_path.read_bytes() == sealed_response, 'origin_response_drift')
    sealed = json.loads(sealed_response)
    old_request = load_stage_request(directory / 'request.json', expected_logical_sha256=sealed['request_sha256'])
    old_result = load_stage_response(response_path, old_request)
    old = old_request['snapshot']
    a, b = old['child_binding'], snapshot['child_binding']
    old_source = old['collection']['monitoring_input']
    new_source = snapshot['collection']['monitoring_input']
    _require(a['run_id'] != b['run_id'] and session.gen == b['run_id'] and session.market == 'kr'
        and session.source_gen == b['source_generation']
        and all(a[k] == b[k] for k in ('market', 'source_generation', 'assessment_date', 'cutoff', 'effective_at', 'message_ids'))
        and old['collection']['production_envelope']['subjects'] == snapshot['collection']['production_envelope']['subjects'],
        'origin_scope_drift')
    session._verify_native_source()
    _require(digest(old_source) == a['consumed_source_sha256'] and digest(new_source) == b['consumed_source_sha256'],
        'consumed_source_hash_drift')
    _require(digest(session.source) == b['consumed_source_sha256'], 'session_source_hash_drift')
    # A changed whole-source snapshot needs the existing live cohort owner.
    # Historical MARKET-only rendering can still replay the exact old snapshot.
    _require(a['consumed_source_sha256'] == b['consumed_source_sha256']
        or session._frozen_cohort is not None, 'current_cohort_source_required')
    if (cohort := session._frozen_cohort) is not None:
        from app.services.model_execution_plan import compile_model_plan

        _require(cohort.sha256 == b['cohort_sha256']
            and compile_model_plan(cohort,topology='CANONICAL_PRODUCTION').sha256 == b['plan_sha256']
            and list(cohort.market_subjects['kr']) == snapshot['collection']['production_envelope']['subjects'],
            'current_cohort_scope_drift')
    stock_only = {'prepared','stocks','coverage','census','whole_source_sha256'}
    _require(set(old_source) == set(new_source) and all(old_source[k] == new_source[k]
        for k in old_source if k not in stock_only | {'markets'}), 'source_scope_drift')
    _require(set(old_source['markets']) == set(new_source['markets']) == {'kr'}
        and _market_content(old_source['markets']['kr']) == _market_content(new_source['markets']['kr']),
        'market_input_source_drift')

    old_build = json.loads(plain_path(directory / 'canonical/sealed/requests/market/kr/batch-01/request-receipt.json').read_bytes())
    old_accept = json.loads(plain_path(directory / 'model-1/attempt-1/receipt.json').read_bytes())
    semantic = json.loads(plain_path(directory / 'canonical/sealed/validated/MARKET/1/semantic.json').read_bytes())
    accepted = json.loads(plain_path(directory / 'canonical/sealed/validated/MARKET/1/accepted.json').read_bytes())
    _require(len(old_result['output']['rows']) == 1, 'origin_market_rows')
    row = old_result['output']['rows'][0]
    payload = item['payload']
    pin, output_sha = digest(payload), sha256_bytes(raw)
    state = read_invocation_journal(journal)
    slot = authorization['slot_scope']['slot_id']
    scope = state['bound'].get(slot)
    _require(scope is not None and scope == authorization['slot_scope'] and scope['stage'] == 'MARKET'
        and scope['market'] == 'kr' and scope['source_generation'] == a['source_generation']
        and scope['cohort_sha256'] == a['cohort_sha256'] and scope['plan_sha256'] == a['plan_sha256']
        and state['used'] == {slot} and state['accepted'] == {slot: output_sha} and state['stopped'],
        'original_invocation_not_accepted')
    _require(old_build['payload'] == payload and old_build['payload_sha256'] == item['payload_sha256'] == pin
        and old_build['internal_schema_sha256'] == item['internal_schema_sha256']
        and old_build['execution_generation_id'] == a['run_id'] and old_build['source_generation_id'] == a['source_generation']
        and digest(old_build) == scope['build_receipt_sha256'] and scope['payload_sha256'] == pin
        and row == dict(batch=1, subjects=[], output=json.loads(raw), payload_sha256=pin, raw_sha256=output_sha)
        and accepted == row['output'] and old_accept == dict(request_sha256=pin, classification='ACCEPTED', ordinal=1, raw_sha256=output_sha)
        and not validate_json_schema(row['output'],payload['response_schema'])
        and semantic == domain.market_owner.validate_market(row['output'], payload['input']) and semantic['status'] == 'PASS',
        'canonical_acceptance_or_payload_drift')
    proof = transport['transport']
    expected_command = [runtime['executable'], *command_prefix(SOL_HIGH_V1)]
    _require(transport['status'] == 'PASS' and proof['transport_attempts'] == 1 and proof['cli_returncode'] == 0
        and proof['command'][:len(expected_command)] == expected_command
        and proof['qualification_sha256'] == runtime['qualification_sha256']
        and proof['execution_policy'] == asdict(SolHighWirePolicy()) and proof['model_plan_scope'] == scope
        and proof['prompt_sha256'] == authorization['prompt_sha256'] == sha256_bytes(payload['prompt'].encode())
        and proof['schema_sha256'] == authorization['schema_sha256'] == sha256_bytes(encoded(payload['response_schema']))
        and proof['request_id'] == authorization['request_id'] and authorization['run_id'] == a['run_id']
        and parent_exit == dict(status='WORKER_EXITED', child_reaped=True, returncode=0, raw_bytes=len(raw), raw_sha256=output_sha),
        'transport_proof_drift')
    lineage = dict(origin_seal_sha256=origin.seal_sha256, origin_execution=a['run_id'], origin_slot=slot,
        origin_request_sha256=sealed['request_sha256'], origin_response_sha256=sha256_bytes(sealed_response),
        origin_journal_sha256=sha256_bytes(journal), source_generation=a['source_generation'],
        output_sha256=output_sha, payload_sha256=pin, prompt_sha256=proof['prompt_sha256'],
        schema_sha256=proof['schema_sha256'], inherited_stage='MARKET', new_model_invocations=0,
        continuation_execution=b['run_id'], continuation_plan_sha256=b['plan_sha256'])
    return row, lineage
