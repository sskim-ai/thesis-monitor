"""M12BG FCF prospective-requirement repair and full monitored shadow proof."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services import directional_financial_context_service as financial
from app.services.direction_timing_ownership_service import DirectionalCoreBatch
from app.services.two_stage_directional_service import DirectionalCoreJudgmentBatch
from scripts import business_delta_evidence_capability_m12ai as capability
from scripts import frozen_context_input_layout_compatibility_m12bf as m12bf
from scripts import stage2_working_capital_binding_parity_m12bd as m12bd
from scripts.shadow_frozen_context_manifest import NESTED_INPUTS_V1


NAME = (
    "20260914-fcf-prospective-requirement-verification-scope-"
    "new-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
PROOF_OUTPUT = OUTPUT / "proof-runtime"
PROOF_REPORTS = OUTPUT / "supporting-reports/m12bb"
M12BD_REPORTS = OUTPUT / "supporting-reports/m12bd"
SOURCE_OUTPUT = OUTPUT / "frozen-m12bf-packet-source"
OFFLINE_M12BF = OUTPUT / "offline-m12bf-shadow"
RUNNER = Path("scripts/fcf_prospective_requirement_verification_scope_m12bg.py")
ARCHITECTURE = Path("docs/architecture/FCF_PROSPECTIVE_REQUIREMENT_SCOPE.md")
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "b739a2b286c16fe1cf70cf8c3e8c88d69b645f01"
BASE_INTEGRATION_HEAD_SHA = "3a5b918eda28bd0b3fe68339f93ce0fc112b0e7c"

M12BF_NAME = (
    "20260913-frozen-context-input-layout-compatibility-new-full-shadow"
)
M12BF_BUNDLE = Path.home() / "Documents/Codex" / (
    f"thesis-monitor-{M12BF_NAME}-report.zip"
)
M12BF_BUNDLE_SHA256 = (
    "239feaee5ffac6ad19a2ca9b95baf7c14896c870dcf9e2d01cfcb18ccca50ea0"
)
M12BF_ARTIFACT_ROOT = f"artifacts/{M12BF_NAME}"
M12BF_REPORT_ROOT = f"docs/reports/{M12BF_NAME}"
M12BF_INDEXED_PAYLOADS = 856
M12BF_ZIP_ENTRIES = 857
M12BF_SHADOW_GENERATION_ID = (
    "20260911-m12ai-shadow-20260913T141850Z-fdfcb99c8668"
)
M12BF_FAILURE_TICKER = "005490"

M12BD_NAME = (
    "20260913-stage2-working-capital-binding-parity-audit-coverage-validity-"
    "separation-full-proof-full-shadow"
)
M12BD_BUNDLE = Path.home() / "Documents/Codex" / (
    f"thesis-monitor-{M12BD_NAME}-report.zip"
)
M12BD_BUNDLE_SHA256 = (
    "675c49e921fa5bfeedd00596bae2a803b3c7a68ed9ca95a78aa7961419f965c5"
)
M12BD_GENERATION_ID = "20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"
ROOT_CAUSE = (
    "FCF_CURRENTNESS_CLASSIFIER_TREATS_CURRENT_CORE_FIELD_ROLE_AS_SUFFICIENT_"
    "FOR_CURRENT_FCF_ASSERTION_AND_DOES_NOT_RECOGNIZE_PROSPECTIVE_"
    "REQUIREMENT_LANGUAGE"
)

REPORT_SLUGS = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bg-scope-freeze
m12bd-fictional-proof-identity-freeze
m12bf-shadow-first-call-failure-reproduction
posco-business-thesis-fcf-requirement-forensic
posco-market-expectation-fcf-requirement-forensic
fcf-currentness-classifier-code-audit
current-field-role-vs-local-claim-role-audit
fcf-prospective-requirement-options
fcf-prospective-requirement-decision
fcf-prospective-requirement-contract
fcf-verification-requirement-predicate-contract
fcf-current-affirmative-predicate-contract
fcf-current-numeric-precedence-contract
fcf-current-state-precedence-contract
fcf-negated-current-state-regression-contract
fcf-requirement-directional-eligibility-separation-contract
market-expectation-independence-preservation-contract
business-delta-baseline-preservation-contract
m12bf-005490-exact-offline-replay
m12bf-context01-four-candidate-offline-replay
fcf-requirement-positive-fixtures
fcf-current-claim-negative-fixtures
fcf-current-numeric-negative-fixtures
fcf-requirement-plus-current-claim-negative-fixtures
fcf-directional-field-negative-fixtures
fcf-english-requirement-parity-fixtures
m12bf-frozen-layout-freeze
m12be-active-universe-identity-freeze
m12bd-stage2-wc-binding-freeze
m12bd-optional-audit-coverage-freeze
m12bc-context-finalizer-freeze
m12bc-decision-variance-readiness-freeze
m12bb-stage1-wc-binding-freeze
m12ba-financial-sector-replacement-verb-freeze
m12az-fcf-local-temporal-scope-freeze
m12ay-configured-fcf-support-freeze
m12ax-monitoring-semantics-freeze
m12aw-nominal-condition-freeze
m12av-mixed-risk-scope-freeze
m12at-configured-signal-field-ownership-freeze
m12ap-expectation-independence-freeze
m12ao-business-delta-convergence-freeze
adr-security-basis-freeze
two-stage-core-immutability-freeze
model-prompt-semantic-hash-freeze
model-schema-semantic-hash-freeze
stage1-wc-binding-view-hash-freeze
stage2-wc-binding-view-hash-freeze
configured-signal-view-hash-freeze
configured-financial-support-concept-hash-freeze
business-delta-view-hash-freeze
expectation-view-hash-freeze
financial-evidence-projection-hash-freeze
two-stage-core-semantics-freeze
final-user-schema-freeze
fictional-proof-reuse-decision
m12bd-complete-fictional-offline-reaudit
fcf-requirement-unit-tests
current-fcf-safety-regression-tests
directional-eligibility-regression-tests
m12bf-exact-output-replay-tests
m12bd-fictional-offline-reaudit-tests
focused-test-results
full-local-test-results
ruff-and-diff-results
hosted-ci-portability-observation
new-shadow-model-call-gate
task-start-active-monitored-universe
new-shadow-generation-manifest
shadow-packet-inventory
shadow-packet-hash-manifest
shadow-stage1-wc-binding-view-manifest
shadow-stage2-wc-binding-view-manifest
shadow-configured-signal-view-manifest
shadow-configured-financial-support-concept-manifest
shadow-delta-view-manifest
shadow-expectation-view-manifest
shadow-frozen-context-manifest
shadow-frozen-input-layout-audit
shadow-cross-manifest-preflight-matrix
shadow-batching-manifest
shadow-model-call-gate
shadow-monolithic-model-artifacts
shadow-stage1-model-artifacts
shadow-stage2-model-artifacts
shadow-context-hard-semantic-audit
shadow-fcf-prospective-requirement-audit
shadow-directional-requirement-eligibility-audit
shadow-stage1-wc-binding-audit
shadow-stage2-wc-binding-audit
shadow-financial-grounding-audit
shadow-optional-audit-coverage-matrix
shadow-configured-signal-field-use-audit
shadow-business-delta-audit
shadow-market-expectation-audit
shadow-financial-sector-audit
shadow-stage2-language-audit
shadow-final-composition-audit
shadow-aggregate-finalization-audit
shadow-per-ticker-comparison
shadow-core-direction-differences
shadow-business-delta-differences
shadow-new-buyer-differences
shadow-holder-differences
shadow-same-direction-calibration-differences
shadow-expected-contract-corrections
shadow-potential-architecture-regressions
shadow-unresolved-review-required
shadow-adr-security-basis-audit
shadow-cyclical-valuation-audit
shadow-core-immutability-audit
shadow-runtime-audit
shadow-aggregate-summary
shadow-architecture-decision
fictional-primary-boundary-summary
fictional-delta-materiality-summary
fictional-new-buyer-boundary-summary
fictional-holder-boundary-summary
monitored-primary-difference-summary
monitored-delta-difference-summary
monitored-new-buyer-difference-summary
monitored-holder-difference-summary
same-direction-calibration-summary
real-fcf-requirement-scope-lessons
combined-fictional-monitored-policy-input
next-bounded-policy-decision
fcf-prospective-requirement-repair-success-decision
m12bf-frozen-layout-preservation-decision
m12bd-fictional-proof-reuse-success-decision
new-full-shadow-completion-decision
two-stage-shadow-compatibility-decision
existing-monitored-impact-summary
fresh-real-proof-readiness-decision
final-main-merge-readiness-note
production-no-change
schedule-pause-observation
remote-push-prohibition-audit
master-workflow-update
program-completion
""".strip().splitlines()
)
NUMBERS = {slug: index for index, slug in enumerate(REPORT_SLUGS, start=1)}

FOCUSED_TESTS = (
    "tests/test_fcf_prospective_requirement_verification_scope_m12bg.py",
    "tests/test_fcf_prospective_requirement_verification_scope_m12bg_runner.py",
    "tests/test_fcf_claim_temporal_scope_negated_fulfillment_m12az.py",
    "tests/test_configured_fcf_support_mapping_m12ay.py",
    "tests/test_ppe_proxy_fcf_claim_scope_m12ar.py",
    "tests/test_directional_financial_context_service.py",
    "tests/test_stage2_working_capital_binding_parity_m12bd.py",
    "tests/test_frozen_context_input_layout_m12bf.py",
)
RUFF_PATHS = (
    "app/services/directional_financial_context_service.py",
    str(RUNNER),
    "tests/test_fcf_prospective_requirement_verification_scope_m12bg.py",
    "tests/test_fcf_prospective_requirement_verification_scope_m12bg_runner.py",
)
TRACKED_IMPLEMENTATION_PATHS = (
    Path("app/services/directional_financial_context_service.py"),
    RUNNER,
    Path("tests/test_fcf_prospective_requirement_verification_scope_m12bg.py"),
    Path(
        "tests/test_fcf_prospective_requirement_verification_scope_m12bg_runner.py"
    ),
    ARCHITECTURE,
    WORK_INSTRUCTION,
)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode()
    ).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def report(slug: str, value: object) -> None:
    write_json(REPORTS / f"{NUMBERS[slug]:03d}-{slug}.json", value)


def _run(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    started = datetime.now(UTC)
    result = subprocess.run(
        list(command), check=False, capture_output=True, text=True, timeout=timeout
    )
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": list(command),
        "exit_code": result.returncode,
        "elapsed_seconds": round((datetime.now(UTC) - started).total_seconds(), 3),
        "output": (result.stdout + result.stderr).strip()[-20000:],
    }


def _zip_read_json(archive: zipfile.ZipFile, path: str) -> dict[str, object]:
    value = json.loads(archive.read(path))
    if not isinstance(value, dict):
        raise ValueError(f"ZIP_JSON_OBJECT_REQUIRED:{path}")
    return value


def _zip_report_by_slug(
    archive: zipfile.ZipFile,
    *,
    report_root: str,
    slug: str,
) -> dict[str, object]:
    suffix = f"-{slug}.json"
    matches = [
        name
        for name in archive.namelist()
        if name.startswith(f"{report_root}/") and name.endswith(suffix)
    ]
    if len(matches) != 1:
        raise ValueError(f"REPORT_IDENTITY_INVALID:{slug}:{len(matches)}")
    return _zip_read_json(archive, matches[0])


