"""Receipt-gated replay of unchanged R3 owners and the accepted Market consumer.

No model transport, source acquisition or production write route is imported.
An incompatible Market input is reported, never converted by a guessed adapter.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

from app.services import canonical_business_quality_owner as quality
from app.services.unified_snapshot_contract import digest
from scripts import m12ds_r4_r4_market as market_owner
from scripts import r2b_r1_offline_closure as r1
from scripts import r2b_r2_preflight as previous
from scripts import r2b_r3_quality as binding
from scripts import r2b_sealed_blind_preflight as io
from scripts.sealed_cohort_offline_proof import network_guard
from scripts.unified_stock_owner_proof import POLICY

RECEIPT_SHA = '9c9eec930400db3e7390984b6045e72961684e3db774eedd633b3f6fa1e9650d'
R3_SHA = '16786785bd476eb2b6241fded2b0e1a92e3411bd807e45f8d6e1a06d94e52bf8'
SUPPLEMENT_SHA = '2d59748a3064a91d1ddcbbb68aefb90a961eaf4e9baa4334619c4e0db38f7edd'
ASSESSMENT_JSON_SHA = '9a083de6bef2b5b0e617136e10a67eed00ff5cacffc79809825f2ea51d34557d'
ASSESSMENT_ZIP_SHA = 'b025e86ba211fafe89d56be8268652c6482d589ea12e8510dbf040442e40ed77'


def verify_receipt(raw):
    quality.require(io.sha(raw) == RECEIPT_SHA, 'neutral_v2_receipt_hash_mismatch')
    receipt = json.loads(raw)
    expected = dict(
        contract='external-independent-blind-freeze-receipt-v2-quality-supplement',
        status='INDEPENDENT_ASSESSMENT_V2_FROZEN',
        blind_source_review_sha256=r1.BLIND_SHA,
        quality_supplement_sha256=SUPPLEMENT_SHA,
        parent_v1_assessment_sha256='95776285ba2653ec102517315f16259c7d9f0f314ab5af01b715308b87dda50b',
        independent_assessment_v2_json_sha256=ASSESSMENT_JSON_SHA,
        independent_assessment_v2_bundle_sha256=ASSESSMENT_ZIP_SHA,
        independent_assessment_content_included=False,
        monitoring_ai_model_outputs_seen_before_freeze=False,
        monitoring_ai_calls_before_freeze=dict(Market=0, Core=0, A=0, B=0),
        review_order='BLIND_SOURCE_PLUS_QUALITY_SUPPLEMENT_FIRST_THEN_MONITORING_AI')
    quality.require(all(receipt.get(k) == v for k, v in expected.items()), 'neutral_v2_receipt_contract_mismatch')
    return dict(status='PASS_V2', receipt_sha256=RECEIPT_SHA,
        source_blind_sha256=r1.BLIND_SHA, quality_supplement_sha256=SUPPLEMENT_SHA,
        independent_content_read=False, assertions_verified_against_neutral_receipt=True,
        assessment_archives_opened=False, assessment_content_hashes_not_independently_read=True)


def market_preflight(packet):
    before = digest(packet)
    result = dict(market=packet['market'], input_sha256=before,
        source_root_keys=sorted(packet), adapter='scripts.m12ds_r4_r4_market.market_context',
        producer='app.services.unified_full_source_cohort.compose_full_source',
        source_policy_modified=False, synthesized_market_context=False)
    try:
        context = market_owner.market_context(packet)
        quality.require(context['parity_status'] == 'PASS', 'market_source_request_parity_failed')
        schema = previous.schema_check(market_owner.market_schema(context))
        numeric = market_owner.numeric_boundary(context, packet['market_context'])
        quality.require(numeric['status'] == 'PASS', 'market_numeric_boundary_failed')
        result.update(status='PASS', context_sha256=digest(context), schema=schema,
                      numeric_boundary=numeric)
    except (KeyError, ValueError, TypeError) as exc:
        result.update(status='BLOCKED', error_type=type(exc).__name__, error=str(exc),
            missing_input_field=exc.args[0] if isinstance(exc, KeyError) else None,
            reason='SEALED_MARKET_PRODUCER_CONSUMER_INPUT_CONTRACT_UNCLOSED')
    quality.require(digest(packet) == before, 'market_consumer_mutated_source')
    return result


def run(args):
    network = network_guard()
    args.output.mkdir(parents=True, exist_ok=False)
    audit = previous.SourceReadAudit([args.receipt, args.r3_zip, args.source_zip],
        [args.receipt.parent, args.r3_zip.parent, args.source_zip.parent,
         Path('/tmp/codex-remote-attachments'), Path.home() / 'Library/Mobile Documents/com~apple~CloudDocs'])
    sys.addaudithook(audit)
    fairness = verify_receipt(args.receipt.read_bytes())
    quality.require(io.sha(args.r3_zip.read_bytes()) == R3_SHA, 'r3_result_hash_mismatch')
    members = []
    with zipfile.ZipFile(args.r3_zip) as archive:
        manifest = json.loads(archive.read('report/bundle-manifest.json'))
        quality.require(len(manifest) == 78 and set(archive.namelist()) ==
            {'report/' + n for n in manifest} | {'report/bundle-manifest.json'}, 'r3_manifest_coverage')
        for name, item in manifest.items():
            raw = archive.read('report/' + name)
            quality.require(io.sha(raw) == item['sha256'] and len(raw) == item['bytes'], 'r3_manifest_integrity')
        inventory = json.loads(archive.read('report/business-quality-owner-applicability-matrix.json'))
        old = json.loads(archive.read('report/final-preflight/preflight.json'))
        accepted_supplements = json.loads(archive.read('report/final-preflight/quality-supplements.json'))
        quality.require(digest(accepted_supplements) == SUPPLEMENT_SHA, 'accepted_quality_supplement_mismatch')
    manifest = io.read_verified_archive(args.source_zip, io.SOURCE_ZIP_SHA)
    generation = '20260928-r2b-r4-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    rows, prepared, supplements = [], {}, {}
    with zipfile.ZipFile(args.source_zip) as archive:
        def read(name):
            members.append(dict(path=name, sha256=manifest[name]['sha256']))
            return archive.read(name)
        combined = json.loads(read('whole-1/combined-full-source-packet.json'))
        for name, expected in r1.SOURCE_HASHES.items():
            quality.require(digest(json.loads(read('whole-1/' + name))) == expected, 'source_identity_mismatch')
        cutoff = datetime.fromisoformat(combined['seed']['started_at'])
        plan = json.loads(read('input/sealed-live/rev8-full-source-acquisition-plan.json'))
        versions = {t: read('input/sealed-live/class-c/business-versioned-' + t + '.json')
                    for ts in io.UNIVERSE.values() for t in ts}
        locals_ = {m: json.loads(read('input/sealed-live/class-c/local-' + m + '.json')) for m in io.UNIVERSE}
        params = dict(versions=versions, version_hashes=plan['class_c_versions'],
                      local_seeds=list(locals_.values()), cutoff=cutoff, policy=POLICY)
        for item in inventory['rows']:
            ticker, market = item['ticker'], item['market']
            stock = combined['packets'][market]['stocks'][ticker]
            authority = combined['authority_graph']['stocks'][ticker]
            if item['classification'] == 'EXPECTED_OWNER_OUTPUT_RECONSTRUCTIBLE':
                supplement = quality.derive(stock=stock, **params)
                quality.require(supplement == accepted_supplements[ticker], 'quality_replay_drift:' + ticker)
                supplements[ticker] = supplement
                stock, authority = binding.bind_supplement(stock, authority, supplement, owner_inputs=params)
            projection = binding.require_quality_owner(stock, authority, decision_mode=item['decision_mode'])
            row, inputs = previous.preflight_subject(stock, authority, locals_[market], generation=generation,
                cutoff=combined['seed']['started_at'], defer_b=True, source_view_owner=binding.quality_source_view)
            row['quality_owner_projection'] = projection
            rows.append(row)
            prepared[ticker] = inputs
        quality.require(sum(r['A'] == 'PASS' for r in rows) == 22, 'whole_a_replay_drift')
        for row in rows:
            data = prepared[row['ticker']]
            if data['mode'] != 'UNKNOWN_LIMIT':
                ctx, entries, valuation = previous.b_input(data['view'], **data['b_probe_inputs'])
                cap = data['b_probe_inputs']['capability']
                row.update(B='PASS', Holder='PASS', status='PASS', b_context_sha256=digest(ctx),
                    b_schema=previous.schema_check(previous.c.decision_schema(data['mode'], cap, valuation, entries, {})))
        quality.require(digest(supplements) == SUPPLEMENT_SHA, 'supplement_aggregate_drift')
        for row, prior in zip(rows, old['rows'], strict=True):
            quality.require(row['ticker'] == prior['ticker'] and row['quality_owner_projection'] ==
                prior['quality_owner_projection'], 'quality_projection_drift')
        stages = {s: sum(r.get(s) == 'PASS' for r in rows) for s in ('Core', 'A', 'B')}
        quality.require(stages == dict(Core=22, A=22, B=22), 'whole_stock_readiness_drift')
        # Actual accepted consumer call, with no invented input translation.
        markets = [market_preflight(combined['packets'][m]) for m in ('us', 'kr')]
    ready = all(m['status'] == 'PASS' for m in markets)
    summary = dict(terminal='R2B_R4_PREFLIGHT_READY_FOR_BINDING' if ready else 'R2B_R4_PREMODEL_CONTRACT_DRIFT',
        status='PASS' if ready else 'BLOCKED', generation_id=generation, blind_fairness_gate=fairness['status'],
        stage_ready=stages, market_input_ready=sum(m['status'] == 'PASS' for m in markets),
        quality_applicability=dict(Counter(r['classification'] for r in inventory['rows'])),
        quality_supplement_sha256=digest(supplements), quality_owner_gaps=0,
        stored_price_rule_versions_pass=sum(r['source_view_receipt']['strategy']['status'] == 'PASS' for r in rows),
        model_visible_time_unclassified=sum(r['canonical_source_time_unclassified'] for r in rows),
        source_hashes=r1.SOURCE_HASHES, neutral_v2_receipt_sha256=RECEIPT_SHA,
        independent_assessment_content_read=False, reveal_gate='CLOSED',
        model_input_binding='NOT_ISSUED', model_calls=dict(Market=0, Core=0, A=0, B=0),
        provider_refresh=0, production_side_effects=0, actual_messages=0,
        instruction_commit='9e825f499baa18ba985a8eda2cea1402c49e1825',
        implementation=io.git('rev-parse', 'HEAD'), worktree_clean=not bool(io.git('status', '--porcelain')),
        prior_missing_receipt_blocker_resolved=True, source_policy_repair_performed=False,
        probes_not_model_outputs=True)
    for name, data in (('summary.json', summary), ('fairness-gate.json', fairness),
        ('stock-preflight.json', rows), ('prepared-inputs.json', prepared),
        ('market-input-contract-audit.json', markets), ('quality-supplements.json', supplements),
        ('source-read-audit.json', {**audit.receipt(), 'source_archive_members': members, 'network': network})):
        io.save(args.output, name, data)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'receipt', 'r3-zip', 'source-zip'):
        parser.add_argument('--' + name, type=Path, required=True)
    run(parser.parse_args())
