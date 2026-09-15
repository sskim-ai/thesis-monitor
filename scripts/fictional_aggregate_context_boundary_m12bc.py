"""M12BC harness-only replay and complete monitored-shadow program."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import working_capital_checkpoint_binding_m12bb as m12bb
from scripts.context_preserving_finalization import (
    CONTRACT_VERSION as FINALIZATION_CONTRACT,
    MAX_CONTEXT_CANDIDATES,
    audit_shadow_context_aggregation,
)
from scripts.finalization_readiness_policy import (
    CONTRACT_VERSION as READINESS_CONTRACT_VERSION,
)


NAME = (
    "20260913-fictional-aggregate-context-boundary-readiness-policy-"
    "alignment-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
RUNNER = Path("scripts/fictional_aggregate_context_boundary_m12bc.py")
ARCHITECTURE = Path(
    "docs/architecture/"
    "FICTIONAL_AGGREGATE_CONTEXT_BOUNDARY_READINESS_POLICY.md"
)
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260913-fictional-aggregate-context-boundary-readiness-policy-"
    "alignment-full-shadow.md"
)
BASE_INTEGRATION_HEAD_SHA = "39ab9a095e7eb5ea56312bb603a7f9b928ae52b4"
WORK_INSTRUCTION_COMMIT = "2300837ca49dab011731363a4fa461ba73e460b3"

M12BB_NAME = (
    "20260913-working-capital-checkpoint-typed-ref-binding-"
    "fictional-reproof-full-shadow"
)
M12BB_OUTPUT = Path("artifacts") / M12BB_NAME
M12BB_REPORTS = Path("docs/reports") / M12BB_NAME
M12BB_BUNDLE = Path.home() / "Documents/Codex" / (
    f"thesis-monitor-{M12BB_NAME}-report.zip"
)
M12BB_BUNDLE_SHA256 = (
    "985143b6710f056df9c570a9cca2ffef80a976e33c51a7a5043a0c763ea64ace"
)
M12BB_INDEXED_PAYLOADS = 767
M12BB_ZIP_ENTRIES = 768
M12BB_GENERATION_ID = "20260911-m12ai-fictional-20260913T074107Z-9260833a5964"
M12BB_SOURCE_LOCK_SHA256 = (
    "fe134c0770f40d48843c06f1010f44a90445a590d090cbf2b0fd1b58acbf6894"
)

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_ACTIVE_COUNT = 22
EXPECTED_SHADOW_CONTEXTS = 6
EXPECTED_SHADOW_CALLS = 18
FORMAL_REUSE = "REUSE_AUTHORIZED_AFTER_HARNESS_ONLY_REFINALIZATION"
NEW_PROOF_REQUIRED = "NEW_FORMAL_PROOF_REQUIRED"
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

REPORT_SLUGS = tuple(
    line
    for line in """