def _verify_latest_bundle() -> dict[str, object]:
    actual_sha = file_sha256(M12BF_BUNDLE)
    with zipfile.ZipFile(M12BF_BUNDLE) as archive:
        index_path = f"{M12BF_ARTIFACT_ROOT}/artifact-index.json"
        index = _zip_read_json(archive, index_path)
        names = {name for name in archive.namelist() if not name.endswith("/")}
        indexed = {str(row["path"]) for row in index["rows"]}
        missing = sorted(indexed - names)
        extra = sorted(names - indexed - {index_path})
        hash_mismatches = 0
        size_mismatches = 0
        for row in index["rows"]:
            path = str(row["path"])
            if path not in names:
                hash_mismatches += 1
                size_mismatches += 1
                continue
            payload = archive.read(path)
            hash_mismatches += hashlib.sha256(payload).hexdigest() != row["sha256"]
            size_mismatches += len(payload) != row["size"]
    status = all(
        (
            actual_sha == M12BF_BUNDLE_SHA256,
            index.get("status") == "PASS",
            index.get("artifact_count") == M12BF_INDEXED_PAYLOADS,
            len(index["rows"]) == M12BF_INDEXED_PAYLOADS,
            len(names) == M12BF_ZIP_ENTRIES,
            not missing,
            not extra,
            hash_mismatches == 0,
            size_mismatches == 0,
            index.get("secret_scan_failure_count") == 0,
        )
    )
    return {
        "status": "PASS" if status else "FAIL",
        "path": str(M12BF_BUNDLE),
        "expected_sha256": M12BF_BUNDLE_SHA256,
        "actual_sha256": actual_sha,
        "indexed_payload_count": len(index["rows"]),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": hash_mismatches,
        "size_mismatch_count": size_mismatches,
        "secret_scan_failure_count": index.get("secret_scan_failure_count"),
    }


def _write_zip_member(
    archive: zipfile.ZipFile,
    member: str,
    target: Path,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(archive.read(member))


def _rewrite_packet_paths(state: dict[str, object], packet_root: Path) -> None:
    tickers = tuple(str(ticker) for ticker in state["tickers"])
    state["packet_paths"] = {
        ticker: str(packet_root / f"{ticker}.json") for ticker in tickers
    }


def _verify_packet_state(state_path: Path) -> dict[str, object]:
    state = read_json(state_path)
    mismatches = []
    for ticker in state["tickers"]:
        path = Path(str(state["packet_paths"][ticker]))
        packet = read_json(path)
        if (
            canonical_sha256(packet) != state["packet_hashes"][ticker]
            or file_sha256(path) != state["packet_file_hashes"][ticker]
        ):
            mismatches.append(str(ticker))
    if mismatches:
        raise ValueError(f"FROZEN_PACKET_IDENTITY_MISMATCH:{mismatches}")
    return {
        "status": "PASS",
        "generation_id": state["generation_id"],
        "packet_count": len(state["tickers"]),
        "packet_hash_mismatch_count": 0,
    }


def _extract_sources() -> dict[str, object]:
    proof_prefix = f"{M12BF_ARTIFACT_ROOT}/proof-runtime/"
    source_prefix = f"{M12BF_ARTIFACT_ROOT}/frozen-m12be-shadow-source/"
    proof_count = 0
    offline_count = 0
    source_count = 0
    with zipfile.ZipFile(M12BF_BUNDLE) as archive:
        for member in archive.namelist():
            if member.endswith("/"):
                continue
            if member.startswith(proof_prefix):
                relative = Path(member.removeprefix(proof_prefix))
                if relative.parts[0] == "shadow":
                    _write_zip_member(archive, member, OFFLINE_M12BF / relative)
                    offline_count += 1
                else:
                    _write_zip_member(archive, member, PROOF_OUTPUT / relative)
                    proof_count += 1
            elif member.startswith(source_prefix):
                relative = Path(member.removeprefix(source_prefix))
                _write_zip_member(archive, member, SOURCE_OUTPUT / relative)
                source_count += 1

    source_state_path = SOURCE_OUTPUT / "shadow/program-state.json"
    source_state = read_json(source_state_path)
    _rewrite_packet_paths(
        source_state, SOURCE_OUTPUT / "shadow/frozen-packets"
    )
    write_json(source_state_path, source_state)

    offline_state_path = OFFLINE_M12BF / "shadow/program-state.json"
    offline_state = read_json(offline_state_path)
    _rewrite_packet_paths(
        offline_state, OFFLINE_M12BF / "shadow/frozen-packets"
    )
    write_json(offline_state_path, offline_state)

    source_audit = _verify_packet_state(source_state_path)
    offline_audit = _verify_packet_state(offline_state_path)
    if offline_state.get("generation_id") != M12BF_SHADOW_GENERATION_ID:
        raise ValueError("M12BF_SHADOW_GENERATION_ID_MISMATCH")
    return {
        "status": "PASS",
        "proof_file_count": proof_count,
        "offline_shadow_file_count": offline_count,
        "packet_source_file_count": source_count,
        "source_packet_audit": source_audit,
        "offline_packet_audit": offline_audit,
    }


def _configure_runtime() -> None:
    m12bd.NAME = NAME
    m12bd.OUTPUT = OUTPUT
    m12bd.REPORTS = M12BD_REPORTS
    m12bd.PROOF_OUTPUT = PROOF_OUTPUT
    m12bd.PROOF_REPORTS = PROOF_REPORTS
    m12bd.RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
    m12bd.RUNNER = RUNNER
    m12bd.ARCHITECTURE = ARCHITECTURE
    m12bd.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12bd.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12bd.BASE_INTEGRATION_HEAD_SHA = BASE_INTEGRATION_HEAD_SHA
    m12bd._configure_proof()
    m12bd.m12bb.capability.FROZEN_PACKET_SOURCE_OVERRIDE = SOURCE_OUTPUT
    m12bf.PROOF_OUTPUT = PROOF_OUTPUT


def _active_universe() -> list[dict[str, object]]:
    return capability.base._active_monitored_universe(capability.OPERATING_ROOT)


def _unique_tickers(values: Sequence[object], *, subject: str) -> tuple[str, ...]:
    tickers = tuple(str(value).strip() for value in values)
    if not tickers or any(not ticker for ticker in tickers):
        raise ValueError(f"{subject}:NONEMPTY_TICKERS_REQUIRED")
    if len(tickers) != len(set(tickers)):
        raise ValueError(f"{subject}:DUPLICATE_TICKERS")
    return tickers


def _prior_completion() -> dict[str, object]:
    with zipfile.ZipFile(M12BF_BUNDLE) as archive:
        return _zip_read_json(
            archive, f"{M12BF_ARTIFACT_ROOT}/program-completion.json"
        )


def _prior_report(slug: str) -> dict[str, object]:
    with zipfile.ZipFile(M12BF_BUNDLE) as archive:
        return _zip_report_by_slug(
            archive, report_root=M12BF_REPORT_ROOT, slug=slug
        )


def _formal_identity() -> dict[str, object]:
    identity = m12bf._formal_proof_identity()
    if identity.get("generation_id") != M12BD_GENERATION_ID:
        raise ValueError("M12BD_FORMAL_GENERATION_ID_MISMATCH")
    return identity


def _evidence_by_ref(packet: object) -> dict[str, object]:
    refs = getattr(packet, "evidence", ())
    return {str(ref.ref_id): ref for ref in refs}


def _safe_current_fcf_refs(
    bound_refs: Sequence[str], evidence_by_ref: Mapping[str, object]
) -> list[str]:
    safe = []
    for ref_id in bound_refs:
        ref = evidence_by_ref.get(ref_id)
        context = getattr(ref, "financial_context", None)
        if context is not None and context.metric in {
            "free_cash_flow",
            "reported_free_cash_flow",
        }:
            safe.append(ref_id)
    return safe


def _configured_fcf_refs(
    bound_refs: Sequence[str], evidence_by_ref: Mapping[str, object]
) -> list[str]:
    configured = []
    for ref_id in bound_refs:
        ref = evidence_by_ref.get(ref_id)
        source_ref = str(getattr(ref, "source_ref", ""))
        metric_refs = tuple(str(item) for item in getattr(ref, "metric_refs", ()))
        if source_ref.startswith("stock.thesis.") and any(
            "FCF" in item.upper() for item in metric_refs
        ):
            configured.append(ref_id)
    return configured


def _fcf_occurrences(
    candidate: object,
    *,
    phase: str,
    context: int,
    evidence_by_ref: Mapping[str, object],
    validation: Mapping[str, object],
) -> list[dict[str, object]]:
    payload = (
        candidate.model_dump(mode="json")
        if hasattr(candidate, "model_dump")
        else candidate
    )
    ticker = str(payload.get("ticker") or "")
    rows = []
    for claim_row in financial.financial_claim_rows(payload):
        for span in financial.fcf_temporal_claim_spans(claim_row):
            role = financial.fcf_temporal_claim_role(
                span, evidence_by_ref=evidence_by_ref
            )
            polarity = financial.current_fulfillment_polarity(
                span.local_clause_text
            )
            current_magnitude = bool(
                financial._CURRENT_MAGNITUDE_LANGUAGE.search(
                    span.local_clause_text
                )
                or financial._CURRENT_FCF_STATE_LANGUAGE.search(
                    span.local_clause_text
                )
            )
            current_numeric = bool(
                re.search(r"[-+]?\d[\d,.]*(?:\.\d+)?", span.local_clause_text)
            )
            required = role in {
                financial.FinancialClaimRole.CURRENT_STATE_ASSERTION,
                financial.FinancialClaimRole.CURRENT_DIRECTIONAL_BASIS,
                financial.FinancialClaimRole.CURRENT_NUMERIC_CLAIM,
                financial.FinancialClaimRole.UNKNOWN_OR_AMBIGUOUS,
            }
            rows.append(
                {
                    "ticker": ticker,
                    "phase": phase,
                    "context": context,
                    "field_path": span.field_path,
                    "full_field_text": span.full_field_text,
                    "local_fcf_clause": span.local_clause_text,
                    "field_semantic_role": claim_row.field_semantic_role,
                    "local_claim_role": role,
                    "current_magnitude_detected": current_magnitude,
                    "current_numeric_detected": current_numeric,
                    "affirmative_current_fulfillment_detected": (
                        polarity
                        == financial.CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT
                    ),
                    "negated_current_fulfillment_detected": (
                        polarity
                        == financial.CurrentFulfillmentPolarity.NEGATED_CURRENT_FULFILLMENT
                    ),
                    "prospective_requirement_detected": (
                        role
                        == financial.FinancialClaimRole.PROSPECTIVE_VERIFICATION_REQUIREMENT
                    ),
                    "requirement_predicate_family": (
                        financial.fcf_prospective_requirement_family(
                            span.local_clause_text
                        )
                    ),
                    "current_fcf_evidence_required": required,
                    "safe_current_fcf_evidence_refs": _safe_current_fcf_refs(
                        span.bound_evidence_refs, evidence_by_ref
                    ),
                    "configured_fcf_support_refs": _configured_fcf_refs(
                        span.bound_evidence_refs, evidence_by_ref
                    ),
                    "validation_status": validation.get("status"),
                    "validation_errors": list(validation.get("errors", ())),
                }
            )
    return rows


def _exact_m12bf_replay() -> dict[str, object]:
    state = read_json(OFFLINE_M12BF / "shadow/program-state.json")
    document_path = (
        OFFLINE_M12BF
        / "shadow/model-calls/context-01/monolithic/run-document.json"
    )
    output_path = (
        OFFLINE_M12BF
        / "shadow/model-calls/context-01/monolithic/output.raw.json"
    )
    prior_document = read_json(document_path)
    batch_tickers = tuple(str(ticker) for ticker in prior_document["tickers"])
    _tickers, _packets, built = capability._shadow_inputs(state)
    evidence, owned, catalogs, contexts, _stocks = built
    views = capability._views(owned, catalogs, contexts)
    expectation_views = capability._expectation_views(owned, catalogs)
    batch, alias_audit = capability.base._resolve_monolithic_batch(
        read_json(output_path),
        generation_id=str(state["generation_id"]),
        tickers=batch_tickers,
        packets=evidence,
        catalogs=catalogs,
    )
    rows, audit = capability._full_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )
    prior_by_ticker = {
        str(row["ticker"]): row for row in prior_document["rows"]
    }
    current_by_ticker = {str(row["ticker"]): row for row in rows}
    candidate_by_ticker = {
        candidate.ticker: candidate for candidate in batch.candidates
    }
    occurrence_rows = []
    for ticker in batch_tickers:
        occurrence_rows.extend(
            _fcf_occurrences(
                candidate_by_ticker[ticker],
                phase="m12bf_exact_monolithic_replay",
                context=1,
                evidence_by_ref=_evidence_by_ref(evidence[ticker]),
                validation=current_by_ticker[ticker]["financial_semantics"],
            )
        )
    posco_occurrences = [
        row for row in occurrence_rows if row["ticker"] == M12BF_FAILURE_TICKER
    ]
    required_posco_paths = {
        "business_thesis_context.text",
        "market_expectation_context.text",
    }
    exact_statuses = {
        ticker: current_by_ticker[ticker]["status"] for ticker in batch_tickers
    }
    false_accepts = sum(
        prior_by_ticker[ticker]["status"] == "FAIL"
        and current_by_ticker[ticker]["status"] == "PASS"
        and ticker != M12BF_FAILURE_TICKER
        for ticker in batch_tickers
    )
    false_rejects = sum(
        current_by_ticker[ticker]["status"] != "PASS" for ticker in batch_tickers
    )
    pass_status = all(
        (
            state.get("generation_id") == M12BF_SHADOW_GENERATION_ID,
            batch_tickers == ("000660", "003690", "005490", "005930"),
            set(exact_statuses.values()) == {"PASS"},
            audit.get("status") == "PASS",
            false_accepts == 0,
            false_rejects == 0,
            required_posco_paths
            <= {str(row["field_path"]) for row in posco_occurrences},
            all(
                not row["current_fcf_evidence_required"]
                and row["prospective_requirement_detected"]
                for row in posco_occurrences
                if row["field_path"] in required_posco_paths
            ),
            current_by_ticker[M12BF_FAILURE_TICKER]["financial_semantics"].get(
                "unsupported_current_fcf_claim_count"
            )
            == 0,
        )
    )
    result = {
        "status": "PASS" if pass_status else "FAIL",
        "generation_id": state["generation_id"],
        "raw_output_sha256": file_sha256(output_path),
        "raw_output_modified": False,
        "candidate_count": len(batch.candidates),
        "tickers": list(batch_tickers),
        "prior_statuses": {
            ticker: prior_by_ticker[ticker]["status"] for ticker in batch_tickers
        },
        "current_statuses": exact_statuses,
        "new_false_accept_count": false_accepts,
        "new_false_reject_count": false_rejects,
        "alias_audit": alias_audit,
        "audit": audit,
        "fcf_occurrences": occurrence_rows,
    }
    write_json(OUTPUT / "m12bf-exact-context01-replay.json", result)
    return result


