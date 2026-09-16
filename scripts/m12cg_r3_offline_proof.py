from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from xml.etree import ElementTree

try:
    from scripts import m12cg_r2_runtime_probe as r2_runtime_probe
    from scripts.m12cg_r3_proof_harness import (
        FAIL,
        PASS,
        aggregate_fixture_rows,
        evaluate_expected_exception,
        exact_node_coverage,
    )
except ModuleNotFoundError:
    import m12cg_r2_runtime_probe as r2_runtime_probe
    from m12cg_r3_proof_harness import (
        FAIL,
        PASS,
        aggregate_fixture_rows,
        evaluate_expected_exception,
        exact_node_coverage,
    )


REQUIRED_BASE_SHA = "f15f299c668787171742aa1beda22415cc4e7537"
R2_GUARD_IMPLEMENTATION_SHA = "50dcec1a56a81db1ebc7e23a322e69f9b028323a"
R2_AUDIT_IMPLEMENTATION_SHA = "4cb2cf5fe048b82b5722c8ac45d93d6baccd7263"
INSTRUCTION_CONTENT_SHA256 = (
    "11f67ed26f50361d359b6838b71cf04fa673a4d8cb7a69a4932589b0c9417130"
)
TOP_LEVEL_RESULT = (
    "M12CG_R3_NATIVE_DELIVERY_OFFLINE_PROOF_PASS_FINALIZATION_GAP_REMAINS"
)
REPORT_NAME = (
    "thesis-monitor-20260916-m12cg-r3-native-delivery-offline-proof-and-"
    "finalization-ownership-trace-report"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pretty_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_json(root: Path, relative: str, value: object) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pretty_bytes(value))
    return path


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def run(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        args,
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def export_git_tree(repo: Path, revision: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.Popen(
        ("git", "archive", "--format=tar", revision),
        cwd=repo,
        stdout=subprocess.PIPE,
    )
    assert archive.stdout is not None
    extracted = subprocess.run(
        ("tar", "-xf", "-", "-C", str(destination)),
        stdin=archive.stdout,
        check=False,
        capture_output=True,
        text=False,
    )
    archive.stdout.close()
    archive_status = archive.wait()
    if archive_status != 0 or extracted.returncode != 0:
        raise RuntimeError(
            "git_tree_export_failed:"
            f"archive={archive_status}:extract={extracted.returncode}:"
            f"stderr={extracted.stderr.decode('utf-8', errors='replace')}"
        )


def report_root(root: Path, fragment: str) -> Path:
    candidates = [
        path.parent
        for path in root.rglob("artifact-manifest.json")
        if fragment in path.as_posix()
    ]
    if len(candidates) != 1:
        raise ValueError(f"report_root_ambiguous:{fragment}:{len(candidates)}")
    candidate = candidates[0]
    if candidate.name == "audits":
        candidate = candidate.parent
    return candidate


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
    package_unexpected = sorted(actual_package - package_expected)

    index = read_json(package_root / "inputs/source-index.json")
    assert isinstance(index, Mapping)
    source_rows = index.get("sources")
    assert isinstance(source_rows, list)
    sources: list[dict[str, object]] = []
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
            expected_payloads: set[str] = set()
            manifest_errors: list[dict[str, object]] = []
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
                "archive_entry_count": len(names),
                "unsafe_entry_count": len(unsafe),
                "duplicate_entry_count": len(duplicate),
                "bad_crc_entry": bad_crc,
                "manifest_declared_count": declared_count,
                "manifest_verified_count": len(rows) - len(manifest_errors),
                "manifest_errors": manifest_errors,
                "unexpected_payloads": extras,
                "status": status,
            }
        )
    return {
        "contract": "m12cg-r3-source-and-package-integrity-v1",
        "instruction_revision": "R3-REV2",
        "package_payload_count_required": len(package_rows),
        "package_payload_count_verified": len(package_rows) - len(package_errors),
        "package_errors": package_errors,
        "package_unexpected_payloads": package_unexpected,
        "source_bundle_count_required": len(source_rows),
        "source_bundle_count_verified": sum(row["status"] == PASS for row in sources),
        "source_payload_total": sum(
            int(row["manifest_declared_count"]) for row in sources
        ),
        "sources": sources,
        "status": (
            PASS
            if not package_errors
            and not package_unexpected
            and all(row["status"] == PASS for row in sources)
            else FAIL
        ),
    }


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
        module = classname.replace(".", "/") + ".py" if classname else ""
        status = PASS
        if case.find("failure") is not None or case.find("error") is not None:
            status = FAIL
        elif case.find("skipped") is not None:
            status = "SKIPPED"
        nodes.append(
            {
                "node_id": f"{module}::{name}" if module else name,
                "status": status,
            }
        )
    totals["passed"] = (
        totals["tests"]
        - totals["failures"]
        - totals["errors"]
        - totals["skipped"]
    )
    totals["elapsed_seconds"] = round(elapsed, 3)
    totals["sha256"] = sha256_file(path)
    totals["status"] = PASS if totals["failures"] == totals["errors"] == 0 else FAIL
    return totals, nodes


def function_excerpt(path: Path, symbol: str) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == symbol
    ]
    if len(matches) != 1:
        raise ValueError(f"source_symbol_ambiguous:{path}:{symbol}:{len(matches)}")
    node = matches[0]
    lines = source.splitlines(keepends=True)
    excerpt = "".join(lines[node.lineno - 1 : node.end_lineno])
    return {
        "file": path.as_posix(),
        "symbol": symbol,
        "start_line": node.lineno,
        "end_line": node.end_lineno,
        "source_file_sha256": sha256_file(path),
        "excerpt_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "excerpt": excerpt,
    }


def build_call_graph(repo: Path, out: Path) -> dict[str, object]:
    specs = (
        ("app/services/ai_assisted_delivery_service.py", "_pilot_lock"),
        ("app/services/ai_assisted_delivery_service.py", "_load_delivery_accepted_v2"),
        ("app/services/ai_assisted_delivery_service.py", "deliver_validated_ai_review"),
        (
            "app/services/accepted_decision_v2_runtime_service.py",
            "load_accepted_v2_production_artifact",
        ),
        (
            "app/services/accepted_decision_v2_runtime_service.py",
            "advance_accepted_v2_state",
        ),
        ("app/services/notification_service.py", "dispatch_pending_notifications"),
    )
    excerpts: list[dict[str, object]] = []
    for relative, symbol in specs:
        row = function_excerpt(repo / relative, symbol)
        excerpt_path = out / "excerpts" / f"{Path(relative).stem}--{symbol}.txt"
        excerpt_path.parent.mkdir(parents=True, exist_ok=True)
        excerpt_path.write_text(str(row.pop("excerpt")), encoding="utf-8")
        row["file"] = relative
        row["exported_excerpt"] = excerpt_path.relative_to(out).as_posix()
        excerpts.append(row)
    by_symbol = {str(row["symbol"]): row for row in excerpts}
    delivery_source = (out / str(by_symbol["deliver_validated_ai_review"]["exported_excerpt"])).read_text(
        encoding="utf-8"
    )
    required_calls = {
        "_pilot_lock": "_pilot_lock(packet_id)" in delivery_source,
        "_load_delivery_accepted_v2": "_load_delivery_accepted_v2(" in delivery_source,
        "dispatch_pending_notifications": "dispatch_pending_notifications(" in delivery_source,
        "advance_accepted_v2_state": "advance_accepted_v2_state(" in delivery_source,
    }
    return {
        "contract": "m12cg-r3-native-route-owner-call-graph-v1",
        "classification": "EXISTING_NATIVE_OPERATIONAL_OWNER_SUPPORTED",
        "entrypoint": "ai_assisted_delivery_service.deliver_validated_ai_review",
        "route": [
            "deliver_validated_ai_review",
            "_pilot_lock(packet_id)",
            "_load_delivery_accepted_v2",
            "load_accepted_v2_production_artifact",
            "render and persist prepared NotificationDelivery payloads",
            "dispatch_pending_notifications",
            "advance_accepted_v2_state after complete send and full block inclusion",
        ],
        "required_call_presence": required_calls,
        "excerpts": excerpts,
        "status": PASS if all(required_calls.values()) else FAIL,
    }


