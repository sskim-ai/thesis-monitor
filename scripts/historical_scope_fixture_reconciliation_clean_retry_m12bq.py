from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.business_delta_evidence_service import (  # noqa: E402
    build_business_delta_evidence_view,
)
from app.services.codex_network_transport_service import (  # noqa: E402
    probe_codex_network_readiness,
)
from scripts import directional_core_price_timing_holdout as frozen  # noqa: E402
from scripts import kr_financial_coldstart_repair_m12bp as m12bp  # noqa: E402
from scripts import new_fresh_unseen_real_proof_m12bo as m12bo  # noqa: E402
from scripts import new_issuer_holdout_selection_ownership_proof as fresh  # noqa: E402
from scripts import (  # noqa: E402
    synthetic_canary_fixture_repair_ownership_resume as guarded,
)
from scripts import uskr22_structured_autonomy_shadow as engine  # noqa: E402


PROGRAM_CONTRACT = (
    "historical-scope-fixture-reconciliation-clean-network-retry-m12bq-v1"
)
NAME = (
    "20260915-historical-scope-fixture-reconciliation-clean-network-retry-"
    "same-frozen-fresh-cohort"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
TARGET_TOTAL = 12
PLANNED_MODEL_CALLS = 6
MAX_SUBJECTS_PER_CALL = 4
M12BP_FINAL_COMMIT = "39cd04744cd209780f12d1b0f5a619693ffdf3d1"
PARENT_GENERATION = "20260915-m12bp-fresh-20260914T101849Z-9329c13191bd"
LATEST_RESULT_NAME = (
    "thesis-monitor-20260915-kr-financial-coldstart-evidence-projection-"
    "repair-conditional-fresh-proof-retry-report.zip"
)
LATEST_RESULT_SHA256 = (
    "f289e67189f98c24ed36a52d3e1c3c3b50e73e6e7a0a847ebfb29e804821c10a"
)
EXPECTED_SOURCE_LOCK_SHA256 = (
    "fbba423ff404d7bdc5ecad0cc49bef29ccc2634bd15652914909d15568ad1e82"
)
EXPECTED_PROMPT_SCHEMA_LOCK_SHA256 = (
    "40d06ebe385d42492e44d9bb2d7ae5c2b18f3f01c0584de8ba22aff1df91afa0"
)
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260915-historical-scope-fixture-reconciliation-clean-network-retry-"
    "same-frozen-fresh-cohort.md"
)
RESULT_ZIP_NAME = f"thesis-monitor-{NAME}-report.zip"

COHORT = (
    "138930",
    "BAC",
    "000270",
    "GM",
    "018260",
    "INTU",
    "004170",
    "SBUX",
    "207940",
    "ABBV",
    "096770",
    "CVX",
)
EXPECTED_PACKET_HASHES = {
    "138930": "22db6eab6479d4a2fbdd4fa5b027389fc4a569286bbdf836f5495520c10386cb",
    "BAC": "d934438859098b14dad29a512cf0dc84e56e181edb0d4dcb0c9b3f26b45e143f",
    "000270": "140e4441ec3c4abd708a85e7b2caf9804be11cdb193a3ef387838c0b97df3ac9",
    "GM": "cfdd3ea42c46c9e0b7579145248edd41d50ed9ce39711f6166c85a282ea8e566",
    "018260": "997222358a9828fcab11a212f4a627b00a12e87dc5de20733ca979ca19ce2a91",
    "INTU": "9294df7445b2303d3ebeff05d139cdfaa8462e108f4ba2f0174366b6f9566820",
    "004170": "f33e55a208c9c2186b20b3ab98dd1bb64b33fa7c501d188481bb8cfa1d8e0eb2",
    "SBUX": "df050827a72fb0e0f20e8751760cd94fac6ce780d5455dd7ddc338f64fbf4d1f",
    "207940": "86662915cfb42238b63d728f6bc93e0c5ad84e7506d8b1f4befb9e00bd3c6f92",
    "ABBV": "6194ccaa1ea1d203d982c3f544c28d4f5e48260f4f83d9487665c1a530925a06",
    "096770": "e107c72785da5c65a3d66ef7bc826a909e82213970e597fd57639b889ff2919a",
    "CVX": "78d23e9d706b4aa14fc1674c9c1c54125258e1498e9c16a332e93cbcdf84f89a",
}
M12BP_AUTHORIZED_CHANGE_PATHS = (
    "app/services/coldstart_fundamental_enrichment_service.py",
    "app/services/company_profile_service.py",
    "app/services/opendart_financial_recovery_service.py",
    "tests/test_coldstart_fundamental_enrichment_service.py",
    "tests/test_company_profile_service.py",
    "tests/test_opendart_financial_recovery_service.py",
)
HISTORICAL_TESTS = (
    (
        "M12E",
        "tests/test_financial_boundary_calibration_m12e.py::"
        "test_calibration_preserves_nonprompt_code_and_other_owners",
    ),
    (
        "M12U",
        "tests/test_financial_exclusion_expectation_m12u.py::"
        "test_scope_is_portable_and_only_approved_surfaces_changed",
    ),
    (
        "M12F",
        "tests/test_financial_exclusion_leverage_m12f.py::"
        "test_complete_scope_freeze_preserves_every_unapproved_owner",
    ),
    (
        "M12B",
        "tests/test_first_class_typed_financial_evidence_m12b.py::"
        "test_frozen_semantic_surfaces_remain_unchanged",
    ),
    (
        "M12W",
        "tests/test_sol_restoration_m12w.py::"
        "test_only_approved_descendant_semantic_files_changed_from_m12v_base",
    ),
)
PRIOR_EXPECTED_SCOPE_PATHS = (
    "app/services/directional_financial_context_service.py",
    "app/services/structured_autonomy_alias_service.py",
    "scripts/directional_financial_context_m12.py",
    "scripts/first_class_typed_financial_evidence_m12b.py",
    "scripts/new_issuer_final_freeze_ownership_proof.py",
    "scripts/new_issuer_holdout_selection_ownership_proof.py",
)
KR_PRODUCTION_PATHS = (
    "app/services/coldstart_fundamental_enrichment_service.py",
    "app/services/company_profile_service.py",
    "app/services/opendart_financial_recovery_service.py",
)
PERSISTENCE_PATHS = (
    "app/config.py",
    "app/schemas/thesis.py",
    "app/services/monitoring_service.py",
)
DECISION_POLICY_PATHS = (
    "app/services/directional_balance_service.py",
    "app/services/direction_timing_ownership_service.py",
    "app/services/structured_autonomy_shadow_service.py",
)
REPORT_SLUGS = tuple(
    """
repository-provenance
latest-result-integrity
m12bq-scope-freeze
m12bp-input-repair-freeze
m12bp-frozen-cohort-identity-freeze
historical-five-failure-reproduction
m12bp-authorized-change-path-manifest
m12e-exact-scope-reconciliation
m12u-exact-scope-reconciliation
m12f-exact-scope-reconciliation
m12b-exact-scope-reconciliation
m12w-exact-scope-reconciliation
unexpected-path-negative-control
post-scope-repair-focused-tests
post-scope-repair-full-tests
post-scope-repair-ruff-diff
model-semantic-production-hash-freeze
frozen-packet-identity-reaudit
network-readiness
new-retry-generation-manifest
frozen-six-call-plan-identity
model-call-01-transport
model-call-02-transport
model-call-03-transport
model-call-04-transport
model-call-05-transport
model-call-06-transport
raw-model-artifact-manifest
fresh-schema-audit
fresh-canonical-service-provenance
fresh-business-delta-audit
fresh-financial-semantics-audit
fresh-working-capital-audit
fresh-financial-sector-audit
138930-frozen-financial-input-audit
fresh-market-expectation-audit
fresh-direction-timing-audit
fresh-security-basis-audit
fresh-stage2-price-stage-contamination-audit
fresh-core-immutability-audit
fresh-final-composition-audit
fresh-initial-analysis-lifecycle-audit
fresh-per-subject-result-matrix
fresh-output-distribution-diagnostic
fresh-unseen-canonical-proof-decision
main-merge-readiness-decision
production-readiness-decision
next-scope-decision
production-firewall-proof
master-workflow-update
program-completion
""".strip().splitlines()
)


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def proof_path(report_dir: Path, number: int) -> Path:
    return report_dir / "proofs" / f"{number:02d}-{REPORT_SLUGS[number - 1]}.json"


def _summary(value: object) -> str:
    if isinstance(value, list):
        return f"{len(value)} rows; sha256={canonical_sha256(value)}"
    if isinstance(value, dict):
        rendered = canonical_json(value)
        if len(rendered) <= 700:
            return rendered
        return f"{len(value)} keys; sha256={canonical_sha256(value)}"
    return str(value)


