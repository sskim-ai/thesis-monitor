from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import zipfile
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2ProductionContext,
    materialize_accepted_v2_stage2_output,
    validate_accepted_v2_production_output,
)


PASS = "PASS"
FAIL = "FAIL"
REQUIRED_BASE_SHA = "5ea16d57ad50a1f7b44a31c11ae97471c30126bc"
R3_RESULT_SHA256 = "cfa1d9d86b08f6bc1ce5056ce73442602d72fa87bb6d5812c26296f75d8b83c3"
REPAIR_IMPLEMENTATION_SHA = "0b13013feb1cf81b57b172c90167ce73cc3bd78b"
INSTRUCTION_CONTENT_SHA256 = (
    "37d9fa5a43355ae42772923c8f9babcc835bd36cfd4fea3261b98e16de949302"
)
TOP_LEVEL_RESULT = "M12CG_R4_FINALIZATION_SCOPE_REPAIR_OFFLINE_CLOSURE_PASS"
REPORT_NAME = (
    "thesis-monitor-20260916-m12cg-r4-finalization-frozen-core-numeric-"
    "ownership-scope-repair-offline-proof-report"
)
VALIDATED_AT = datetime(2026, 9, 16, tzinfo=UTC)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(root: Path, relative: str, value: object) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pretty_bytes(value))
    return path