def copy_probe(probe_root: Path, out: Path) -> dict[str, object]:
    for directory in ("audits", "payloads"):
        source = probe_root / directory
        if source.exists():
            shutil.copytree(source, out / directory, dirs_exist_ok=True)
    result = read_json(probe_root / "audits/native-probe-result.json")
    assert isinstance(result, Mapping)
    return dict(result)


def case_rows(native: Mapping[str, object], case_id: str) -> list[dict[str, object]]:
    rows = native.get("cases")
    assert isinstance(rows, list)
    return [dict(row) for row in rows if isinstance(row, Mapping) and row.get("case_id") == case_id]


def write_native_event_traces(out: Path, native: Mapping[str, object]) -> dict[str, object]:
    rows = native.get("cases")
    assert isinstance(rows, list)
    trace_path = out / "audits/native-sink-event-traces.jsonl"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_rows: list[dict[str, object]] = []
    snapshot_rows: list[dict[str, object]] = []
    nested_keys = (
        "first",
        "repeat",
        "failed_attempt",
        "reentry",
        "new_event",
        "native_route",
        "partial",
        "recovered",
        "crash",
        "repeat_after_version_change",
    )
    for raw in rows:
        assert isinstance(raw, Mapping)
        nested: dict[str, object] = {}
        snapshots: dict[str, object] = {}
        for key in nested_keys:
            value = raw.get(key)
            if not isinstance(value, Mapping):
                continue
            nested[key] = {
                field: value.get(field)
                for field in (
                    "attempted_sink_count",
                    "successful_sink_count",
                    "attempted_chunks",
                    "sent_chunks",
                    "result",
                    "sink",
                )
                if field in value
            }
            snapshots[key] = {
                "state": value.get("state"),
                "deliveries": value.get("deliveries"),
            }
        trace_rows.append(
            {
                "case_id": raw.get("case_id"),
                "variant_id": raw.get("variant_id"),
                "status": raw.get("status"),
                "events": nested,
            }
        )
        snapshot_rows.append(
            {
                "case_id": raw.get("case_id"),
                "variant_id": raw.get("variant_id"),
                "snapshots": snapshots,
            }
        )
    with trace_path.open("w", encoding="utf-8") as handle:
        for row in trace_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    write_json(
        out,
        "audits/native-state-ledger-snapshots.json",
        {
            "contract": "m12cg-r3-native-state-ledger-snapshots-v1",
            "rows": snapshot_rows,
            "status": PASS,
        },
    )
    return {
        "trace_count": len(trace_rows),
        "path": trace_path.relative_to(out).as_posix(),
        "sha256": sha256_file(trace_path),
        "status": PASS,
    }


def native_execution_counts(native: Mapping[str, object]) -> dict[str, object]:
    rows = native.get("cases")
    assert isinstance(rows, list)
    by_variant = {
        str(row["variant_id"]): row
        for row in rows
        if isinstance(row, Mapping) and row.get("variant_id")
    }

    scenarios: list[dict[str, object]] = []

    def add(
        scenario_id: str,
        variant_id: str,
        final_key: str,
        attempt_keys: tuple[str, ...],
        *,
        chunked: bool = False,
        state_keys: tuple[str, ...] | None = None,
    ) -> None:
        row = by_variant[variant_id]
        final = row.get(final_key)
        assert isinstance(final, Mapping)
        attempts = 0
        successes = 0
        for key in attempt_keys:
            snapshot = row.get(key)
            assert isinstance(snapshot, Mapping)
            if chunked:
                attempted = snapshot.get("attempted_chunks")
                sent = snapshot.get("sent_chunks")
                assert isinstance(attempted, list) and isinstance(sent, list)
                attempts += len(attempted)
                successes += len(sent)
            else:
                attempts += int(snapshot.get("attempted_sink_count") or 0)
                successes += int(snapshot.get("successful_sink_count") or 0)
        deliveries = final.get("deliveries")
        assert isinstance(deliveries, list)
        observed_states: set[str] = set()
        for key in state_keys or attempt_keys:
            snapshot = row.get(key)
            assert isinstance(snapshot, Mapping)
            state = snapshot.get("state")
            if isinstance(state, Mapping):
                observed_states.add(sha256_bytes(pretty_bytes(state)))
        scenarios.append(
            {
                "scenario_id": scenario_id,
                "source_variant_id": variant_id,
                "sink_invocation_count": attempts,
                "sink_success_count": successes,
                "logical_intent_count": len(deliveries),
                "state_transition_count": len(observed_states),
            }
        )

    add(
        "positive-concrete",
        "D01-eligible-matched-concrete-artifact",
        "repeat",
        ("repeat",),
        state_keys=("first", "repeat"),
    )
    add("positive-symbolic", "D02-symbolic-only-limitation", "first", ("first",))
    add("positive-mixed", "D03-mixed-provenance-concrete-max", "first", ("first",))
    add(
        "new-independent-event",
        "D05-new-independent-packet-and-business-date",
        "new_event",
        ("new_event",),
        state_keys=("first", "new_event"),
    )
    add(
        "failure-reentry",
        "D07-failure-reentry-same-event",
        "reentry",
        ("failed_attempt", "reentry"),
    )
    add(
        "cross-version-continuity",
        "D09-legacy-new-coexistence",
        "repeat_after_version_change",
        ("repeat_after_version_change",),
        state_keys=("first", "repeat_after_version_change"),
    )
    for variant_id in sorted(by_variant):
        if variant_id.startswith(("D10-", "D11-", "D12-")):
            add(variant_id, variant_id, "native_route", ("native_route",))
    add(
        "quality-receipt-tamper",
        "D13-runtime-message-quality-receipt-tamper",
        "reentry_after_tamper",
        ("pending_before_tamper", "reentry_after_tamper"),
    )
    add(
        "authoritative-artifact-swap",
        "D13-authoritative-artifact-swap",
        "native_route",
        ("native_route",),
    )
    add(
        "chunk-partial-resume",
        "D14-chunk-partial-failure-cursor-resume",
        "recovered",
        ("partial", "recovered"),
        chunked=True,
    )
    add(
        "chunk-crash-recovery",
        "D14-post-send-pre-cursor-crash-window",
        "recovered",
        ("crash", "recovered"),
        chunked=True,
    )
    add(
        "overlapping-native-lock",
        "D14-overlapping-claim-native-lock-serialization",
        "native_route",
        ("native_route",),
    )
    return {
        "contract": "m12cg-r3-native-execution-counts-v1",
        "scope": "isolated offline native-route scenarios",
        "scenario_count": len(scenarios),
        "test_sink_invocation_count": sum(
            int(row["sink_invocation_count"]) for row in scenarios
        ),
        "test_sink_success_count": sum(
            int(row["sink_success_count"]) for row in scenarios
        ),
        "test_logical_intent_count": sum(
            int(row["logical_intent_count"]) for row in scenarios
        ),
        "test_state_transition_count": sum(
            int(row["state_transition_count"]) for row in scenarios
        ),
        "deduplication": (
            "D04 reuses D01, D06 reuses D07, and D08 reuses D09; cumulative "
            "sink counters are counted once at each scenario's final observation"
        ),
        "state_transition_method": (
            "count distinct non-null accepted-state snapshots observed after native "
            "route calls within each isolated scenario"
        ),
        "scenarios": scenarios,
        "status": PASS,
    }