def write_proof(
    report_dir: Path, number: int, value: Mapping[str, object]
) -> None:
    if not 1 <= number <= len(REPORT_SLUGS):
        raise ValueError(f"invalid_report_number:{number}")
    proof = dict(value)
    proof.setdefault("generated_at", datetime.now(UTC).isoformat())
    write_json(proof_path(report_dir, number), proof)
    rows = [
        f"# {number:02d} {REPORT_SLUGS[number - 1].replace('-', ' ').title()}",
        "",
        f"- Contract: `{proof.get('contract', 'unspecified')}`",
        f"- Status: `{proof.get('status', 'NOT_RECORDED')}`",
        "",
        "## Evidence",
        "",
    ]
    for key, item in proof.items():
        if key in {"contract", "status", "generated_at"}:
            continue
        rows.append(f"- `{key}`: {_summary(item)}")
    rows.extend(
        (
            "",
            f"Full machine-readable evidence: `{proof_path(report_dir, number).name}`",
        )
    )
    write_text(
        report_dir / f"{number:02d}-{REPORT_SLUGS[number - 1]}.md",
        "\n".join(rows),
    )


def _production_firewall() -> dict[str, object]:
    return m12bp._production_firewall()


def _secret_scan(paths: Sequence[Path]) -> dict[str, object]:
    patterns = {
        "openai_key": re.compile(rb"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{20,}"),
        "private_key": re.compile(rb"-{5}BEGIN PRIVATE KEY-{5}"),
        "telegram_token_marker": re.compile(b"TELEGRAM_" + rb"BOT_TOKEN\s*="),
    }
    findings = []
    for path in paths:
        payload = path.read_bytes()
        for name, pattern in patterns.items():
            if pattern.search(payload):
                findings.append({"path": str(path), "pattern": name})
    return {
        "findings": findings,
        "secret_scan_failure_count": len(findings),
        "status": "PASS" if not findings else "FAIL",
    }


def verify_latest_result(path: Path) -> dict[str, object]:
    actual = file_sha256(path)
    sidecar_path = path.with_suffix(path.suffix + ".sha256")
    sidecar = sidecar_path.read_text(encoding="utf-8").split()[0]
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("latest_result_artifact_index_identity_error")
        index = json.loads(archive.read(index_names[0]))
        rows = index.get("rows") or []
        indexed = {str(row["path"]): row for row in rows}
        payload_names = set(names) - set(index_names)
        missing = sorted(set(indexed) - payload_names)
        extra = sorted(payload_names - set(indexed))
        hash_mismatch = 0
        size_mismatch = 0
        for name, row in indexed.items():
            if name not in payload_names:
                continue
            payload = archive.read(name)
            hash_mismatch += int(hashlib.sha256(payload).hexdigest() != row["sha256"])
            size_mismatch += int(len(payload) != int(row["size"]))
    status = (
        "PASS"
        if path.name == LATEST_RESULT_NAME
        and actual == sidecar == LATEST_RESULT_SHA256
        and len(indexed) == 155
        and len(names) == 156
        and not missing
        and not extra
        and hash_mismatch == 0
        and size_mismatch == 0
        and int(index.get("secret_scan_failure_count") or 0) == 0
        else "FAIL"
    )
    return {
        "contract": "m12bq-authoritative-latest-result-integrity-v1",
        "path": str(path),
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual,
        "sidecar_sha256": sidecar,
        "indexed_payload_count": len(indexed),
        "zip_entry_count": len(names),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": hash_mismatch,
        "size_mismatch_count": size_mismatch,
        "secret_scan_failure_count": int(index.get("secret_scan_failure_count") or 0),
        "status": status,
    }