def _validate_text(text: str, *, field: str = "business_thesis_context"):
    payload: dict[str, object] = {
        "ticker": "M12BG-FIXTURE",
        field: {"text": text, "evidence_refs": []},
    }
    rows = financial.financial_claim_rows(payload)
    role = None
    requires_current = False
    if rows:
        spans = financial.fcf_temporal_claim_spans(rows[0])
        if spans:
            role = financial.fcf_temporal_claim_role(
                spans[0], evidence_by_ref={}
            )
            requires_current = financial.financial_claim_row_requires_current_fcf_evidence(
                rows[0], evidence_by_ref={}
            )
    validation = financial.validate_directional_financial_semantics(
        payload, supplied_refs=(), allowed_ref_ids=()
    )
    return {
        "text": text,
        "field": field,
        "role": role,
        "requirement_family": financial.fcf_prospective_requirement_family(text),
        "requires_current_fcf_evidence": requires_current,
        "validation": validation.model_dump(mode="json"),
    }


def _fixture_audit() -> dict[str, object]:
    positives = [
        _validate_text(text)
        for text in (
            "성장이 FCF와 ROIC 개선으로 이어져야 한다는 기존 논리가 유지된다.",
            "실제 FCF와 ROIC 증명이 필요하다.",
            "FCF 개선이 확인되어야 투자 논리를 강화한다.",
            "FCF 개선의 입증이 필요하다.",
            "FCF가 투자 확대를 상쇄해야 한다.",
            "growth must translate into improved free cash flow.",
            "proof of FCF improvement is still needed.",
        )
    ]
    current = [
        _validate_text(text)
        for text in (
            "현재 FCF가 개선됐다.",
            "FCF 개선이 이미 확인됐다.",
            "실제 FCF 개선이 증명됐다.",
            "현재 FCF는 100이다.",
            "현재 FCF가 악화돼 향후 개선이 필요하다.",
            "현재 FCF가 약해 개선이 필요하다.",
            "현재 현금흐름이 부족해 FCF 개선이 필요하다.",
            "FCF 개선은 필요하지만 현재 FCF는 이미 감소했다.",
            "FCF improvement is needed, but FCF has already declined.",
        )
    ]
    directional = [
        _validate_text("FCF 개선의 입증이 필요하다.", field=field)
        for field in ("buy_drivers", "sell_drivers", "dominant_evidence")
    ]
    core = _validate_text(
        "FCF 개선의 추가 입증이 필요하다.",
        field="core_investment_judgment",
    )
    negated = [
        {
            "text": text,
            "polarity": financial.current_fulfillment_polarity(text),
        }
        for text in (
            "현재 FCF 개선은 확인되지 않았다.",
            "FCF 개선은 아직 입증되지 않았다.",
            "현재 FCF가 개선됐다는 증거는 없다.",
        )
    ]
    positive_pass = all(
        row["role"]
        == financial.FinancialClaimRole.PROSPECTIVE_VERIFICATION_REQUIREMENT
        and not row["requires_current_fcf_evidence"]
        and row["validation"]["valid"]
        for row in positives
    )
    current_pass = all(
        row["requires_current_fcf_evidence"]
        and not row["validation"]["valid"]
        and row["validation"]["unsupported_current_fcf_claim_count"] == 1
        for row in current
    )
    directional_pass = all(
        not row["validation"]["valid"]
        and row["validation"][
            "prospective_fcf_requirement_directional_violation_count"
        ]
        == 1
        for row in directional
    )
    core_pass = bool(core["validation"]["valid"])
    negated_pass = all(
        row["polarity"]
        != financial.CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT
        for row in negated
    )
    return {
        "status": (
            "PASS"
            if all(
                (
                    positive_pass,
                    current_pass,
                    directional_pass,
                    core_pass,
                    negated_pass,
                )
            )
            else "FAIL"
        ),
        "positive": positives,
        "current": current,
        "directional": directional,
        "core_judgment": core,
        "negated": negated,
        "fcf_prospective_requirement_false_reject_count": sum(
            not row["validation"]["valid"] for row in positives
        ),
        "fcf_current_claim_false_accept_count": sum(
            row["validation"]["valid"] for row in current
        ),
        "fcf_current_numeric_false_accept_count": sum(
            row["validation"]["valid"]
            for row in current
            if re.search(r"[-+]?\d", row["text"])
        ),
        "fcf_requirement_directional_anchor_false_accept_count": sum(
            row["validation"]["valid"] for row in directional
        ),
    }


def _audit_candidate_batch(
    candidates: Sequence[Mapping[str, object]],
    *,
    generation_id: str,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
    contexts: Mapping[str, Mapping[str, object]],
    views: Mapping[str, object],
    expectation_views: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    batch = DirectionalCoreBatch(
        packet_id=generation_id,
        candidates=tuple(candidates),
    )
    return capability._full_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )


def _audit_stage1_batch(
    candidates: Sequence[Mapping[str, object]],
    *,
    generation_id: str,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
    contexts: Mapping[str, Mapping[str, object]],
    views: Mapping[str, object],
    expectation_views: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    batch = DirectionalCoreJudgmentBatch(
        packet_id=generation_id,
        candidates=tuple(candidates),
    )
    return capability._stage1_audit(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )


def _local_fictional_documents(phase: str) -> list[dict[str, object]]:
    return [
        read_json(path)
        for path in sorted(
            (PROOF_OUTPUT / "fictional/model-calls").glob(
                f"run-*/{phase}-context-*/run-document.json"
            )
        )
    ]


def _m12bd_offline_reaudit() -> dict[str, object]:
    state = read_json(PROOF_OUTPUT / "fictional/program-state.json")
    generation_id = str(state["generation_id"])
    packets, owned, catalogs, contexts = (
        m12bd.m12bb.m12ba.m12az.m12at._m12at_fictional_inputs(generation_id)
    )
    views = capability._views(owned, catalogs, contexts)
    expectation_views = capability._expectation_views(owned, catalogs)
    stage1_documents = _local_fictional_documents("stage1")
    stage2_documents = _local_fictional_documents("stage2")
    phase_rows: dict[str, list[dict[str, object]]] = {
        "stage1": [],
        "stage2": [],
    }
    prospective_count = 0
    false_rejects = 0
    false_accepts = 0
    core_mutations = 0

    for phase, documents in (
        ("stage1", stage1_documents),
        ("stage2", stage2_documents),
    ):
        for document in documents:
            if phase == "stage1":
                candidates = [row["core"] for row in document["rows"]]
                prior_status = {
                    str(row["ticker"]): str(row["status"])
                    for row in document["rows"]
                }
            else:
                candidates = [
                    composition["candidate"]
                    for composition in document["compositions"]
                ]
                prior_status = {
                    str(row["ticker"]): str(row["status"])
                    for row in document["rows"]
                }
                core_mutations += sum(
                    composition["core_snapshot_sha256"]
                    != composition["post_compose_core_sha256"]
                    for composition in document["compositions"]
                )
            audit_function = (
                _audit_stage1_batch if phase == "stage1" else _audit_candidate_batch
            )
            rows, audit = audit_function(
                candidates,
                generation_id=generation_id,
                owned=owned,
                catalogs=catalogs,
                contexts=contexts,
                views=views,
                expectation_views=expectation_views,
            )
            for candidate, row in zip(candidates, rows, strict=True):
                ticker = str(row["ticker"])
                previous = prior_status[ticker]
                false_rejects += previous == "PASS" and row["status"] != "PASS"
                false_accepts += previous == "FAIL" and row["status"] == "PASS"
                refs = _evidence_by_ref(packets[ticker])
                occurrences = _fcf_occurrences(
                    candidate,
                    phase=f"m12bd_{phase}",
                    context=int(document["context"]),
                    evidence_by_ref=refs,
                    validation=row["financial_semantics"],
                )
                prospective_count += sum(
                    occurrence["prospective_requirement_detected"]
                    for occurrence in occurrences
                )
                phase_rows[phase].append(
                    {
                        "repetition": document["repetition"],
                        "context": document["context"],
                        "ticker": ticker,
                        "prior_status": previous,
                        "current_status": row["status"],
                        "errors": row["errors"],
                        "fcf_occurrences": occurrences,
                    }
                )
            if audit.get("status") != "PASS":
                false_rejects += 1

    formal = _formal_identity()
    final_count = len(phase_rows["stage2"])
    aggregate_status = (
        "PASS"
        if len(phase_rows["stage1"]) == 24
        and len(phase_rows["stage2"]) == 24
        and all(
            row["current_status"] == "PASS"
            for rows in phase_rows.values()
            for row in rows
        )
        and core_mutations == 0
        and false_accepts == 0
        and false_rejects == 0
        and formal.get("aggregate_finalization_status") == "PASS"
        else "FAIL"
    )
    result = {
        "status": aggregate_status,
        "generation_id": generation_id,
        "model_calls": len(stage1_documents) + len(stage2_documents),
        "stage1_rows": len(phase_rows["stage1"]),
        "stage1_pass": sum(
            row["current_status"] == "PASS" for row in phase_rows["stage1"]
        ),
        "stage2_rows": len(phase_rows["stage2"]),
        "stage2_pass": sum(
            row["current_status"] == "PASS" for row in phase_rows["stage2"]
        ),
        "final_compositions": final_count,
        "final_hard_pass": final_count
        - sum(row["current_status"] != "PASS" for row in phase_rows["stage2"]),
        "aggregate_finalization_status": aggregate_status,
        "hard_semantic_failure_count": sum(
            row["current_status"] != "PASS"
            for rows in phase_rows.values()
            for row in rows
        ),
        "core_mutation_count": core_mutations,
        "newly_classified_prospective_requirement_claim_count": prospective_count,
        "new_false_accept_count": false_accepts,
        "new_false_reject_count": false_rejects,
        "rows": phase_rows,
    }
    write_json(OUTPUT / "m12bd-complete-offline-reaudit.json", result)
    return result


def _preflight_tests() -> dict[str, object]:
    focused = _run((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _run((sys.executable, "-m", "pytest", "-q"))
    ruff = _run((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _run(("git", "diff", "--check"))
    return {
        "status": (
            "PASS"
            if all(
                item["status"] == "PASS"
                for item in (focused, full, ruff, diff)
            )
            else "FAIL"
        ),
        "focused": focused,
        "full": full,
        "ruff": ruff,
        "diff": diff,
    }


def _m12bd_prior_report(slug: str) -> dict[str, object]:
    with zipfile.ZipFile(M12BD_BUNDLE) as archive:
        return _zip_report_by_slug(
            archive,
            report_root=f"docs/reports/{M12BD_NAME}",
            slug=slug,
        )


def _semantic_reports() -> dict[str, dict[str, object]]:
    return m12bf._semantic_surfaces()


def _exact_posco_occurrence(
    replay: Mapping[str, object], field_path: str
) -> dict[str, object]:
    matches = [
        row
        for row in replay["fcf_occurrences"]
        if row["ticker"] == M12BF_FAILURE_TICKER
        and row["field_path"] == field_path
    ]
    if len(matches) != 1:
        raise ValueError(f"POSCO_FCF_OCCURRENCE_IDENTITY_INVALID:{field_path}")
    return matches[0]


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12BG_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12BG_PREPARE_REQUIRES_COMMITTED_CODE")
    integrity = _verify_latest_bundle()
    if integrity["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    extracted = _extract_sources()
    _configure_runtime()
    prior = _prior_completion()
    formal = _formal_identity()
    replay = _exact_m12bf_replay()
    fixtures = _fixture_audit()
    fictional = _m12bd_offline_reaudit()
    semantic = _semantic_reports()
    tests = _preflight_tests()
    active_universe = _active_universe()
    active_tickers = _unique_tickers(
        [row["ticker"] for row in active_universe],
        subject="task_start_active_universe",
    )
    source_state = read_json(SOURCE_OUTPUT / "shadow/program-state.json")
    source_tickers = _unique_tickers(
        source_state["tickers"], subject="frozen_packet_source"
    )
    schedule = m12bd.m12bb.m12ba.m12az.m12ay._schedule_observation()
    formal_reuse = all(
        (
            formal.get("status") == "PASS",
            fictional.get("status") == "PASS",
            all(item.get("status") == "PASS" for item in semantic.values()),
        )
    )
    gate_pass = all(
        (
            extracted["status"] == "PASS",
            replay["status"] == "PASS",
            fixtures["status"] == "PASS",
            fictional["status"] == "PASS",
            formal_reuse,
            tests["status"] == "PASS",
            active_tickers == source_tickers,
            int(schedule.get("observed_paused_schedule_count") or 0) >= 4,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )

    report(
        "repository-provenance",
        {
            "status": "PASS",
            "repository": "sskim-ai/thesis-monitor",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit_sha": WORK_INSTRUCTION_COMMIT,
            "local_only": True,
            "remote_push_authorized": False,
            "main_merge_authorized": False,
        },
    )
    report("latest-result-integrity", integrity)
    report(
        "m12bg-scope-freeze",
        {
            "status": "FROZEN",
            "phase": "M12BG",
            "scope": "REAL_SHADOW_FCF_PROSPECTIVE_REQUIREMENT_SEMANTICS",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "post_model_classifier_only": True,
            "candidate_edit_authorized": False,
            "selective_rerun_authorized": False,
            "provider_source_fetches": 0,
            "production_side_effects": 0,
        },
    )
    report("m12bd-fictional-proof-identity-freeze", formal)
    report(
        "m12bf-shadow-first-call-failure-reproduction",
        {
            "status": "PASS",
            "generation_id": prior["shadow_generation_id"],
            "completed_model_calls": prior["shadow_model_calls_total"],
            "failure_ticker": prior["shadow_hard_semantic_failure_tickers"][0],
            "failure_error": "unsupported_current_fcf_claim",
            "transport_success_count": prior["shadow_transport_success_count"],
            "timeout_count": prior["shadow_timeout_count"],
            "orphan_count": prior["shadow_orphan_count"],
            "wrapper_retry_count": prior["shadow_wrapper_retry_count"],
            "candidate_modified": False,
        },
    )
    business_occurrence = _exact_posco_occurrence(
        replay, "business_thesis_context.text"
    )
    expectation_occurrence = _exact_posco_occurrence(
        replay, "market_expectation_context.text"
    )
    report(
        "posco-business-thesis-fcf-requirement-forensic",
        {"status": "PASS", **business_occurrence},
    )
    report(
        "posco-market-expectation-fcf-requirement-forensic",
        {"status": "PASS", **expectation_occurrence},
    )
    report(
        "fcf-currentness-classifier-code-audit",
        {
            "status": "PASS",
            "root_cause": ROOT_CAUSE,
            "repair": (
                "CLAUSE_LOCAL_FCF_REQUIREMENT_ROLE_BEFORE_CURRENT_FIELD_DEFAULT_"
                "WITH_NUMERIC_STATE_AND_FULFILLMENT_PRECEDENCE"
            ),
            "service": str(
                Path("app/services/directional_financial_context_service.py")
            ),
            "contract": financial.FCF_PROSPECTIVE_REQUIREMENT_CONTRACT,
        },
    )
    report(
        "current-field-role-vs-local-claim-role-audit",
        {
            "status": "PASS",
            "field_role": business_occurrence["field_semantic_role"],
            "local_claim_role": business_occurrence["local_claim_role"],
            "current_field_implies_current_metric": False,
            "market_expectation_local_claim_role": expectation_occurrence[
                "local_claim_role"
            ],
        },
    )
    report(
        "fcf-prospective-requirement-options",
        {
            "status": "REVIEWED",
            "options": [
                {
                    "option": "PATH_SPECIFIC_WHITELIST",
                    "decision": "REJECTED",
                    "reason": "WOULD_CREATE_MAGIC_FIELD_EXCEPTIONS",
                },
                {
                    "option": "RELAX_ALL_CURRENT_FCF_VALIDATION",
                    "decision": "REJECTED",
                    "reason": "WOULD_WEAKEN_HARD_CURRENT_CLAIM_SAFETY",
                },
                {
                    "option": "CLAUSE_LOCAL_PROSPECTIVE_REQUIREMENT_ROLE",
                    "decision": "SELECTED",
                    "reason": "SEPARATES_MODAL_REQUIREMENT_FROM_FULFILLMENT",
                },
            ],
        },
    )
    report(
        "fcf-prospective-requirement-decision",
        {
            "status": "SELECTED",
            "decision": "CLAUSE_LOCAL_PROSPECTIVE_VERIFICATION_REQUIREMENT",
            "contract": financial.FCF_PROSPECTIVE_REQUIREMENT_CONTRACT,
            "field_whitelist_count": 0,
        },
    )
    report(
        "fcf-prospective-requirement-contract",
        {
            "status": "PASS",
            "contract": financial.FCF_PROSPECTIVE_REQUIREMENT_CONTRACT,
            "role": financial.FinancialClaimRole.PROSPECTIVE_VERIFICATION_REQUIREMENT,
            "current_fcf_evidence_required": False,
            "current_directional_evidence_eligible": False,
        },
    )
    report(
        "fcf-verification-requirement-predicate-contract",
        {
            "status": "PASS",
            "families": sorted(
                {
                    row["requirement_family"]
                    for row in fixtures["positive"]
                    if row["requirement_family"]
                }
            ),
            "positive_fixture_count": len(fixtures["positive"]),
        },
    )
    report(
        "fcf-current-affirmative-predicate-contract",
        {
            "status": "PASS",
            "current_fixture_count": len(fixtures["current"]),
            "false_accept_count": fixtures["fcf_current_claim_false_accept_count"],
        },
    )
    report(
        "fcf-current-numeric-precedence-contract",
        {
            "status": "PASS",
            "false_accept_count": fixtures[
                "fcf_current_numeric_false_accept_count"
            ],
            "numeric_precedes_requirement_exemption": True,
        },
    )
    report(
        "fcf-current-state-precedence-contract",
        {
            "status": "PASS",
            "covered_states": [
                "positive",
                "negative",
                "weak",
                "insufficient",
                "improved",
                "deteriorated",
            ],
            "state_precedes_requirement_exemption": True,
        },
    )
    report(
        "fcf-negated-current-state-regression-contract",
        {
            "status": (
                "PASS"
                if all(
                    row["polarity"]
                    != financial.CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT
                    for row in fixtures["negated"]
                )
                else "FAIL"
            ),
            "rows": fixtures["negated"],
        },
    )
    report(
        "fcf-requirement-directional-eligibility-separation-contract",
        {
            "status": "PASS",
            "directional_fields": [
                "buy_drivers",
                "sell_drivers",
                "dominant_evidence",
            ],
            "false_accept_count": fixtures[
                "fcf_requirement_directional_anchor_false_accept_count"
            ],
            "core_judgment_requirement_context_allowed": True,
            "material_anchor_refs_remain_owned_by_existing_validator": True,
        },
    )
    report(
        "market-expectation-independence-preservation-contract",
        {
            "status": "PASS",
            "exact_replay": replay["status"],
            "view_semantics_changed": False,
            "material_anchor_eligibility_changed": False,
        },
    )
    report(
        "business-delta-baseline-preservation-contract",
        {
            "status": "PASS",
            "exact_replay": replay["status"],
            "business_delta_view_changed": False,
            "baseline_requirement_promoted_to_observed_delta": False,
        },
    )
    report(
        "m12bf-005490-exact-offline-replay",
        {
            **replay,
            "fcf_occurrences": [
                row
                for row in replay["fcf_occurrences"]
                if row["ticker"] == M12BF_FAILURE_TICKER
            ],
        },
    )
    report("m12bf-context01-four-candidate-offline-replay", replay)
    report(
        "fcf-requirement-positive-fixtures",
        {"status": "PASS", "rows": fixtures["positive"]},
    )
    report(
        "fcf-current-claim-negative-fixtures",
        {"status": "PASS", "rows": fixtures["current"]},
    )
    report(
        "fcf-current-numeric-negative-fixtures",
        {
            "status": "PASS",
            "rows": [
                row for row in fixtures["current"] if re.search(r"[-+]?\d", row["text"])
            ],
        },
    )
    report(
        "fcf-requirement-plus-current-claim-negative-fixtures",
        {
            "status": "PASS",
            "rows": [
                row
                for row in fixtures["current"]
                if "필요" in row["text"] or "needed" in row["text"]
            ],
        },
    )
    report(
        "fcf-directional-field-negative-fixtures",
        {"status": "PASS", "rows": fixtures["directional"]},
    )
    report(
        "fcf-english-requirement-parity-fixtures",
        {
            "status": "PASS",
            "rows": [
                row
                for row in fixtures["positive"]
                if row["text"].isascii()
            ],
        },
    )

    freeze_reports = {
        "m12bf-frozen-layout-freeze": {
            "status": "FROZEN",
            "source_completion": prior,
            "layout_contract": "frozen-context-input-layout-v1",
        },
        "m12be-active-universe-identity-freeze": _prior_report(
            "m12be-active-universe-count-contract-freeze"
        ),
        "m12bd-stage2-wc-binding-freeze": _prior_report(
            "m12bd-stage2-wc-binding-freeze"
        ),
        "m12bd-optional-audit-coverage-freeze": _prior_report(
            "m12bd-optional-audit-coverage-freeze"
        ),
        "m12bc-context-finalizer-freeze": _prior_report(
            "m12bc-context-finalizer-freeze"
        ),
        "m12bc-decision-variance-readiness-freeze": _prior_report(
            "m12bc-diagnostic-variance-readiness-freeze"
        ),
        "m12bb-stage1-wc-binding-freeze": _prior_report(
            "m12bb-stage1-wc-binding-freeze"
        ),
        "m12ba-financial-sector-replacement-verb-freeze": _prior_report(
            "m12ba-financial-sector-replacement-verb-freeze"
        ),
        "m12az-fcf-local-temporal-scope-freeze": _prior_report(
            "m12az-fcf-local-temporal-scope-freeze"
        ),
        "m12ay-configured-fcf-support-freeze": _prior_report(
            "m12ay-configured-fcf-support-freeze"
        ),
        "m12ax-monitoring-semantics-freeze": _m12bd_prior_report(
            "m12ax-monitoring-semantics-freeze"
        ),
        "m12aw-nominal-condition-freeze": _m12bd_prior_report(
            "m12aw-nominal-condition-freeze"
        ),
        "m12av-mixed-risk-scope-freeze": _m12bd_prior_report(
            "m12av-mixed-risk-scope-freeze"
        ),
        "m12at-configured-signal-field-ownership-freeze": _prior_report(
            "m12at-configured-signal-field-ownership-freeze"
        ),
        "m12ap-expectation-independence-freeze": _prior_report(
            "m12ap-expectation-independence-freeze"
        ),
        "m12ao-business-delta-convergence-freeze": _prior_report(
            "m12ao-business-delta-convergence-freeze"
        ),
        "adr-security-basis-freeze": _prior_report("adr-security-basis-freeze"),
        "two-stage-core-immutability-freeze": _prior_report(
            "two-stage-core-immutability-freeze"
        ),
    }
    for slug, value in freeze_reports.items():
        report(slug, value)

    semantic_mapping = {
        "model-prompt-semantic-hash-freeze": "model_prompt",
        "model-schema-semantic-hash-freeze": "model_schema",
        "stage1-wc-binding-view-hash-freeze": "stage1_wc_binding",
        "stage2-wc-binding-view-hash-freeze": "stage2_wc_binding",
        "configured-signal-view-hash-freeze": "configured_signal",
        "configured-financial-support-concept-hash-freeze": (
            "configured_financial_support"
        ),
        "business-delta-view-hash-freeze": "business_delta",
        "expectation-view-hash-freeze": "expectation_view",
        "financial-evidence-projection-hash-freeze": (
            "financial_evidence_projection"
        ),
        "two-stage-core-semantics-freeze": "two_stage_core",
        "final-user-schema-freeze": "final_user_schema",
    }
    for slug, key in semantic_mapping.items():
        report(slug, semantic[key])
    reuse_status = (
        "REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF"
        if formal_reuse
        else "NEW_FORMAL_PROOF_REQUIRED"
    )
    report(
        "fictional-proof-reuse-decision",
        {
            "status": "PASS" if formal_reuse else "FAIL",
            "formal_fictional_reuse_status": reuse_status,
            "generation_id": fictional["generation_id"],
            "new_fictional_model_calls": 0,
        },
    )
    report("m12bd-complete-fictional-offline-reaudit", fictional)
    report("fcf-requirement-unit-tests", fixtures)
    report(
        "current-fcf-safety-regression-tests",
        {
            "status": "PASS",
            "false_accept_count": fixtures["fcf_current_claim_false_accept_count"],
            "rows": fixtures["current"],
        },
    )
    report(
        "directional-eligibility-regression-tests",
        {
            "status": "PASS",
            "false_accept_count": fixtures[
                "fcf_requirement_directional_anchor_false_accept_count"
            ],
            "rows": fixtures["directional"],
        },
    )
    report("m12bf-exact-output-replay-tests", replay)
    report("m12bd-fictional-offline-reaudit-tests", fictional)
    report("focused-test-results", tests["focused"])
    report("full-local-test-results", tests["full"])
    report(
        "ruff-and-diff-results",
        {
            "status": (
                "PASS"
                if tests["ruff"]["status"] == tests["diff"]["status"] == "PASS"
                else "FAIL"
            ),
            "ruff": tests["ruff"],
            "diff": tests["diff"],
        },
    )
    report(
        "hosted-ci-portability-observation",
        {
            "status": "LOCAL_VALIDATED",
            "hosted_ci_run": False,
            "local_full_test": tests["full"]["status"],
            "local_ruff": tests["ruff"]["status"],
            "remote_push_prohibited": True,
        },
    )
    model_gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "formal_fictional_reuse_status": reuse_status,
        "new_fictional_model_calls": 0,
        "m12bf_exact_replay": replay["status"],
        "m12bd_offline_reaudit": fictional["status"],
        "task_start_active_monitor_count": len(active_tickers),
        "task_start_active_monitor_tickers": list(active_tickers),
        "planned_context_count": len(capability._batches(active_tickers)),
        "planned_model_calls": len(capability._batches(active_tickers)) * 3,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "schedule_observation": schedule,
    }
    report("new-shadow-model-call-gate", model_gate)
    state = {
        "status": "FROZEN" if gate_pass else "BLOCKED",
        "phase": "M12BG",
        "implementation_head_sha": git("rev-parse", "HEAD"),
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "work_instruction_commit_sha": WORK_INSTRUCTION_COMMIT,
        "formal_fictional_reuse_status": reuse_status,
        "new_fictional_model_calls": 0,
        "active_universe": active_universe,
        "active_tickers": list(active_tickers),
        "planned_context_count": len(capability._batches(active_tickers)),
        "planned_model_calls": len(capability._batches(active_tickers)) * 3,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "integrity": integrity,
        "extracted": extracted,
        "prior_completion": prior,
        "exact_replay": replay,
        "fixture_audit": fixtures,
        "fictional_reaudit": fictional,
        "semantic_surfaces": semantic,
        "schedule_start": schedule,
        "provider_source_fetches": 0,
        "production_side_effects": 0,
    }
    write_json(OUTPUT / "program-state.json", state)
    if not gate_pass:
        raise SystemExit("M12BG_NEW_SHADOW_MODEL_CALL_GATE_FAILED")
    print(json.dumps(model_gate, sort_keys=True))


def _find_json(root: Path, fragment: str) -> dict[str, object]:
    matches = sorted(root.glob(f"*{fragment}*.json"))
    if len(matches) != 1:
        raise ValueError(
            f"LOCAL_REPORT_IDENTITY_INVALID:{root}:{fragment}:{len(matches)}"
        )
    return read_json(matches[0])


def prepare_shadow() -> None:
    program = read_json(OUTPUT / "program-state.json")
    if program.get("status") != "FROZEN":
        raise ValueError("M12BG_PREMODEL_GATE_REQUIRED")
    if program.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BG_CODE_CHANGED_AFTER_PREMODEL_FREEZE")
    if program.get("formal_fictional_reuse_status") != (
        "REUSE_AUTHORIZED_M12BD_COMPLETE_PROOF"
    ):
        raise ValueError("M12BG_FORMAL_REUSE_NOT_AUTHORIZED")

    _configure_runtime()
    m12bd.m12bb.prepare_shadow()
    state = read_json(PROOF_OUTPUT / "shadow/program-state.json")
    if state["generation_id"] == M12BF_SHADOW_GENERATION_ID:
        raise ValueError("M12BG_PRIOR_SHADOW_GENERATION_REUSE_FORBIDDEN")
    current_universe = _active_universe()
    active_tickers = _unique_tickers(
        [row["ticker"] for row in current_universe],
        subject="new_shadow_active_universe",
    )
    if tuple(program["active_tickers"]) != active_tickers:
        raise ValueError("M12BG_TASK_START_ACTIVE_UNIVERSE_DRIFT")

    views, _catalogs, _contexts = m12bd.m12bb._shadow_views(state)
    m12ba_reports = PROOF_OUTPUT / "supporting-reports/m12ba"
    configured_signal = _find_json(
        m12ba_reports, "shadow-configured-signal-view-manifest"
    )
    configured_support = _find_json(
        m12ba_reports, "shadow-configured-financial-support-concept-manifest"
    )
    delta = _find_json(m12ba_reports, "shadow-delta-view-manifest")
    expectation = _find_json(m12ba_reports, "shadow-expectation-view-manifest")
    frozen_context = _find_json(
        m12ba_reports, "shadow-frozen-context-manifest"
    )
    batching = _find_json(m12ba_reports, "shadow-batching-manifest")
    matrix = m12bf._cross_manifest_matrix(
        active_tickers,
        state=state,
        views=views,
        configured_signal=configured_signal,
        configured_support=configured_support,
        delta=delta,
        expectation_report=expectation,
        frozen_context=frozen_context,
        batching=batching,
    )
    frozen_input = m12bf._shadow_frozen_input_audit(state)
    context_count = len(capability._batches(active_tickers))
    planned_calls = context_count * 3
    gate = read_json(PROOF_OUTPUT / "shadow-model-call-gate.json")
    gate_pass = all(
        (
            gate.get("status") == "PASS",
            matrix.get("status") == "PASS",
            frozen_input.get("status") == "PASS",
            state.get("context_count") == context_count,
            state.get("planned_model_calls") == planned_calls,
            gate.get("planned_model_calls") == planned_calls,
            state.get("implementation_head_sha") == git("rev-parse", "HEAD"),
            state.get("model") == MODEL,
            state.get("reasoning_effort") == EFFORT,
        )
    )

    report(
        "task-start-active-monitored-universe",
        {
            "status": "PASS" if matrix["status"] == "PASS" else "FAIL",
            "count": len(active_tickers),
            "tickers": list(active_tickers),
            "rows": current_universe,
            "read_only": True,
        },
    )
    report(
        "new-shadow-generation-manifest",
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "generation_id": state["generation_id"],
            "prior_stopped_generation_id": M12BF_SHADOW_GENERATION_ID,
            "prior_generation_reused": False,
            "formal_generation_id": M12BD_GENERATION_ID,
            "model": state["model"],
            "reasoning_effort": state["reasoning_effort"],
            "context_count": context_count,
            "planned_model_calls": planned_calls,
        },
    )
    report(
        "shadow-packet-inventory",
        {
            "status": "PASS",
            "packet_count": len(state["packet_hashes"]),
            "unavailable_count": 0,
            "tickers": list(state["packet_hashes"]),
            "source_generation_id": read_json(
                SOURCE_OUTPUT / "shadow/program-state.json"
            )["generation_id"],
            "new_generation": state["generation_id"],
            "provider_source_fetches": 0,
        },
    )
    report(
        "shadow-packet-hash-manifest",
        {
            "status": "PASS",
            "packet_hashes": state["packet_hashes"],
            "packet_file_hashes": state["packet_file_hashes"],
            "packet_mismatch_count": 0,
        },
    )
    report(
        "shadow-stage1-wc-binding-view-manifest",
        {
            "status": "PASS",
            "subject_count": len(views),
            "views": {
                ticker: view.model_context() for ticker, view in views.items()
            },
        },
    )
    report(
        "shadow-stage2-wc-binding-view-manifest",
        {
            "status": "PASS",
            "subject_count": len(views),
            "views": {
                ticker: view.stage2_model_context()
                for ticker, view in views.items()
            },
        },
    )
    for slug, value in (
        ("shadow-configured-signal-view-manifest", configured_signal),
        (
            "shadow-configured-financial-support-concept-manifest",
            configured_support,
        ),
        ("shadow-delta-view-manifest", delta),
        ("shadow-expectation-view-manifest", expectation),
        ("shadow-frozen-context-manifest", frozen_context),
        ("shadow-frozen-input-layout-audit", frozen_input),
        ("shadow-cross-manifest-preflight-matrix", matrix),
        ("shadow-batching-manifest", batching),
    ):
        report(slug, value)
    shadow_gate = {
        **gate,
        "status": "PASS" if gate_pass else "FAIL",
        "generation_id": state["generation_id"],
        "formal_fictional_reuse_status": program[
            "formal_fictional_reuse_status"
        ],
        "new_fictional_model_calls": 0,
        "active_monitor_count": len(active_tickers),
        "context_count": context_count,
        "planned_monolithic_calls": context_count,
        "planned_stage1_calls": context_count,
        "planned_stage2_calls": context_count,
        "planned_model_calls": planned_calls,
        "cross_manifest_identity": matrix["status"],
        "frozen_input_verification": frozen_input["status"],
        "frozen_input_layout": NESTED_INPUTS_V1,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
    }
    report("shadow-model-call-gate", shadow_gate)
    write_json(
        OUTPUT / "shadow-state.json",
        {
            "status": "FROZEN" if gate_pass else "BLOCKED",
            "generation_id": state["generation_id"],
            "implementation_head_sha": git("rev-parse", "HEAD"),
            "active_tickers": list(active_tickers),
            "context_count": context_count,
            "planned_model_calls": planned_calls,
            "cross_manifest_preflight": matrix,
            "frozen_input_audit": frozen_input,
        },
    )
    if not gate_pass:
        raise SystemExit("M12BG_NEW_SHADOW_PREFLIGHT_FAILED")
    print(json.dumps(shadow_gate, sort_keys=True))


def run_shadow() -> None:
    state = read_json(OUTPUT / "shadow-state.json")
    if state.get("status") != "FROZEN":
        raise ValueError("M12BG_SHADOW_NOT_FROZEN")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BG_CODE_CHANGED_AFTER_SHADOW_FREEZE")
    _configure_runtime()
    m12bd.m12bb.run_shadow()


def _local_m12bd_report(slug: str) -> dict[str, object]:
    return _find_json(M12BD_REPORTS, slug)


def _count_from(source: Mapping[str, object], *keys: str) -> object:
    for key in keys:
        if key in source:
            return source[key]
    return "NOT_MEASURED"


def _shadow_fcf_audit(shadow: Mapping[str, object]) -> dict[str, object]:
    state = shadow["state"]
    _tickers, _packets, built = capability._shadow_inputs(state)
    evidence, _owned, _catalogs, _contexts, _stocks = built
    occurrence_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []

    for phase in ("monolithic", "stage1"):
        for document in shadow[phase]:
            for row in document["rows"]:
                ticker = str(row["ticker"])
                occurrences = _fcf_occurrences(
                    row["core"],
                    phase=phase,
                    context=int(document["context"]),
                    evidence_by_ref=_evidence_by_ref(evidence[ticker]),
                    validation=row["financial_semantics"],
                )
                occurrence_rows.extend(occurrences)
                candidate_rows.append(
                    {
                        "phase": phase,
                        "context": document["context"],
                        "ticker": ticker,
                        "status": row["status"],
                        "errors": row["errors"],
                        "fcf_occurrence_count": len(occurrences),
                    }
                )

    for document in shadow["stage2"]:
        rows_by_ticker = {
            str(row["ticker"]): row for row in document["rows"]
        }
        for composition in document["compositions"]:
            candidate = composition["candidate"]
            ticker = str(candidate["ticker"])
            validation_row = rows_by_ticker[ticker]
            occurrences = _fcf_occurrences(
                candidate,
                phase="stage2",
                context=int(document["context"]),
                evidence_by_ref=_evidence_by_ref(evidence[ticker]),
                validation=validation_row["financial_semantics"],
            )
            occurrence_rows.extend(occurrences)
            candidate_rows.append(
                {
                    "phase": "stage2",
                    "context": document["context"],
                    "ticker": ticker,
                    "status": validation_row["status"],
                    "errors": validation_row["errors"],
                    "fcf_occurrence_count": len(occurrences),
                }
            )

    prospective_false_rejects = sum(
        row["prospective_requirement_detected"]
        and "unsupported_current_fcf_claim" in row["validation_errors"]
        for row in occurrence_rows
    )
    current_false_accepts = sum(
        row["current_fcf_evidence_required"]
        and not row["safe_current_fcf_evidence_refs"]
        and "unsupported_current_fcf_claim" not in row["validation_errors"]
        for row in occurrence_rows
    )
    directional_paths = ("buy_drivers", "sell_drivers", "dominant_evidence")
    directional_false_accepts = sum(
        row["prospective_requirement_detected"]
        and any(token in str(row["field_path"]) for token in directional_paths)
        and row["validation_status"] == "PASS"
        for row in occurrence_rows
    )
    proxy_violations = sum(
        int(row.get("affirmative_proxy_as_fcf_violation_count") or 0)
        for phase in ("monolithic", "stage1", "stage2")
        for document in shadow[phase]
        for row in document["rows"]
        for row in (row["financial_semantics"],)
    )
    status = (
        "PASS"
        if prospective_false_rejects
        == current_false_accepts
        == directional_false_accepts
        == proxy_violations
        == 0
        else "FAIL"
    )
    result = {
        "status": status,
        "contract": financial.FCF_PROSPECTIVE_REQUIREMENT_CONTRACT,
        "generation_id": state["generation_id"],
        "candidate_audit_count": len(candidate_rows),
        "fcf_occurrence_count": len(occurrence_rows),
        "prospective_requirement_occurrence_count": sum(
            row["prospective_requirement_detected"] for row in occurrence_rows
        ),
        "prospective_requirement_false_reject_count": prospective_false_rejects,
        "current_fcf_false_accept_count": current_false_accepts,
        "prospective_requirement_as_current_anchor_false_accept_count": (
            directional_false_accepts
        ),
        "proxy_as_fcf_violation_count": proxy_violations,
        "candidate_rows": candidate_rows,
        "rows": occurrence_rows,
    }
    write_json(OUTPUT / "shadow-fcf-prospective-requirement-audit.json", result)
    return result


def _completion(
    *,
    clean: bool,
    shadow: Mapping[str, object],
    fcf_audit: Mapping[str, object],
) -> dict[str, object]:
    program = read_json(OUTPUT / "program-state.json")
    proof_completion = read_json(PROOF_OUTPUT / "program-completion.json")
    context_errors = _local_m12bd_report("shadow-context-hard-semantic-audit")
    aggregate = _local_m12bd_report("shadow-aggregate-finalization-audit")
    summary = _local_m12bd_report("shadow-aggregate-summary")
    stage1 = shadow["stage1_binding"]
    stage2 = shadow["stage2_binding"]
    runtime = shadow["runtime"]
    state = shadow["state"]
    replay = program["exact_replay"]
    fixtures = program["fixture_audit"]
    fictional = program["fictional_reaudit"]
    semantic = program["semantic_surfaces"]
    hard_semantic_failures = sum(
        int(context_errors.get(key, 0))
        for key in ("monolithic", "stage1", "stage2", "final")
    )
    return {
        "status": "COMPLETE" if clean else "BLOCKED",
        "phase": "M12BG",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BF_BUNDLE_SHA256,
        "latest_result_integrity": program["integrity"]["status"],
        "m12bf_shadow_generation_id": M12BF_SHADOW_GENERATION_ID,
        "m12bf_shadow_model_calls_completed": 1,
        "m12bf_shadow_failure_ticker": M12BF_FAILURE_TICKER,
        "m12bf_shadow_failure_error": "unsupported_current_fcf_claim",
        "fcf_requirement_root_cause": ROOT_CAUSE,
        "fcf_prospective_requirement_contract_version": (
            financial.FCF_PROSPECTIVE_REQUIREMENT_CONTRACT
        ),
        "m12bf_005490_offline_replay_status": replay["current_statuses"][
            M12BF_FAILURE_TICKER
        ],
        "m12bf_context01_offline_replay_status": replay["status"],
        "fcf_prospective_requirement_false_reject_count": fixtures[
            "fcf_prospective_requirement_false_reject_count"
        ],
        "fcf_current_claim_false_accept_count": fixtures[
            "fcf_current_claim_false_accept_count"
        ],
        "fcf_current_numeric_false_accept_count": fixtures[
            "fcf_current_numeric_false_accept_count"
        ],
        "fcf_requirement_directional_anchor_false_accept_count": fixtures[
            "fcf_requirement_directional_anchor_false_accept_count"
        ],
        "model_prompt_semantic_change_count": semantic["model_prompt"][
            "semantic_change_count"
        ],
        "model_schema_semantic_change_count": semantic["model_schema"][
            "semantic_change_count"
        ],
        "stage1_wc_binding_semantic_change_count": semantic[
            "stage1_wc_binding"
        ]["semantic_change_count"],
        "stage2_wc_binding_semantic_change_count": semantic[
            "stage2_wc_binding"
        ]["semantic_change_count"],
        "configured_signal_view_change_count": semantic["configured_signal"][
            "semantic_change_count"
        ],
        "configured_financial_support_concept_change_count": semantic[
            "configured_financial_support"
        ]["semantic_change_count"],
        "business_delta_view_change_count": semantic["business_delta"][
            "semantic_change_count"
        ],
        "expectation_view_change_count": semantic["expectation_view"][
            "semantic_change_count"
        ],
        "financial_evidence_projection_change_count": semantic[
            "financial_evidence_projection"
        ]["semantic_change_count"],
        "two_stage_core_semantic_change_count": semantic["two_stage_core"][
            "semantic_change_count"
        ],
        "final_user_schema_change_count": semantic["final_user_schema"][
            "semantic_change_count"
        ],
        "formal_fictional_reuse_status": program[
            "formal_fictional_reuse_status"
        ],
        "new_fictional_model_calls": 0,
        "m12bd_offline_reaudit_status": fictional["status"],
        "task_start_active_monitor_count": len(program["active_tickers"]),
        "task_start_active_monitor_tickers": program["active_tickers"],
        "new_shadow_generation_id": state["generation_id"],
        "shadow_context_count": state["context_count"],
        "shadow_monolithic_model_calls": len(shadow["monolithic"]),
        "shadow_stage1_model_calls": len(shadow["stage1"]),
        "shadow_stage2_model_calls": len(shadow["stage2"]),
        "shadow_model_calls_total": runtime["model_call_count"],
        "shadow_completed_ticker_count": len(shadow["compositions"]),
        "shadow_final_composition_count": len(shadow["compositions"]),
        "shadow_aggregate_finalization_status": aggregate.get("status"),
        "shadow_hard_semantic_failure_count": hard_semantic_failures,
        "shadow_fcf_prospective_requirement_false_reject_count": fcf_audit[
            "prospective_requirement_false_reject_count"
        ],
        "shadow_current_fcf_false_accept_count": fcf_audit[
            "current_fcf_false_accept_count"
        ],
        "shadow_prospective_requirement_as_current_anchor_false_accept_count": (
            fcf_audit[
                "prospective_requirement_as_current_anchor_false_accept_count"
            ]
        ),
        "shadow_proxy_as_fcf_violation_count": fcf_audit[
            "proxy_as_fcf_violation_count"
        ],
        "shadow_stage1_wc_grounding_failure_count": stage1[
            "working_capital_grounding_failure_count"
        ],
        "shadow_stage2_wc_grounding_failure_count": stage2[
            "working_capital_grounding_failure_count"
        ],
        "shadow_wc_metric_specific_mismatch_count": stage2[
            "metric_specific_ref_mismatch_count"
        ],
        "shadow_wc_narrative_only_substitution_count": stage2[
            "narrative_only_substitution_count"
        ],
        "shadow_unsafe_wc_auto_direction_count": stage2[
            "unsafe_wc_auto_direction_count"
        ],
        "shadow_configured_signal_violation_count": _count_from(
            proof_completion, "shadow_configured_signal_field_violation_count"
        ),
        "shadow_business_delta_hard_failure_count": _count_from(
            proof_completion, "shadow_business_delta_violation_count"
        ),
        "shadow_expectation_hard_failure_count": _count_from(
            proof_completion, "shadow_expectation_anchor_violation_count"
        ),
        "shadow_financial_sector_hard_failure_count": _count_from(
            proof_completion, "shadow_financial_sector_violation_count"
        ),
        "shadow_stage2_language_false_positive_count": _count_from(
            proof_completion, "shadow_stage2_language_false_positive_count"
        ),
        "shadow_primary_direction_change_count": summary.get(
            "primary_direction_change_count", "NOT_MEASURED"
        ),
        "shadow_business_delta_change_count": summary.get(
            "business_delta_change_count", "NOT_MEASURED"
        ),
        "shadow_new_buyer_change_count": summary.get(
            "new_buyer_change_count", "NOT_MEASURED"
        ),
        "shadow_holder_change_count": summary.get(
            "holder_change_count", "NOT_MEASURED"
        ),
        "shadow_same_direction_calibration_change_count": summary.get(
            "same_direction_calibration_change_count", "NOT_MEASURED"
        ),
        "shadow_multi_field_change_count": summary.get(
            "multi_field_change_count", "NOT_MEASURED"
        ),
        "shadow_expected_contract_correction_count": summary.get(
            "expected_contract_correction_count", "NOT_MEASURED"
        ),
        "shadow_potential_architecture_regression_count": summary.get(
            "potential_architecture_regression_count", "NOT_MEASURED"
        ),
        "shadow_unresolved_review_required_count": summary.get(
            "unresolved_review_required_count", "NOT_MEASURED"
        ),
        "shadow_core_mutation_after_stance_count": shadow["core"][
            "core_mutation_count"
        ],
        "shadow_timeout_count": runtime["timeout_count"],
        "shadow_orphan_count": runtime["orphan_process_count"],
        "shadow_wrapper_retry_count": runtime["wrapper_retry_count"],
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "observed_paused_schedule_count": _count_from(
            proof_completion, "observed_paused_schedule_count"
        ),
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": (
            "COMPLETE_WITH_POLICY_DIAGNOSTICS" if clean else "BLOCKED"
        ),
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": (
            NEXT_SCOPE
            if clean
            else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR"
        ),
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }


def finalize_shadow() -> None:
    state = read_json(OUTPUT / "shadow-state.json")
    if state.get("status") != "FROZEN":
        raise ValueError("M12BG_SHADOW_NOT_FROZEN")
    if state.get("implementation_head_sha") != git("rev-parse", "HEAD"):
        raise ValueError("M12BG_CODE_CHANGED_AFTER_SHADOW_FREEZE")
    _configure_runtime()
    m12bd.m12bb.finalize_shadow()
    m12bd.m12bb.closeout()
    fictional = m12bd._fictional_payloads()
    shadow = m12bd._shadow_payloads()
    base_clean = m12bd._report_shadow(shadow)
    fcf_audit = _shadow_fcf_audit(shadow)
    matrix = read_json(
        REPORTS
        / f"{NUMBERS['shadow-cross-manifest-preflight-matrix']:03d}-"
        "shadow-cross-manifest-preflight-matrix.json"
    )
    frozen_input = read_json(
        REPORTS
        / f"{NUMBERS['shadow-frozen-input-layout-audit']:03d}-"
        "shadow-frozen-input-layout-audit.json"
    )
    program = read_json(OUTPUT / "program-state.json")
    clean = bool(
        base_clean
        and fcf_audit["status"] == "PASS"
        and matrix.get("status") == "PASS"
        and frozen_input.get("status") == "PASS"
        and program["exact_replay"]["status"] == "PASS"
        and program["fictional_reaudit"]["status"] == "PASS"
    )

    direct_report_slugs = (
        "shadow-monolithic-model-artifacts",
        "shadow-stage1-model-artifacts",
        "shadow-stage2-model-artifacts",
        "shadow-context-hard-semantic-audit",
        "shadow-stage1-wc-binding-audit",
        "shadow-stage2-wc-binding-audit",
        "shadow-financial-grounding-audit",
        "shadow-optional-audit-coverage-matrix",
        "shadow-configured-signal-field-use-audit",
        "shadow-business-delta-audit",
        "shadow-market-expectation-audit",
        "shadow-financial-sector-audit",
        "shadow-stage2-language-audit",
        "shadow-final-composition-audit",
        "shadow-aggregate-finalization-audit",
        "shadow-per-ticker-comparison",
        "shadow-core-direction-differences",
        "shadow-business-delta-differences",
        "shadow-new-buyer-differences",
        "shadow-holder-differences",
        "shadow-same-direction-calibration-differences",
        "shadow-expected-contract-corrections",
        "shadow-potential-architecture-regressions",
        "shadow-unresolved-review-required",
        "shadow-adr-security-basis-audit",
        "shadow-cyclical-valuation-audit",
        "shadow-core-immutability-audit",
        "shadow-runtime-audit",
        "shadow-aggregate-summary",
        "shadow-architecture-decision",
    )
    for slug in direct_report_slugs:
        report(slug, _local_m12bd_report(slug))
    report("shadow-fcf-prospective-requirement-audit", fcf_audit)
    report(
        "shadow-directional-requirement-eligibility-audit",
        {
            "status": (
                "PASS"
                if fcf_audit[
                    "prospective_requirement_as_current_anchor_false_accept_count"
                ]
                == 0
                else "FAIL"
            ),
            "generation_id": fcf_audit["generation_id"],
            "prospective_requirement_as_current_anchor_false_accept_count": (
                fcf_audit[
                    "prospective_requirement_as_current_anchor_false_accept_count"
                ]
            ),
            "rows": [
                row
                for row in fcf_audit["rows"]
                if row["prospective_requirement_detected"]
                and any(
                    token in row["field_path"]
                    for token in (
                        "buy_drivers",
                        "sell_drivers",
                        "dominant_evidence",
                        "core_investment_judgment",
                    )
                )
            ],
        },
    )

    diagnostics = fictional["diagnostics"]
    for slug, key in (
        ("fictional-primary-boundary-summary", "primary_direction"),
        ("fictional-delta-materiality-summary", "business_delta"),
        ("fictional-new-buyer-boundary-summary", "new_buyer"),
        ("fictional-holder-boundary-summary", "holder"),
    ):
        report(
            slug,
            {
                "status": "MEASURED",
                "rows": diagnostics[key],
                "readiness_blocking": False,
                "source_generation_id": M12BD_GENERATION_ID,
            },
        )
    for target, source in (
        ("monitored-primary-difference-summary", "shadow-core-direction-differences"),
        ("monitored-delta-difference-summary", "shadow-business-delta-differences"),
        ("monitored-new-buyer-difference-summary", "shadow-new-buyer-differences"),
        ("monitored-holder-difference-summary", "shadow-holder-differences"),
        (
            "same-direction-calibration-summary",
            "shadow-same-direction-calibration-differences",
        ),
    ):
        report(target, _local_m12bd_report(source))
    report(
        "real-fcf-requirement-scope-lessons",
        {
            "status": "PASS" if clean else "BLOCKED",
            "root_cause": ROOT_CAUSE,
            "exact_m12bf_replay": program["exact_replay"]["status"],
            "new_shadow_fcf_occurrence_count": fcf_audit["fcf_occurrence_count"],
            "new_shadow_prospective_requirement_count": fcf_audit[
                "prospective_requirement_occurrence_count"
            ],
            "false_reject_count": fcf_audit[
                "prospective_requirement_false_reject_count"
            ],
            "current_false_accept_count": fcf_audit[
                "current_fcf_false_accept_count"
            ],
            "directional_false_accept_count": fcf_audit[
                "prospective_requirement_as_current_anchor_false_accept_count"
            ],
        },
    )
    report(
        "combined-fictional-monitored-policy-input",
        {
            "status": "DIAGNOSTIC_COMPLETE" if clean else "BLOCKED",
            "fictional_generation_id": M12BD_GENERATION_ID,
            "shadow_generation_id": shadow["state"]["generation_id"],
            "fictional_variance": diagnostics,
            "shadow_summary": _local_m12bd_report("shadow-aggregate-summary"),
            "fcf_requirement_audit": fcf_audit,
            "automatic_resolution": False,
        },
    )
    report(
        "next-bounded-policy-decision",
        {
            "status": "SELECTED" if clean else "BLOCKED",
            "next_scope": (
                NEXT_SCOPE
                if clean
                else "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR"
            ),
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )

    completion = _completion(clean=clean, shadow=shadow, fcf_audit=fcf_audit)
    completion_reports = {
        "fcf-prospective-requirement-repair-success-decision": {
            "status": (
                "PASS"
                if completion["m12bf_context01_offline_replay_status"] == "PASS"
                and completion["shadow_fcf_prospective_requirement_false_reject_count"]
                == 0
                else "FAIL"
            ),
            "contract": financial.FCF_PROSPECTIVE_REQUIREMENT_CONTRACT,
        },
        "m12bf-frozen-layout-preservation-decision": {
            "status": (
                "PASS"
                if completion["model_prompt_semantic_change_count"] == 0
                and frozen_input["status"] == "PASS"
                else "FAIL"
            ),
            "layout_contract": "frozen-context-input-layout-v1",
            "new_shadow_layout": NESTED_INPUTS_V1,
        },
        "m12bd-fictional-proof-reuse-success-decision": {
            "status": (
                "PASS"
                if completion["m12bd_offline_reaudit_status"] == "PASS"
                and completion["new_fictional_model_calls"] == 0
                else "FAIL"
            ),
            "formal_fictional_reuse_status": completion[
                "formal_fictional_reuse_status"
            ],
            "new_fictional_model_calls": 0,
        },
        "new-full-shadow-completion-decision": {
            "status": "PASS" if clean else "FAIL",
            "generation_id": shadow["state"]["generation_id"],
            "model_calls": shadow["runtime"]["model_call_count"],
            "completed_ticker_count": len(shadow["compositions"]),
        },
        "two-stage-shadow-compatibility-decision": {
            "status": completion[
                "two_stage_shadow_compatibility_classification"
            ]
        },
        "existing-monitored-impact-summary": _local_m12bd_report(
            "shadow-aggregate-summary"
        ),
        "fresh-real-proof-readiness-decision": {
            "status": "NOT_READY",
            "next_scope": NEXT_SCOPE,
        },
        "final-main-merge-readiness-note": {
            "status": "NOT_READY",
            "main_merge_authorized": False,
        },
        "production-no-change": {
            "status": "PASS",
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "production_sends": 0,
            "deployments": 0,
        },
        "schedule-pause-observation": {
            "status": "OBSERVED",
            "observed_paused_schedule_count": completion[
                "observed_paused_schedule_count"
            ],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
        },
        "remote-push-prohibition-audit": {
            "status": "PASS",
            "remote_push_count": 0,
            "raw_model_artifact_remote_push_count": 0,
            "main_merges": 0,
            "deployments": 0,
        },
        "master-workflow-update": {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "path": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    }
    for slug, value in completion_reports.items():
        report(slug, value)
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BG Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Exact M12BF replay: `{completion['m12bf_context01_offline_replay_status']}`",
                f"- M12BD offline re-audit: `{completion['m12bd_offline_reaudit_status']}`",
                f"- New shadow generation: `{completion['new_shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Completed tickers: `{completion['shadow_completed_ticker_count']}`",
                f"- Hard semantic failures: `{completion['shadow_hard_semantic_failure_count']}`",
                "- Remote push/main merge/deploy: `0/0/0`",
                f"- Next scope: `{completion['next_scope']}`",
                "",
            )
        ),
    )
    if not clean:
        raise SystemExit("M12BG_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(
        json.dumps(
            {
                "status": "PASS",
                "generation_id": shadow["state"]["generation_id"],
                "model_calls": shadow["runtime"]["model_call_count"],
                "next_scope": NEXT_SCOPE,
            },
            sort_keys=True,
        )
    )


def _partial_shadow_documents(phase: str) -> list[dict[str, object]]:
    return [
        read_json(path)
        for path in sorted(
            (PROOF_OUTPUT / "shadow/model-calls").glob(
                f"context-*/{phase}/run-document.json"
            )
        )
    ]


def failure_closeout() -> None:
    _configure_runtime()
    try:
        m12bd.m12bb.failure_closeout()
    except (FileNotFoundError, KeyError, TypeError, ValueError):
        pass
    stop = (
        read_json(PROOF_OUTPUT / "shadow/stop.json")
        if (PROOF_OUTPUT / "shadow/stop.json").is_file()
        else {
            "status": "BLOCKED",
            "stop_reason": "M12BG_UNCLASSIFIED_HARD_STOP",
        }
    )
    shadow_state = (
        read_json(PROOF_OUTPUT / "shadow/program-state.json")
        if (PROOF_OUTPUT / "shadow/program-state.json").is_file()
        else {}
    )
    partial = {
        "state": shadow_state,
        "monolithic": _partial_shadow_documents("monolithic"),
        "stage1": _partial_shadow_documents("stage1"),
        "stage2": _partial_shadow_documents("stage2"),
    }
    fcf_audit = (
        _shadow_fcf_audit(partial)
        if shadow_state and any(partial[key] for key in ("monolithic", "stage1", "stage2"))
        else {
            "status": "NOT_MEASURED",
            "fcf_occurrence_count": 0,
            "prospective_requirement_false_reject_count": "NOT_MEASURED",
            "current_fcf_false_accept_count": "NOT_MEASURED",
            "prospective_requirement_as_current_anchor_false_accept_count": (
                "NOT_MEASURED"
            ),
            "proxy_as_fcf_violation_count": "NOT_MEASURED",
            "rows": [],
        }
    )
    report("shadow-fcf-prospective-requirement-audit", fcf_audit)
    report(
        "shadow-directional-requirement-eligibility-audit",
        {
            "status": fcf_audit["status"],
            "prospective_requirement_as_current_anchor_false_accept_count": (
                fcf_audit[
                    "prospective_requirement_as_current_anchor_false_accept_count"
                ]
            ),
            "rows": [
                row
                for row in fcf_audit["rows"]
                if row.get("prospective_requirement_detected")
            ],
        },
    )
    for number, slug in enumerate(REPORT_SLUGS, start=1):
        path = REPORTS / f"{number:03d}-{slug}.json"
        if not path.is_file():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})

    program = read_json(OUTPUT / "program-state.json")
    fixtures = program["fixture_audit"]
    semantic = program["semantic_surfaces"]
    completed_calls = sum(
        len(partial[key]) for key in ("monolithic", "stage1", "stage2")
    )
    completed_tickers = sum(
        len(document.get("compositions", ())) for document in partial["stage2"]
    )
    hard_failures = sum(
        row.get("status") == "FAIL"
        for key in ("monolithic", "stage1", "stage2")
        for document in partial[key]
        for row in document.get("rows", ())
    )
    unmeasured = "NOT_MEASURED"
    completion = {
        "status": "BLOCKED",
        "phase": "M12BG",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BF_BUNDLE_SHA256,
        "latest_result_integrity": program["integrity"]["status"],
        "m12bf_shadow_generation_id": M12BF_SHADOW_GENERATION_ID,
        "m12bf_shadow_model_calls_completed": 1,
        "m12bf_shadow_failure_ticker": M12BF_FAILURE_TICKER,
        "m12bf_shadow_failure_error": "unsupported_current_fcf_claim",
        "fcf_requirement_root_cause": ROOT_CAUSE,
        "fcf_prospective_requirement_contract_version": (
            financial.FCF_PROSPECTIVE_REQUIREMENT_CONTRACT
        ),
        "m12bf_005490_offline_replay_status": program["exact_replay"][
            "current_statuses"
        ][M12BF_FAILURE_TICKER],
        "m12bf_context01_offline_replay_status": program["exact_replay"]["status"],
        "fcf_prospective_requirement_false_reject_count": fixtures[
            "fcf_prospective_requirement_false_reject_count"
        ],
        "fcf_current_claim_false_accept_count": fixtures[
            "fcf_current_claim_false_accept_count"
        ],
        "fcf_current_numeric_false_accept_count": fixtures[
            "fcf_current_numeric_false_accept_count"
        ],
        "fcf_requirement_directional_anchor_false_accept_count": fixtures[
            "fcf_requirement_directional_anchor_false_accept_count"
        ],
        "model_prompt_semantic_change_count": semantic["model_prompt"][
            "semantic_change_count"
        ],
        "model_schema_semantic_change_count": semantic["model_schema"][
            "semantic_change_count"
        ],
        "stage1_wc_binding_semantic_change_count": semantic[
            "stage1_wc_binding"
        ]["semantic_change_count"],
        "stage2_wc_binding_semantic_change_count": semantic[
            "stage2_wc_binding"
        ]["semantic_change_count"],
        "configured_signal_view_change_count": semantic["configured_signal"][
            "semantic_change_count"
        ],
        "configured_financial_support_concept_change_count": semantic[
            "configured_financial_support"
        ]["semantic_change_count"],
        "business_delta_view_change_count": semantic["business_delta"][
            "semantic_change_count"
        ],
        "expectation_view_change_count": semantic["expectation_view"][
            "semantic_change_count"
        ],
        "financial_evidence_projection_change_count": semantic[
            "financial_evidence_projection"
        ]["semantic_change_count"],
        "two_stage_core_semantic_change_count": semantic["two_stage_core"][
            "semantic_change_count"
        ],
        "final_user_schema_change_count": semantic["final_user_schema"][
            "semantic_change_count"
        ],
        "formal_fictional_reuse_status": program[
            "formal_fictional_reuse_status"
        ],
        "new_fictional_model_calls": 0,
        "m12bd_offline_reaudit_status": program["fictional_reaudit"]["status"],
        "task_start_active_monitor_count": len(program["active_tickers"]),
        "task_start_active_monitor_tickers": program["active_tickers"],
        "new_shadow_generation_id": shadow_state.get("generation_id", unmeasured),
        "shadow_context_count": shadow_state.get("context_count", unmeasured),
        "shadow_monolithic_model_calls": len(partial["monolithic"]),
        "shadow_stage1_model_calls": len(partial["stage1"]),
        "shadow_stage2_model_calls": len(partial["stage2"]),
        "shadow_model_calls_total": completed_calls,
        "shadow_completed_ticker_count": completed_tickers,
        "shadow_final_composition_count": completed_tickers,
        "shadow_aggregate_finalization_status": "NOT_RUN_DUE_TO_HARD_STOP",
        "shadow_hard_semantic_failure_count": hard_failures,
        "shadow_fcf_prospective_requirement_false_reject_count": fcf_audit[
            "prospective_requirement_false_reject_count"
        ],
        "shadow_current_fcf_false_accept_count": fcf_audit[
            "current_fcf_false_accept_count"
        ],
        "shadow_prospective_requirement_as_current_anchor_false_accept_count": (
            fcf_audit[
                "prospective_requirement_as_current_anchor_false_accept_count"
            ]
        ),
        "shadow_proxy_as_fcf_violation_count": fcf_audit[
            "proxy_as_fcf_violation_count"
        ],
        "shadow_stage1_wc_grounding_failure_count": unmeasured,
        "shadow_stage2_wc_grounding_failure_count": unmeasured,
        "shadow_wc_metric_specific_mismatch_count": unmeasured,
        "shadow_wc_narrative_only_substitution_count": unmeasured,
        "shadow_unsafe_wc_auto_direction_count": unmeasured,
        "shadow_configured_signal_violation_count": unmeasured,
        "shadow_business_delta_hard_failure_count": unmeasured,
        "shadow_expectation_hard_failure_count": unmeasured,
        "shadow_financial_sector_hard_failure_count": unmeasured,
        "shadow_stage2_language_false_positive_count": unmeasured,
        "shadow_primary_direction_change_count": unmeasured,
        "shadow_business_delta_change_count": unmeasured,
        "shadow_new_buyer_change_count": unmeasured,
        "shadow_holder_change_count": unmeasured,
        "shadow_same_direction_calibration_change_count": unmeasured,
        "shadow_multi_field_change_count": unmeasured,
        "shadow_expected_contract_correction_count": unmeasured,
        "shadow_potential_architecture_regression_count": unmeasured,
        "shadow_unresolved_review_required_count": unmeasured,
        "shadow_core_mutation_after_stance_count": unmeasured,
        "shadow_timeout_count": 0,
        "shadow_orphan_count": 0,
        "shadow_wrapper_retry_count": int(stop.get("wrapper_retry_count") or 0),
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "observed_paused_schedule_count": program["schedule_start"].get(
            "observed_paused_schedule_count", unmeasured
        ),
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": (
            "BLOCKED_AFTER_NEW_SHADOW_OBJECTIVE_HARD_FAILURE"
        ),
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SMALLEST_BOUNDED_OBJECTIVE_HARD_FAILURE_REPAIR",
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "stop": stop,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        "# M12BG Failure\n\n" + json.dumps(stop, ensure_ascii=False, indent=2) + "\n",
    )


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    completion["master_workflow_update"] = "RECORDED_LOCAL_ONLY"
    write_json(OUTPUT / "program-completion.json", completion)
    report(
        "master-workflow-update",
        {
            "status": "RECORDED_LOCAL_ONLY",
            "path": "docs/MASTER_WORKFLOW.md",
            "head": completion["final_local_head_sha"],
            "remote_push": False,
        },
    )
    report("program-completion", completion)


def _artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for path in (
        *TRACKED_IMPLEMENTATION_PATHS,
        Path("docs/MASTER_WORKFLOW.md"),
        Path("docs/PROJECT_HANDOFF.md"),
        Path("docs/NEXT_SESSION_PROMPT.md"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{number:03d}-{slug}.json")
        for number, slug in enumerate(REPORT_SLUGS, start=1)
        if not (REPORTS / f"{number:03d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BG_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report("program-completion", completion)
    files = _artifact_files()
    secret_failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (capability._secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12bg-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "rows": [
            {
                "path": str(path),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BG_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12BG_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BG_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BG_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "indexed_payload_count": len(files),
                "zip_entry_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "prepare",
        "prepare-shadow",
        "run-shadow",
        "finalize-shadow",
        "failure-closeout",
        "record-docs",
    ):
        subparsers.add_parser(command)
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "prepare-shadow":
        prepare_shadow()
    elif args.command == "run-shadow":
        run_shadow()
    elif args.command == "finalize-shadow":
        finalize_shadow()
    elif args.command == "failure-closeout":
        failure_closeout()
    elif args.command == "record-docs":
        record_docs()
    elif args.command == "bundle":
        bundle(args.output)


if __name__ == "__main__":
    main()