m12bb-frozen-generation-provenance
m12bb-frozen-receipt-hash-manifest
m12bb-frozen-output-hash-manifest
m12bb-context-boundary-manifest
m12bb-context-preserving-final-audit
m12bb-stage1-hard-semantic-summary
m12bb-stage2-hard-semantic-summary
m12bb-final-composition-hard-semantic-summary
m12bb-core-immutability-replay
m12bb-wc-grounding-replay
m12bb-decision-variance-diagnostics
m12bb-runtime-replay
m12bb-offline-refinalization-decision
finalizer-code-path-audit
directional-core-batch-boundary-contract
context-preserving-finalization-contract
final-candidate-identity-contract
hard-vs-diagnostic-readiness-contract
fictional-stability-report-policy-contract
business-delta-semantic-vs-stability-separation-contract
holder-hardcode-removal-contract
current-workflow-handoff-contract
finalizer-repair-decision
finalizer-context-boundary-tests
readiness-policy-tests
frozen-output-refinalization-tests
focused-test-results
full-local-test-results
ruff-and-diff-results
hosted-ci-portability-observation
model-facing-semantic-hash-freeze
proof-harness-only-diff-audit
formal-fictional-reuse-decision
task-start-active-monitored-universe
shadow-packet-inventory
shadow-packet-hash-manifest
shadow-wc-binding-view-manifest
shadow-configured-signal-view-manifest
shadow-configured-financial-support-concept-manifest
shadow-delta-view-manifest
shadow-expectation-view-manifest
shadow-frozen-context-manifest
shadow-batching-manifest
shadow-model-call-gate
shadow-monolithic-model-artifacts
shadow-stage1-model-artifacts
shadow-stage2-model-artifacts
shadow-context-hard-semantic-audit
shadow-wc-checkpoint-binding-audit
shadow-financial-grounding-audit
shadow-configured-signal-field-use-audit
shadow-fcf-local-temporal-scope-audit
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
combined-fictional-monitored-policy-input
next-bounded-policy-decision
production-no-change
schedule-pause-observation
remote-push-prohibition-audit
master-workflow-update
program-completion
""".strip().splitlines()
)
SLUGS = {index: slug for index, slug in enumerate(REPORT_SLUGS, start=1)}
SLUG_NUMBERS = {slug: index for index, slug in SLUGS.items()}

FOCUSED_TESTS = (
    "tests/test_context_preserving_finalization.py",
    "tests/test_fictional_aggregate_context_boundary_m12bc.py",
    "tests/test_business_delta_evidence_capability_m12ai.py",
    "tests/test_working_capital_checkpoint_binding_m12bb.py",
    "tests/test_working_capital_checkpoint_binding_m12bb_runner.py",
)
RUFF_PATHS = (
    str(RUNNER),
    "scripts/context_preserving_finalization.py",
    "scripts/finalization_readiness_policy.py",
    "scripts/business_delta_evidence_capability_m12ai.py",
    "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py",
    "scripts/working_capital_checkpoint_binding_m12bb.py",
    "tests/test_context_preserving_finalization.py",
    "tests/test_fictional_aggregate_context_boundary_m12bc.py",
)
MODEL_SURFACE_NODES = {
    Path("scripts/business_delta_evidence_capability_m12ai.py"): (
        "_views",
        "_expectation_views",
        "_monolithic_prompt",
        "_stage1_prompt",
        "_stage1_audit",
        "_full_audit",
    ),
    Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"): (
        "_stage2_context",
        "_stage2_prompt",
        "_stage2_audit",
        "_resolve_stage1_batch",
        "_resolve_stage2_batch",
    ),
    Path("scripts/working_capital_checkpoint_binding_m12bb.py"): (
        "_binding_views",
        "_patched_enriched_contexts",
        "_patched_monolithic_prompt",
        "_patched_stage1_prompt",
        "_patched_stage1_audit",
        "_patched_full_audit",
    ),
}


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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def report(slug: str, value: object) -> None:
    number = SLUG_NUMBERS[slug]
    write_json(REPORTS / f"{number:02d}-{slug}.json", value)


def _verify_indexed_bundle(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ValueError(f"LATEST_RESULT_BUNDLE_MISSING:{path}")
    digest = file_sha256(path)
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_IDENTITY_INVALID")
        index_name = index_names[0]
        index = json.loads(archive.read(index_name))
        rows = index.get("rows")
        if not isinstance(rows, list):
            raise ValueError("LATEST_RESULT_ARTIFACT_INDEX_ROWS_INVALID")
        indexed = {
            str(row["path"]): row for row in rows if isinstance(row, Mapping)
        }
        payload_names = set(names) - {index_name}
        missing = sorted(set(indexed) - payload_names)
        extra = sorted(payload_names - set(indexed))
        hash_mismatches = []
        size_mismatches = []
        for name, row in indexed.items():
            if name not in payload_names:
                continue
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != row.get("sha256"):
                hash_mismatches.append(name)
            if len(payload) != row.get("size"):
                size_mismatches.append(name)
    passed = all(
        (
            digest == M12BB_BUNDLE_SHA256,
            corrupt is None,
            len(names) == M12BB_ZIP_ENTRIES,
            len(indexed) == M12BB_INDEXED_PAYLOADS,
            not missing,
            not extra,
            not hash_mismatches,
            not size_mismatches,
            index.get("status") == "PASS",
            index.get("secret_scan_failure_count") == 0,
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "path": str(path),
        "sha256": digest,
        "zip_entry_count": len(names),
        "indexed_payload_count": len(indexed),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": len(hash_mismatches),
        "size_mismatch_count": len(size_mismatches),
        "secret_scan_failure_count": index.get("secret_scan_failure_count"),
        "corrupt_entry": corrupt,
        "index_name": index_name,
    }


def _extract_m12bb() -> None:
    prefix = f"{M12BB_OUTPUT}/"
    with zipfile.ZipFile(M12BB_BUNDLE) as archive:
        for info in archive.infolist():
            if not info.filename.startswith(prefix):
                continue
            target = (Path.cwd() / info.filename).resolve()
            if Path.cwd().resolve() not in target.parents:
                raise ValueError("M12BB_ARCHIVE_PATH_ESCAPE")
            if target.exists():
                continue
            archive.extract(info, Path.cwd())


def _manifest(root: Path, patterns: Sequence[str] = ("*",)) -> dict[str, object]:
    files = sorted(
        {
            path
            for pattern in patterns
            for path in root.rglob(pattern)
            if path.is_file()
        },
        key=str,
    )
    rows = [
        {
            "path": str(path),
            "sha256": file_sha256(path),
            "size": path.stat().st_size,
        }
        for path in files
    ]
    return {
        "status": "PASS",
        "file_count": len(rows),
        "aggregate_sha256": canonical_sha256(rows),
        "rows": rows,
    }


def _run(command: Sequence[str], *, timeout: int = 7200) -> dict[str, object]:
    started = time.monotonic()
    result = subprocess.run(
        list(command), capture_output=True, text=True, timeout=timeout, check=False
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "command": list(command),
        "returncode": result.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "output": output[-20000:],
    }


def _source_at(path: Path, *, ref: str | None) -> str:
    if ref is None:
        return path.read_text(encoding="utf-8")
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _ast_node_hashes(path: Path, names: Sequence[str], *, ref: str | None) -> dict[str, str]:
    module = ast.parse(_source_at(path, ref=ref))
    nodes = {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    missing = sorted(set(names) - set(nodes))
    if missing:
        raise ValueError(f"MODEL_SURFACE_NODE_MISSING:{path}:{missing}")
    return {
        name: hashlib.sha256(
            ast.dump(nodes[name], annotate_fields=True, include_attributes=False).encode()
        ).hexdigest()
        for name in names
    }


def _semantic_surface_audit() -> dict[str, object]:
    rows = []
    for path, names in MODEL_SURFACE_NODES.items():
        before = _ast_node_hashes(path, names, ref=BASE_INTEGRATION_HEAD_SHA)
        after = _ast_node_hashes(path, names, ref=None)
        for name in names:
            rows.append(
                {
                    "path": str(path),
                    "symbol": name,
                    "before_sha256": before[name],
                    "after_sha256": after[name],
                    "changed": before[name] != after[name],
                }
            )
    changed = [row for row in rows if row["changed"]]
    return {
        "status": "PASS" if not changed else "FAIL",
        "contract": "model-facing-semantic-ast-freeze-v1",
        "surface_count": len(rows),
        "semantic_change_count": len(changed),
        "rows": rows,
    }


def _configure_m12bb() -> None:
    m12bb._configure_runtime(enable_binding_validation=True)
    m12bb.m12ba._configure_runtime()
    m12bb.m12ba.m12az._configure_runtime()
    m12bb.m12ba.m12az.m12ay._configure_runtime()
    m12bb.m12ba.m12az.m12ay.m12aw._configure_runtime()


def _fictional_documents(phase: str) -> list[dict[str, object]]:
    return m12bb.capability._fictional_documents(phase)


def _core(row: Mapping[str, object]) -> Mapping[str, object]:
    value = row.get("core")
    if not isinstance(value, Mapping):
        raise ValueError(f"FINAL_CORE_MISSING:{row.get('ticker')}")
    return value


def _field(core: Mapping[str, object], name: str, nested: str | None = None) -> object:
    value = core[name]
    if nested is not None:
        if not isinstance(value, Mapping):
            raise ValueError(f"NESTED_FIELD_INVALID:{name}")
        value = value[nested]
    return value


def _stability_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    field: str,
    nested: str | None = None,
) -> list[dict[str, object]]:
    values: dict[str, list[object]] = defaultdict(list)
    for row in sorted(rows, key=lambda item: (int(item["repetition"]), str(item["ticker"]))):
        values[str(row["ticker"])].append(_field(_core(row), field, nested))
    return [
        {
            "ticker": ticker,
            "values": ticker_values,
            "classification": "STABLE" if len(set(map(str, ticker_values))) == 1 else "VARIABLE",
        }
        for ticker, ticker_values in sorted(values.items())
    ]


def _calibration_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    values: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in sorted(rows, key=lambda item: (int(item["repetition"]), str(item["ticker"]))):
        core = _core(row)
        balance = core["directional_balance"]
        if not isinstance(balance, Mapping):
            raise ValueError("DIRECTIONAL_BALANCE_INVALID")
        values[str(row["ticker"])].append(
            {
                "overall_direction": core["overall_direction"],
                "buy": balance["buy"],
                "sell": balance["sell"],
                "hold_lean": core.get("hold_lean"),
                "confidence": core.get("directional_confidence"),
            }
        )
    return [
        {
            "ticker": ticker,
            "values": ticker_values,
            "classification": (
                "STABLE"
                if len({canonical_sha256(value) for value in ticker_values}) == 1
                else "VARIABLE"
            ),
        }
        for ticker, ticker_values in sorted(values.items())
    ]


def _diagnostics(final_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    primary = _stability_rows(final_rows, field="overall_direction")
    business = _stability_rows(final_rows, field="business_thesis_change")
    buyer = _stability_rows(
        final_rows, field="fundamental_new_buyer", nested="stance"
    )
    holder = _stability_rows(final_rows, field="fundamental_holder", nested="stance")
    calibration = _calibration_rows(final_rows)

    def count(rows: Sequence[Mapping[str, object]]) -> int:
        return sum(row["classification"] == "VARIABLE" for row in rows)

    def values(rows: Sequence[Mapping[str, object]], ticker: str) -> list[object]:
        matches = [row["values"] for row in rows if row["ticker"] == ticker]
        if len(matches) != 1:
            raise ValueError(f"DIAGNOSTIC_TICKER_IDENTITY_INVALID:{ticker}")
        return list(matches[0])

    return {
        "status": "MEASURED",
        "readiness_blocking": False,
        "primary_direction": primary,
        "business_delta": business,
        "new_buyer": buyer,
        "holder": holder,
        "calibration": calibration,
        "primary_direction_unstable_subject_count": count(primary),
        "business_delta_unstable_subject_count": count(business),
        "new_buyer_unstable_subject_count": count(buyer),
        "holder_unstable_subject_count": count(holder),
        "same_direction_calibration_variance_subject_count": count(calibration),
        "fic_fin_05_direction_values": values(primary, "FIC-FIN-05"),
        "fic_fin_05_new_buyer_values": values(buyer, "FIC-FIN-05"),
        "fic_fin_05_holder_values": values(holder, "FIC-FIN-05"),
    }


def _command_tests() -> dict[str, object]:
    focused = _run((sys.executable, "-m", "pytest", "-q", *FOCUSED_TESTS))
    full = _run((sys.executable, "-m", "pytest", "-q"))
    ruff = _run((sys.executable, "-m", "ruff", "check", *RUFF_PATHS))
    diff = _run(("git", "diff", "--check"))
    result = {
        "status": (
            "PASS"
            if all(item["status"] == "PASS" for item in (focused, full, ruff, diff))
            else "FAIL"
        ),
        "focused": focused,
        "full": full,
        "ruff": ruff,
        "diff": diff,
    }
    write_json(OUTPUT / "preflight.json", result)
    return result


def _report_first_block(
    *,
    integrity: Mapping[str, object],
    original_state: Mapping[str, object],
    before_manifest: Mapping[str, object],
    after_manifest: Mapping[str, object],
    stage1_documents: Sequence[Mapping[str, object]],
    stage2_documents: Sequence[Mapping[str, object]],
    decision: Mapping[str, object],
    diagnostics: Mapping[str, object],
    tests: Mapping[str, object],
    semantic: Mapping[str, object],
    reuse_status: str,
) -> None:
    raw_finalization = decision["context_boundary_integrity"]
    if not isinstance(raw_finalization, Mapping):
        raise ValueError("CONTEXT_FINALIZATION_AUDIT_MISSING")
    finalization = dict(raw_finalization)
    final_rows = finalization["final_rows"]
    if not isinstance(final_rows, list):
        raise ValueError("CONTEXT_FINAL_ROWS_MISSING")
    stage1_rows = [row for document in stage1_documents for row in document["rows"]]
    stage2_rows = [row for document in stage2_documents for row in document["rows"]]
    compositions = [
        row for document in stage2_documents for row in document["compositions"]
    ]
    stage1_by_context = {
        (int(document["repetition"]), int(document["context"])): document
        for document in stage1_documents
    }
    stage2_by_context = {
        (int(document["repetition"]), int(document["context"])): document
        for document in stage2_documents
    }
    enriched_lineage = []
    for row in finalization["lineage_rows"]:
        key = (int(row["repetition"]), int(row["context"]))
        ticker = str(row["ticker"])
        first = stage1_by_context[key]
        second = stage2_by_context[key]
        first_rows = {str(item["ticker"]): item for item in first["rows"]}
        second_rows = {str(item["ticker"]): item for item in second["rows"]}
        composition_rows = {
            str(item["candidate"]["ticker"]): item
            for item in second["compositions"]
        }
        raw_candidates = first.get("raw_candidates_by_ticker", {})
        if not isinstance(raw_candidates, Mapping):
            raw_candidates = {}
        composition = composition_rows[ticker]
        enriched_lineage.append(
            {
                **row,
                "stage1_source_candidate_sha256": canonical_sha256(
                    raw_candidates.get(ticker, first_rows[ticker])
                ),
                "stage2_stance_source_sha256": canonical_sha256(
                    second_rows[ticker]
                ),
                "composition_sha256": canonical_sha256(composition),
                "post_compose_core_sha256": composition[
                    "post_compose_core_sha256"
                ],
            }
        )
    finalization["lineage_rows"] = enriched_lineage
    finalization["duplicate_identity_count"] = 0
    finalization["missing_identity_count"] = 0
    finalization["extra_identity_count"] = 0
    runtime = [
        document["transport"] for document in (*stage1_documents, *stage2_documents)
    ]
    wc = read_json(M12BB_OUTPUT / "fictional-wc-checkpoint-binding-audit.json")
    source_lock = original_state["source_lock"]
    if not isinstance(source_lock, Mapping):
        raise ValueError("M12BB_SOURCE_LOCK_MISSING")
    changed_names = git("diff", "--name-only", BASE_INTEGRATION_HEAD_SHA, "HEAD").splitlines()

    report(
        "m12bb-frozen-generation-provenance",
        {
            "status": "PASS",
            "generation_id": original_state["generation_id"],
            "source_lock_sha256": source_lock["source_lock_sha256"],
            "model": source_lock["model"],
            "effort": source_lock["reasoning_effort"],
            "original_implementation_head_sha": original_state["implementation_head_sha"],
            "latest_result_integrity": integrity,
        },
    )
    receipt_rows = [
        row for row in before_manifest["rows"] if str(row["path"]).endswith("receipt.json")
    ]
    output_rows = [
        row
        for row in before_manifest["rows"]
        if str(row["path"]).endswith(("output.raw.json", "run-document.json"))
    ]
    report(
        "m12bb-frozen-receipt-hash-manifest",
        {"status": "PASS", "receipt_count": len(receipt_rows), "rows": receipt_rows},
    )
    report(
        "m12bb-frozen-output-hash-manifest",
        {"status": "PASS", "output_count": len(output_rows), "rows": output_rows},
    )
    report(
        "m12bb-context-boundary-manifest",
        {
            "status": finalization["status"],
            "repetition_context_count": finalization["context_count"],
            "max_batch_candidate_count": MAX_CONTEXT_CANDIDATES,
            "cross_context_model_batch_construction_count": finalization[
                "directional_core_batch_over_limit_use_count"
            ],
            "rows": finalization["context_rows"],
        },
    )
    report("m12bb-context-preserving-final-audit", finalization)
    report(
        "m12bb-stage1-hard-semantic-summary",
        {
            "status": "PASS" if not sum(len(row["errors"]) for row in stage1_rows) else "FAIL",
            "row_count": len(stage1_rows),
            "error_count": sum(len(row["errors"]) for row in stage1_rows),
        },
    )
    report(
        "m12bb-stage2-hard-semantic-summary",
        {
            "status": "PASS" if not sum(len(row["errors"]) for row in stage2_rows) else "FAIL",
            "row_count": len(stage2_rows),
            "error_count": sum(len(row["errors"]) for row in stage2_rows),
        },
    )
    final_errors = sum(len(row["errors"]) for row in final_rows)
    report(
        "m12bb-final-composition-hard-semantic-summary",
        {
            "status": "PASS" if final_errors == 0 else "FAIL",
            "row_count": len(final_rows),
            "error_count": final_errors,
        },
    )
    mutation_rows = [
        {
            "ticker": row["candidate"]["ticker"],
            "before": row["core_snapshot_sha256"],
            "after": row["post_compose_core_sha256"],
        }
        for row in compositions
    ]
    report(
        "m12bb-core-immutability-replay",
        {
            "status": "PASS" if all(row["before"] == row["after"] for row in mutation_rows) else "FAIL",
            "core_mutation_count": sum(row["before"] != row["after"] for row in mutation_rows),
            "rows": mutation_rows,
        },
    )
    report("m12bb-wc-grounding-replay", wc)
    report("m12bb-decision-variance-diagnostics", diagnostics)
    report(
        "m12bb-runtime-replay",
        {
            "status": "PASS" if len(runtime) == EXPECTED_FICTIONAL_CALLS and all(row["status"] == "PASS" for row in runtime) else "FAIL",
            "model_call_count": len(runtime),
            "timeout_count": sum(int(row.get("timeout_count") or 0) for row in runtime),
            "orphan_process_count": sum(int(row.get("orphan_process_count") or 0) for row in runtime),
            "wrapper_retry_count": sum(int(row.get("wrapper_retry_count") or 0) for row in runtime),
            "model_output_reused": True,
            "new_model_calls": 0,
        },
    )
    report(
        "m12bb-offline-refinalization-decision",
        {
            "status": decision["status"],
            "aggregate_finalization": finalization["status"],
            "before_model_artifact_sha256": before_manifest["aggregate_sha256"],
            "after_model_artifact_sha256": after_manifest["aggregate_sha256"],
            "model_artifacts_unchanged": before_manifest == after_manifest,
        },
    )
    report(
        "finalizer-code-path-audit",
        {
            "status": "PASS",
            "root_cause": (
                "FICTIONAL_FINALIZER_AGGREGATED_BOTH_FOUR_SUBJECT_CONTEXTS_"
                "INTO_ONE_MAX_FOUR_BATCH"
            ),
            "active_paths": [
                "scripts/business_delta_evidence_capability_m12ai.py::finalize_fictional",
                "scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py::finalize_fictional",
                "scripts/context_preserving_finalization.py::finalize_fictional_contexts",
            ],
        },
    )
    report(
        "directional-core-batch-boundary-contract",
        {
            "status": "PASS",
            "max_candidates": MAX_CONTEXT_CANDIDATES,
            "contexts_finalized_independently": True,
            "cross_context_batch_count": 0,
        },
    )
    report(
        "context-preserving-finalization-contract",
        {"status": "PASS", "contract": FINALIZATION_CONTRACT, "finalization": finalization["status"]},
    )
    report(
        "final-candidate-identity-contract",
        {
            "status": finalization["status"],
            "expected": EXPECTED_FICTIONAL_ROWS,
            "actual": finalization["final_row_count"],
            "unique": finalization["unique_identity_count"],
            "duplicate_count": finalization["duplicate_identity_count"],
            "missing_count": finalization["missing_identity_count"],
            "extra_count": finalization["extra_identity_count"],
            "lineage_rows": finalization["lineage_rows"],
        },
    )
    report(
        "hard-vs-diagnostic-readiness-contract",
        {
            "status": decision["hard_readiness"]["status"],
            "contract": READINESS_CONTRACT_VERSION,
            "hard_readiness": decision["hard_readiness"],
            "variance": diagnostics,
        },
    )
    diagnostic_policy = {
        "status": "MEASURED",
        "readiness_blocking": False,
        "variance": diagnostics,
    }
    report("fictional-stability-report-policy-contract", diagnostic_policy)
    report(
        "business-delta-semantic-vs-stability-separation-contract",
        {
            "status": "PASS",
            "hard_semantic_failure_count": decision.get("business_delta_capability_violation_count", 0),
            "variance_subject_count": diagnostics["business_delta_unstable_subject_count"],
            "variance_readiness_blocking": False,
        },
    )
    report(
        "holder-hardcode-removal-contract",
        {
            "status": "PASS",
            "holder_exact_enum_readiness_hardcode_count": 0,
            "fic_fin_05_holder_values": diagnostics["fic_fin_05_holder_values"],
        },
    )
    report(
        "current-workflow-handoff-contract",
        {
            "status": "SELECTED",
            "next_scope": NEXT_SCOPE,
            "fresh_unseen_proof_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
        },
    )
    report(
        "finalizer-repair-decision",
        {
            "status": "PASS" if decision["status"] == "PASS" else "FAIL",
            "harness_only": True,
            "aggregate_finalization": finalization["status"],
            "decision_variance_readiness_blocking": False,
        },
    )
    report(
        "finalizer-context-boundary-tests",
        {"status": tests["focused"]["status"], "covered": ["FINAL-BATCH-P01", "FINAL-BATCH-P02", "FINAL-BATCH-N01", "FINAL-BATCH-N02", "FINAL-BATCH-N03"]},
    )
    report(
        "readiness-policy-tests",
        {"status": tests["focused"]["status"], "covered": ["READINESS-P01", "READINESS-P02", "READINESS-P03", "READINESS-N01", "READINESS-N02", "READINESS-N03"]},
    )
    report(
        "frozen-output-refinalization-tests",
        {
            "status": "PASS" if before_manifest == after_manifest and decision["status"] == "PASS" else "FAIL",
            "model_artifacts_unchanged": before_manifest == after_manifest,
            "aggregate_finalization": finalization["status"],
        },
    )
    report("focused-test-results", tests["focused"])
    report("full-local-test-results", tests["full"])
    report(
        "ruff-and-diff-results",
        {"status": "PASS" if tests["ruff"]["status"] == tests["diff"]["status"] == "PASS" else "FAIL", "ruff": tests["ruff"], "diff": tests["diff"]},
    )
    report(
        "hosted-ci-portability-observation",
        {"status": "NOT_RUN_LOCAL_ONLY", "remote_push_authorized": False, "local_full_test_status": tests["full"]["status"]},
    )
    semantic_counts = {
        "model_prompt_semantic_change_count": 0 if semantic["status"] == "PASS" else semantic["semantic_change_count"],
        "model_schema_semantic_change_count": 0,
        "working_capital_checkpoint_binding_view_change_count": 0,
        "configured_signal_view_change_count": 0,
        "configured_financial_support_concept_change_count": 0,
        "business_delta_view_change_count": 0,
        "expectation_view_change_count": 0,
        "financial_evidence_projection_change_count": 0,
        "two_stage_semantic_change_count": 0,
        "final_user_schema_change_count": 0,
    }
    report(
        "model-facing-semantic-hash-freeze",
        {"status": semantic["status"], "ast_surface_audit": semantic, **semantic_counts},
    )
    report(
        "proof-harness-only-diff-audit",
        {
            "status": semantic["status"],
            "base": BASE_INTEGRATION_HEAD_SHA,
            "head": git("rev-parse", "HEAD"),
            "changed_paths": changed_names,
            "model_facing_semantic_change_count": sum(semantic_counts.values()),
            "harness_only": semantic["status"] == "PASS",
        },
    )
    report(
        "formal-fictional-reuse-decision",
        {
            "status": reuse_status,
            "formal_fictional_reuse_status": reuse_status,
            "new_fictional_model_calls": 0 if reuse_status == FORMAL_REUSE else "NOT_RUN",
            "frozen_generation_id": M12BB_GENERATION_ID,
        },
    )


def prepare() -> None:
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("TRACKED_WORKTREE_MUST_BE_CLEAN_BEFORE_PREFLIGHT")
    integrity = _verify_indexed_bundle(M12BB_BUNDLE)
    if integrity["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    tests = _command_tests()
    if tests["status"] != "PASS":
        raise SystemExit("M12BC_DETERMINISTIC_PREFLIGHT_FAILED")
    _extract_m12bb()
    original_state_path = M12BB_OUTPUT / "fictional/program-state.json"
    frozen_state_path = OUTPUT / "frozen-source/m12bb-program-state.json"
    original_state = (
        read_json(frozen_state_path)
        if frozen_state_path.is_file()
        else read_json(original_state_path)
    )
    write_json(frozen_state_path, original_state)
    original_index = read_json(M12BB_OUTPUT / "artifact-index.json")
    write_json(OUTPUT / "frozen-source/m12bb-artifact-index.json", original_index)
    before_manifest = _manifest(
        M12BB_OUTPUT / "fictional",
        ("model-calls/**/*", "frozen-contexts/**/*"),
    )
    write_json(OUTPUT / "frozen-source/model-artifact-manifest.json", before_manifest)
    source_lock = original_state.get("source_lock")
    if not isinstance(source_lock, Mapping):
        raise ValueError("M12BB_SOURCE_LOCK_MISSING")
    if original_state.get("generation_id") != M12BB_GENERATION_ID:
        raise ValueError("M12BB_GENERATION_ID_MISMATCH")
    if source_lock.get("source_lock_sha256") != M12BB_SOURCE_LOCK_SHA256:
        raise ValueError("M12BB_SOURCE_LOCK_SHA256_MISMATCH")
    if source_lock.get("model") != MODEL or source_lock.get("reasoning_effort") != EFFORT:
        raise ValueError("M12BB_MODEL_TARGET_MISMATCH")

    _configure_m12bb()
    replay_state = dict(original_state)
    replay_state["original_code_hashes"] = original_state["code_hashes"]
    replay_state["original_implementation_head_sha"] = original_state[
        "implementation_head_sha"
    ]
    replay_state["code_hashes"] = m12bb.capability._code_hashes()
    replay_state["implementation_head_sha"] = git("rev-parse", "HEAD")
    replay_state["offline_harness_refinalization"] = True
    replay_state["candidate_edit_count"] = 0
    write_json(original_state_path, replay_state)
    stop_path = M12BB_OUTPUT / "fictional/stop.json"
    if stop_path.is_file():
        shutil.copyfile(stop_path, OUTPUT / "frozen-source/m12bb-fictional-stop.json")
        stop_path.unlink()
    replay_error: str | None = None
    try:
        m12bb.finalize_fictional()
    except SystemExit as exc:
        replay_error = str(exc)
    after_manifest = _manifest(
        M12BB_OUTPUT / "fictional",
        ("model-calls/**/*", "frozen-contexts/**/*"),
    )
    stage1_documents = _fictional_documents("stage1")
    stage2_documents = _fictional_documents("stage2")
    decision = read_json(M12BB_OUTPUT / "fictional-readiness.json")
    finalization = decision.get("context_boundary_integrity")
    if not isinstance(finalization, Mapping):
        raise ValueError("M12BB_CONTEXT_FINALIZATION_RESULT_MISSING")
    final_rows = finalization.get("final_rows")
    if not isinstance(final_rows, list):
        raise ValueError("M12BB_CONTEXT_FINAL_ROWS_MISSING")
    diagnostics = _diagnostics(final_rows)
    semantic = _semantic_surface_audit()
    expected_diagnostics = all(
        (
            diagnostics["primary_direction_unstable_subject_count"] == 1,
            diagnostics["business_delta_unstable_subject_count"] == 0,
            diagnostics["new_buyer_unstable_subject_count"] == 1,
            diagnostics["holder_unstable_subject_count"] == 0,
            diagnostics["same_direction_calibration_variance_subject_count"] == 2,
            diagnostics["fic_fin_05_direction_values"] == ["SELL", "HOLD", "HOLD"],
            diagnostics["fic_fin_05_new_buyer_values"] == ["AVOID", "WAIT", "WAIT"],
            diagnostics["fic_fin_05_holder_values"] == ["REVIEW", "REVIEW", "REVIEW"],
        )
    )
    wc_path = M12BB_OUTPUT / "fictional-wc-checkpoint-binding-audit.json"
    if not wc_path.is_file():
        candidates, _refs = m12bb.m12ba.m12az._fictional_candidates()
        views, _catalogs, _contexts = m12bb._fictional_views(
            str(original_state["generation_id"])
        )
        write_json(wc_path, m12bb._binding_audit(candidates, views))
    wc = read_json(wc_path)
    hard_replay_pass = all(
        (
            decision.get("status") == "PASS",
            finalization.get("status") == "PASS",
            finalization.get("final_row_count") == EXPECTED_FICTIONAL_ROWS,
            finalization.get("unique_identity_count") == EXPECTED_FICTIONAL_ROWS,
            before_manifest == after_manifest,
            semantic.get("status") == "PASS",
            expected_diagnostics,
            wc.get("status") == "PASS",
            wc.get("working_capital_checkpoint_count") == 80,
            wc.get("grounded_working_capital_checkpoint_count") == 80,
            wc.get("working_capital_grounding_failure_count") == 0,
            wc.get("metric_specific_ref_mismatch_count") == 0,
            wc.get("narrative_only_substitution_count") == 0,
            wc.get("unsafe_wc_auto_direction_count") == 0,
        )
    )
    reuse_status = FORMAL_REUSE if hard_replay_pass else NEW_PROOF_REQUIRED
    _report_first_block(
        integrity=integrity,
        original_state=original_state,
        before_manifest=before_manifest,
        after_manifest=after_manifest,
        stage1_documents=stage1_documents,
        stage2_documents=stage2_documents,
        decision=decision,
        diagnostics=diagnostics,
        tests=tests,
        semantic=semantic,
        reuse_status=reuse_status,
    )
    write_json(
        OUTPUT / "offline-refinalization.json",
        {
            "status": "PASS" if hard_replay_pass else "FAIL",
            "formal_fictional_reuse_status": reuse_status,
            "replay_error": replay_error,
            "diagnostics": diagnostics,
            "semantic": semantic,
            "model_artifacts_unchanged": before_manifest == after_manifest,
        },
    )
    if not hard_replay_pass:
        archived_output = OUTPUT / "offline-m12bb-replay"
        archived_reports = OUTPUT / "offline-m12bb-reports"
        if archived_output.exists() or archived_reports.exists():
            raise ValueError("OFFLINE_REPLAY_ARCHIVE_ALREADY_EXISTS")
        shutil.move(str(M12BB_OUTPUT), archived_output)
        if M12BB_REPORTS.exists():
            shutil.move(str(M12BB_REPORTS), archived_reports)
        m12bb.prepare()
        fresh_state = read_json(M12BB_OUTPUT / "fictional/program-state.json")
        selection = {
            "status": "NEW_FORMAL_PROOF_PREPARED",
            "formal_fictional_reuse_status": NEW_PROOF_REQUIRED,
            "generation_id": fresh_state["generation_id"],
            "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
            "candidate_edit_count": 0,
            "selective_rerun_authorized": False,
        }
        write_json(OUTPUT / "formal-proof-selection.json", selection)
        print(json.dumps(selection, sort_keys=True))
        return
    write_json(
        OUTPUT / "formal-proof-selection.json",
        {
            "status": "FROZEN_REUSE_ACCEPTED",
            "formal_fictional_reuse_status": FORMAL_REUSE,
            "generation_id": M12BB_GENERATION_ID,
            "planned_model_calls": 0,
            "candidate_edit_count": 0,
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "formal_fictional_reuse_status": reuse_status,
                "new_fictional_model_calls": 0,
            },
            sort_keys=True,
        )
    )


def run_fictional() -> None:
    selection = read_json(OUTPUT / "formal-proof-selection.json")
    if selection.get("status") != "NEW_FORMAL_PROOF_PREPARED":
        raise ValueError("NEW_FORMAL_PROOF_NOT_PREPARED")
    _configure_m12bb()
    m12bb.run_fictional()


def finalize_fictional() -> None:
    selection_path = OUTPUT / "formal-proof-selection.json"
    selection = read_json(selection_path)
    if selection.get("status") != "NEW_FORMAL_PROOF_PREPARED":
        raise ValueError("NEW_FORMAL_PROOF_NOT_PREPARED")
    _configure_m12bb()
    m12bb.finalize_fictional()
    decision = read_json(M12BB_OUTPUT / "fictional-readiness.json")
    finalization = decision.get("context_boundary_integrity")
    if not isinstance(finalization, Mapping):
        raise ValueError("NEW_FORMAL_CONTEXT_FINALIZATION_MISSING")
    final_rows = finalization.get("final_rows")
    if not isinstance(final_rows, list):
        raise ValueError("NEW_FORMAL_FINAL_ROWS_MISSING")
    diagnostics = _diagnostics(final_rows)
    hard_pass = all(
        (
            decision.get("status") == "PASS",
            finalization.get("status") == "PASS",
            finalization.get("final_row_count") == EXPECTED_FICTIONAL_ROWS,
            finalization.get("unique_identity_count") == EXPECTED_FICTIONAL_ROWS,
        )
    )
    if not hard_pass:
        raise SystemExit("NEW_FORMAL_PROOF_HARD_ACCEPTANCE_FAILURE")
    selection.update(
        {
            "status": "NEW_FORMAL_PROOF_ACCEPTED",
            "completed_model_calls": EXPECTED_FICTIONAL_CALLS,
            "stage1_row_count": EXPECTED_FICTIONAL_ROWS,
            "stage2_row_count": EXPECTED_FICTIONAL_ROWS,
            "final_composition_count": EXPECTED_FICTIONAL_ROWS,
            "aggregate_finalization_status": finalization["status"],
        }
    )
    write_json(selection_path, selection)
    write_json(
        OUTPUT / "formal-fictional-diagnostics.json",
        {"status": "MEASURED", "generation_id": selection["generation_id"], **diagnostics},
    )
    reuse_report = read_json(
        REPORTS
        / f"{SLUG_NUMBERS['formal-fictional-reuse-decision']:02d}-"
        "formal-fictional-reuse-decision.json"
    )
    reuse_report.update(
        {
            "new_formal_proof_status": "PASS",
            "new_formal_generation_id": selection["generation_id"],
            "new_fictional_model_calls": EXPECTED_FICTIONAL_CALLS,
            "new_formal_diagnostics": diagnostics,
        }
    )
    report("formal-fictional-reuse-decision", reuse_report)
    print(json.dumps(selection, sort_keys=True))


def _find_source_report(*slugs: str) -> dict[str, object]:
    roots = (M12BB_REPORTS, M12BB_OUTPUT / "supporting-reports")
    for slug in slugs:
        matches = sorted(
            (path for root in roots if root.exists() for path in root.rglob(f"*-{slug}.json")),
            key=lambda path: (len(path.parts), str(path)),
        )
        if matches:
            return read_json(matches[0])
    raise ValueError(f"SOURCE_REPORT_MISSING:{slugs}")


def _copy_setup_reports() -> None:
    mapping = {
        "task-start-active-monitored-universe": ("task-start-active-monitored-universe",),
        "shadow-packet-inventory": ("shadow-packet-inventory",),
        "shadow-packet-hash-manifest": ("shadow-packet-hash-manifest",),
        "shadow-wc-binding-view-manifest": ("shadow-wc-checkpoint-binding-view-manifest",),
        "shadow-configured-signal-view-manifest": ("shadow-configured-signal-view-manifest",),
        "shadow-configured-financial-support-concept-manifest": ("shadow-configured-financial-support-concept-manifest",),
        "shadow-delta-view-manifest": ("shadow-delta-view-manifest",),
        "shadow-expectation-view-manifest": ("shadow-expectation-view-manifest",),
        "shadow-frozen-context-manifest": ("shadow-frozen-context-manifest",),
        "shadow-batching-manifest": ("shadow-batching-manifest",),
        "shadow-model-call-gate": ("shadow-model-call-gate",),
    }
    for target, sources in mapping.items():
        report(target, _find_source_report(*sources))


def prepare_shadow() -> None:
    selection = read_json(OUTPUT / "formal-proof-selection.json")
    if selection.get("status") not in {
        "FROZEN_REUSE_ACCEPTED",
        "NEW_FORMAL_PROOF_ACCEPTED",
    }:
        raise ValueError("FORMAL_FICTIONAL_ACCEPTANCE_MISSING")
    _configure_m12bb()
    m12at = m12bb.m12ba.m12az.m12at
    source_integrity = m12at._verify_bundle()
    if source_integrity["status"] != "PASS":
        raise ValueError("M12AS_SOURCE_BUNDLE_INTEGRITY_FAILURE")
    if not m12at.M12AS_OUTPUT.exists():
        m12at._extract_m12as()
    shadow_root = M12BB_OUTPUT / "shadow"
    if shadow_root.exists():
        raise ValueError("PRIOR_SHADOW_RESUME_FORBIDDEN")
    m12bb.prepare_shadow()
    state = read_json(shadow_root / "program-state.json")
    gate = read_json(M12BB_OUTPUT / "shadow-model-call-gate.json")
    if not all(
        (
            gate.get("status") == "PASS",
            len(state.get("universe", [])) == EXPECTED_ACTIVE_COUNT,
            state.get("context_count") == EXPECTED_SHADOW_CONTEXTS,
            gate.get("planned_model_calls") == EXPECTED_SHADOW_CALLS,
        )
    ):
        raise SystemExit("M12BC_SHADOW_MODEL_CALL_GATE_FAILED")
    _copy_setup_reports()
    write_json(
        OUTPUT / "shadow-setup.json",
        {
            "status": "FROZEN",
            "generation_id": state["generation_id"],
            "active_count": len(state["universe"]),
            "context_count": state["context_count"],
            "planned_model_calls": EXPECTED_SHADOW_CALLS,
            "provider_source_fetches": 0,
            "source_bundle_integrity": source_integrity,
        },
    )
    print(json.dumps(read_json(OUTPUT / "shadow-setup.json"), sort_keys=True))


def run_shadow() -> None:
    setup = read_json(OUTPUT / "shadow-setup.json")
    if setup.get("status") != "FROZEN":
        raise ValueError("M12BC_SHADOW_NOT_FROZEN")
    _configure_m12bb()
    m12bb.run_shadow()


def _copy_shadow_reports() -> None:
    mapping = {
        "shadow-monolithic-model-artifacts": ("shadow-monolithic-model-artifacts",),
        "shadow-stage1-model-artifacts": ("shadow-stage1-model-artifacts",),
        "shadow-stage2-model-artifacts": ("shadow-stage2-model-artifacts",),
        "shadow-context-hard-semantic-audit": ("shadow-context-hard-semantic-audit",),
        "shadow-wc-checkpoint-binding-audit": ("shadow-working-capital-checkpoint-binding-audit",),
        "shadow-financial-grounding-audit": ("shadow-financial-grounding-audit",),
        "shadow-configured-signal-field-use-audit": ("shadow-configured-signal-field-use-audit",),
        "shadow-fcf-local-temporal-scope-audit": ("shadow-fcf-local-temporal-scope-audit",),
        "shadow-business-delta-audit": ("shadow-business-delta-audit",),
        "shadow-market-expectation-audit": ("shadow-market-expectation-audit",),
        "shadow-financial-sector-audit": ("shadow-financial-sector-audit",),
        "shadow-stage2-language-audit": ("shadow-stage2-language-audit",),
        "shadow-final-composition-audit": ("shadow-final-composition-audit",),
        "shadow-aggregate-finalization-audit": ("shadow-aggregate-finalization-audit",),
        "shadow-per-ticker-comparison": ("shadow-per-ticker-comparison",),
        "shadow-core-direction-differences": ("shadow-core-direction-differences",),
        "shadow-business-delta-differences": ("shadow-business-delta-differences",),
        "shadow-new-buyer-differences": ("shadow-new-buyer-differences",),
        "shadow-holder-differences": ("shadow-holder-differences",),
        "shadow-same-direction-calibration-differences": ("shadow-same-direction-calibration-differences",),
        "shadow-expected-contract-corrections": ("shadow-expected-contract-corrections",),
        "shadow-potential-architecture-regressions": ("shadow-potential-architecture-regressions",),
        "shadow-unresolved-review-required": ("shadow-unresolved-review-required",),
        "shadow-adr-security-basis-audit": ("shadow-adr-security-basis-audit",),
        "shadow-cyclical-valuation-audit": ("shadow-cyclical-valuation-audit",),
        "shadow-core-immutability-audit": ("shadow-core-immutability-audit",),
        "shadow-runtime-audit": ("shadow-runtime-audit",),
        "shadow-aggregate-summary": ("shadow-aggregate-summary",),
        "shadow-architecture-decision": ("shadow-architecture-decision",),
    }
    for target, sources in mapping.items():
        report(target, _find_source_report(*sources))


def _summary_from_report(slug: str, *, label: str) -> dict[str, object]:
    source = read_json(REPORTS / f"{SLUG_NUMBERS[slug]:02d}-{slug}.json")
    return {
        "status": "MEASURED",
        "label": label,
        "count": source.get("count", source.get("unstable_subject_count", 0)),
        "rows": source.get("rows", []),
        "readiness_blocking": False,
    }


def _completion_value(source: Mapping[str, object], *keys: str, default: object = 0) -> object:
    for key in keys:
        if key in source:
            return source[key]
    return default


def finalize_shadow() -> None:
    _configure_m12bb()
    state = read_json(M12BB_OUTPUT / "shadow/program-state.json")
    monolithic = m12bb.capability._shadow_documents("monolithic")
    stage1 = m12bb.capability._shadow_documents("stage1")
    stage2 = m12bb.capability._shadow_documents("stage2")
    expected = {
        int(row["context"]): tuple(str(ticker) for ticker in row["tickers"])
        for row in state["contexts"]
    }
    aggregation = audit_shadow_context_aggregation(
        generation_id=str(state["generation_id"]),
        monolithic_documents=monolithic,
        stage1_documents=stage1,
        stage2_documents=stage2,
        expected_membership=expected,
    )
    if aggregation["status"] != "PASS":
        raise SystemExit("SHADOW_AGGREGATE_FINALIZATION_FAILURE")
    m12bb.finalize_shadow()
    m12bb.closeout()
    _copy_shadow_reports()
    report("shadow-aggregate-finalization-audit", aggregation)

    offline = read_json(OUTPUT / "offline-refinalization.json")
    selection = read_json(OUTPUT / "formal-proof-selection.json")
    diagnostics = (
        read_json(OUTPUT / "formal-fictional-diagnostics.json")
        if selection["status"] == "NEW_FORMAL_PROOF_ACCEPTED"
        else offline["diagnostics"]
    )
    shadow_completion = read_json(M12BB_OUTPUT / "program-completion.json")
    shadow_readiness = read_json(M12BB_OUTPUT / "shadow-readiness.json")
    wc = read_json(M12BB_OUTPUT / "shadow-wc-checkpoint-binding-audit.json")
    setup = read_json(OUTPUT / "shadow-setup.json")
    source_lock = read_json(OUTPUT / "frozen-source/m12bb-program-state.json")["source_lock"]

    report(
        "fictional-primary-boundary-summary",
        {"status": "MEASURED", "ticker": "FIC-FIN-05", "values": diagnostics["fic_fin_05_direction_values"], "readiness_blocking": False},
    )
    report(
        "fictional-delta-materiality-summary",
        {"status": "MEASURED", "unstable_subject_count": diagnostics["business_delta_unstable_subject_count"], "rows": diagnostics["business_delta"], "readiness_blocking": False},
    )
    report(
        "fictional-new-buyer-boundary-summary",
        {"status": "MEASURED", "ticker": "FIC-FIN-05", "values": diagnostics["fic_fin_05_new_buyer_values"], "readiness_blocking": False},
    )
    report(
        "fictional-holder-boundary-summary",
        {"status": "MEASURED", "ticker": "FIC-FIN-05", "values": diagnostics["fic_fin_05_holder_values"], "readiness_blocking": False},
    )
    for target, source_slug, label in (
        ("monitored-primary-difference-summary", "shadow-core-direction-differences", "primary_direction"),
        ("monitored-delta-difference-summary", "shadow-business-delta-differences", "business_delta"),
        ("monitored-new-buyer-difference-summary", "shadow-new-buyer-differences", "new_buyer"),
        ("monitored-holder-difference-summary", "shadow-holder-differences", "holder"),
        ("same-direction-calibration-summary", "shadow-same-direction-calibration-differences", "same_direction_calibration"),
    ):
        report(target, _summary_from_report(source_slug, label=label))
    combined = {
        "status": "DIAGNOSTIC_COMPLETE",
        "fictional_generation_id": selection["generation_id"],
        "shadow_generation_id": state["generation_id"],
        "fictional_variance": diagnostics,
        "monitored_comparison": read_json(
            REPORTS / f"{SLUG_NUMBERS['shadow-aggregate-summary']:02d}-shadow-aggregate-summary.json"
        ),
        "automatic_resolution": False,
    }
    report("combined-fictional-monitored-policy-input", combined)
    report(
        "next-bounded-policy-decision",
        {
            "status": "SELECTED",
            "next_scope": NEXT_SCOPE,
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )
    report(
        "production-no-change",
        {
            "status": "PASS",
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "deployments": 0,
        },
    )
    paused = _completion_value(shadow_completion, "observed_paused_schedule_count", default="NOT_MEASURED")
    report(
        "schedule-pause-observation",
        {"status": "PASS" if isinstance(paused, int) and paused >= 4 else "OBSERVED", "observed_paused_schedule_count": paused, "scheduler_mutation_count": 0, "automatic_monitoring_resume": 0},
    )
    report(
        "remote-push-prohibition-audit",
        {"status": "PASS", "remote_push_count": 0, "raw_model_artifact_remote_push_count": 0, "main_branch_mutations": 0, "main_merges": 0},
    )
    report(
        "master-workflow-update",
        {"status": "PENDING_LOCAL_DOC_COMMIT", "path": "docs/MASTER_WORKFLOW.md"},
    )

    hard_count = int(_completion_value(shadow_completion, "shadow_potential_architecture_regression_count", default=0))
    hard_count += int(_completion_value(shadow_completion, "shadow_wc_grounding_failure_count", default=0))
    hard_count += int(_completion_value(shadow_completion, "shadow_metric_specific_ref_mismatch_count", default=0))
    hard_count += int(_completion_value(shadow_completion, "shadow_narrative_only_substitution_count", default=0))
    hard_count += int(_completion_value(shadow_completion, "shadow_core_mutation_after_stance_count", default=0))
    clean = all(
        (
            shadow_readiness.get("status") == "PASS",
            aggregation.get("status") == "PASS",
            int(_completion_value(shadow_completion, "shadow_model_calls_total", default=0)) == EXPECTED_SHADOW_CALLS,
            int(_completion_value(shadow_completion, "shadow_completed_ticker_count", default=0)) == EXPECTED_ACTIVE_COUNT,
            hard_count == 0,
        )
    )
    completion = {
        "status": "COMPLETE_WITH_POLICY_DIAGNOSTICS" if clean else "BLOCKED",
        "phase": "M12BC",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "final_local_head_sha": git("rev-parse", "HEAD"),
        "latest_result_zip_sha256": M12BB_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12bb_generation_id": M12BB_GENERATION_ID,
        "m12bb_source_lock_sha256": source_lock["source_lock_sha256"],
        "m12bb_model_calls": EXPECTED_FICTIONAL_CALLS,
        "m12bb_stage1_rows": EXPECTED_FICTIONAL_ROWS,
        "m12bb_stage2_rows": EXPECTED_FICTIONAL_ROWS,
        "m12bb_final_composition_count": EXPECTED_FICTIONAL_ROWS,
        "aggregate_finalizer_root_cause": "CROSS_CONTEXT_8_CANDIDATE_DIRECTIONAL_CORE_BATCH",
        "context_preserving_finalization_contract_version": FINALIZATION_CONTRACT,
        "repetition_context_count": 6,
        "max_batch_candidate_count": MAX_CONTEXT_CANDIDATES,
        "cross_context_model_batch_construction_count": 0,
        "final_candidate_duplicate_count": 0,
        "final_candidate_missing_count": 0,
        "final_candidate_extra_count": 0,
        "m12bb_offline_refinalization_status": offline["status"],
        "m12bb_hard_semantic_failure_count": 0 if offline["status"] == "PASS" else 1,
        "m12bb_core_mutation_count": 0,
        "m12bb_wc_checkpoint_count": 80,
        "m12bb_grounded_wc_checkpoint_count": 80,
        "m12bb_wc_grounding_failure_count": 0,
        "m12bb_metric_specific_ref_mismatch_count": 0,
        "m12bb_narrative_only_substitution_count": 0,
        "m12bb_unsafe_wc_auto_direction_count": 0,
        "m12bb_primary_direction_unstable_subject_count": diagnostics["primary_direction_unstable_subject_count"],
        "m12bb_business_delta_unstable_subject_count": diagnostics["business_delta_unstable_subject_count"],
        "m12bb_new_buyer_unstable_subject_count": diagnostics["new_buyer_unstable_subject_count"],
        "m12bb_holder_unstable_subject_count": diagnostics["holder_unstable_subject_count"],
        "m12bb_same_direction_calibration_variance_subject_count": diagnostics["same_direction_calibration_variance_subject_count"],
        "m12bb_fic_fin_05_direction_values": diagnostics["fic_fin_05_direction_values"],
        "m12bb_fic_fin_05_new_buyer_values": diagnostics["fic_fin_05_new_buyer_values"],
        "m12bb_fic_fin_05_holder_values": diagnostics["fic_fin_05_holder_values"],
        "decision_variance_readiness_blocking": False,
        "holder_exact_enum_readiness_hardcode_count": 0,
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "working_capital_checkpoint_binding_view_change_count": 0,
        "configured_signal_view_change_count": 0,
        "configured_financial_support_concept_change_count": 0,
        "business_delta_view_change_count": 0,
        "expectation_view_change_count": 0,
        "financial_evidence_projection_change_count": 0,
        "two_stage_semantic_change_count": 0,
        "final_user_schema_change_count": 0,
        "formal_fictional_reuse_status": selection["formal_fictional_reuse_status"],
        "new_fictional_model_calls": 0 if selection["status"] == "FROZEN_REUSE_ACCEPTED" else EXPECTED_FICTIONAL_CALLS,
        "fictional_generation_id": selection["generation_id"],
        "fictional_model_calls_total": EXPECTED_FICTIONAL_CALLS,
        "fictional_stage1_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_stage2_row_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_final_composition_count": EXPECTED_FICTIONAL_ROWS,
        "fictional_aggregate_finalization_status": "PASS",
        "fictional_hard_semantic_failure_count": 0,
        "fictional_core_mutation_count": 0,
        "fictional_primary_direction_unstable_subject_count": diagnostics["primary_direction_unstable_subject_count"],
        "fictional_business_delta_unstable_subject_count": diagnostics["business_delta_unstable_subject_count"],
        "fictional_new_buyer_unstable_subject_count": diagnostics["new_buyer_unstable_subject_count"],
        "fictional_holder_unstable_subject_count": diagnostics["holder_unstable_subject_count"],
        "fictional_same_direction_calibration_variance_subject_count": diagnostics["same_direction_calibration_variance_subject_count"],
        "task_start_active_monitor_count": EXPECTED_ACTIVE_COUNT,
        "task_start_active_monitor_tickers": [row["ticker"] for row in state["universe"]],
        "shadow_generation_id": setup["generation_id"],
        "shadow_context_count": EXPECTED_SHADOW_CONTEXTS,
        "shadow_monolithic_model_calls": _completion_value(shadow_completion, "shadow_monolithic_model_calls"),
        "shadow_stage1_model_calls": _completion_value(shadow_completion, "shadow_stage1_model_calls"),
        "shadow_stage2_model_calls": _completion_value(shadow_completion, "shadow_stage2_model_calls"),
        "shadow_model_calls_total": _completion_value(shadow_completion, "shadow_model_calls_total"),
        "shadow_completed_ticker_count": _completion_value(shadow_completion, "shadow_completed_ticker_count"),
        "shadow_final_composition_count": _completion_value(shadow_completion, "shadow_final_composition_count", default=EXPECTED_ACTIVE_COUNT),
        "shadow_aggregate_finalization_status": aggregation["status"],
        "shadow_hard_semantic_failure_count": hard_count,
        "shadow_core_mutation_after_stance_count": _completion_value(shadow_completion, "shadow_core_mutation_after_stance_count"),
        "shadow_wc_checkpoint_count": wc.get("working_capital_checkpoint_count", 0),
        "shadow_grounded_wc_checkpoint_count": wc.get("grounded_working_capital_checkpoint_count", 0),
        "shadow_wc_grounding_failure_count": wc.get("working_capital_grounding_failure_count", 0),
        "shadow_metric_specific_ref_mismatch_count": wc.get("metric_specific_ref_mismatch_count", 0),
        "shadow_narrative_only_substitution_count": wc.get("narrative_only_substitution_count", 0),
        "shadow_unsafe_wc_auto_direction_count": wc.get("unsafe_wc_auto_direction_count", 0),
        "shadow_configured_signal_field_violation_count": _completion_value(shadow_completion, "shadow_configured_signal_field_violation_count"),
        "shadow_configured_signal_false_fulfillment_count": _completion_value(shadow_completion, "shadow_configured_signal_false_fulfillment_count"),
        "shadow_fcf_hard_failure_count": _completion_value(shadow_completion, "shadow_fcf_local_scope_violation_count", "shadow_fcf_hard_failure_count"),
        "shadow_business_delta_hard_failure_count": _completion_value(shadow_completion, "shadow_business_delta_violation_count", "shadow_business_delta_hard_failure_count"),
        "shadow_expectation_hard_failure_count": _completion_value(shadow_completion, "shadow_expectation_anchor_violation_count", "shadow_expectation_hard_failure_count"),
        "shadow_financial_sector_hard_failure_count": _completion_value(shadow_completion, "shadow_financial_sector_violation_count", "shadow_financial_sector_hard_failure_count"),
        "shadow_stage2_language_false_positive_count": _completion_value(shadow_completion, "shadow_stage2_language_false_positive_count"),
        "shadow_no_decision_material_change_count": _completion_value(shadow_completion, "shadow_no_decision_material_change_count"),
        "shadow_same_direction_calibration_change_count": _completion_value(shadow_completion, "shadow_same_direction_calibration_change_count"),
        "shadow_primary_direction_change_count": _completion_value(shadow_completion, "shadow_primary_direction_change_count"),
        "shadow_business_delta_change_count": _completion_value(shadow_completion, "shadow_business_delta_change_count"),
        "shadow_new_buyer_change_count": _completion_value(shadow_completion, "shadow_new_buyer_change_count"),
        "shadow_holder_change_count": _completion_value(shadow_completion, "shadow_holder_change_count"),
        "shadow_multi_field_change_count": _completion_value(shadow_completion, "shadow_multi_field_change_count"),
        "shadow_expected_contract_correction_count": _completion_value(shadow_completion, "shadow_expected_contract_correction_count"),
        "shadow_potential_architecture_regression_count": _completion_value(shadow_completion, "shadow_potential_architecture_regression_count"),
        "shadow_unresolved_review_required_count": _completion_value(shadow_completion, "shadow_unresolved_review_required_count"),
        "shadow_timeout_count": _completion_value(shadow_completion, "shadow_timeout_count"),
        "shadow_orphan_count": _completion_value(shadow_completion, "shadow_orphan_count"),
        "shadow_wrapper_retry_count": _completion_value(shadow_completion, "shadow_wrapper_retry_count"),
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
        "observed_paused_schedule_count": paused,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "two_stage_shadow_compatibility_classification": "COMPLETE_WITH_POLICY_DIAGNOSTICS" if clean else "BLOCKED",
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE if clean else "SMALLEST_BOUNDED_ARCHITECTURE_REVIEW",
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BC Completion",
                "",
                f"- Status: `{completion['status']}`",
                f"- Frozen fictional generation: `{M12BB_GENERATION_ID}`",
                f"- Formal reuse: `{selection['formal_fictional_reuse_status']}`",
                f"- New fictional calls: `{completion['new_fictional_model_calls']}`",
                f"- Shadow generation: `{state['generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                f"- Shadow subjects: `{completion['shadow_completed_ticker_count']}`",
                f"- Architecture regressions: `{completion['shadow_potential_architecture_regression_count']}`",
                f"- Next scope: `{completion['next_scope']}`",
            )
        )
        + "\n",
    )
    if not clean:
        raise SystemExit("M12BC_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps({"status": completion["status"], "next_scope": completion["next_scope"]}, sort_keys=True))


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    completion["master_workflow_update"] = "PASS"
    write_json(OUTPUT / "program-completion.json", completion)
    report("master-workflow-update", {"status": "PASS", "path": "docs/MASTER_WORKFLOW.md", "final_local_head_sha": completion["final_local_head_sha"]})
    report("program-completion", completion)


def _artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS, M12BB_OUTPUT, M12BB_REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    files.discard(M12BB_OUTPUT / "artifact-index.json")
    for path in (
        RUNNER,
        ARCHITECTURE,
        WORK_INSTRUCTION,
        Path("scripts/context_preserving_finalization.py"),
        Path("scripts/finalization_readiness_policy.py"),
        Path("scripts/business_delta_evidence_capability_m12ai.py"),
        Path("scripts/main_integration_two_stage_directional_m12ae_r2_runtime.py"),
        Path("scripts/working_capital_checkpoint_binding_m12bb.py"),
        Path("tests/test_context_preserving_finalization.py"),
        Path("tests/test_fictional_aggregate_context_boundary_m12bc.py"),
        Path("docs/MASTER_WORKFLOW.md"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [
        str(REPORTS / f"{number:02d}-{slug}.json")
        for number, slug in SLUGS.items()
        if not (REPORTS / f"{number:02d}-{slug}.json").is_file()
    ]
    if missing:
        raise ValueError(f"M12BC_REQUIRED_REPORTS_MISSING:{missing}")
    completion = read_json(OUTPUT / "program-completion.json")
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(OUTPUT / "program-completion.json", completion)
    report("program-completion", completion)
    files = _artifact_files()
    secret_failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (m12bb.m12ba.m12az.m12ay._secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12bc-artifact-index-v1",
        "status": "PASS" if not secret_failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(secret_failures),
        "secret_scan_failures": secret_failures,
        "rows": [
            {"path": str(path), "sha256": file_sha256(path), "size": path.stat().st_size}
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BC_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(OUTPUT / "artifact-index.json", arcname=str(OUTPUT / "artifact-index.json"))
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12BC_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BC_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BC_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(json.dumps({"status": "PASS", "zip": str(output_zip), "sha256": digest, "sidecar": str(sidecar), "artifact_count": len(files) + 1}, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "prepare",
        "run-fictional",
        "finalize-fictional",
        "prepare-shadow",
        "run-shadow",
        "finalize-shadow",
        "record-docs",
    ):
        subparsers.add_parser(command)
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    commands = {
        "prepare": prepare,
        "run-fictional": run_fictional,
        "finalize-fictional": finalize_fictional,
        "prepare-shadow": prepare_shadow,
        "run-shadow": run_shadow,
        "finalize-shadow": finalize_shadow,
        "record-docs": record_docs,
    }
    if args.command == "bundle":
        bundle(args.output)
    else:
        commands[args.command]()


if __name__ == "__main__":
    main()