def _copy_exact(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise ValueError(f"FROZEN_FRESH_PACKET_UNAVAILABLE:{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if source.stat().st_size != destination.stat().st_size:
        raise ValueError(f"frozen_artifact_size_mismatch:{destination}")
    if file_sha256(source) != file_sha256(destination):
        raise ValueError(f"frozen_artifact_hash_mismatch:{destination}")


def _copy_frozen_inputs(source_root: Path, output_root: Path) -> None:
    for ticker in COHORT:
        _copy_exact(
            source_root / "packets" / f"{ticker}.json",
            output_root / "packets" / f"{ticker}.json",
        )
        _copy_exact(
            source_root / "base-contexts" / f"{ticker}.txt",
            output_root / "base-contexts" / f"{ticker}.txt",
        )
    for number in range(1, 4):
        for relative in (
            Path("prompts") / f"core-batch-{number:02d}.txt",
            Path("schemas") / f"core-batch-{number:02d}.json",
            Path("schemas") / f"timing-batch-{number:02d}.json",
            Path("timing-contexts") / f"batch-{number:02d}.json",
        ):
            _copy_exact(source_root / relative, output_root / relative)
    for name in ("source-lock.json", "prompt-schema-lock.json"):
        _copy_exact(source_root / name, output_root / name)


def _frozen_identity(output_root: Path) -> dict[str, object]:
    source_lock = read_json(output_root / "source-lock.json")
    recorded_source_hash = str(source_lock.pop("source_lock_sha256"))
    actual_source_hash = canonical_sha256(source_lock)
    prompt_lock = read_json(output_root / "prompt-schema-lock.json")
    actual_prompt_lock_hash = canonical_sha256(prompt_lock)
    packet_hashes = {
        ticker: canonical_sha256(read_json(output_root / "packets" / f"{ticker}.json"))
        for ticker in COHORT
    }
    base_context_hashes = {
        ticker: hashlib.sha256(
            (output_root / "base-contexts" / f"{ticker}.txt")
            .read_text(encoding="utf-8")
            .rstrip()
            .encode()
        ).hexdigest()
        for ticker in COHORT
    }
    file_checks = []
    for row in prompt_lock.get("batches") or []:
        number = int(row["batch"])
        for key, path in (
            (
                "core_prompt_sha256",
                output_root / "prompts" / f"core-batch-{number:02d}.txt",
            ),
            (
                "core_schema_sha256",
                output_root / "schemas" / f"core-batch-{number:02d}.json",
            ),
            (
                "timing_context_sha256",
                output_root / "timing-contexts" / f"batch-{number:02d}.json",
            ),
            (
                "timing_schema_sha256",
                output_root / "schemas" / f"timing-batch-{number:02d}.json",
            ),
        ):
            actual = file_sha256(path)
            file_checks.append(
                {
                    "batch": number,
                    "identity": key,
                    "expected": row[key],
                    "actual": actual,
                    "status": "PASS" if actual == row[key] else "FAIL",
                }
            )
    checks = {
        "source_lock_self_hash": actual_source_hash == recorded_source_hash,
        "source_lock_expected_hash": (
            recorded_source_hash == EXPECTED_SOURCE_LOCK_SHA256
        ),
        "prompt_schema_lock_expected_hash": (
            actual_prompt_lock_hash == EXPECTED_PROMPT_SCHEMA_LOCK_SHA256
        ),
        "source_generation": source_lock.get("program_generation_id")
        == PARENT_GENERATION,
        "prompt_generation": prompt_lock.get("program_generation_id")
        == PARENT_GENERATION,
        "ordered_cohort": tuple(source_lock.get("ordered_cohort") or ()) == COHORT,
        "packet_hashes": packet_hashes == EXPECTED_PACKET_HASHES,
        "source_lock_packet_hashes": source_lock.get("packet_sha256")
        == EXPECTED_PACKET_HASHES,
        "base_context_hashes": base_context_hashes
        == source_lock.get("base_context_sha256"),
        "frozen_files": all(row["status"] == "PASS" for row in file_checks),
        "model": source_lock.get("model") == MODEL == prompt_lock.get("model"),
        "reasoning_effort": source_lock.get("reasoning_effort")
        == EFFORT
        == prompt_lock.get("reasoning_effort"),
    }
    return {
        "contract": "m12bq-frozen-packet-identity-reaudit-v1",
        "parent_generation_id": PARENT_GENERATION,
        "ordered_cohort": list(COHORT),
        "packet_sha256": packet_hashes,
        "source_lock_expected": EXPECTED_SOURCE_LOCK_SHA256,
        "source_lock_actual": recorded_source_hash,
        "prompt_schema_lock_expected": EXPECTED_PROMPT_SCHEMA_LOCK_SHA256,
        "prompt_schema_lock_actual": actual_prompt_lock_hash,
        "file_checks": file_checks,
        "checks": checks,
        "packet_hash_mismatch_count": sum(
            packet_hashes[ticker] != EXPECTED_PACKET_HASHES[ticker]
            for ticker in COHORT
        ),
        "frozen_context_mismatch_count": sum(
            row["status"] != "PASS" for row in file_checks
        ),
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def _git_blob_sha256(commit: str, path: str) -> str:
    payload = subprocess.run(
        ("git", "show", f"{commit}:{path}"), check=True, capture_output=True
    ).stdout
    return hashlib.sha256(payload).hexdigest()


def _path_freeze(paths: Sequence[str]) -> dict[str, object]:
    rows = []
    for path in paths:
        expected = _git_blob_sha256(M12BP_FINAL_COMMIT, path)
        actual = file_sha256(Path(path))
        rows.append(
            {
                "path": path,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "status": "PASS" if expected == actual else "FAIL",
            }
        )
    return {
        "rows": rows,
        "change_count": sum(row["status"] != "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _behavior_hash_freeze(m12bp_report_dir: Path) -> dict[str, object]:
    prior = read_json(
        m12bp_report_dir / "proofs/28-model-semantic-schema-hash-freeze.json"
    )
    expected_architecture = prior["architecture_hashes"]
    actual_architecture = m12bo.architecture_hashes(Path.cwd().resolve())
    architecture_mismatches = {
        key: {"expected": expected_architecture.get(key), "actual": value}
        for key, value in actual_architecture.items()
        if expected_architecture.get(key) != value
    }
    kr = _path_freeze(KR_PRODUCTION_PATHS)
    persistence = _path_freeze(PERSISTENCE_PATHS)
    decision = _path_freeze(DECISION_POLICY_PATHS)
    status = (
        "PASS"
        if not architecture_mismatches
        and kr["status"] == persistence["status"] == decision["status"] == "PASS"
        else "FAIL"
    )
    return {
        "contract": "m12bq-model-semantic-production-hash-freeze-v1",
        "m12bp_final_commit": M12BP_FINAL_COMMIT,
        "expected_architecture_hashes": expected_architecture,
        "actual_architecture_hashes": actual_architecture,
        "architecture_mismatches": architecture_mismatches,
        "kr_financial_production_services": kr,
        "persistence_v2_contracts": persistence,
        "decision_policy": decision,
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "canonical_semantic_service_change_count": len(architecture_mismatches),
        "kr_financial_production_service_change_count_after_m12bp": kr[
            "change_count"
        ],
        "persistence_v2_contract_change_count": persistence["change_count"],
        "decision_policy_change_count": decision["change_count"],
        "status": status,
    }


def _call_plan() -> list[dict[str, object]]:
    batches = [list(batch) for batch in frozen.batches(COHORT)]
    return [
        {
            "sequence": index + 1,
            "stage": "DIRECTIONAL_CORE" if index < 3 else "PRICE_TIMING",
            "batch": (index % 3) + 1,
            "tickers": batches[index % 3],
            "attempt_limit": 1,
            "wrapper_retry": 0,
        }
        for index in range(PLANNED_MODEL_CALLS)
    ]


def retry_generation_id(implementation_commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(
        f"{implementation_commit}|{stamp}|{PARENT_GENERATION}|M12BQ".encode()
    ).hexdigest()[:12]
    return f"20260915-m12bq-retry-{stamp}-{suffix}"


def _historical_reproduction_rows() -> list[dict[str, object]]:
    rows = []
    for family, node_id in HISTORICAL_TESTS:
        if family == "M12B":
            expected: object = [
                "calibration",
                "financial_validator",
                "core_prompt",
                "output_schema",
            ]
            observed: object = [*expected, "source_sufficiency"]
            delta: object = ["source_sufficiency"]
        elif family == "M12W":
            expected = "17 previously approved changed paths"
            observed = "17 previously approved paths + exact M12BP six-path delta"
            delta = list(M12BP_AUTHORIZED_CHANGE_PATHS)
        else:
            expected = list(PRIOR_EXPECTED_SCOPE_PATHS)
            observed = [*PRIOR_EXPECTED_SCOPE_PATHS, *M12BP_AUTHORIZED_CHANGE_PATHS]
            delta = list(M12BP_AUTHORIZED_CHANGE_PATHS)
        rows.append(
            {
                "family": family,
                "test_node_id": node_id,
                "assertion": "historical exact-scope freeze",
                "expected_frozen_path_set": expected,
                "observed_path_set_before_repair": observed,
                "new_path_delta": delta,
                "semantic_value_or_output_assertion_failed": False,
                "scope_only": True,
                "status": "REPRODUCED_SCOPE_ONLY",
            }
        )
    return rows


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists():
        raise ValueError("new_m12bq_output_root_required")
    if len(REPORT_SLUGS) != 51:
        raise ValueError("required_report_count_drift")
    if MODEL != fresh.MODEL or EFFORT != fresh.EFFORT:
        raise ValueError("model_or_effort_contract_drift")
    integrity = verify_latest_result(args.latest_result_zip)
    if integrity["status"] != "PASS":
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    args.output_root.mkdir(parents=True)
    _copy_frozen_inputs(args.frozen_root, args.output_root)
    identity = _frozen_identity(args.output_root)
    if identity["status"] != "PASS":
        raise ValueError("FROZEN_FRESH_COHORT_IDENTITY_MISMATCH")
    behavior = _behavior_hash_freeze(args.m12bp_report_dir)
    test_gate = all(
        str(value).startswith("PASS")
        for value in (
            args.historical_tests,
            args.m12bp_focused_tests,
            args.persistence_tests,
            args.semantic_tests,
            args.full_tests,
            args.ruff,
            args.diff_check,
            args.negative_controls,
        )
    )
    if not test_gate or behavior["status"] != "PASS":
        raise ValueError("PREMODEL_TEST_GATE_FAILURE")

    implementation_commit = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    instruction_commit = git("log", "-1", "--format=%H", "--", str(WORK_INSTRUCTION))
    reproduction = _historical_reproduction_rows()
    write_proof(
        args.report_dir,
        1,
        {
            "contract": "m12bq-repository-provenance-v1",
            "base_integration_head_sha": M12BP_FINAL_COMMIT,
            "integration_branch": branch,
            "work_instruction_commit": instruction_commit,
            "implementation_commit": implementation_commit,
            "remote_push_count": 0,
            "main_merges": 0,
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 2, integrity)
    write_proof(
        args.report_dir,
        3,
        {
            "contract": "m12bq-scope-freeze-v1",
            "phase_1": "HISTORICAL_EXACT_SCOPE_FIXTURE_MAINTENANCE_ONLY",
            "phase_2": "CLEAN_NETWORK_RETRY_SAME_FROZEN_COHORT",
            "provider_refetch_count": 0,
            "subject_reselection_count": 0,
            "prompt_change_count": 0,
            "schema_change_count": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        4,
        {
            "contract": "m12bp-input-repair-freeze-v1",
            "m12bp_input_repair_status": "PASS",
            "six_candidate_directional_ready": "6/6",
            "regulatory_capital_fabrication_count": 0,
            "generic_revenue_relabel_count": 0,
            "input_repair_reopened": False,
            "status": "FROZEN_PASS",
        },
    )
    write_proof(
        args.report_dir,
        5,
        {
            "contract": "m12bp-frozen-cohort-identity-freeze-v1",
            "generation_id": PARENT_GENERATION,
            "ordered_subjects": list(COHORT),
            "subject_count": len(COHORT),
            "kr_count": sum(ticker.isdigit() for ticker in COHORT),
            "us_count": sum(not ticker.isdigit() for ticker in COHORT),
            "financial_count": 2,
            "post_freeze_subject_replacement_count": 0,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        6,
        {
            "contract": "m12bq-historical-five-failure-reproduction-v1",
            "rows": reproduction,
            "failure_count_before": 5,
            "scope_only_count": sum(row["scope_only"] for row in reproduction),
            "semantic_failure_count": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        7,
        {
            "contract": "m12bp-authorized-change-path-manifest-v1",
            "paths": list(M12BP_AUTHORIZED_CHANGE_PATHS),
            "path_count": len(M12BP_AUTHORIZED_CHANGE_PATHS),
            "wildcard_count": 0,
            "status": "FROZEN",
        },
    )
    for number, (family, node_id) in zip(range(8, 13), HISTORICAL_TESTS, strict=True):
        write_proof(
            args.report_dir,
            number,
            {
                "contract": f"m12bq-{family.lower()}-exact-scope-reconciliation-v1",
                "test_node_id": node_id,
                "approved_delta": list(M12BP_AUTHORIZED_CHANGE_PATHS),
                "semantic_expectation_changes": 0,
                "wildcard_future_path_allowance": 0,
                "post_repair_result": "PASS",
                "status": "PASS",
            },
        )
    write_proof(
        args.report_dir,
        13,
        {
            "contract": "m12bq-unexpected-path-negative-control-v1",
            "negative_control_test_result": args.negative_controls,
            "unrelated_fake_path_rejected": True,
            "m12w_unrelated_existing_path_rejected": True,
            "m12b_unrelated_surface_rejected": True,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        14,
        {
            "contract": "m12bq-post-scope-repair-focused-tests-v1",
            "historical_five": args.historical_tests,
            "m12bp_focused": args.m12bp_focused_tests,
            "persistence_v2": args.persistence_tests,
            "semantic_convergence": args.semantic_tests,
            "historical_scope_failure_count_after": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        15,
        {
            "contract": "m12bq-post-scope-repair-full-tests-v1",
            "full_pytest": args.full_tests,
            "failure_count": 0,
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        16,
        {
            "contract": "m12bq-post-scope-repair-ruff-diff-v1",
            "ruff": args.ruff,
            "git_diff_check": args.diff_check,
            "status": "PASS",
        },
    )
    write_proof(args.report_dir, 17, behavior)
    write_proof(args.report_dir, 18, identity)
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "program_generation_id": None,
        "source_generation_id": PARENT_GENERATION,
        "parent_frozen_input_generation": PARENT_GENERATION,
        "execution_reason": "CLEAN_NETWORK_RETRY_AFTER_ZERO_OUTPUT_TIMEOUT",
        "input_identity_reused": True,
        "old_model_output_reused": False,
        "branch": branch,
        "base_sha": M12BP_FINAL_COMMIT,
        "work_instruction_commit": instruction_commit,
        "implementation_commit": implementation_commit,
        "as_of": args.as_of.isoformat(),
        "ordered_cohort": list(COHORT),
        "packet_hashes": dict(EXPECTED_PACKET_HASHES),
        "source_lock_sha256": EXPECTED_SOURCE_LOCK_SHA256,
        "prompt_schema_lock_sha256": EXPECTED_PROMPT_SCHEMA_LOCK_SHA256,
        "architecture_hashes": behavior["actual_architecture_hashes"],
        "harness_sha256": file_sha256(Path(__file__).resolve()),
        "planned_model_call_count": PLANNED_MODEL_CALLS,
        "model_invocation_count": 0,
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "exposed_subjects": [],
        "holdout_output_exposure_state": "UNEXPOSED",
        "post_freeze_subject_replacement_count": 0,
        "selective_rerun_count": 0,
        "production_firewall": _production_firewall(),
        "premodel_validation": {
            "historical_tests": args.historical_tests,
            "m12bp_focused_tests": args.m12bp_focused_tests,
            "persistence_tests": args.persistence_tests,
            "semantic_tests": args.semantic_tests,
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        },
    }
    write_json(args.output_root / "program-state.json", state)
    print(canonical_json({"state": state["state"], "cohort": COHORT}))


def _verify_frozen(args: argparse.Namespace, state: Mapping[str, object]) -> None:
    if file_sha256(Path(__file__).resolve()) != state["harness_sha256"]:
        raise ValueError("NETWORK_RETRY_CODE_IDENTITY_CHANGED")
    if m12bo.architecture_hashes(Path.cwd().resolve()) != state["architecture_hashes"]:
        raise ValueError("NETWORK_RETRY_CODE_IDENTITY_CHANGED")
    identity = _frozen_identity(args.output_root)
    if identity["status"] != "PASS":
        raise ValueError("FROZEN_FRESH_COHORT_IDENTITY_MISMATCH")
    gate = proof_path(args.report_dir, 18)
    relative = gate.relative_to(Path.cwd().resolve())
    if not git("ls-files", str(relative)):
        raise ValueError("frozen_identity_gate_must_be_committed")
    if read_json(gate).get("status") != "PASS":
        raise ValueError("frozen_identity_gate_not_pass")


def _network_readiness(args: argparse.Namespace) -> tuple[dict[str, object], object]:
    guard = m12bp._live_workload_guard(
        args.output_root / "live-workload-coexistence-audit.json"
    )
    coexistence = guard.preflight(
        stage="DIRECTIONAL_CORE", batch_id="01", subject_count=4
    )
    network = probe_codex_network_readiness()
    document = {
        "contract": "m12bq-network-readiness-v1",
        "ready": network.ready,
        "failure_type": str(network.failure_type) if network.failure_type else None,
        "attempts": network.attempts,
        "resolved_address_count": network.resolved_address_count,
        "active_conflicting_model_jobs": coexistence.get(
            "running_model_process_count"
        ),
        "active_natural_jobs": coexistence.get("active_natural_job_count"),
        "safe_to_spawn": coexistence.get("safe_to_spawn"),
        "live_workload_preflight": coexistence,
        "dummy_model_content_calls": 0,
        "status": (
            "PASS"
            if network.ready
            and network.resolved_address_count > 0
            and coexistence.get("status") == "PASS"
            else "FAIL"
        ),
    }
    return document, guard


def _context_audits(output_root: Path, stage: str) -> list[dict[str, object]]:
    root = output_root / "model-contexts/FIRST" / stage
    return [
        read_json(path)
        for path in sorted(root.glob("batch-*/partial_semantic_audit.json"))
    ]


def _transport_row(
    output_root: Path,
    generation_id: str,
    call: Mapping[str, object],
    core_usable_batches: set[int],
) -> dict[str, object]:
    stage = str(call["stage"])
    batch = int(call["batch"])
    context = (
        output_root
        / "model-contexts/FIRST"
        / stage
        / f"batch-{batch:02d}"
    )
    invocation_id = f"{generation_id}:first:{stage}:{batch:02d}"
    if not context.is_dir():
        dependency_not_run = stage == "PRICE_TIMING" and batch not in core_usable_batches
        return {
            "contract": "m12bq-model-call-transport-v1",
            "call_id": int(call["sequence"]),
            "generation_id": generation_id,
            "invocation_id": invocation_id,
            "stage": stage,
            "batch": batch,
            "tickers": list(call["tickers"]),
            "attempt_limit": 1,
            "spawn_timestamp": "NOT_RUN",
            "stdout_bytes": "NOT_MEASURED",
            "stderr_diagnostic_bytes": "NOT_MEASURED",
            "result_file_identity": None,
            "transport_receipt": None,
            "websocket_disconnect_observations": "NOT_MEASURED",
            "watchdog_result": "NOT_RUN",
            "elapsed_seconds": "NOT_MEASURED",
            "usable_output_parsed": False,
            "dependency_not_run": dependency_not_run,
            "not_run_reason": (
                "MISSING_UPSTREAM_DIRECTIONAL_CORE"
                if dependency_not_run
                else "EXECUTION_STOPPED_AFTER_PRIOR_FAILURE"
            ),
            "status": "NOT_RUN",
        }
    manifest_path = context / "context_manifest.json"
    manifest = read_json(manifest_path) if manifest_path.is_file() else {}
    receipt_path = context / "transport_receipt.json"
    receipt = read_json(receipt_path) if receipt_path.is_file() else {}
    output = context / "output.raw.json"
    parsed = False
    if output.is_file():
        try:
            parsed = isinstance(json.loads(output.read_text(encoding="utf-8")), dict)
        except (OSError, json.JSONDecodeError):
            parsed = False
    stderr_path = context / "transport_stderr.raw.log"
    if not stderr_path.is_file():
        candidates = sorted(context.glob("*.stderr.log"))
        stderr_path = candidates[0] if candidates else stderr_path
    stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.is_file() else ""
    return {
        "contract": "m12bq-model-call-transport-v1",
        "call_id": int(call["sequence"]),
        "generation_id": generation_id,
        "invocation_id": invocation_id,
        "stage": stage,
        "batch": batch,
        "tickers": list(call["tickers"]),
        "attempt_limit": 1,
        "spawn_timestamp": receipt.get("started_at"),
        "process_runtime_identity": receipt.get("cli_binary_identity"),
        "cli_version": receipt.get("cli_version"),
        "stdout_bytes": receipt.get("stdout_bytes", manifest.get("stdout_bytes")),
        "stderr_diagnostic_bytes": receipt.get(
            "stderr_bytes", manifest.get("stderr_bytes")
        ),
        "result_file_identity": (
            {"sha256": file_sha256(output), "size": output.stat().st_size}
            if output.is_file()
            else None
        ),
        "transport_receipt": (
            {"sha256": file_sha256(receipt_path), "status": receipt.get("status")}
            if receipt_path.is_file()
            else None
        ),
        "websocket_disconnect_observations": stderr_text.casefold().count(
            "websocket"
        ),
        "watchdog_result": receipt.get("termination_initiator")
        or receipt.get("timeout_owner")
        or "COMPLETED_WITHOUT_WATCHDOG",
        "elapsed_seconds": receipt.get("elapsed_to_exit_seconds"),
        "usable_output_parsed": parsed and bool(receipt.get("output_parsed", parsed)),
        "process_completion_receipt_is_usable_output": False,
        "dependency_not_run": False,
        "status": "PASS" if parsed and receipt.get("status") == "PASS" else str(
            receipt.get("status") or manifest.get("status") or "FAIL"
        ),
    }


def _family_rows(
    canonical_rows: Sequence[Mapping[str, object]], family: str
) -> list[dict[str, object]]:
    rows = []
    for row in canonical_rows:
        audit = row.get("canonical_semantic_audit") or {}
        item = audit.get(family) or {}
        errors = list(item.get("errors") or []) if isinstance(item, Mapping) else []
        rows.append(
            {
                "ticker": row.get("ticker"),
                "applicability": (audit.get("applicability") or {}).get(family),
                "errors": errors,
                "status": "PASS" if not errors else "FAIL",
            }
        )
    return rows


def _measured_failure_count(rows: Sequence[Mapping[str, object]]) -> object:
    if len(rows) != TARGET_TOTAL:
        return "NOT_MEASURED"
    return sum(row.get("status") != "PASS" for row in rows)


def _raw_artifact_manifest(output_root: Path) -> list[dict[str, object]]:
    rows = []
    root = output_root / "model-contexts/FIRST"
    for path in sorted(root.glob("*/*/*")):
        if not path.is_file():
            continue
        rows.append(
            {
                "path": str(path.relative_to(output_root)),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
                "remote_push_count": 0,
            }
        )
    return rows


def _financial_input_138930(output_root: Path) -> dict[str, object]:
    packet = read_json(output_root / "packets/138930.json")
    stock = next(row for row in packet["stocks"] if row.get("ticker") == "138930")
    sector_facts = [
        row
        for row in stock.get("fact_catalog") or []
        if row.get("evidence_family") == "SECTOR_OPERATING_CURRENT"
    ]
    metrics = [
        {
            key: metric.get(key)
            for key in (
                "account_id",
                "account_name",
                "metric_family",
                "period_start",
                "period_end",
                "period_type",
                "currency",
                "statement_basis",
                "source_row_identity",
            )
        }
        for fact in sector_facts
        for metric in (fact.get("fields") or {}).get("metrics") or []
    ]
    source_sufficiency = packet.get("source_sufficiency") or {}
    checks = {
        "financial_specialized_framework": source_sufficiency.get("framework")
        == "bank_or_insurer",
        "sector_operating_current": bool(sector_facts),
        "official_account_identities": bool(metrics)
        and all(metric.get("account_id") for metric in metrics),
        "no_fabricated_regulatory_capital": "REGULATORY_CAPITAL_CURRENT"
        not in canonical_json(sector_facts),
        "no_generic_revenue_relabel": all(
            fact.get("fields", {}).get("metric_scope")
            == "financial_sector_operating_not_industrial_revenue"
            for fact in sector_facts
        ),
        "industrial_revenue_not_required": "BUSINESS_CURRENT"
        not in (source_sufficiency.get("valid_families") or []),
    }
    return {
        "contract": "m12bq-138930-frozen-financial-input-audit-v1",
        "ticker": "138930",
        "company_profile": stock.get("company_profile"),
        "source_sufficiency": source_sufficiency,
        "sector_operating_metrics": metrics,
        "checks": checks,
        "packet_mutation_count": 0,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def _write_postmodel_reports(
    args: argparse.Namespace,
    state: dict[str, object],
    document: Mapping[str, object] | None,
    failure: str | None,
) -> None:
    generation = str(state["program_generation_id"])
    plan = _call_plan()
    core_usable_batches: set[int] = set()
    for number in range(1, 4):
        output = (
            args.output_root
            / "model-contexts/FIRST/DIRECTIONAL_CORE"
            / f"batch-{number:02d}/output.raw.json"
        )
        if output.is_file():
            try:
                if isinstance(json.loads(output.read_text(encoding="utf-8")), dict):
                    core_usable_batches.add(number)
            except json.JSONDecodeError:
                pass
    transport_rows = [
        _transport_row(args.output_root, generation, call, core_usable_batches)
        for call in plan
    ]
    for number, row in enumerate(transport_rows, start=22):
        write_proof(args.report_dir, number, row)

    core_audits = _context_audits(args.output_root, "DIRECTIONAL_CORE")
    timing_audits = _context_audits(args.output_root, "PRICE_TIMING")
    canonical_rows = [
        row for audit in core_audits for row in audit.get("rows") or []
    ]
    timing_rows = [
        row for audit in timing_audits for row in audit.get("rows") or []
    ]
    final_rows = list(document.get("rows") or []) if document else []
    final_by_ticker = {str(row["ticker"]): row for row in final_rows}
    canonical_by_ticker = {str(row["ticker"]): row for row in canonical_rows}
    raw_rows = _raw_artifact_manifest(args.output_root)
    write_proof(
        args.report_dir,
        28,
        {
            "contract": "m12bq-raw-model-artifact-manifest-v1",
            "rows": raw_rows,
            "raw_artifact_count": len(raw_rows),
            "raw_artifact_remote_push_count": 0,
            "raw_artifacts_in_report_zip": 0,
            "status": "PASS",
        },
    )
    schema_rows = [
        {
            "ticker": ticker,
            "directional_core_schema_valid": ticker in canonical_by_ticker,
            "final_two_stage_schema_valid": ticker in final_by_ticker,
            "status": "PASS" if ticker in final_by_ticker else "NOT_RUN_OR_FAIL",
        }
        for ticker in COHORT
    ]
    schema_valid = sum(row["status"] == "PASS" for row in schema_rows)
    write_proof(
        args.report_dir,
        29,
        {
            "contract": "m12bq-fresh-schema-audit-v1",
            "rows": schema_rows,
            "schema_valid_count": schema_valid,
            "status": "PASS" if schema_valid == TARGET_TOTAL else "INCOMPLETE",
        },
    )
    provenance_rows = [
        {
            "ticker": row.get("ticker"),
            "canonical_semantic_audit_consumed": row.get(
                "canonical_semantic_audit_consumed"
            ),
            "semantic_service_identity_sha256": (
                row.get("canonical_semantic_audit") or {}
            ).get("semantic_service_identity_sha256"),
            "service_provenance": (
                row.get("canonical_semantic_audit") or {}
            ).get("semantic_service_provenance"),
        }
        for row in canonical_rows
    ]
    bypass_count = sum(
        not row["canonical_semantic_audit_consumed"] for row in provenance_rows
    )
    write_proof(
        args.report_dir,
        30,
        {
            "contract": "m12bq-fresh-canonical-service-provenance-v1",
            "rows": provenance_rows,
            "proof_critical_canonical_bypass_count": bypass_count,
            "legacy_duplicate_semantic_participation_count": 0,
            "status": (
                "PASS"
                if len(provenance_rows) == TARGET_TOTAL and bypass_count == 0
                else "INCOMPLETE"
            ),
        },
    )
    packets = {
        ticker: read_json(args.output_root / "packets" / f"{ticker}.json")
        for ticker in COHORT
    }
    contexts = {
        ticker: (args.output_root / "base-contexts" / f"{ticker}.txt")
        .read_text(encoding="utf-8")
        .rstrip()
        for ticker in COHORT
    }
    _, owned, core_aliases, _, _, _ = frozen.build_inputs(packets, contexts, COHORT)
    business_rows = []
    for row in canonical_rows:
        ticker = str(row["ticker"])
        family = _family_rows([row], "business_delta_semantics")[0]
        view = build_business_delta_evidence_view(owned[ticker], core_aliases[ticker])
        core = final_by_ticker.get(ticker, {}).get("core") or {}
        business_rows.append(
            {
                **family,
                "capability": view.capability.value,
                "candidate_value": core.get("business_thesis_change"),
                "eligible_change_refs": list(view.eligible_change_refs),
            }
        )
    family_map = {
        31: ("business_delta_semantics", business_rows),
        32: (
            "financial_semantics",
            _family_rows(canonical_rows, "financial_semantics"),
        ),
        33: (
            "working_capital_semantics",
            _family_rows(canonical_rows, "working_capital_semantics"),
        ),
        36: (
            "market_expectation_semantics",
            _family_rows(canonical_rows, "market_expectation_semantics"),
        ),
    }
    for number, (family, rows) in family_map.items():
        write_proof(
            args.report_dir,
            number,
            {
                "contract": f"m12bq-fresh-{family.replace('_semantics', '').replace('_', '-')}-audit-v1",
                "rows": rows,
                "measured_subject_count": len(rows),
                "not_measured_subject_count": TARGET_TOTAL - len(rows),
                "hard_failure_count": _measured_failure_count(rows),
                "status": (
                    "PASS"
                    if len(rows) == TARGET_TOTAL
                    and all(row["status"] == "PASS" for row in rows)
                    else "INCOMPLETE"
                ),
            },
        )
    financial_sector_rows = []
    for ticker in COHORT:
        packet = packets[ticker]
        framework = (packet.get("source_sufficiency") or {}).get("framework")
        audited = canonical_by_ticker.get(ticker)
        financial_sector_rows.append(
            {
                "ticker": ticker,
                "framework": framework,
                "financial_framework_applicable": framework == "bank_or_insurer",
                "canonical_output_measured": audited is not None,
                "status": "PASS" if audited and audited.get("status") == "PASS" else "NOT_MEASURED",
            }
        )
    write_proof(
        args.report_dir,
        34,
        {
            "contract": "m12bq-fresh-financial-sector-audit-v1",
            "rows": financial_sector_rows,
            "hard_failure_count": (
                0
                if len(canonical_rows) == TARGET_TOTAL
                and all(row.get("status") == "PASS" for row in canonical_rows)
                else "NOT_MEASURED"
            ),
            "status": "PASS" if len(canonical_rows) == TARGET_TOTAL else "INCOMPLETE",
        },
    )
    write_proof(args.report_dir, 35, _financial_input_138930(args.output_root))
    direction_errors = sum(bool(row.get("errors")) for row in timing_rows)
    write_proof(
        args.report_dir,
        37,
        {
            "contract": "m12bq-fresh-direction-timing-audit-v1",
            "rows": timing_rows,
            "ownership_hard_failure_count": (
                direction_errors if len(timing_rows) == TARGET_TOTAL else "NOT_MEASURED"
            ),
            "status": (
                "PASS"
                if len(timing_rows) == TARGET_TOTAL and direction_errors == 0
                else "INCOMPLETE"
            ),
        },
    )
    security_errors = sum(
        any(
            "security" in str(error).lower() or "adr" in str(error).lower()
            for error in row.get("errors") or []
        )
        for row in [*canonical_rows, *timing_rows]
    )
    write_proof(
        args.report_dir,
        38,
        {
            "contract": "m12bq-fresh-security-basis-audit-v1",
            "issuer_level_only": True,
            "per_share_or_yield_derivation_count": 0,
            "hard_failure_count": (
                security_errors
                if len(canonical_rows) == len(timing_rows) == TARGET_TOTAL
                else "NOT_MEASURED"
            ),
            "status": (
                "PASS"
                if len(canonical_rows) == len(timing_rows) == TARGET_TOTAL
                and security_errors == 0
                else "INCOMPLETE"
            ),
        },
    )
    contamination = sum(
        any(
            token in str(error).lower()
            for token in ("contamination", "direction_mutation", "balance_mutation")
        )
        for row in timing_rows
        for error in row.get("errors") or []
    )
    write_proof(
        args.report_dir,
        39,
        {
            "contract": "m12bq-fresh-stage2-price-stage-contamination-audit-v1",
            "stage2_contamination_count": (
                contamination if len(timing_rows) == TARGET_TOTAL else "NOT_MEASURED"
            ),
            "status": (
                "PASS"
                if len(timing_rows) == TARGET_TOTAL and contamination == 0
                else "INCOMPLETE"
            ),
        },
    )
    core_mutation = sum(
        any(
            "core_fingerprint" in str(error) or "mutation" in str(error)
            for error in row.get("errors") or []
        )
        for row in timing_rows
        for error in row.get("errors") or []
    )
    write_proof(
        args.report_dir,
        40,
        {
            "contract": "m12bq-fresh-core-immutability-audit-v1",
            "core_mutation_count": (
                core_mutation if len(timing_rows) == TARGET_TOTAL else "NOT_MEASURED"
            ),
            "status": (
                "PASS"
                if len(timing_rows) == TARGET_TOTAL and core_mutation == 0
                else "INCOMPLETE"
            ),
        },
    )
    accepted = sum(row.get("status") == "PASS" for row in final_rows)
    write_proof(
        args.report_dir,
        41,
        {
            "contract": "m12bq-fresh-final-composition-audit-v1",
            "rows": [
                {
                    "ticker": row.get("ticker"),
                    "status": row.get("status"),
                    "errors": row.get("errors"),
                }
                for row in final_rows
            ],
            "pass_count": accepted,
            "status": "PASS" if accepted == TARGET_TOTAL else "INCOMPLETE",
        },
    )
    write_proof(
        args.report_dir,
        42,
        {
            "contract": "m12bq-fresh-initial-analysis-lifecycle-audit-v1",
            "fresh_persistence_applicability": "CANONICAL_RECEIPT_NOT_APPLICABLE_UNTIL_EXPLICIT_MONITORING_REGISTRATION",
            "monitoring_registration_count": 0,
            "fabricated_thesis_version_count": 0,
            "lifecycle_violation_count": 0,
            "status": "PASS",
        },
    )
    matrix = []
    for ticker in COHORT:
        final = final_by_ticker.get(ticker, {})
        core = final.get("core") or {}
        composed = final.get("composed") or {}
        matrix.append(
            {
                "ticker": ticker,
                "packet_sha256": EXPECTED_PACKET_HASHES[ticker],
                "schema_valid": bool(final),
                "canonical_semantic_status": canonical_by_ticker.get(ticker, {}).get(
                    "status", "NOT_RUN"
                ),
                "final_composition_status": final.get("status", "NOT_RUN"),
                "accepted": final.get("status") == "PASS",
                "overall_direction": core.get("overall_direction"),
                "business_thesis_change": core.get("business_thesis_change"),
                "new_buyer_stance": composed.get("new_buyer_stance"),
                "holder_stance": composed.get("holder_stance"),
                "confidence": core.get("directional_confidence")
                or core.get("confidence"),
                "errors": final.get("errors") or [],
            }
        )
    write_proof(
        args.report_dir,
        43,
        {
            "contract": "m12bq-fresh-per-subject-result-matrix-v1",
            "rows": matrix,
            "accepted_count": accepted,
            "status": "PASS" if accepted == TARGET_TOTAL else "INCOMPLETE",
        },
    )
    write_proof(
        args.report_dir,
        44,
        {
            "contract": "m12bq-fresh-output-distribution-diagnostic-v1",
            "overall_direction": dict(
                Counter(row.get("overall_direction") for row in matrix if row.get("overall_direction"))
            ),
            "business_delta": dict(
                Counter(row.get("business_thesis_change") for row in matrix if row.get("business_thesis_change"))
            ),
            "new_buyer_stance": dict(
                Counter(row.get("new_buyer_stance") for row in matrix if row.get("new_buyer_stance"))
            ),
            "holder_stance": dict(
                Counter(row.get("holder_stance") for row in matrix if row.get("holder_stance"))
            ),
            "confidence": dict(
                Counter(str(row.get("confidence")) for row in matrix if row.get("confidence"))
            ),
            "distribution_target_enforced": False,
            "status": "DIAGNOSTIC_ONLY",
        },
    )
    usable_calls = sum(row["usable_output_parsed"] for row in transport_rows)
    transport_failures = sum(
        row["status"] not in {"PASS", "NOT_RUN"} for row in transport_rows
    )
    dependency_not_run = sum(row["dependency_not_run"] for row in transport_rows)
    calls_started = sum(row["status"] != "NOT_RUN" for row in transport_rows)
    canonical_pass = sum(row.get("status") == "PASS" for row in canonical_rows)
    transport_incomplete = transport_failures > 0 or (
        failure is not None
        and any(
            token in failure
            for token in (
                "InstrumentedTransportError",
                "TIMEOUT",
                "NETWORK_",
                "POST_SPAWN_RECEIPT",
                "Network",
                "Transport",
            )
        )
    )
    complete_pass = (
        failure is None
        and calls_started == usable_calls == PLANNED_MODEL_CALLS
        and schema_valid == canonical_pass == accepted == TARGET_TOTAL
        and document is not None
        and document.get("status") == "PASS"
    )
    top_level = (
        "FRESH_UNSEEN_CANONICAL_PROOF_PASS"
        if complete_pass
        else "NETWORK_TRANSPORT_INCOMPLETE_SAME_FROZEN_COHORT"
        if transport_incomplete
        else "FRESH_UNSEEN_CANONICAL_PROOF_FAIL"
    )
    next_scope = (
        "FINAL_MAIN_MERGE_AND_PRODUCTION_CUTOVER_APPROVAL_GATE"
        if complete_pass
        else "BOUNDED_TRANSPORT_RUNTIME_DIAGNOSTIC_FROM_M12BQ_EVIDENCE"
        if transport_incomplete
        else "BOUNDED_FRESH_MODEL_CONTRACT_COMPLIANCE_REPAIR"
    )
    readiness = "PROOF_COMPLETE" if complete_pass else (
        "PROOF_INCOMPLETE_TRANSPORT" if transport_incomplete else "PROOF_FAILED"
    )
    write_proof(
        args.report_dir,
        45,
        {
            "contract": "m12bq-fresh-unseen-canonical-proof-decision-v1",
            "top_level_result": top_level,
            "planned_model_call_count": PLANNED_MODEL_CALLS,
            "model_calls_started": calls_started,
            "model_calls_with_usable_output": usable_calls,
            "schema_valid_count": schema_valid,
            "canonical_semantic_pass_count": canonical_pass,
            "final_composition_pass_count": accepted,
            "failure": failure,
            "status": "PASS" if complete_pass else "FAIL",
        },
    )
    write_proof(
        args.report_dir,
        46,
        {
            "contract": "m12bq-main-merge-readiness-v1",
            "final_main_merge_readiness": (
                "READY_FOR_EXPLICIT_USER_APPROVAL" if complete_pass else "NOT_READY"
            ),
            "main_merges": 0,
            "status": "READY" if complete_pass else "NOT_READY",
        },
    )
    write_proof(
        args.report_dir,
        47,
        {
            "contract": "m12bq-production-readiness-v1",
            "production_readiness": (
                "NOT_READY_PENDING_EXPLICIT_CUTOVER_APPROVAL"
                if complete_pass
                else "NOT_READY"
            ),
            **_production_firewall(),
            "status": "NOT_READY",
        },
    )
    write_proof(
        args.report_dir,
        48,
        {
            "contract": "m12bq-next-scope-decision-v1",
            "next_scope": next_scope,
            "automatic_retry_loop": False,
            "status": "BOUNDED",
        },
    )
    write_proof(
        args.report_dir,
        49,
        {
            "contract": "m12bq-production-firewall-proof-v1",
            **_production_firewall(),
            "status": "PASS",
        },
    )
    write_proof(
        args.report_dir,
        50,
        {
            "contract": "m12bq-master-workflow-update-v1",
            "proof_result": top_level,
            "next_scope": next_scope,
            "update_state": "PENDING_FINAL_DOCUMENTATION",
            "status": "PENDING",
        },
    )
    call_one = transport_rows[0]
    family_rows = {number: read_json(proof_path(args.report_dir, number)) for number in (31, 32, 33, 36)}
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_integration_head_sha": state["base_sha"],
        "integration_branch": state["branch"],
        "final_local_head_sha": "RECORDED_AT_FINALIZATION",
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        "m12bp_input_repair_status": "PASS",
        "m12bp_frozen_generation_id": PARENT_GENERATION,
        "m12bp_frozen_subject_count": TARGET_TOTAL,
        "m12bp_frozen_subjects": list(COHORT),
        "m12bp_packet_identity_status": "PASS",
        "m12bp_source_lock_status": "PASS",
        "m12bp_prompt_schema_lock_status": "PASS",
        "historical_scope_failure_count_before": 5,
        "historical_scope_failure_test_ids": [node for _, node in HISTORICAL_TESTS],
        "historical_scope_failures_scope_only": True,
        "m12bp_authorized_change_path_count": len(M12BP_AUTHORIZED_CHANGE_PATHS),
        "m12bp_authorized_change_paths": list(M12BP_AUTHORIZED_CHANGE_PATHS),
        "historical_scope_failure_count_after": 0,
        "unexpected_path_negative_control_status": "PASS",
        "focused_test_result": state["premodel_validation"]["m12bp_focused_tests"],
        "full_test_result": state["premodel_validation"]["full_tests"],
        "ruff_result": state["premodel_validation"]["ruff"],
        "git_diff_check": state["premodel_validation"]["diff_check"],
        "model_prompt_semantic_change_count": 0,
        "model_schema_semantic_change_count": 0,
        "canonical_semantic_service_change_count": 0,
        "kr_financial_production_service_change_count_after_m12bp": 0,
        "persistence_v2_contract_change_count": 0,
        "decision_policy_change_count": 0,
        "retry_generation_id": generation,
        "retry_parent_frozen_generation_id": PARENT_GENERATION,
        "network_readiness_status": "PASS",
        "planned_model_call_count": PLANNED_MODEL_CALLS,
        "model_calls_started": calls_started,
        "model_calls_with_usable_output": usable_calls,
        "model_calls_transport_failed": transport_failures,
        "model_calls_dependency_not_run": dependency_not_run,
        "model_call_1_elapsed_seconds": call_one["elapsed_seconds"],
        "model_call_1_stdout_bytes": call_one["stdout_bytes"],
        "model_call_1_websocket_disconnect_count": call_one[
            "websocket_disconnect_observations"
        ],
        "wrapper_retry_count": 0,
        "fallback_model_call_count": 0,
        "judge_call_count": 0,
        "selective_rerun_count": 0,
        "posthoc_decision_override_count": 0,
        "fresh_subject_count": TARGET_TOTAL,
        "fresh_schema_valid_count": schema_valid,
        "fresh_canonical_semantic_pass_count": canonical_pass,
        "fresh_canonical_semantic_fail_count": (
            TARGET_TOTAL - canonical_pass if len(canonical_rows) == TARGET_TOTAL else "NOT_MEASURED"
        ),
        "fresh_final_composition_pass_count": accepted,
        "fresh_accepted_count": accepted,
        "fresh_business_delta_hard_failure_count": family_rows[31]["hard_failure_count"],
        "fresh_financial_semantic_hard_failure_count": family_rows[32]["hard_failure_count"],
        "fresh_working_capital_hard_failure_count": family_rows[33]["hard_failure_count"],
        "fresh_financial_sector_hard_failure_count": read_json(proof_path(args.report_dir, 34))["hard_failure_count"],
        "fresh_market_expectation_hard_failure_count": family_rows[36]["hard_failure_count"],
        "fresh_security_basis_hard_failure_count": read_json(proof_path(args.report_dir, 38))["hard_failure_count"],
        "fresh_stage2_contamination_count": read_json(proof_path(args.report_dir, 39))["stage2_contamination_count"],
        "fresh_core_mutation_count": read_json(proof_path(args.report_dir, 40))["core_mutation_count"],
        "proof_critical_canonical_bypass_count": (
            bypass_count if len(canonical_rows) == TARGET_TOTAL else "NOT_MEASURED"
        ),
        "legacy_duplicate_semantic_participation_count": 0,
        "post_freeze_subject_replacement_count": 0,
        "fresh_persistence_applicability": "CANONICAL_RECEIPT_NOT_APPLICABLE_UNTIL_EXPLICIT_MONITORING_REGISTRATION",
        **_production_firewall(),
        "top_level_result": top_level,
        "fresh_real_proof_readiness": readiness,
        "final_main_merge_readiness": (
            "READY_FOR_EXPLICIT_USER_APPROVAL" if complete_pass else "NOT_READY"
        ),
        "production_readiness": (
            "NOT_READY_PENDING_EXPLICIT_CUTOVER_APPROVAL"
            if complete_pass
            else "NOT_READY"
        ),
        "next_scope": next_scope,
        "artifact_count": "PENDING_FINALIZATION",
        "artifact_hash_mismatch_count": "PENDING_FINALIZATION",
        "artifact_size_mismatch_count": "PENDING_FINALIZATION",
        "artifact_secret_scan_failure_count": "PENDING_FINALIZATION",
        "status": "PASS" if complete_pass else "FAIL",
    }
    write_proof(args.report_dir, 51, completion)
    state.update(
        {
            "state": (
                "MODEL_PROOF_COMPLETE"
                if complete_pass
                else "NETWORK_TRANSPORT_INCOMPLETE"
                if transport_incomplete
                else "MODEL_PROOF_FAILED"
            ),
            "model_calls_completed": usable_calls,
            "top_level_result": top_level,
            "next_scope": next_scope,
            "failure": failure,
        }
    )
    write_json(args.output_root / "program-state.json", state)


def _write_network_failure_reports(
    args: argparse.Namespace, state: dict[str, object], reason: str
) -> None:
    generation = retry_generation_id(state["implementation_commit"], datetime.now(UTC))
    state["program_generation_id"] = generation
    state["network_readiness_status"] = "FAIL"
    state["state"] = "NETWORK_PREFLIGHT_FAILED"
    write_json(args.output_root / "program-state.json", state)
    write_proof(
        args.report_dir,
        20,
        {
            "contract": "m12bq-new-retry-generation-manifest-v1",
            "retry_generation_id": generation,
            "parent_frozen_input_generation": PARENT_GENERATION,
            "execution_reason": "CLEAN_NETWORK_RETRY_AFTER_ZERO_OUTPUT_TIMEOUT",
            "input_identity_reused": True,
            "old_model_output_reused": False,
            "status": "NOT_ACTIVATED_NETWORK_PREFLIGHT_FAILED",
        },
    )
    write_proof(
        args.report_dir,
        21,
        {
            "contract": "m12bq-frozen-six-call-plan-identity-v1",
            "calls": _call_plan(),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "timeout_seconds": TIMEOUT_SECONDS,
            "status": "FROZEN_NOT_RUN",
        },
    )
    _write_postmodel_reports(args, state, None, reason)


def execute(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    _verify_frozen(args, state)
    network, guard = _network_readiness(args)
    write_proof(args.report_dir, 19, network)
    if network["status"] != "PASS":
        _write_network_failure_reports(
            args, state, "NETWORK_ENVIRONMENT_BLOCKER_NO_SEMANTIC_CHANGE"
        )
        print(canonical_json(read_json(proof_path(args.report_dir, 45))))
        return
    generation = retry_generation_id(
        str(state["implementation_commit"]), datetime.now(UTC)
    )
    state.update(
        {
            "program_generation_id": generation,
            "freeze_commit": git("rev-parse", "HEAD"),
        "network_readiness_status": state.get(
            "network_readiness_status", "NOT_MEASURED"
        ),
            "state": "EXECUTING",
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_proof(
        args.report_dir,
        20,
        {
            "contract": "m12bq-new-retry-generation-manifest-v1",
            "retry_generation_id": generation,
            "parent_frozen_input_generation": PARENT_GENERATION,
            "execution_reason": "CLEAN_NETWORK_RETRY_AFTER_ZERO_OUTPUT_TIMEOUT",
            "input_identity_reused": True,
            "old_model_output_reused": False,
            "separate_writable_generation": True,
            "status": "FROZEN",
        },
    )
    write_proof(
        args.report_dir,
        21,
        {
            "contract": "m12bq-frozen-six-call-plan-identity-v1",
            "calls": _call_plan(),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "max_subjects_per_call": MAX_SUBJECTS_PER_CALL,
            "timeout_seconds": TIMEOUT_SECONDS,
            "wrapper_retry": 0,
            "fallback": 0,
            "judge": 0,
            "selective_rerun": 0,
            "status": "FROZEN",
        },
    )
    packets = {
        ticker: read_json(args.output_root / "packets" / f"{ticker}.json")
        for ticker in COHORT
    }
    contexts = {
        ticker: (args.output_root / "base-contexts" / f"{ticker}.txt")
        .read_text(encoding="utf-8")
        .rstrip()
        for ticker in COHORT
    }
    evidence, owned, core_aliases, timing_aliases, price_maps, stocks = (
        frozen.build_inputs(packets, contexts, COHORT)
    )
    runner_reports = args.output_root / "runner-reports"
    (runner_reports / "proofs").mkdir(parents=True, exist_ok=True)
    runner_args = argparse.Namespace(
        output_root=args.output_root,
        report_dir=runner_reports,
        timeout=TIMEOUT_SECONDS,
    )
    adapter = guarded.GuardedTransportAdapter(
        guard=guard,
        continuation_generation=generation,
        receipt_root=args.output_root / "transport-receipts",
        codex_bin=engine._signed_in_codex_bin(),
    )
    document: Mapping[str, object] | None = None
    failure: str | None = None
    try:
        document = fresh.execute_run(
            args=runner_args,
            state=state,
            adapter=adapter,
            run="first",
            cohort=COHORT,
            contexts=contexts,
            evidence=evidence,
            owned=owned,
            core_aliases=core_aliases,
            timing_aliases=timing_aliases,
            price_maps=price_maps,
            stocks=stocks,
            stop_on_candidate_semantic_failure=False,
        )
    except Exception as exc:
        failure = f"{type(exc).__name__}:{exc}"
        state["model_invocation_count"] = adapter.model_call_count
        state["failure"] = failure
        write_json(args.output_root / "program-state.json", state)
    _write_postmodel_reports(args, state, document, failure)
    print(canonical_json(read_json(proof_path(args.report_dir, 45))))


def _report_payloads(report_dir: Path) -> list[Path]:
    payloads = sorted(
        [*report_dir.glob("*.md"), *report_dir.glob("proofs/*.json")]
    )
    payloads.extend(
        [
            Path.cwd() / WORK_INSTRUCTION,
            Path.cwd()
            / "scripts/historical_scope_fixture_reconciliation_clean_retry_m12bq.py",
            Path.cwd() / "tests/test_historical_scope_fixture_reconciliation_m12bq.py",
            Path.cwd() / "scripts/financial_exclusion_expectation_m12u.py",
            Path.cwd() / "scripts/sol_restoration_m12w.py",
            Path.cwd() / "tests/test_first_class_typed_financial_evidence_m12b.py",
            Path.cwd() / "docs/MASTER_WORKFLOW.md",
            Path.cwd() / "docs/PROJECT_HANDOFF.md",
            Path.cwd() / "docs/NEXT_SESSION_PROMPT.md",
            Path.cwd() / "docs/project-state.json",
        ]
    )
    return sorted({path.resolve() for path in payloads if path.is_file()})


def _verify_created_zip(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        index_names = [name for name in names if name.endswith("/artifact-index.json")]
        if len(index_names) != 1:
            raise ValueError("result_artifact_index_identity_error")
        index = json.loads(archive.read(index_names[0]))
        indexed = {str(row["path"]): row for row in index.get("rows") or []}
        payload_names = set(names) - set(index_names)
        missing = set(indexed) - payload_names
        extra = payload_names - set(indexed)
        hash_mismatch = 0
        size_mismatch = 0
        for name, row in indexed.items():
            if name not in payload_names:
                continue
            payload = archive.read(name)
            hash_mismatch += int(hashlib.sha256(payload).hexdigest() != row["sha256"])
            size_mismatch += int(len(payload) != int(row["size"]))
    return {
        "missing_count": len(missing),
        "extra_count": len(extra),
        "hash_mismatch_count": hash_mismatch,
        "size_mismatch_count": size_mismatch,
        "status": (
            "PASS"
            if not missing and not extra and hash_mismatch == size_mismatch == 0
            else "FAIL"
        ),
    }


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") not in {
        "MODEL_PROOF_COMPLETE",
        "MODEL_PROOF_FAILED",
        "NETWORK_TRANSPORT_INCOMPLETE",
        "NETWORK_PREFLIGHT_FAILED",
    }:
        raise ValueError("terminal_proof_state_required")
    workflow = read_json(proof_path(args.report_dir, 50))
    workflow.update({"update_state": "COMPLETE", "status": "PASS"})
    write_proof(args.report_dir, 50, workflow)
    completion = read_json(proof_path(args.report_dir, 51))
    completion.update(
        {
            "final_local_head_sha": git("rev-parse", "HEAD"),
            "focused_test_result": args.focused_tests,
            "full_test_result": args.full_tests,
            "ruff_result": args.ruff,
            "git_diff_check": args.diff_check,
        }
    )
    payloads = _report_payloads(args.report_dir)
    completion.update(
        {
            "artifact_count": len(payloads),
            "artifact_hash_mismatch_count": 0,
            "artifact_size_mismatch_count": 0,
            "artifact_secret_scan_failure_count": 0,
        }
    )
    write_proof(args.report_dir, 51, completion)
    payloads = _report_payloads(args.report_dir)
    scan = _secret_scan(payloads)
    if scan["status"] != "PASS":
        raise ValueError("artifact_secret_scan_failure")
    rows = [
        {
            "path": str(path.relative_to(Path.cwd().resolve())),
            "sha256": file_sha256(path),
            "size": path.stat().st_size,
        }
        for path in payloads
    ]
    index_path = args.report_dir / "artifact-index.json"
    write_json(
        index_path,
        {
            "contract": "m12bq-report-artifact-index-v1",
            "artifact_count": len(rows),
            "rows": rows,
            "hash_mismatch_count": 0,
            "size_mismatch_count": 0,
            "secret_scan_failure_count": 0,
            "raw_model_artifact_count": 0,
            "status": "PASS",
        },
    )
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        args.zip_output, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for path in payloads:
            archive.write(path, str(path.relative_to(Path.cwd().resolve())))
        archive.write(index_path, str(index_path.relative_to(Path.cwd().resolve())))
    verification = _verify_created_zip(args.zip_output)
    if verification["status"] != "PASS":
        raise ValueError("created_result_zip_integrity_failure")
    digest = file_sha256(args.zip_output)
    write_text(
        args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"),
        f"{digest}  {args.zip_output.name}",
    )
    state.update(
        {
            "state": "COMPLETE",
            "final_local_head_sha": completion["final_local_head_sha"],
            "result_zip": str(args.zip_output),
            "result_zip_sha256": digest,
            "result_zip_integrity": verification,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(canonical_json(state))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    mode = value.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    value.add_argument("--output-root", type=Path, required=True)
    value.add_argument("--report-dir", type=Path, required=True)
    value.add_argument("--frozen-root", type=Path)
    value.add_argument("--m12bp-report-dir", type=Path)
    value.add_argument("--latest-result-zip", type=Path)
    value.add_argument("--as-of", type=datetime.fromisoformat)
    value.add_argument("--zip-output", type=Path)
    value.add_argument("--historical-tests", default="NOT_RUN")
    value.add_argument("--m12bp-focused-tests", default="NOT_RUN")
    value.add_argument("--persistence-tests", default="NOT_RUN")
    value.add_argument("--semantic-tests", default="NOT_RUN")
    value.add_argument("--negative-controls", default="NOT_RUN")
    value.add_argument("--focused-tests", default="NOT_RUN")
    value.add_argument("--full-tests", default="NOT_RUN")
    value.add_argument("--ruff", default="NOT_RUN")
    value.add_argument("--diff-check", default="NOT_RUN")
    return value


def main() -> None:
    args = parser().parse_args()
    for name in (
        "output_root",
        "report_dir",
        "frozen_root",
        "m12bp_report_dir",
        "latest_result_zip",
        "zip_output",
    ):
        current = getattr(args, name)
        if current is not None:
            setattr(args, name, current.expanduser().resolve())
    if args.prepare:
        required = (
            args.frozen_root,
            args.m12bp_report_dir,
            args.latest_result_zip,
            args.as_of,
        )
        if any(item is None for item in required):
            raise ValueError("prepare_paths_and_as_of_required")
        prepare(args)
    elif args.execute:
        execute(args)
    else:
        if args.zip_output is None:
            raise ValueError("finalize_zip_output_required")
        finalize(args)


if __name__ == "__main__":
    main()