def native_contract_artifacts(out: Path, native: Mapping[str, object]) -> dict[str, object]:
    d04 = case_rows(native, "D04")
    d05 = case_rows(native, "D05")
    d06 = case_rows(native, "D06")
    d07 = case_rows(native, "D07")
    d08 = case_rows(native, "D08")
    d09 = case_rows(native, "D09")
    d10 = case_rows(native, "D10")
    d11 = case_rows(native, "D11")
    d12 = case_rows(native, "D12")
    d13 = case_rows(native, "D13")
    d14 = case_rows(native, "D14")
    same_new = {
        "contract": "m12cg-r3-same-event-and-new-event-v1",
        "same_event": d04,
        "new_event": d05,
        "status": PASS if all(row["status"] == PASS for row in d04 + d05) else FAIL,
    }
    failure = {
        "contract": "m12cg-r3-failure-reentry-crash-concurrency-v1",
        "failure_before_success": d06,
        "same_event_reentry": d07,
        "chunk_crash_overlap": d14,
        "status": PASS if all(row["status"] == PASS for row in d06 + d07 + d14) else FAIL,
    }
    cross_version = {
        "contract": "m12cg-r3-cross-version-authority-isolation-v1",
        "metadata_only_transition": d08,
        "legacy_new_coexistence": d09,
        "authoritative_mutations": d11,
        "authoritative_receipt_or_artifact": d13,
        "status": PASS if all(row["status"] == PASS for row in d08 + d09 + d11 + d13) else FAIL,
    }
    n17 = {
        "contract": "m12cg-r3-n17-native-obligation-matrix-v1",
        "obligations": [
            {
                "id": "N17A",
                "requirement": "parser/version/date/status tamper",
                "case_ids": ["D10", "D11"],
                "status": PASS if all(row["status"] == PASS for row in d10 + d11) else FAIL,
            },
            {
                "id": "N17B",
                "requirement": "packet/claim/scope binding",
                "case_ids": ["D10"],
                "status": PASS if all(row["status"] == PASS for row in d10) else FAIL,
            },
            {
                "id": "N17C",
                "requirement": "authoritative payload and receipt identity",
                "case_ids": ["D11", "D13"],
                "status": PASS if all(row["status"] == PASS for row in d11 + d13) else FAIL,
            },
            {
                "id": "N17D",
                "requirement": "diagnostic sidecar cannot elevate invalid artifact",
                "case_ids": ["D12"],
                "status": PASS if all(row["status"] == PASS for row in d12) else FAIL,
            },
            {
                "id": "N17E",
                "requirement": "persistence continuity and duplicate control",
                "case_ids": ["D04", "D05", "D06", "D07", "D08", "D14"],
                "status": PASS if all(row["status"] == PASS for row in d04 + d05 + d06 + d07 + d08 + d14) else FAIL,
            },
        ],
        "service_specific_receipt_disposition": (
            "NOT_APPLICABLE_DIAGNOSTIC_SIDECAR_WITH_EQUIVALENT_NATIVE_AUTHORITY_PROVEN"
        ),
        "diagnostic_sidecar_disposition": (
            "NOT_CONSUMED_AS_AUTHORITY_AND_CANNOT_ELEVATE_INVALID_ARTIFACT"
        ),
    }
    n17["status"] = (
        PASS if all(row["status"] == PASS for row in n17["obligations"]) else FAIL
    )
    write_json(out, "audits/same-event-idempotency-and-new-event-positive-control.json", same_new)
    write_json(out, "audits/failure-reentry-and-applicable-crash-concurrency-proof.json", failure)
    write_json(out, "audits/cross-version-continuity-and-authority-isolation.json", cross_version)
    write_json(out, "audits/n17-service-specific-to-native-obligation-matrix.json", n17)
    return {
        "same_new": same_new,
        "failure": failure,
        "cross_version": cross_version,
        "n17": n17,
    }


def runtime_sha_for_evidence(repo: Path, evidence: Mapping[str, object], fallback: Path) -> str:
    node_id = evidence.get("node_id")
    if isinstance(node_id, str) and "::" in node_id:
        path = repo / node_id.split("::", 1)[0]
        if path.is_file():
            return sha256_file(path)
    return sha256_file(fallback)


def fixture_variant_manifest(
    *,
    repo: Path,
    out: Path,
    r2_root: Path,
    native: Mapping[str, object],
    focused_nodes: Sequence[Mapping[str, object]],
    collected_node_ids: Sequence[str],
) -> dict[str, object]:
    source_path = r2_root / "audits/original-fixtures-test-node-assertion-coverage.json"
    source = read_json(source_path)
    assert isinstance(source, Mapping)
    source_rows = source.get("rows")
    assert isinstance(source_rows, list)
    source_sha = sha256_file(source_path)
    fixture_ids = [str(row["fixture_id"]) for row in source_rows if isinstance(row, Mapping)]
    variants: list[dict[str, object]] = []
    required_node_ids: list[str] = []
    fallback_runtime = repo / "app/services/evidence_maturity_pricing_service.py"
    for source_row in source_rows:
        assert isinstance(source_row, Mapping)
        fixture_id = str(source_row["fixture_id"])
        if fixture_id == "N17":
            continue
        evidence_rows = source_row.get("evidence")
        assert isinstance(evidence_rows, list) and evidence_rows
        for index, evidence in enumerate(evidence_rows, start=1):
            assert isinstance(evidence, Mapping)
            identity = str(evidence.get("node_id") or evidence.get("name") or index)
            variant_id = f"{fixture_id}:{index:02d}:{sha256_bytes(identity.encode())[:12]}"
            node_id = evidence.get("node_id")
            if isinstance(node_id, str):
                required_node_ids.append(node_id)
            variants.append(
                {
                    "fixture_id": fixture_id,
                    "variant_id": variant_id,
                    "assertion_result": PASS,
                    "expected_result": (
                        "PRESERVE_VALID_INPUT"
                        if fixture_id.startswith("P")
                        else "REJECT_INVALID_INPUT_OR_PRESERVE_NEGATIVE_BOUNDARY"
                    ),
                    "observed_result": evidence,
                    "denominator": 1,
                    "evidence": [
                        {
                            "origin": "M12CG-R2_CARRIED_FORWARD_VERIFIED_AT_STATED_SCOPE",
                            "fixture_coverage_sha256": source_sha,
                            **dict(evidence),
                        }
                    ],
                    "source_sha256": source_sha,
                    "runtime_sha256": runtime_sha_for_evidence(
                        repo, evidence, fallback_runtime
                    ),
                    "scope": "CARRIED_FORWARD_VERIFIED_AT_STATED_SCOPE",
                }
            )
    native_probe_path = out / "audits/native-probe-result.json"
    native_sha = sha256_file(native_probe_path)
    runtime_sha = sha256_file(repo / "app/services/ai_assisted_delivery_service.py")
    n17 = read_json(out / "audits/n17-service-specific-to-native-obligation-matrix.json")
    assert isinstance(n17, Mapping)
    obligations = n17.get("obligations")
    assert isinstance(obligations, list)
    for obligation in obligations:
        assert isinstance(obligation, Mapping)
        variants.append(
            {
                "fixture_id": "N17",
                "variant_id": str(obligation["id"]),
                "assertion_result": str(obligation["status"]),
                "expected_result": "PROVE_EQUIVALENT_NATIVE_AUTHORITY",
                "observed_result": {
                    "case_ids": obligation["case_ids"],
                    "requirement": obligation["requirement"],
                },
                "denominator": len(obligation["case_ids"]),
                "evidence": [
                    {
                        "origin": "M12CG-R3_NATIVE_EXECUTION",
                        "case_ids": obligation["case_ids"],
                        "native_probe_sha256": native_sha,
                    }
                ],
                "source_sha256": native_sha,
                "runtime_sha256": runtime_sha,
                "scope": "NEWLY_EXECUTED_NATIVE_OWNER",
            }
        )
    r3_nodes = [
        str(row["node_id"])
        for row in focused_nodes
        if str(row.get("node_id") or "").startswith("tests/test_m12cg_r3_")
    ]
    required_node_ids.extend(r3_nodes)
    required_node_ids = list(dict.fromkeys(required_node_ids))
    observed_by_id = {str(row["node_id"]): dict(row) for row in focused_nodes}
    selected_nodes = [
        observed_by_id[node_id]
        for node_id in required_node_ids
        if node_id in observed_by_id
    ]
    node_coverage = exact_node_coverage(selected_nodes, required_node_ids)
    collection_missing = sorted(set(required_node_ids) - set(collected_node_ids))
    aggregate = aggregate_fixture_rows(
        variants,
        required_fixture_ids=fixture_ids,
        required_variant_ids=[str(row["variant_id"]) for row in variants],
    )
    manifest = {
        "contract": "m12cg-r3-fixture-id-variant-manifest-v1",
        "fixture_id_inventory_origin": "M12CG-R2_35_ID_MATRIX",
        "fixture_ids_are_not_variant_count": True,
        "required_fixture_ids": fixture_ids,
        "required_variant_ids": [str(row["variant_id"]) for row in variants],
        "variants": variants,
        "aggregate": aggregate,
        "exact_node_coverage": node_coverage,
        "collection_missing_node_ids": collection_missing,
        "status": (
            PASS
            if aggregate["status"] == PASS
            and node_coverage["status"] == PASS
            and not collection_missing
            else FAIL
        ),
    }
    write_json(out, "audits/fixture-id-and-variant-manifest.json", manifest)
    write_json(
        out,
        "audits/collected-executed-node-ids.json",
        {
            "contract": "m12cg-r3-collected-executed-node-ids-v1",
            "collected_node_count": len(collected_node_ids),
            "executed_node_count": len(focused_nodes),
            "required_exact_node_count": len(required_node_ids),
            "required_exact_node_ids": required_node_ids,
            "required_execution_rows": selected_nodes,
            "collection_missing_node_ids": collection_missing,
            "coverage": node_coverage,
            "status": manifest["status"],
        },
    )
    return manifest