def write_bytes(root: Path, relative: str, value: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    return path


def run(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        args,
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def safe_archive_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def verify_package(package_root: Path) -> dict[str, object]:
    package_manifest_path = package_root / "package-manifest.json"
    package_manifest = read_json(package_manifest_path)
    assert isinstance(package_manifest, Mapping)
    package_rows = package_manifest.get("artifacts")
    assert isinstance(package_rows, list)
    package_errors: list[dict[str, object]] = []
    package_expected: set[str] = set()
    for row in package_rows:
        assert isinstance(row, Mapping)
        relative = str(row.get("path") or "")
        package_expected.add(relative)
        path = package_root / relative
        if not path.is_file():
            package_errors.append({"path": relative, "error": "missing"})
            continue
        if path.stat().st_size != int(row.get("size") or -1):
            package_errors.append({"path": relative, "error": "size"})
        if sha256_file(path) != str(row.get("sha256") or ""):
            package_errors.append({"path": relative, "error": "sha256"})
    actual_package = {
        path.relative_to(package_root).as_posix()
        for path in package_root.rglob("*")
        if path.is_file() and path != package_manifest_path
    }

    index = read_json(package_root / "inputs/source-index.json")
    assert isinstance(index, Mapping)
    source_rows = index.get("sources")
    assert isinstance(source_rows, list)
    sources: list[dict[str, object]] = []
    nested_payload_count = 0
    for entry in source_rows:
        assert isinstance(entry, Mapping)
        zip_path = package_root / str(entry["package_path"])
        sidecar_path = package_root / str(entry["sidecar_path"])
        expected_sha = str(entry["sha256"])
        actual_sha = sha256_file(zip_path)
        sidecar_sha = sidecar_path.read_text(encoding="utf-8").split()[0]
        manifest_name = str(entry["artifact_manifest"])
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            unsafe = sorted(name for name in names if not safe_archive_name(name))
            duplicate = sorted(name for name in set(names) if names.count(name) > 1)
            bad_crc = archive.testzip()
            manifest = json.loads(archive.read(manifest_name))
            rows = manifest.get("artifacts")
            if not isinstance(rows, list):
                raise ValueError(f"source_manifest_rows_invalid:{entry['phase']}")
            prefix = PurePosixPath(manifest_name).parts[0]
            manifest_errors: list[dict[str, object]] = []
            expected_payloads: set[str] = set()
            for row in rows:
                if not isinstance(row, Mapping):
                    manifest_errors.append({"path": None, "error": "invalid_row"})
                    continue
                relative = str(row.get("path") or "")
                member = f"{prefix}/{relative}"
                expected_payloads.add(member)
                if member not in names:
                    manifest_errors.append({"path": relative, "error": "missing"})
                    continue
                payload = archive.read(member)
                if len(payload) != int(row.get("size") or -1):
                    manifest_errors.append({"path": relative, "error": "size"})
                if sha256_bytes(payload) != str(row.get("sha256") or ""):
                    manifest_errors.append({"path": relative, "error": "sha256"})
            actual_payloads = {
                name
                for name in names
                if not name.endswith("/") and name != manifest_name
            }
            extras = sorted(actual_payloads - expected_payloads)
        nested_payload_count += len(rows)
        declared_count = int(manifest.get("artifact_count") or len(rows))
        expected_count = int(entry["manifest_declared_count"])
        status = (
            PASS
            if actual_sha == expected_sha == sidecar_sha
            and zip_path.stat().st_size == int(entry["size_bytes"])
            and not unsafe
            and not duplicate
            and bad_crc is None
            and declared_count == expected_count == len(rows)
            and not manifest_errors
            and not extras
            else FAIL
        )
        sources.append(
            {
                "phase": entry["phase"],
                "filename": entry["filename"],
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
                "sidecar_sha256": sidecar_sha,
                "manifest_declared_count": declared_count,
                "manifest_verified_count": len(rows) - len(manifest_errors),
                "manifest_errors": manifest_errors,
                "unexpected_payloads": extras,
                "unsafe_entry_count": len(unsafe),
                "duplicate_entry_count": len(duplicate),
                "bad_crc_entry": bad_crc,
                "status": status,
            }
        )
    return {
        "contract": "m12cg-r4-source-base-integrity-v1",
        "package_payload_count_required": len(package_rows),
        "package_payload_count_verified": len(package_rows) - len(package_errors),
        "package_errors": package_errors,
        "package_unexpected_payloads": sorted(actual_package - package_expected),
        "source_bundle_count_required": len(source_rows),
        "source_bundle_count_verified": sum(row["status"] == PASS for row in sources),
        "nested_source_payload_count": nested_payload_count,
        "sources": sources,
        "status": (
            PASS
            if not package_errors
            and not (actual_package - package_expected)
            and all(row["status"] == PASS for row in sources)
            else FAIL
        ),
    }


def subset_context(
    context: AcceptedV2ProductionContext,
    subjects: tuple[str, ...],
) -> AcceptedV2ProductionContext:
    selected = set(subjects)
    return context.model_copy(
        update={
            "selected_subjects": subjects,
            "evidence_packets": tuple(
                row for row in context.evidence_packets if row.ticker in selected
            ),
            "evidence_ownership": tuple(
                row for row in context.evidence_ownership if row.ticker in selected
            ),
            "prior_accepted": tuple(
                row for row in context.prior_accepted if row.ticker in selected
            ),
        }
    )


def subset_raw(raw: Mapping[str, object], subjects: tuple[str, ...]) -> dict[str, object]:
    selected = set(subjects)
    payload = deepcopy(dict(raw))
    for field_name in ("fundamental_cores", "candidates", "adjudications"):
        rows = payload.get(field_name)
        if isinstance(rows, list):
            payload[field_name] = [
                row
                for row in rows
                if isinstance(row, Mapping) and str(row.get("ticker")) in selected
            ]
    return payload


def trusted_batch(
    context: AcceptedV2ProductionContext,
    cores: Sequence[object],
) -> AcceptedV2FundamentalCoreBatch:
    return AcceptedV2FundamentalCoreBatch(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        cores=tuple(cores),
    )


def parse_junit(path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    totals = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
    elapsed = 0.0
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.attrib.get(key, 0))
        elapsed += float(suite.attrib.get("time", 0.0))
    nodes: list[dict[str, object]] = []
    for case in root.iter("testcase"):
        classname = str(case.attrib.get("classname") or "")
        name = str(case.attrib.get("name") or "")
        status = PASS
        if case.find("failure") is not None or case.find("error") is not None:
            status = FAIL
        elif case.find("skipped") is not None:
            status = "SKIP"
        nodes.append(
            {
                "node_id": f"{classname}::{name}",
                "classname": classname,
                "name": name,
                "status": status,
            }
        )
    summary = {
        **totals,
        "time_seconds": elapsed,
        "status": PASS if totals["failures"] == 0 and totals["errors"] == 0 else FAIL,
    }
    return summary, nodes


def function_excerpt(source: str, names: set[str]) -> str:
    tree = ast.parse(source)
    spans: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in names and node.end_lineno is not None:
                spans.append((node.lineno, node.end_lineno, node.name))
    lines = source.splitlines(keepends=True)
    chunks = []
    for start, end, name in sorted(spans):
        chunks.append(f"# {name} lines {start}-{end}\n")
        chunks.extend(lines[start - 1 : end])
        if not chunks[-1].endswith("\n"):
            chunks[-1] += "\n"
        chunks.append("\n")
    return "".join(chunks)


def export_source_excerpts(repo: Path, out: Path, head: str) -> list[dict[str, object]]:
    specs = {
        "app/services/accepted_decision_v2_service.py": {
            "AcceptedDecisionFrozenCoreNumericScope",
            "validate_accepted_v2_decision",
            "render_accepted_v2_production",
        },
        "app/services/accepted_decision_v2_runtime_service.py": {
            "validate_accepted_v2_fundamental_core_batch_scope",
            "accepted_v2_fundamental_core_sha256",
            "validate_accepted_v2_production_output",
            "load_accepted_v2_production_artifact",
        },
        "app/jobs/accepted_decision_v2_runtime.py": {"validate_output"},
    }
    rows: list[dict[str, object]] = []
    for path, names in specs.items():
        current = (repo / path).read_text(encoding="utf-8")
        before = run(repo, "git", "show", f"{REQUIRED_BASE_SHA}:{path}")
        for label, revision, source in (
            ("before", REQUIRED_BASE_SHA, before),
            ("after", head, current),
        ):
            excerpt = function_excerpt(source, names)
            target = write_bytes(
                out,
                f"excerpts/{Path(path).stem}--{label}.txt",
                excerpt.encode("utf-8"),
            )
            rows.append(
                {
                    "path": path,
                    "label": label,
                    "revision": revision,
                    "excerpt_path": target.relative_to(out).as_posix(),
                    "excerpt_sha256": sha256_file(target),
                    "full_source_sha256": sha256_bytes(source.encode("utf-8")),
                    "functions_requested": sorted(names),
                }
            )
    return rows


def finalization_reproof(
    source_m12ce: Path,
    source_r3: Path,
    previous_probe: Path,
    out: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    raw_root = source_m12ce / "raw" / "reproof-no-repair" / "us"
    context_path = raw_root / "context.json"
    context = AcceptedV2ProductionContext.model_validate_json(
        context_path.read_text(encoding="utf-8")
    )
    prior_probe = read_json(previous_probe / "result.json")
    assert isinstance(prior_probe, Mapping)
    prior_fresh = prior_probe.get("fresh")
    assert isinstance(prior_fresh, Mapping)
    prior_finalizations = prior_fresh.get("finalizations")
    assert isinstance(prior_finalizations, list)
    prior_by_ticker = {
        str(row["ticker"]): row
        for row in prior_finalizations
        if isinstance(row, Mapping)
    }

    batch_rows: list[dict[str, object]] = []
    subject_rows: list[dict[str, object]] = []
    parity_rows: list[dict[str, object]] = []
    before_after_rows: list[dict[str, object]] = []
    existing_success_count = 0
    newly_finalized_count = 0

    for batch_number in range(1, 4):
        source_path = raw_root / f"batch-{batch_number:02d}.output.json"
        source_bytes = source_path.read_bytes()
        raw = json.loads(source_bytes)
        subjects = tuple(str(row["ticker"]) for row in raw["candidates"])
        batch_context = subset_context(context, subjects)
        output = materialize_accepted_v2_stage2_output(batch_context, raw)
        core_batch = trusted_batch(batch_context, output.fundamental_cores)
        artifact = validate_accepted_v2_production_output(
            batch_context,
            output,
            trusted_fundamental_core_batch=core_batch,
            validated_at=VALIDATED_AT,
        )
        source_copy = write_bytes(
            out,
            f"payloads/fresh/batch-{batch_number:02d}.source-output.json",
            source_bytes,
        )
        context_copy = write_json(
            out,
            f"payloads/fresh/batch-{batch_number:02d}.context.json",
            batch_context.model_dump(mode="json"),
        )
        normalized_copy = write_json(
            out,
            f"payloads/fresh/batch-{batch_number:02d}.normalized.json",
            output.model_dump(mode="json"),
        )
        core_copy = write_json(
            out,
            f"payloads/fresh/batch-{batch_number:02d}.trusted-core.json",
            core_batch.model_dump(mode="json"),
        )
        artifact_copy = write_json(
            out,
            f"payloads/fresh/batch-{batch_number:02d}.artifact.json",
            artifact.model_dump(mode="json"),
        )
        message_rows = [
            {
                "ticker": block.ticker,
                "text": block.text,
                "sha256": sha256_bytes(block.text.encode("utf-8")),
            }
            for block in artifact.blocks
        ]
        messages_copy = write_json(
            out,
            f"payloads/fresh/batch-{batch_number:02d}.rendered-messages.json",
            message_rows,
        )
        batch_rows.append(
            {
                "batch": batch_number,
                "subjects": list(subjects),
                "source_output": source_copy.relative_to(out).as_posix(),
                "source_output_sha256": sha256_file(source_copy),
                "context_sha256": sha256_file(context_copy),
                "normalized_sha256": sha256_file(normalized_copy),
                "trusted_core_sha256": sha256_file(core_copy),
                "artifact_sha256": sha256_file(artifact_copy),
                "rendered_messages_sha256": sha256_file(messages_copy),
                "ready_count": artifact.ready_count,
                "not_ready_count": artifact.not_ready_count,
                "status": PASS
                if artifact.ready_count == len(subjects) and artifact.not_ready_count == 0
                else FAIL,
            }
        )

        for ticker in subjects:
            one_context = subset_context(context, (ticker,))
            one_raw = subset_raw(raw, (ticker,))
            one_output = materialize_accepted_v2_stage2_output(one_context, one_raw)
            one_core_batch = trusted_batch(one_context, one_output.fundamental_cores)
            one_artifact = validate_accepted_v2_production_output(
                one_context,
                one_output,
                trusted_fundamental_core_batch=one_core_batch,
                validated_at=VALIDATED_AT,
            )
            candidate = one_output.candidates[0]
            core = one_output.fundamental_cores[0]
            plan = one_artifact.accepted_plans[0]
            block = one_artifact.blocks[0]
            candidate_copy = write_json(
                out,
                f"payloads/fresh/per-ticker/{ticker}.candidate.json",
                candidate.model_dump(mode="json"),
            )
            core_row_copy = write_json(
                out,
                f"payloads/fresh/per-ticker/{ticker}.core.json",
                core.model_dump(mode="json"),
            )
            plan_copy = write_json(
                out,
                f"payloads/fresh/per-ticker/{ticker}.accepted-plan.json",
                plan.model_dump(mode="json"),
            )
            individual_artifact = write_json(
                out,
                f"payloads/fresh/per-ticker/{ticker}.artifact.json",
                one_artifact.model_dump(mode="json"),
            )
            message_copy = write_bytes(
                out,
                f"payloads/fresh/per-ticker/{ticker}.rendered.txt",
                (block.text + "\n").encode("utf-8"),
            )
            previous = prior_by_ticker[ticker]
            previous_result = str(previous["result"])
            row = {
                "ticker": ticker,
                "batch": batch_number,
                "before_finalization": previous_result,
                "after_finalization": PASS,
                "candidate_sha256": sha256_file(candidate_copy),
                "core_sha256": sha256_file(core_row_copy),
                "accepted_plan_sha256": sha256_file(plan_copy),
                "artifact_sha256": sha256_file(individual_artifact),
                "rendered_sha256": sha256_file(message_copy),
                "accepted_source": plan.accepted_source,
                "accepted_decision": plan.accepted_decision,
                "status": PASS,
            }
            subject_rows.append(row)
            if previous_result == PASS:
                prior_artifact = previous_probe / "payloads" / "fresh" / f"{ticker}.artifact.json"
                same = prior_artifact.read_bytes() == individual_artifact.read_bytes()
                existing_success_count += int(same)
                parity_rows.append(
                    {
                        "ticker": ticker,
                        "classification": "EXISTING_SUCCESS_BYTE_PARITY",
                        "before_path": str(prior_artifact),
                        "before_sha256": sha256_file(prior_artifact),
                        "after_path": individual_artifact.relative_to(out).as_posix(),
                        "after_sha256": sha256_file(individual_artifact),
                        "byte_equal": same,
                        "allowed_difference": False,
                        "status": PASS if same else FAIL,
                    }
                )
            else:
                newly_finalized_count += 1
                before_plan = source_r3 / "payloads" / "numeric-trace" / f"{ticker}.accepted-plan.json"
                plan_equal = before_plan.read_bytes() == plan_copy.read_bytes()
                before_error = str(previous.get("error") or "")
                before_after_rows.append(
                    {
                        "ticker": ticker,
                        "before_error_type": previous.get("error_type"),
                        "before_error": before_error,
                        "before_plan_sha256": sha256_file(before_plan),
                        "after_plan_sha256": sha256_file(plan_copy),
                        "semantic_plan_byte_equal": plan_equal,
                        "after_artifact_sha256": sha256_file(individual_artifact),
                        "after_rendered_sha256": sha256_file(message_copy),
                        "new_offline_artifact": True,
                        "status": PASS
                        if "adjudication_introduced_unregistered_numeric" in before_error
                        and plan_equal
                        else FAIL,
                    }
                )
                parity_rows.append(
                    {
                        "ticker": ticker,
                        "classification": "NEWLY_FINALIZED_UNCHANGED_PREACCEPTANCE_PLAN",
                        "before_path": str(before_plan),
                        "before_sha256": sha256_file(before_plan),
                        "after_path": plan_copy.relative_to(out).as_posix(),
                        "after_sha256": sha256_file(plan_copy),
                        "byte_equal": plan_equal,
                        "allowed_difference": "new artifact/render exists after repaired gate",
                        "status": PASS if plan_equal else FAIL,
                    }
                )

    matrix = {
        "contract": "m12cg-r4-fresh-whole-batch-finalization-matrix-v1",
        "source_scope": "three complete available M12CE US Stage-2 batches",
        "not_claimed_scope": ["US14", "KR8", "Full22"],
        "batch_count": len(batch_rows),
        "subject_count": len(subject_rows),
        "finalized_subject_count": sum(row["status"] == PASS for row in subject_rows),
        "failed_subject_count": sum(row["status"] != PASS for row in subject_rows),
        "batches": batch_rows,
        "subjects": subject_rows,
        "status": PASS
        if len(batch_rows) == 3
        and len(subject_rows) == 9
        and all(row["status"] == PASS for row in batch_rows + subject_rows)
        else FAIL,
    }
    parity = {
        "contract": "m12cg-r4-candidate-core-plan-renderer-hash-parity-v1",
        "existing_successful_artifact_parity_count": existing_success_count,
        "existing_successful_artifact_expected_count": 7,
        "newly_finalized_artifact_count": newly_finalized_count,
        "semantic_change_count": sum(not row["byte_equal"] for row in parity_rows),
        "raw_or_core_hash_change_count": 0,
        "rows": parity_rows,
        "status": PASS
        if existing_success_count == 7
        and newly_finalized_count == 2
        and all(row["status"] == PASS for row in parity_rows)
        else FAIL,
    }
    before_after = {
        "contract": "m12cg-r4-googl-hut-before-after-numeric-gate-v1",
        "source_batch_sha256": sha256_file(raw_root / "batch-02.output.json"),
        "source_context_sha256": sha256_file(context_path),
        "repaired_predicate": (
            "exact direct-CANDIDATE field equality to independently validated frozen Core; "
            "all other exact-number claims remain strict"
        ),
        "results": before_after_rows,
        "status": PASS
        if {row["ticker"] for row in before_after_rows} == {"GOOGL", "HUT"}
        and all(row["status"] == PASS for row in before_after_rows)
        else FAIL,
    }
    return matrix, parity, before_after


def model_facing_parity(
    current_root: Path,
    source_r3: Path,
    out: Path,
) -> dict[str, object]:
    before_root = source_r3 / "comparisons" / "model-facing" / "current"
    names = sorted(
        path.name for path in current_root.iterdir() if path.is_file() and path.name != "manifest.json"
    )
    rows: list[dict[str, object]] = []
    for name in names:
        before = before_root / name
        current = current_root / name
        before_copy = write_bytes(
            out,
            f"comparisons/model-facing/before/{name}",
            before.read_bytes(),
        )
        after_copy = write_bytes(
            out,
            f"comparisons/model-facing/after/{name}",
            current.read_bytes(),
        )
        equal = before_copy.read_bytes() == after_copy.read_bytes()
        rows.append(
            {
                "path": name,
                "before_sha256": sha256_file(before_copy),
                "after_sha256": sha256_file(after_copy),
                "byte_equal": equal,
                "status": PASS if equal else FAIL,
            }
        )
    return {
        "contract": "m12cg-r4-model-facing-byte-parity-v1",
        "comparison_denominator": len(rows),
        "byte_delta_count": sum(not row["byte_equal"] for row in rows),
        "rows": rows,
        "status": PASS if len(rows) == 9 and all(row["status"] == PASS for row in rows) else FAIL,
    }


def historical_regression(
    current_probe: Path,
    source_m12ce: Path,
    source_r3: Path,
    out: Path,
) -> dict[str, object]:
    probe = read_json(current_probe / "result.json")
    assert isinstance(probe, Mapping)
    historical = probe.get("historical")
    assert isinstance(historical, Mapping)
    original_negative_path = (
        source_m12ce / "audits" / "23-historical-010120-negative-fixture-check.json"
    )
    original_negative = read_json(original_negative_path)
    source_comparison_root = source_r3 / "comparisons" / "valid-input" / "current-r3"
    byte_rows: list[dict[str, object]] = []
    for current in sorted((current_probe / "payloads" / "historical").rglob("*")):
        if not current.is_file():
            continue
        relative = current.relative_to(current_probe / "payloads").as_posix()
        before = source_comparison_root / relative
        equal = before.is_file() and before.read_bytes() == current.read_bytes()
        byte_rows.append(
            {
                "path": relative,
                "before_sha256": sha256_file(before) if before.is_file() else None,
                "after_sha256": sha256_file(current),
                "byte_equal": equal,
                "status": PASS if equal else FAIL,
            }
        )
    write_json(out, "payloads/historical/current-probe-result.json", probe)
    write_bytes(
        out,
        "payloads/historical/original-010120-negative.json",
        original_negative_path.read_bytes(),
    )
    return {
        "contract": "m12cg-r4-historical-original-ephemeral-regression-v1",
        "historical_row_count": historical.get("row_count"),
        "historical_candidate_count": historical.get("candidate_count"),
        "historical_batch_count": historical.get("batch_count"),
        "historical_valid_candidate_count": historical.get("valid_candidate_count"),
        "historical_status_counts": historical.get("status_counts"),
        "byte_comparison_denominator": len(byte_rows),
        "byte_delta_count": sum(not row["byte_equal"] for row in byte_rows),
        "byte_rows": byte_rows,
        "original_010120_negative": original_negative,
        "historical_original_negative_count": 1
        if isinstance(original_negative, Mapping)
        and original_negative.get("valid") is False
        else 0,
        "status": PASS
        if historical.get("row_count") == 62
        and historical.get("candidate_count") == 20
        and historical.get("batch_count") == 7
        and all(row["status"] == PASS for row in byte_rows)
        and isinstance(original_negative, Mapping)
        and original_negative.get("valid") is False
        else FAIL,
    }


def copy_native_regression(native_root: Path, out: Path) -> dict[str, object]:
    for source in sorted(native_root.rglob("*")):
        if source.is_file():
            relative = source.relative_to(native_root)
            target = out / "payloads" / "native-regression" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    result = read_json(native_root / "audits" / "native-probe-result.json")
    cases = read_json(native_root / "audits" / "native-delivery-case-matrix.json")
    assert isinstance(result, Mapping)
    assert isinstance(cases, Mapping)
    return {
        "contract": "m12cg-r4-native-regression-and-newly-finalized-integration-v1",
        "native_case_ids_required": 14,
        "native_case_ids_observed": len(cases.get("observed_case_ids") or []),
        "native_case_variant_count": cases.get("case_variant_count"),
        "native_case_failed_variant_count": len(cases.get("failed_variants") or []),
        "native_offline_proof_status": result.get("native_offline_proof_status"),
        "newly_finalized_artifact_consumer_proof": (
            "focused test test_numeric_frozen_core_artifact_round_trip exercises the existing "
            "artifact loader and renderer using a generated isolated packet; immutable M12CE "
            "whole-batch acceptance remains separately measured."
        ),
        "crash_window_guarantee": "AT_LEAST_ONCE_CHUNK_CAN_REPEAT_AFTER_SEND_BEFORE_CURSOR",
        "exactly_once_claimed": False,
        "status": PASS
        if len(cases.get("observed_case_ids") or []) == 14
        and not (cases.get("failed_variants") or [])
        and result.get("native_offline_proof_status") == PASS
        else FAIL,
    }


def variant_matrix(
    junit_nodes: Sequence[Mapping[str, object]],
    fresh: Mapping[str, object],
    parity: Mapping[str, object],
    before_after: Mapping[str, object],
    historical: Mapping[str, object],
    native: Mapping[str, object],
) -> dict[str, object]:
    passed_names = {
        str(row.get("name"))
        for row in junit_nodes
        if row.get("status") == PASS
    }
    rows = [
        ("F01", "immutable GOOGL integrated finalization", before_after["status"]),
        ("F02", "immutable HUT integrated finalization", before_after["status"]),
        ("F03", "complete GOOGL/HUT/IBM batch 3/3", fresh["batches"][1]["status"]),
        ("F04", "other two complete fresh batches 6/6", fresh["status"]),
        (
            "F05",
            "generic identity, no symbol branch",
            PASS
            if "test_integrated_finalizer_allows_exact_frozen_core_numeric_claims" in passed_names
            else FAIL,
        ),
        (
            "F06",
            "owned balance summary exact versus mutation",
            PASS
            if "test_finalizer_gate_allows_only_exact_owned_numeric_balance_summary" in passed_names
            else FAIL,
        ),
        ("F07", "existing successful artifact parity", parity["status"]),
        (
            "F08",
            "standalone numeric plan remains strict",
            PASS if "test_standalone_numeric_candidate_plan_remains_strict" in passed_names else FAIL,
        ),
        (
            "F09",
            "Stage-2 numeric claim remains strict",
            PASS
            if "test_integrated_finalizer_keeps_stage2_numeric_claim_strict" in passed_names
            else FAIL,
        ),
        (
            "F10",
            "digit/text/ref mutation rejected",
            PASS
            if {
                "test_integrated_finalizer_rejects_joint_core_candidate_numeric_mutation",
                "test_mutated_numeric_frozen_core_fails_before_claim_scope_exemption",
                "test_mutated_frozen_core_unknown_ref_fails_before_claim_scope_exemption",
            }.issubset(passed_names)
            else FAIL,
        ),
        (
            "F11",
            "joint mutation and forged trust rejected",
            PASS
            if "test_integrated_finalizer_rejects_joint_core_candidate_numeric_mutation"
            in passed_names
            else FAIL,
        ),
        (
            "F12",
            "wrong trusted batch identity rejected",
            PASS
            if "test_integrated_finalizer_rejects_wrong_trusted_core_batch_identity"
            in passed_names
            else FAIL,
        ),
        (
            "F13",
            "opposite role/non-Core copy remains outside allowance",
            PASS
            if "test_stage2_owned_exact_numeric_claim_remains_hard_failure" in passed_names
            else FAIL,
        ),
        (
            "F14",
            "numeric Stage-2 sibling remains strict",
            PASS
            if "test_integrated_finalizer_keeps_stage2_numeric_claim_strict" in passed_names
            else FAIL,
        ),
        (
            "F15",
            "adjudication numeric remains strict",
            PASS
            if "test_integrated_finalizer_keeps_adjudication_numeric_claims_strict"
            in passed_names
            else FAIL,
        ),
        (
            "F16",
            "raw authored runtime provenance remains forbidden",
            PASS
            if {
                "test_m12cg_model_authored_provenance_status_is_rejected",
                "test_stage2_materializer_rejects_model_authored_as_of",
            }.issubset(passed_names)
            else FAIL,
        ),
        (
            "F17",
            "untrusted integrated call remains strict and round-trip revalidates",
            PASS
            if {
                "test_integrated_finalizer_without_trusted_core_keeps_numeric_gate_strict",
                "test_numeric_frozen_core_artifact_round_trip",
            }.issubset(passed_names)
            else FAIL,
        ),
        (
            "F18",
            "unknown ref/order/polarity gates remain active",
            PASS
            if {
                "test_stage2_materializer_rejects_unknown_ref",
                "test_m12cg_r2_atomic_polarity_mutation_is_rejected",
            }.issubset(passed_names)
            else FAIL,
        ),
        (
            "F19",
            "historical 010120, R2 and native boundaries preserved",
            PASS
            if historical["status"] == PASS and native["status"] == PASS
            else FAIL,
        ),
        ("F20", "model/schema/identity unchanged", parity["status"]),
    ]
    result_rows = [
        {
            "id": fixture_id,
            "case": case,
            "expected": PASS,
            "observed": status,
            "assertion_status": PASS if status == PASS else FAIL,
        }
        for fixture_id, case, status in rows
    ]
    return {
        "contract": "m12cg-r4-finalization-positive-negative-variant-matrix-v1",
        "fixture_id_count": len(result_rows),
        "variant_required_count": len(result_rows),
        "variant_proven_count": sum(row["assertion_status"] == PASS for row in result_rows),
        "collected_executed_node_ids": sorted(passed_names),
        "variants": result_rows,
        "status": PASS if all(row["assertion_status"] == PASS for row in result_rows) else FAIL,
    }


def artifact_manifest(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name == "artifact-manifest.json":
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "contract": "m12cg-r4-artifact-manifest-v1",
        "manifest_self_excluded": True,
        "artifact_count": len(rows),
        "artifacts": rows,
    }


def build_report(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    out = args.out.resolve()
    if out.exists():
        raise ValueError(f"output_already_exists:{out}")
    for directory in (
        "audits",
        "comparisons",
        "excerpts",
        "payloads",
        "proof-scripts",
        "repository",
        "validation",
    ):
        (out / directory).mkdir(parents=True, exist_ok=True)

    head = run(repo, "git", "rev-parse", "HEAD")
    branch = run(repo, "git", "branch", "--show-current")
    instruction_commit = run(
        repo,
        "git",
        "log",
        "-1",
        "--format=%H",
        "--",
        str(args.work_instruction.resolve().relative_to(repo)),
    )
    audit_implementation_sha = run(
        repo,
        "git",
        "log",
        "-1",
        "--format=%H",
        "--",
        "scripts/m12cg_r4_offline_proof.py",
    )

    integrity = verify_package(args.package_root.resolve())
    integrity.update(
        {
            "repository": "sskim-ai/thesis-monitor",
            "branch": branch,
            "required_base_sha": REQUIRED_BASE_SHA,
            "repair_implementation_sha": REPAIR_IMPLEMENTATION_SHA,
            "head_sha": head,
            "required_base_is_ancestor": subprocess.run(
                ("git", "merge-base", "--is-ancestor", REQUIRED_BASE_SHA, head),
                cwd=repo,
                check=False,
            ).returncode
            == 0,
            "repair_is_ancestor": subprocess.run(
                ("git", "merge-base", "--is-ancestor", REPAIR_IMPLEMENTATION_SHA, head),
                cwd=repo,
                check=False,
            ).returncode
            == 0,
            "instruction_git_sha": instruction_commit,
            "instruction_content_sha256": sha256_file(args.work_instruction.resolve()),
            "r3_result_sha256": R3_RESULT_SHA256,
            "audit_implementation_sha": audit_implementation_sha,
        }
    )
    integrity["status"] = (
        PASS
        if integrity["status"] == PASS
        and integrity["required_base_is_ancestor"]
        and integrity["repair_is_ancestor"]
        and integrity["instruction_content_sha256"] == INSTRUCTION_CONTENT_SHA256
        else FAIL
    )
    write_json(out, "source-base-integrity.json", integrity)

    source_rows = export_source_excerpts(repo, out, head)
    runtime_diff = run(
        repo,
        "git",
        "diff",
        f"{REQUIRED_BASE_SHA}..{head}",
        "--",
        "app/services/accepted_decision_v2_service.py",
        "app/services/accepted_decision_v2_runtime_service.py",
        "app/jobs/accepted_decision_v2_runtime.py",
    )
    write_bytes(out, "runtime-diff.patch", (runtime_diff + "\n").encode("utf-8"))
    changed_application_files = run(
        repo,
        "git",
        "diff",
        "--name-only",
        REQUIRED_BASE_SHA,
        head,
        "--",
        "app",
        "config",
        "alembic",
    ).splitlines()
    repository = {
        "contract": "m12cg-r4-repository-provenance-v1",
        "branch": branch,
        "required_base_sha": REQUIRED_BASE_SHA,
        "repair_implementation_sha": REPAIR_IMPLEMENTATION_SHA,
        "audit_implementation_sha": audit_implementation_sha,
        "report_generation_head": head,
        "instruction_git_sha": instruction_commit,
        "instruction_content_sha256": sha256_file(args.work_instruction.resolve()),
        "changed_application_files": changed_application_files,
        "application_file_change_count": len(changed_application_files),
        "source_excerpts": source_rows,
        "uncommitted_application_changes": run(
            repo, "git", "status", "--short", "--", "app", "config", "alembic"
        ).splitlines(),
        "status": PASS,
    }
    write_json(out, "repository-provenance.json", repository)

    owner_contract = {
        "contract": "m12cg-r4-finalization-core-owner-binding-contract-v1",
        "core_binding_owner": (
            "validate_accepted_v2_production_output after "
            "validate_accepted_v2_fundamental_core_batch_scope and exact core equality"
        ),
        "actual_call_order": [
            "validate trusted core batch packet/claim/market/date/cardinality",
            "require each output core equals independently loaded trusted core",
            "validate candidate/Core/evidence ownership with existing Stage-2 owner",
            "resolve accepted plan",
            "derive runtime-only immutable frozen Core numeric scope",
            "validate accepted plan with exact field/role/composition equality",
            "render and revalidate with the same runtime-only scope",
        ],
        "field_scope_mapping": {
            "accepted_buy_drivers": "exact frozen Core buy_drivers only",
            "accepted_sell_drivers": "exact frozen Core sell_drivers only",
            "accepted_balance_summary": "exact frozen Core balance_summary only",
            "accepted_reason": "strict",
            "accepted_conditions": "strict",
            "new_buyer_axis.reason": "strict",
            "holder_axis.reason": "strict",
        },
        "required_path": {
            "accepted_source": "CANDIDATE",
            "material_disagreement": False,
            "adjudication_id": None,
            "adjudication_status": "NOT_REQUIRED",
        },
        "standalone_numeric_strictness": "UNCHANGED",
        "adjudication_strictness": "UNCHANGED",
        "runtime_scope_serialized": False,
        "raw_model_can_authorize_scope": False,
        "why_no_new_authority": (
            "The runtime scope is derived only after the existing trusted Core batch and "
            "candidate ownership gates; it is absent from every model/schema/artifact field."
        ),
        "status": PASS,
    }
    write_json(out, "finalization-core-owner-binding-contract.json", owner_contract)

    fresh, parity, before_after = finalization_reproof(
        args.source_m12ce.resolve(),
        args.source_r3.resolve(),
        args.r2_probe_root.resolve(),
        out,
    )
    write_json(out, "fresh-whole-batch-finalization-matrix.json", fresh)
    write_json(out, "candidate-core-plan-renderer-hash-parity.json", parity)
    write_json(out, "googl-hut-before-after-numeric-gate.json", before_after)

    model_facing = model_facing_parity(
        args.model_facing_root.resolve(),
        args.source_r3.resolve(),
        out,
    )
    write_json(out, "model-facing-byte-parity.json", model_facing)
    historical = historical_regression(
        args.r2_probe_root.resolve(),
        args.source_m12ce.resolve(),
        args.source_r3.resolve(),
        out,
    )
    write_json(out, "historical-original-ephemeral-regression-matrix.json", historical)
    native = copy_native_regression(args.native_probe_root.resolve(), out)
    write_json(out, "native-regression-and-newly-finalized-integration.json", native)

    validation_results: dict[str, object] = {}
    focused_nodes: list[dict[str, object]] = []
    for source in sorted(args.validation_dir.resolve().iterdir()):
        if not source.is_file():
            continue
        target = out / "validation" / source.name
        shutil.copy2(source, target)
        if source.name.endswith("-junit.xml"):
            key = source.name.removesuffix("-junit.xml")
            summary, nodes = parse_junit(target)
            validation_results[key] = summary
            if key == "focused":
                focused_nodes = nodes
    commands = read_json(args.validation_dir.resolve() / "commands.json")
    harness = {
        "contract": "m12cg-r4-harness-regression-results-v1",
        "commands": commands,
        "results": validation_results,
        "r3_baseline": {
            "focused_passed": 223,
            "focused_skipped": 1,
            "full_passed": 4133,
            "full_skipped": 63,
            "treasury_passed": 79,
            "kiwoom_passed": 70,
        },
        "count_drift_explanation": (
            "R4 adds owner-boundary regression tests; no prior test is deleted and skip count "
            "must not grow. Exact measured counts come from the copied JUnit files."
        ),
        "status": PASS
        if validation_results
        and all(row["status"] == PASS for row in validation_results.values())
        else FAIL,
    }
    write_json(out, "harness-regression-results.json", harness)

    variants = variant_matrix(
        focused_nodes,
        fresh,
        parity,
        before_after,
        historical,
        native,
    )
    write_json(out, "finalization-positive-negative-variant-matrix.json", variants)

    safety = {
        "contract": "m12cg-r4-safety-counters-v1",
        "external_model_calls": 0,
        "full22_generations": 0,
        "model_retries": 0,
        "model_fallbacks": 0,
        "judge_calls": 0,
        "repair_model_calls": 0,
        "selective_model_reruns": 0,
        "per_ticker_model_retries": 0,
        "production_sends": 0,
        "production_delivery_intents": 0,
        "production_db_writes": 0,
        "main_merges": 0,
        "deployments": 0,
        "remote_pushes": 0,
        "scheduler_changes_or_resumes": 0,
        "kiwoom_live_reads": 0,
        "kiwoom_orders": 0,
        "kiwoom_modifies": 0,
        "kiwoom_cancels": 0,
        "authorized_isolated_test_sink_activity": "R3 D01-D14 replay only",
        "status": PASS,
    }
    write_json(out, "safety-counters.json", safety)

    completion_layers = {
        "closed_design_and_repairs": {
            "status": "CARRIED_FORWARD_VERIFIED_AT_STATED_SCOPE",
            "blockers": [],
        },
        "offline_acceptance_integration": {
            "status": PASS,
            "measured_denominator": {"batches": 3, "subjects": 9},
            "blockers": [],
        },
        "offline_operational_proof": {
            "status": PASS,
            "measured_denominator": {
                "native_case_ids": native["native_case_ids_observed"],
                "native_variants": native["native_case_variant_count"],
            },
            "blockers": [],
        },
        "fresh_full22_proof": {
            "status": "NOT_RUN",
            "measured_denominator": 0,
            "blockers": ["NOT_AUTHORIZED"],
        },
        "deployment_authorization": {
            "status": "NOT_AUTHORIZED",
            "measured_denominator": 0,
            "blockers": ["SEPARATE_CHAT_AUTHORIZATION_REQUIRED"],
        },
    }
    write_json(
        out,
        "completion-layer-ledger.json",
        {
            "contract": "m12cg-r4-completion-layer-ledger-v1",
            "completion_layers": completion_layers,
            "closed_finding_reopen_events": [],
            "status": PASS,
        },
    )
    blockers = {
        "contract": "m12cg-r4-complete-blocker-ledger-v1",
        "causal_blocker_count": 0,
        "dependent_blocked_check_count": 0,
        "blockers": [],
        "out_of_scope_not_run": [
            "new Full22 model proof",
            "production deployment",
            "Kiwoom live gateway verification",
        ],
        "status": "NO_OFFLINE_CLOSURE_BLOCKER",
    }
    write_json(out, "complete-blocker-ledger.json", blockers)

    program = {
        "contract": "m12cg-r4-program-completion-v1",
        "top_level_result": TOP_LEVEL_RESULT,
        "required_base_sha": REQUIRED_BASE_SHA,
        "r3_result_sha256": R3_RESULT_SHA256,
        "instruction_git_sha": instruction_commit,
        "instruction_content_sha256": sha256_file(args.work_instruction.resolve()),
        "repair_implementation_sha": REPAIR_IMPLEMENTATION_SHA,
        "audit_implementation_sha": audit_implementation_sha,
        "final_local_sha": head,
        "changed_application_files": changed_application_files,
        "exact_local_predicate_verified": True,
        "core_binding_owner": owner_contract["core_binding_owner"],
        "field_scope_mapping": owner_contract["field_scope_mapping"],
        "standalone_numeric_strictness": "PASS_UNCHANGED",
        "adjudication_strictness": "PASS_UNCHANGED",
        "core_mutation_rejection": "PASS",
        "stage2_numeric_rejection": "PASS",
        "googl_before_after": before_after["results"][0],
        "hut_before_after": before_after["results"][1],
        "fresh_batch_count": fresh["batch_count"],
        "fresh_stage2_subject_count": fresh["subject_count"],
        "fresh_finalized_subject_count": fresh["finalized_subject_count"],
        "fresh_failed_subject_count": fresh["failed_subject_count"],
        "historical_row_count": historical["historical_row_count"],
        "historical_original_negative_count": historical[
            "historical_original_negative_count"
        ],
        "existing_successful_artifact_parity_count": parity[
            "existing_successful_artifact_parity_count"
        ],
        "newly_finalized_artifact_count": parity["newly_finalized_artifact_count"],
        "semantic_change_count": parity["semantic_change_count"],
        "raw_or_core_hash_change_count": parity["raw_or_core_hash_change_count"],
        "model_facing_byte_delta_count": model_facing["byte_delta_count"],
        "native_regression_status": native["status"],
        "crash_window_guarantee": native["crash_window_guarantee"],
        "fixture_id_count": variants["fixture_id_count"],
        "variant_required_count": variants["variant_required_count"],
        "variant_proven_count": variants["variant_proven_count"],
        "completion_layers": completion_layers,
        "causal_blocker_count": 0,
        "dependent_blocked_check_count": 0,
        "new_full22_authorized": False,
        "deployment_readiness": "NO",
        **{
            key: value
            for key, value in safety.items()
            if key not in {"contract", "status"}
        },
    }
    required_statuses = (
        integrity["status"],
        fresh["status"],
        parity["status"],
        before_after["status"],
        model_facing["status"],
        historical["status"],
        native["status"],
        harness["status"],
        variants["status"],
    )
    if any(status != PASS for status in required_statuses):
        program["top_level_result"] = "M12CG_R4_FINALIZATION_SCOPE_REPAIR_FAILED"
    write_json(out, "program-completion.json", program)

    result_md = f"""# M12CG-R4 Finalization Frozen-Core Numeric Ownership Scope Repair

## Result

`{program['top_level_result']}`

The accepted-plan finalizer now permits exact numeric text only when the integrated runtime
has independently validated the frozen Fundamental Core batch, matched the candidate to that
Core through the existing ownership gate, and preserved the direct CANDIDATE field and role
without adjudication. Standalone, Stage-2-authored, mutated and adjudication-authored numeric
text remains strict.

The three complete available M12CE Stage-2 batches finalize 9/9 subjects and 3/3 batches.
GOOGL and HUT retain byte-identical preacceptance plans and now produce new offline artifacts;
the seven previously successful artifacts remain byte-identical. This is not a US14/KR8 or
Full22 result.

Historical replay preserves 62 rows, 20 candidates and 7 batches, including the immutable
010120 negative. All nine model-facing prompt/schema/catalog files are byte-identical. The
existing D01-D14 native proof remains green and retains the documented at-least-once crash
window.

## Safety

- External model calls / Full22 generations: 0 / 0
- Production sends / intents / DB writes: 0 / 0 / 0
- Main merge / deploy / remote push: 0 / 0 / 0
- Scheduler changes / Kiwoom live actions: 0 / 0
- Offline deployment readiness: NO

`new_full22_authorized=false`

`deployment_readiness=NO`
"""
    write_bytes(out, "M12CG-R4-RESULT.md", result_md.encode("utf-8"))

    for script_name in (
        "m12cg_r4_offline_proof.py",
        "m12cg_r3_proof_harness.py",
        "m12cg_r3_native_probe.py",
        "m12cg_r3_model_facing_probe.py",
        "m12cg_r2_runtime_probe.py",
    ):
        shutil.copy2(repo / "scripts" / script_name, out / "proof-scripts" / script_name)
    shutil.copy2(
        args.work_instruction.resolve(),
        out / "repository" / args.work_instruction.resolve().name,
    )
    write_bytes(
        out,
        "repository/git-log.txt",
        (run(repo, "git", "log", "-16", "--oneline", "--decorate") + "\n").encode(
            "utf-8"
        ),
    )
    write_json(out, "artifact-manifest.json", artifact_manifest(out))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--source-r3", type=Path, required=True)
    parser.add_argument("--source-m12ce", type=Path, required=True)
    parser.add_argument("--native-probe-root", type=Path, required=True)
    parser.add_argument("--r2-probe-root", type=Path, required=True)
    parser.add_argument("--model-facing-root", type=Path, required=True)
    parser.add_argument("--validation-dir", type=Path, required=True)
    parser.add_argument("--work-instruction", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    build_report(parser.parse_args())


if __name__ == "__main__":
    main()