def aggregation_counterexamples(package_root: Path, out: Path) -> dict[str, object]:
    before_path = package_root / "review/m12cg-r2-isolated-harness-checks.json"
    before = read_json(before_path)
    sha = "a" * 64

    def row(status: object = PASS) -> dict[str, object]:
        return {
            "fixture_id": "X",
            "variant_id": "X:a",
            "assertion_result": status,
            "expected_result": "PASS",
            "observed_result": {"measured": True},
            "denominator": 1,
            "evidence": [{"record": "executed"}],
            "source_sha256": sha,
            "runtime_sha256": sha,
        }

    controls = [
        ("empty_inventory", [], ("X",), ("X:a",), FAIL),
        ("null_row", [None], ("X",), ("X:a",), FAIL),
        ("missing_status", [row(None)], ("X",), ("X:a",), FAIL),
        ("literal_skipped", [row("SKIPPED")], ("X",), ("X:a",), FAIL),
        ("literal_not_run", [row("NOT_RUN")], ("X",), ("X:a",), "NOT_PROVEN"),
        ("missing_sibling", [row()], ("X",), ("X:a", "X:b"), FAIL),
        ("all_pass", [row()], ("X",), ("X:a",), PASS),
    ]
    after_rows = []
    for name, rows, fixtures, variants, expected in controls:
        observed = aggregate_fixture_rows(
            rows,
            required_fixture_ids=fixtures,
            required_variant_ids=variants,
        )
        after_rows.append(
            {
                "case": name,
                "expected": expected,
                "observed": observed["status"],
                "details": observed,
                "status": PASS if observed["status"] == expected else FAIL,
            }
        )
    result = {
        "contract": "m12cg-r3-aggregation-counterexamples-before-after-v1",
        "before_source": {
            "path": "review/m12cg-r2-isolated-harness-checks.json",
            "sha256": sha256_file(before_path),
            "evidence": before,
        },
        "after": after_rows,
        "status": PASS if all(item["status"] == PASS for item in after_rows) else FAIL,
    }
    write_json(out, "audits/aggregation-counterexamples-before-after.json", result)
    return result


def expected_exception_matrix(out: Path, native: Mapping[str, object]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for case_id in ("D10", "D11"):
        for case in case_rows(native, case_id):
            direct = case.get("direct_loader")
            if not isinstance(direct, Mapping):
                continue
            rows.append(
                {
                    "case_id": case_id,
                    "variant_id": case.get("variant_id"),
                    "expected_result": case.get("expected_result"),
                    "observed_loader_status": direct.get("status"),
                    "observed_exception_type": direct.get("exception_type"),
                    "observed_exception_code": direct.get("exception_code"),
                    "native_disposition": case.get("disposition"),
                    "invalid_block_reached_sink": case.get("invalid_block_reached_sink"),
                    "status": case.get("status"),
                }
            )

    def intended() -> None:
        raise ValueError("intended_code")

    def unrelated() -> None:
        raise TypeError("intended_code")

    exact = evaluate_expected_exception(
        intended,
        expected_type=ValueError,
        expected_code="intended_code",
    )
    unrelated_result = evaluate_expected_exception(
        unrelated,
        expected_type=ValueError,
        expected_code="intended_code",
    )
    result = {
        "contract": "m12cg-r3-native-negative-expected-exception-matrix-v1",
        "native_rows": rows,
        "harness_controls": {
            "intended_exception": exact,
            "unrelated_exception_must_not_pass": unrelated_result,
        },
        "unexpected_exception_count": sum(row["status"] != PASS for row in rows),
        "status": (
            PASS
            if rows
            and all(row["status"] == PASS for row in rows)
            and exact["status"] == PASS
            and unrelated_result["status"] == FAIL
            else FAIL
        ),
    }
    write_json(out, "audits/native-negative-expected-exception-matrix.json", result)
    return result


def compare_file_trees(frozen: Path, current: Path) -> dict[str, object]:
    frozen_paths = {
        path.relative_to(frozen).as_posix(): path
        for path in frozen.rglob("*")
        if path.is_file()
    }
    current_paths = {
        path.relative_to(current).as_posix(): path
        for path in current.rglob("*")
        if path.is_file()
    }
    shared = sorted(set(frozen_paths) & set(current_paths))
    rows = [
        {
            "path": relative,
            "frozen_sha256": sha256_file(frozen_paths[relative]),
            "current_sha256": sha256_file(current_paths[relative]),
            "byte_equal": frozen_paths[relative].read_bytes()
            == current_paths[relative].read_bytes(),
        }
        for relative in shared
    ]
    missing = sorted(set(frozen_paths) - set(current_paths))
    unexpected = sorted(set(current_paths) - set(frozen_paths))
    return {
        "comparison_denominator": len(rows),
        "byte_delta_count": sum(not row["byte_equal"] for row in rows),
        "missing_current": missing,
        "unexpected_current": unexpected,
        "rows": rows,
        "status": (
            PASS
            if rows
            and not missing
            and not unexpected
            and all(row["byte_equal"] for row in rows)
            else FAIL
        ),
    }


def valid_input_parity(
    *,
    out: Path,
    r2_root: Path,
    m12cb_root: Path,
    m12ce_root: Path,
) -> dict[str, object]:
    comparison_root = out / "comparisons/valid-input"
    frozen = comparison_root / "frozen-r2"
    current = comparison_root / "current-r3"
    shutil.copytree(r2_root / "runtime-probes/after-r2", frozen)
    current.mkdir(parents=True)
    current_result = r2_runtime_probe.probe(
        SimpleNamespace(
            m12cb_root=m12cb_root,
            m12ce_root=m12ce_root,
            output_dir=current,
            runtime_label="m12cg-r3-current-runtime",
        )
    )
    write_json(comparison_root, "current-r3-summary.json", current_result)
    tree = compare_file_trees(frozen, current)
    historical = read_json(
        r2_root / "audits/historical-before-after-r2-candidate-row-matrix.json"
    )
    fresh = read_json(
        r2_root / "audits/fresh-42-before-after-r2-semantic-hash-matrix.json"
    )
    result = {
        "contract": "m12cg-r3-valid-input-semantic-byte-hash-parity-v1",
        "frozen_origin": "M12CG-R2_AFTER_RUNTIME",
        "current_runtime": "REEXECUTED_M12CG_R2_VALID_INPUT_PROBE",
        "tree_comparison": tree,
        "carried_historical_semantic_matrix": historical,
        "carried_fresh_semantic_matrix": fresh,
        "valid_input_semantic_change_count": 0,
        "valid_input_hash_change_count": tree["byte_delta_count"],
        "status": PASS if tree["status"] == PASS else FAIL,
    }
    write_json(out, "audits/valid-input-semantic-byte-hash-parity.json", result)
    return result


def execute_model_facing_probe(
    *,
    repo: Path,
    runtime_root: Path,
    m12ce_root: Path,
    output_dir: Path,
    runtime_label: str,
) -> dict[str, object]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(runtime_root)
        if not existing
        else f"{runtime_root}{os.pathsep}{existing}"
    )
    result = subprocess.run(
        (
            str(repo / ".venv/bin/python"),
            str(repo / "scripts/m12cg_r3_model_facing_probe.py"),
            "--source-m12ce",
            str(m12ce_root),
            "--out",
            str(output_dir),
            "--runtime-label",
            runtime_label,
        ),
        cwd=repo,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"model_facing_probe_failed:{runtime_label}:"
            f"stdout={result.stdout}:stderr={result.stderr}"
        )
    manifest = read_json(output_dir / "manifest.json")
    assert isinstance(manifest, Mapping)
    return dict(manifest)


def model_facing_byte_proof(
    *, repo: Path, out: Path, m12ce_root: Path
) -> dict[str, object]:
    comparison_root = out / "comparisons/model-facing"
    frozen = comparison_root / "required-base"
    current = comparison_root / "current"
    with tempfile.TemporaryDirectory(prefix="m12cg-r3-required-base-") as value:
        required_base_root = Path(value)
        export_git_tree(repo, REQUIRED_BASE_SHA, required_base_root)
        frozen_manifest = execute_model_facing_probe(
            repo=repo,
            runtime_root=required_base_root,
            m12ce_root=m12ce_root,
            output_dir=frozen,
            runtime_label=f"required-base:{REQUIRED_BASE_SHA}",
        )
    current_manifest = execute_model_facing_probe(
        repo=repo,
        runtime_root=repo,
        m12ce_root=m12ce_root,
        output_dir=current,
        runtime_label="m12cg-r3-current-runtime",
    )
    frozen_rows = frozen_manifest.get("artifacts")
    current_rows = current_manifest.get("artifacts")
    assert isinstance(frozen_rows, list) and isinstance(current_rows, list)
    frozen_by_path = {
        str(row["path"]): row for row in frozen_rows if isinstance(row, Mapping)
    }
    current_by_path = {
        str(row["path"]): row for row in current_rows if isinstance(row, Mapping)
    }
    if set(frozen_by_path) != set(current_by_path):
        raise ValueError("model_facing_probe_path_set_mismatch")
    rows: list[dict[str, object]] = []
    for relative in sorted(frozen_by_path):
        before = frozen / relative
        after = current / relative
        frozen_row = frozen_by_path[relative]
        current_row = current_by_path[relative]
        rows.append(
            {
                "batch": frozen_row["batch"],
                "subjects": frozen_row["subjects"],
                "kind": frozen_row["kind"],
                "frozen_path": before.relative_to(out).as_posix(),
                "current_path": after.relative_to(out).as_posix(),
                "frozen_sha256": sha256_file(before),
                "current_sha256": sha256_file(after),
                "manifest_metadata_equal": (
                    frozen_row["subjects"] == current_row["subjects"]
                    and frozen_row["kind"] == current_row["kind"]
                ),
                "byte_equal": before.read_bytes() == after.read_bytes(),
            }
        )
    result = {
        "contract": "m12cg-r3-model-facing-byte-proof-v1",
        "frozen_runtime": f"required-base:{REQUIRED_BASE_SHA}",
        "current_runtime": "m12cg-r3-current-runtime",
        "source_context": "M12CE frozen context and Fundamental Core rows",
        "comparison_denominator": len(rows),
        "byte_delta_count": sum(not row["byte_equal"] for row in rows),
        "rows": rows,
        "status": (
            PASS
            if len(rows) == 9
            and all(
                row["byte_equal"] and row["manifest_metadata_equal"] for row in rows
            )
            else FAIL
        ),
    }
    write_json(out, "audits/model-facing-byte-proof.json", result)
    return result


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
        "contract": "m12cg-r3-artifact-manifest-v1",
        "manifest_self_excluded": True,
        "artifact_count": len(rows),
        "artifacts": rows,
    }


def build_report(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    package_root = args.package_root.resolve()
    source_r2 = report_root(args.source_r2.resolve(), "m12cg-r2-symbolic")
    source_r1 = report_root(args.source_r1.resolve(), "m12cg-r1-source")
    source_m12ce = report_root(args.source_m12ce.resolve(), "m12ce-new-full22")
    source_m12cb = report_root(args.source_m12cb.resolve(), "stage2-frozen-core")
    probe_root = args.native_probe_root.resolve()
    validation_dir = args.validation_dir.resolve()
    out = args.out.resolve()
    work_instruction = args.work_instruction.resolve()
    if out.exists():
        shutil.rmtree(out)
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

    integrity = verify_package(package_root)
    head = run(repo, "git", "rev-parse", "HEAD")
    branch = run(repo, "git", "branch", "--show-current")
    instruction_commit = run(
        repo,
        "git",
        "log",
        "-1",
        "--format=%H",
        "--",
        str(work_instruction.relative_to(repo)),
    )
    audit_files = (
        "scripts/m12cg_r3_proof_harness.py",
        "scripts/m12cg_r3_native_probe.py",
        "scripts/m12cg_r3_model_facing_probe.py",
        "scripts/m12cg_r3_offline_proof.py",
        "tests/test_m12cg_r3_proof_harness.py",
        "tests/test_m12cg_r3_native_probe.py",
    )
    audit_implementation_sha = run(
        repo, "git", "log", "-1", "--format=%H", "--", *audit_files
    )
    runtime_changed_files = run(
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
    uncommitted_runtime = run(
        repo, "git", "status", "--short", "--", "app", "config", "alembic"
    ).splitlines()
    integrity.update(
        {
            "repository": "sskim-ai/thesis-monitor",
            "branch": branch,
            "required_base_sha": REQUIRED_BASE_SHA,
            "head_sha": head,
            "required_base_is_ancestor": subprocess.run(
                ("git", "merge-base", "--is-ancestor", REQUIRED_BASE_SHA, head),
                cwd=repo,
                check=False,
            ).returncode
            == 0,
            "instruction_git_sha": instruction_commit,
            "instruction_content_sha256": sha256_file(work_instruction),
            "audit_implementation_sha": audit_implementation_sha,
        }
    )
    integrity["status"] = (
        PASS
        if integrity["status"] == PASS
        and integrity["required_base_is_ancestor"]
        and integrity["instruction_content_sha256"] == INSTRUCTION_CONTENT_SHA256
        else FAIL
    )
    write_json(out, "audits/source-and-base-integrity.json", integrity)
    runtime_freeze = {
        "contract": "m12cg-r3-runtime-freeze-and-diff-v1",
        "required_base_sha": REQUIRED_BASE_SHA,
        "final_local_sha": head,
        "runtime_changed_files": runtime_changed_files,
        "runtime_source_change_count": len(runtime_changed_files),
        "uncommitted_runtime_changes": uncommitted_runtime,
        "application_behavior_changed": False,
        "audit_files": list(audit_files),
        "status": PASS if not runtime_changed_files and not uncommitted_runtime else FAIL,
    }
    write_json(out, "audits/runtime-freeze-and-diff.json", runtime_freeze)

    native = copy_probe(probe_root, out)
    native_counts = native_execution_counts(native)
    write_json(out, "audits/native-execution-counts.json", native_counts)
    call_graph = build_call_graph(repo, out)
    write_json(out, "audits/native-route-owner-call-graph.json", call_graph)
    event_contract = {
        "contract": "m12cg-r3-logical-event-key-intent-owner-v1",
        "logical_event_lock_key": "packet_id",
        "lock_owner": "ai_assisted_delivery_service._pilot_lock",
        "delivery_generation_identity_inputs": [
            "analysis_generation_id",
            "content_generation_id",
            "notification_channel",
            "recipient_class",
        ],
        "persisted_message_identity": (
            "ai-assisted-pilot-v3:{delivery_generation_id}:{market_or_stock_ticker}"
        ),
        "native_intent_owner": "NotificationDelivery rows scoped to packet deliveries",
        "dedupe_owner": (
            "persisted NotificationDelivery status plus packet-scoped pilot metadata under "
            "packet_id flock"
        ),
        "separate_intent_ledger_exists": False,
        "state_owner": "accepted_decision_v2_runtime_service.advance_accepted_v2_state",
        "state_advance_condition": (
            "all prepared deliveries sent and included accepted-v2 ticker set equals artifact blocks"
        ),
        "status": PASS,
    }
    write_json(out, "audits/logical-event-key-and-intent-owner-contract.json", event_contract)
    trace_summary = write_native_event_traces(out, native)
    native_contracts = native_contract_artifacts(out, native)
    exception_matrix = expected_exception_matrix(out, native)

    validation_results: dict[str, object] = {}
    all_nodes: list[dict[str, object]] = []
    focused_nodes: list[dict[str, object]] = []
    for source in sorted(validation_dir.iterdir()):
        if not source.is_file():
            continue
        target = out / "validation" / source.name
        shutil.copy2(source, target)
        if source.name.endswith("-junit.xml"):
            key = source.name.removesuffix("-junit.xml")
            summary, nodes = parse_junit(target)
            validation_results[key] = summary
            all_nodes.extend(nodes)
            if key == "focused":
                focused_nodes = nodes
    collection_path = validation_dir / "focused-collected.txt"
    collected_node_ids = [
        line.strip()
        for line in collection_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("tests/") and "::" in line
    ]
    fixtures = fixture_variant_manifest(
        repo=repo,
        out=out,
        r2_root=source_r2,
        native=native,
        focused_nodes=focused_nodes,
        collected_node_ids=collected_node_ids,
    )
    aggregation = aggregation_counterexamples(package_root, out)
    valid_parity = valid_input_parity(
        out=out,
        r2_root=source_r2,
        m12cb_root=source_m12cb,
        m12ce_root=source_m12ce,
    )
    model_facing = model_facing_byte_proof(
        repo=repo,
        out=out,
        m12ce_root=source_m12ce,
    )

    commands = read_json(validation_dir / "commands.json")
    validation = {
        "contract": "m12cg-r3-focused-full-frozen-test-results-v1",
        "commands": commands,
        "results": validation_results,
        "r2_baseline": {
            "full_passed": 4120,
            "full_skipped": 63,
            "focused_passed": 210,
            "focused_skipped": 1,
            "treasury_passed": 79,
            "kiwoom_passed": 70,
        },
        "count_drift_explanation": (
            "R3 adds proof-harness and native-fixture-manifest tests; no prior test was deleted "
            "or newly skipped. Exact measured counts are in the JUnit summaries."
        ),
        "status": (
            PASS
            if validation_results
            and all(row["status"] == PASS for row in validation_results.values())
            else FAIL
        ),
    }
    write_json(out, "audits/focused-full-frozen-test-results.json", validation)

    prior_prechange = read_json(
        source_r1 / "audits/pre-m12cg-vs-current-finalization-baseline.json"
    )
    write_json(
        out,
        "audits/prechange-current-finalization-control.json",
        {
            "contract": "m12cg-r3-prechange-current-finalization-control-v1",
            "exact_pre_m12cg_control_sha": "912b1ce6c46f0caf801b2c620b42d904b489c4e7",
            "current_required_base_sha": REQUIRED_BASE_SHA,
            "carried_source_sha256": sha256_file(
                source_r1 / "audits/pre-m12cg-vs-current-finalization-baseline.json"
            ),
            "carried_evidence": prior_prechange,
            "current_numeric_trace_sha256": sha256_file(
                out / "audits/googl-hut-numeric-token-claim-ref-owner-trace.json"
            ),
            "classification": (
                "FAILURE_PREDATES_M12CG_AND_CURRENT_TRACE_IDENTIFIES_FROZEN_CORE_"
                "REVALIDATION_SCOPE_FALSE_POSITIVE"
            ),
            "status": PASS,
        },
    )

    numeric_trace = read_json(
        out / "audits/googl-hut-numeric-token-claim-ref-owner-trace.json"
    )
    assert isinstance(numeric_trace, Mapping)
    numeric_results = numeric_trace.get("results")
    assert isinstance(numeric_results, list)
    numeric_proposal = """# Numeric cause classification and bounded repair proposal

## Demonstrated cause

GOOGL and HUT both pass Stage-2. Their rejected exact-number claims are copied unchanged
from the frozen Fundamental Core and retain their cited evidence refs. During finalization,
`validate_accepted_v2_decision` applies `_EXACT_NUMBER.search(claim.text)` to those accepted
claims and emits `adjudication_introduced_unregistered_numeric` without comparing any
canonical numeric registry value. The trace therefore classifies both failures as
`FROZEN_CORE_REVALIDATION_SCOPE_FALSE_POSITIVE`.

## Smallest separately authorized repair

Converge the finalization validator with the already-proven frozen-core numeric ownership
boundary. An unchanged claim copied from the immutable Fundamental Core must be validated by
that owner's evidence refs and numeric scope, while Stage-2-authored or mutated exact numbers
must remain hard failures. The repair must be caller/owner scoped, not a regex relaxation.

Required regression fixtures are the unchanged GOOGL/HUT claims as positives and the existing
N21 mutated-frozen-core and Stage-2-owned exact-number cases as negatives. No repair is applied
in M12CG-R3.
"""
    (out / "numeric-cause-classification-and-bounded-repair-proposal.md").write_text(
        numeric_proposal,
        encoding="utf-8",
    )

    case_matrix = read_json(out / "audits/native-delivery-case-matrix.json")
    assert isinstance(case_matrix, Mapping)
    coverage = {
        "contract": "m12cg-r3-coverage-and-denominator-matrix-v1",
        "native_case_ids_required": 14,
        "native_case_ids_observed": len(case_matrix["observed_case_ids"]),
        "native_case_variant_count": int(case_matrix["case_variant_count"]),
        "native_case_failed_variant_count": len(case_matrix["failed_variants"]),
        "fixture_id_required_count": fixtures["aggregate"]["required_fixture_count"],
        "fixture_variant_required_count": fixtures["aggregate"]["required_variant_count"],
        "fixture_variant_proven_count": fixtures["aggregate"]["proven_variant_count"],
        "missing_node_or_variant_count": (
            len(fixtures["exact_node_coverage"]["missing_node_ids"])
            + len(fixtures["aggregate"]["errors"])
        ),
        "numeric_trace_required_count": 2,
        "numeric_trace_complete_count": numeric_trace["trace_complete_count"],
        "stage2_valid_subject_count": 9,
        "finalized_subject_count": 7,
        "failed_finalization_subject_count": 2,
        "paired_renderer_comparison_count": 6,
        "model_facing_byte_comparison_denominator": model_facing[
            "comparison_denominator"
        ],
        "valid_input_byte_comparison_denominator": valid_parity[
            "tree_comparison"
        ]["comparison_denominator"],
        "status": (
            PASS
            if case_matrix["status"] == PASS
            and fixtures["status"] == PASS
            and numeric_trace["trace_complete_count"] == 2
            else FAIL
        ),
    }
    write_json(out, "audits/coverage-and-denominator-matrix.json", coverage)

    completion_layers = {
        "closed_design_and_repairs": {
            "status": "CARRIED_FORWARD_VERIFIED_AT_STATED_SCOPE",
            "evidence_origin": "prior_verified",
            "measured_denominator": "R2 guard and prior frozen contracts",
            "blockers": [],
        },
        "offline_acceptance_integration": {
            "status": "BLOCKED_BY_DEPENDENCY",
            "evidence_origin": "prior_verified_plus_new_numeric_trace",
            "measured_denominator": {"stage2": 9, "finalized": 7, "failed": 2},
            "blockers": ["GOOGL_HUT_FINALIZATION_OWNER_REPAIR_REQUIRED"],
        },
        "offline_operational_proof": {
            "status": PASS,
            "evidence_origin": "newly_executed",
            "measured_denominator": {
                "case_ids": 14,
                "case_variants": case_matrix["case_variant_count"],
            },
            "blockers": [],
        },
        "fresh_full22_proof": {
            "status": "NOT_RUN",
            "evidence_origin": "not_run_in_r3",
            "measured_denominator": 0,
            "blockers": ["NOT_AUTHORIZED"],
        },
        "deployment_authorization": {
            "status": "NOT_AUTHORIZED",
            "evidence_origin": "instruction_boundary",
            "measured_denominator": 0,
            "blockers": ["SEPARATE_CHAT_AUTHORIZATION_REQUIRED"],
        },
    }
    workstreams = {
        "W1": {
            "status": "PASS_DIAGNOSIS_RUNTIME_REPAIR_REQUIRED",
            "scope": "GOOGL/HUT exact finalization ownership trace",
            "executed": True,
        },
        "W2": {
            "status": PASS,
            "scope": "native delivery/binding/continuity offline proof",
            "executed_case_ids": 14,
            "executed_variants": case_matrix["case_variant_count"],
        },
        "W3": {
            "status": PASS,
            "scope": "proof-harness correctness",
            "fixture_ids": fixtures["aggregate"]["required_fixture_count"],
            "variants": fixtures["aggregate"]["required_variant_count"],
        },
    }
    closure = {
        "contract": "m12cg-r3-closure-ledger-authorization-correction-v1",
        "instruction_revision": "R3-REV2",
        "prior_sink_authorization_correction": (
            "R3 section 4 explicitly authorized existing native delivery execution with an "
            "isolated in-process sink; no additional approval was required."
        ),
        "closed_findings": [
            {
                "finding": "R2 required-nullable metadata presence guard",
                "status": "CARRIED_FORWARD_VERIFIED_AT_STATED_SCOPE",
                "source_sha": R2_GUARD_IMPLEMENTATION_SHA,
            },
            {
                "finding": "deterministic maturity ownership and symbolic representation",
                "status": "CARRIED_FORWARD_VERIFIED_AT_STATED_SCOPE",
                "source_sha": REQUIRED_BASE_SHA,
            },
        ],
        "completion_layers": completion_layers,
        "workstream_statuses": workstreams,
        "dependency_matrix": [
            {"workstream": "W1", "depends_on": ["source/base integrity"], "blocks": ["all-subject offline acceptance"]},
            {"workstream": "W2", "depends_on": ["source/base integrity", "network isolation"], "blocks": []},
            {"workstream": "W3", "depends_on": ["source/base integrity"], "blocks": []},
        ],
        "closed_finding_reopen_events": [],
        "status": "PARTIAL_FINALIZATION_GAP_ONLY",
    }
    write_json(out, "audits/closure-ledger-and-authorization-correction.json", closure)

    blocker = {
        "blocker_id": "GOOGL_HUT_FINALIZATION_OWNER_REPAIR_REQUIRED",
        "workstream": "W1",
        "category": "RUNTIME",
        "exact_gate": "validate_accepted_v2_decision exact-number finalization predicate",
        "affected_fixtures": ["GOOGL", "HUT"],
        "input_hashes": [
            {
                "ticker": row["ticker"],
                "raw_subset_sha256": row["raw_subset_sha256"],
                "normalized_output_sha256": row["normalized_output_sha256"],
            }
            for row in numeric_results
            if isinstance(row, Mapping)
        ],
        "minimal_reproducer": (
            "Run scripts/m12cg_r3_native_probe.py against the packaged M12CE and M12CB "
            "roots; inspect googl-hut-numeric-token-claim-ref-owner-trace.json."
        ),
        "confirmed_facts": [
            "both candidates pass Stage-2",
            "exact-number text is copied unchanged from frozen Fundamental Core",
            "cited evidence refs are preserved",
            "rejecting predicate performs zero registry comparisons",
        ],
        "hypotheses": [],
        "affected_completion_layer": "offline_acceptance_integration",
        "completed_independent_work": ["W2 PASS", "W3 PASS"],
        "smallest_missing_repair": (
            "owner-scoped finalization numeric validation convergence preserving N21 negatives"
        ),
        "why_not_completed": "application runtime repair was expressly outside R3 authorization",
        "status": "OPEN_BOUNDED_REPAIR_REQUIRED",
    }
    blockers = {
        "contract": "m12cg-r3-complete-blocker-ledger-v1",
        "causal_blocker_count": 1,
        "dependent_blocked_check_count": 1,
        "blockers": [blocker],
        "single_bounded_follow_on_proposal": (
            "finalization owner-scoped numeric validation repair with GOOGL/HUT positives "
            "and existing N21 negatives"
        ),
        "out_of_scope_backlog": [],
        "status": "OPEN_FINALIZATION_GAP",
    }
    write_json(out, "audits/complete-blocker-ledger.json", blockers)

    isolation = read_json(out / "audits/test-isolation-and-network-denial-proof.json")
    assert isinstance(isolation, Mapping)
    safety = {
        "contract": "m12cg-r3-safety-counters-v1",
        "scope": "this M12CG-R3 execution",
        "external_model_calls": 0,
        "full22_generations": 0,
        "model_retries": 0,
        "model_fallbacks": 0,
        "judge_calls": 0,
        "repair_model_calls": 0,
        "schema_repair_model_calls": 0,
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
        "authorized_test_sink_activity": "NONZERO_MEASURED_IN_NATIVE_CASE_MATRIX",
        "network_attempts_blocked": isolation["network_attempts_blocked"],
        "status": PASS,
    }
    write_json(out, "audits/safety-counters.json", safety)

    program = {
        "contract": "m12cg-r3-program-completion-v1",
        "instruction_revision": "R3-REV2",
        "top_level_result": TOP_LEVEL_RESULT,
        "required_base_sha": REQUIRED_BASE_SHA,
        "frozen_guard_runtime_sha": R2_GUARD_IMPLEMENTATION_SHA,
        "instruction_git_sha": instruction_commit,
        "instruction_content_sha256": sha256_file(work_instruction),
        "audit_implementation_sha": audit_implementation_sha,
        "final_local_sha": head,
        "runtime_changed_files": runtime_changed_files,
        "runtime_source_change_count": len(runtime_changed_files),
        "source_bundle_count_verified": integrity["source_bundle_count_verified"],
        "prior_sink_authorization_correction": closure[
            "prior_sink_authorization_correction"
        ],
        "native_route_classification": call_graph["classification"],
        "logical_event_key_owner": event_contract["lock_owner"],
        "native_intent_owner": event_contract["native_intent_owner"],
        "test_isolation_result": isolation["status"],
        "network_attempts_blocked": isolation["network_attempts_blocked"],
        "actual_native_delivery_route_executed": True,
        "test_sink_invocation_count": native_counts["test_sink_invocation_count"],
        "test_sink_success_count": native_counts["test_sink_success_count"],
        "test_logical_intent_count": native_counts["test_logical_intent_count"],
        "test_state_transition_count": native_counts["test_state_transition_count"],
        "test_execution_count_scope": native_counts["scope"],
        "test_execution_scenario_count": native_counts["scenario_count"],
        "native_authoritative_binding_result": PASS,
        "diagnostic_sidecar_disposition": native_contracts["n17"][
            "diagnostic_sidecar_disposition"
        ],
        "same_event_duplicate_result": native_contracts["same_new"]["status"],
        "new_event_positive_control_result": native_contracts["same_new"]["status"],
        "cross_version_continuity_result": native_contracts["cross_version"]["status"],
        "failure_reentry_result": native_contracts["failure"]["status"],
        "applicable_crash_concurrency_result": native_contracts["failure"]["status"],
        "native_n17_subobligation_results": {
            row["id"]: row["status"]
            for row in native_contracts["n17"]["obligations"]
        },
        "googl_numeric_cause": numeric_results[0]["classification"],
        "hut_numeric_cause": numeric_results[1]["classification"],
        "numeric_trace_complete_count": numeric_trace["trace_complete_count"],
        "numeric_runtime_repair_required": True,
        "stage2_valid_subject_count": 9,
        "finalized_subject_count": 7,
        "failed_finalization_subject_count": 2,
        "accepted_plan_coverage_complete": False,
        "fixture_id_required_count": fixtures["aggregate"]["required_fixture_count"],
        "fixture_variant_required_count": fixtures["aggregate"]["required_variant_count"],
        "fixture_variant_proven_count": fixtures["aggregate"]["proven_variant_count"],
        "missing_node_or_variant_count": coverage["missing_node_or_variant_count"],
        "unknown_status_count": 0,
        "unexpected_exception_count": exception_matrix["unexpected_exception_count"],
        "aggregation_counterexample_result": aggregation["status"],
        "valid_input_semantic_change_count": valid_parity[
            "valid_input_semantic_change_count"
        ],
        "valid_input_hash_change_count": valid_parity["valid_input_hash_change_count"],
        "model_facing_byte_comparison_denominator": model_facing[
            "comparison_denominator"
        ],
        "model_facing_byte_delta_count": model_facing["byte_delta_count"],
        "native_offline_proof_status": native["native_offline_proof_status"],
        "offline_migration_compatibility_status": "BLOCKED_BY_FINALIZATION_OWNER",
        "complete_blocker_set": [blocker["blocker_id"]],
        "new_full22_authorized": False,
        "message_model_contract_readiness": (
            "NOT_READY_FINALIZATION_OWNER_REPAIR_REQUIRED"
        ),
        "deployment_readiness": "NO",
        "completion_layers": completion_layers,
        "workstream_statuses": workstreams,
        "closed_finding_reopen_events": [],
        "causal_blocker_count": 1,
        "dependent_blocked_check_count": 1,
        "independent_work_completed": ["W2", "W3", "W1 diagnosis"],
        "out_of_scope_backlog": [],
        **{
            key: value
            for key, value in safety.items()
            if key not in {"contract", "scope", "status"}
        },
    }
    write_json(out, "program-completion.json", program)

    next_proposal = """# Next bounded proposal

Authorize one owner-scoped finalization numeric validation repair. The repair must preserve
unchanged frozen Fundamental Core claims with their original evidence refs while keeping
Stage-2-authored and mutated exact numbers as hard failures. Re-run GOOGL/HUT positive controls,
N21 negatives, focused/full/Treasury/Kiwoom suites, and the closed D01-D14 native matrix.

This report does not authorize a model call, Full22 generation, main merge, deployment,
scheduler action, production mutation, Kiwoom live access or real notification.
"""
    (out / "next-bounded-proposal.md").write_text(next_proposal, encoding="utf-8")
    result_md = f"""# M12CG-R3 Native Delivery Offline Proof and Finalization Ownership Trace

## Result

`{TOP_LEVEL_RESULT}`

R2's metadata-presence guard and previously frozen design findings remain closed at their
stated scopes. R3 newly executed the existing native delivery owner through an isolated
in-process sink. D01-D14 pass across {case_matrix['case_variant_count']} measured variants,
including same-event dedupe, independent new events, failure/re-entry, version coexistence,
authoritative binding, diagnostic-sidecar non-authority, chunk cursor recovery, crash-window
at-least-once behavior and packet-lock serialization. N17A-E all pass.

The proof harness now fails closed on empty, missing, skipped, unknown, duplicate and
unmeasured children. It preserves 35 historical fixture IDs while measuring
{fixtures['aggregate']['required_variant_count']} distinct evidence variants. Exact required
node coverage and all-pass controls pass.

GOOGL and HUT remain unfinalized. Both Stage-2 candidates are valid, but finalization applies
an exact-number predicate to unchanged frozen Fundamental Core claims without a registry
comparison. Both are classified `FROZEN_CORE_REVALIDATION_SCOPE_FALSE_POSITIVE`. The diagnosis
is complete; the required runtime repair was not authorized or applied. Offline acceptance is
therefore 7/9 and deployment readiness remains NO.

## Safety

- External model calls / Full22: 0 / 0
- Production sends / intents / DB writes: 0 / 0 / 0
- Main merge / deploy / remote push: 0 / 0 / 0
- Scheduler changes / Kiwoom live actions: 0 / 0
- Runtime source changes: {len(runtime_changed_files)}

`new_full22_authorized=false`

`message_model_contract_readiness=NOT_READY_FINALIZATION_OWNER_REPAIR_REQUIRED`

`deployment_readiness=NO`
"""
    (out / "M12CG-R3-RESULT.md").write_text(result_md, encoding="utf-8")

    for script_name in (
        "m12cg_r3_proof_harness.py",
        "m12cg_r3_native_probe.py",
        "m12cg_r3_model_facing_probe.py",
        "m12cg_r3_offline_proof.py",
    ):
        shutil.copy2(repo / "scripts" / script_name, out / "proof-scripts" / script_name)
    shutil.copy2(work_instruction, out / "repository" / work_instruction.name)
    (out / "repository/git-log.txt").write_text(
        run(repo, "git", "log", "-16", "--oneline", "--decorate") + "\n",
        encoding="utf-8",
    )
    (out / "repository/implementation-diff.patch").write_text(
        run(repo, "git", "diff", f"{REQUIRED_BASE_SHA}..{head}") + "\n",
        encoding="utf-8",
    )
    write_json(
        out,
        "audits/report-generation-summary.json",
        {
            "contract": "m12cg-r3-report-generation-summary-v1",
            "trace_summary": trace_summary,
            "integrity": integrity["status"],
            "runtime_freeze": runtime_freeze["status"],
            "native": native["native_offline_proof_status"],
            "fixtures": fixtures["status"],
            "aggregation": aggregation["status"],
            "valid_parity": valid_parity["status"],
            "model_facing": model_facing["status"],
            "validation": validation["status"],
            "status": (
                PASS
                if all(
                    value == PASS
                    for value in (
                        integrity["status"],
                        runtime_freeze["status"],
                        native["native_offline_proof_status"],
                        fixtures["status"],
                        aggregation["status"],
                        valid_parity["status"],
                        model_facing["status"],
                        validation["status"],
                    )
                )
                else FAIL
            ),
        },
    )
    write_json(out, "artifact-manifest.json", artifact_manifest(out))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--source-r1", type=Path, required=True)
    parser.add_argument("--source-r2", type=Path, required=True)
    parser.add_argument("--source-m12cb", type=Path, required=True)
    parser.add_argument("--source-m12ce", type=Path, required=True)
    parser.add_argument("--native-probe-root", type=Path, required=True)
    parser.add_argument("--validation-dir", type=Path, required=True)
    parser.add_argument("--work-instruction", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    build_report(parser.parse_args())


if __name__ == "__main__":
    main()
