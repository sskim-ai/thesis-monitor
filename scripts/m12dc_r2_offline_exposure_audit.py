"""Read pinned archives, never execute transcript commands or import model runners."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


BASE = "fac9e4cccb7a2e274cf358c79b6973c3434fd2ad"
A_BASE = "3e1bdeab6176f6e6996f4e389529d4a7034f9b46"
STATUS = re.compile(r"^ (?:succeeded|exited \d+) in .*:$")
PATH = re.compile(
    r"(?:\./)?(?:docs|scripts|tests|app|\.agents)/[\w./-]+\.(?:py|md|json|txt|toml|yaml)"
)
PRIOR_VALUE = re.compile(
    r'"(?:prior_accepted_decision|overall_direction|original_overall_direction|'
    r'original_new_buyer|original_holder|archetype|company_archetype|valuation_regime_tier)"'
    r'\s*:\s*"[A-Z][A-Z_]+"'
)
BOUNDARIES = {"exec", "codex", "thinking", "user"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def safe_member(name: str) -> bool:
    return (
        bool(name)
        and not PurePosixPath(name).is_absolute()
        and ".." not in PurePosixPath(name).parts
        and "\\" not in name
    )


def read_archive(path: Path, expected: dict) -> tuple[dict[str, bytes], dict]:
    data = path.read_bytes()
    if sha(data) != expected["sha256"] or len(data) != expected["size"]:
        raise ValueError("archive_hash_or_size_mismatch")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate_archive_member")
        for entry in archive.infolist():
            if not safe_member(entry.filename) or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("unsafe_archive_member")
        if archive.testzip() is not None:
            raise ValueError("archive_crc_failed")
        manifest_name = min(
            (n for n in names if PurePosixPath(n).name == "artifact-manifest.json"),
            key=lambda n: n.count("/"),
        )
        prefix = manifest_name.removesuffix("artifact-manifest.json")
        files = {
            n[len(prefix) :]: archive.read(n)
            for n in names
            if not n.endswith("/") and n.startswith(prefix)
        }
    manifest = json.loads(files["artifact-manifest.json"])
    rows = manifest.get("files", manifest.get("payloads"))
    if len(rows) != expected["manifest_payload_count"]:
        raise ValueError("payload_count_mismatch")
    seen = set()
    for row in rows:
        if not safe_member(row["path"]) or row["path"] in seen:
            raise ValueError("invalid_manifest_path")
        seen.add(row["path"])
        blob = files[row["path"]]
        if sha(blob) != row["sha256"] or len(blob) != row.get("size", row.get("bytes")):
            raise ValueError("payload_identity_mismatch:" + row["path"])
    if set(files) - seen - {"artifact-manifest.json"} != set(expected["known_nonpayload_members"]):
        raise ValueError("unmanifested_member")
    return files, {
        "path": str(path),
        "sha256": sha(data),
        "bytes": len(data),
        "payload_count": len(rows),
        "status": "PASS",
    }


def parse_events(lines: list[str]) -> list[dict]:
    """Keep overlapping command/status attribution unresolved, rather than guessing."""
    starts = [i for i, line in enumerate(lines) if line == "exec"]
    finals = [i for i, line in enumerate(lines) if line == "codex"]
    final = finals[-1] if finals else None
    result = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        statuses = [i for i in range(start + 1, end) if STATUS.match(lines[i])]
        command_end = statuses[0] if statuses else end
        command = "\n".join(lines[start + 1 : command_end]).strip()
        payload_end = end
        if statuses:
            payload_end = next(
                (i for i in range(statuses[0] + 1, end) if lines[i] in BOUNDARIES), end
            )
        status = lines[statuses[0]] if len(statuses) == 1 else None
        output = "\n".join(lines[statuses[0] + 1 : payload_end]) if statuses else ""
        result.append(
            {
                "event_ordinal": index + 1,
                "command_line_start": start + 2,
                "command": command,
                "status_line": statuses[0] + 1 if statuses else None,
                "status": status,
                "status_count": len(statuses),
                "attribution": "UNAMBIGUOUS" if len(statuses) == 1 else "INTERLEAVED_OR_UNRESOLVED",
                "returned_line_start": statuses[0] + 2 if statuses else None,
                "returned_line_end": payload_end if statuses else None,
                "returned_text": output,
                "returned_utf8_sha256": sha(output.encode()),
                "before_final_response": final is not None and payload_end <= final,
                "final_response_line": final + 1 if final is not None else None,
                "log_truncation_marker_present": bool(
                    re.search(r"(?:tokens truncated|bytes omitted|output truncated)", output, re.I)
                ),
            }
        )
    return result


def classify_event(event: dict) -> tuple[list[str], str]:
    text = event["returned_text"]
    command = event["command"]
    if event["attribution"] != "UNAMBIGUOUS":
        return (
            ["UNRESOLVED_FROM_LOG"],
            "Interleaved completions have no call IDs; group content is retained without false attribution.",
        )
    if not text.strip() or "command not found:" in text:
        return [
            "PATH_ONLY_OR_NO_CONTENT"
        ], "No source content returned; exit-zero pipelines can still contain failed commands."
    nonempty = [line for line in text.splitlines() if line.strip()]
    if all(
        re.match(r"^\s*\d+\s+(?:\.?/?[\w.-]+/|/Users/)", line)
        or re.match(r"^\s*\d+\s+total$", line)
        for line in nonempty
    ):
        return [
            "PATH_ONLY_OR_NO_CONTENT"
        ], "File line-count metadata only, not instruction contents."
    if all(
        re.match(r"^(?:\./)?(?:docs/|data/|scripts/|tests/|app/|/Users/|/tmp/)", line)
        and not re.search(r"\.\w+:\d+:", line)
        for line in nonempty
    ):
        return ["PATH_ONLY_OR_NO_CONTENT"], "Filename-only output; not a content read."
    if ".agents/skills/" in command:
        return [
            "UNDECLARED_PROJECT_OR_SKILL_INSTRUCTION"
        ], "Repository daily-review instructions are outside the frozen analytical prompt."
    # Existing definitions are not automatically approved model-visible inputs.
    paths = PATH.findall(command)
    if (
        paths
        and all(p.startswith(("scripts/", "app/")) for p in paths)
        and "docs/reports" not in text
    ):
        return (
            ["APPROVED_STATIC_CONTRACT"],
            "Existing implementation definition, not a historical outcome; declaration/selection approval is still absent.",
        )
    normalized = text.replace('\\"', '"')
    historical_values_in_search = any(
        "docs/reports/" in line and PRIOR_VALUE.search(line) for line in normalized.splitlines()
    )
    if (
        "docs/reports" in command and PRIOR_VALUE.search(normalized)
    ) or historical_values_in_search:
        return (
            ["PRIOR_JUDGMENT_OR_CLASSIFICATION"],
            "Non-null classification/direction values returned from historical report content; no causal inference.",
        )
    if paths and all(p.startswith("docs/work-instructions/") for p in paths):
        return [
            "UNDECLARED_PROJECT_OR_SKILL_INSTRUCTION"
        ], "Legacy instructions were not an explicit per-request allowlisted contract bundle."
    return (
        ["OTHER_UNBOUND_SOURCE"],
        "Source text/fixtures/search output outside declared request; not automatically an investment-label exposure.",
    )


def subject_tickers(context: object) -> list[str]:
    rows = context.get("subjects") if isinstance(context, dict) else context
    if not isinstance(rows, list) or not rows:
        raise ValueError("subject_context_shape_unrecognized")
    tickers = [str(row["ticker"]) for row in rows]
    if len(set(tickers)) != len(tickers):
        raise ValueError("subject_context_duplicate_identity")
    return tickers


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL)


def audit(package: Path, repo: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    ix = json.loads((package / "source-index.json").read_text())
    archives = [read_archive(package / src["path"], src) for src in ix["sources"]]
    r1, old = archives[0][0], archives[1][0]
    subset = {
        k.removeprefix("upstream-a/"): v for k, v in r1.items() if k.startswith("upstream-a/")
    }
    assert len(subset) == ix["expected_upstream_A_subset_exact_files"] == 131
    assert all(old.get(k) == v for k, v in subset.items())
    inventory = json.loads(
        (package / "review-evidence/runtime-exposure-inventory.json").read_text()
    )
    sources = {}
    batches, all_events = [], []
    excerpts = []
    confirmed = inventory["confirmed_cases"]
    for supplied in inventory["event_inventory"]:
        log_name = supplied["transport_log_path"]
        blob = r1[log_name]
        assert sha(blob) == supplied["transport_log_sha256"]
        lines = blob.decode().splitlines()
        events = parse_events(lines)
        assert len(events) == supplied["visible_exec_event_count"]
        stage, market, batch = supplied["stage"], supplied["market"], supplied["batch"]
        key = f"{stage}-{market.upper()}{batch:02d}"
        prefix = f"{'upstream-a/' if stage == 'A' else ''}frozen-requests/pass-{stage.lower()}/{market}/batch-{batch:02d}/"
        receipt = json.loads(r1[prefix + "request-receipt.json"])
        request_hashes = {
            name[len(prefix) :]: sha(data) for name, data in r1.items() if name.startswith(prefix)
        }
        for identity, filename in {
            "prompt": "prompt.txt",
            "context": "subject-context.json",
            "wire_schema": "provider-wire-schema.json",
            "internal_schema": "internal-semantic-schema.json",
            "ref_catalog": "ref-catalog.json",
            "source_binding": "source-use-and-consumed-source-binding.json",
        }.items():
            assert request_hashes[filename] == receipt["file_sha256"][identity]
        context = json.loads(r1[prefix + "subject-context.json"])
        tickers = subject_tickers(context)
        copy_dir = out / "pinned-evidence" / key
        copy_dir.mkdir(parents=True)
        (copy_dir / "transport.log").write_bytes(blob)
        (copy_dir / "request-receipt.json").write_bytes(r1[prefix + "request-receipt.json"])
        matched_cases = [c for c in confirmed if c["log"] == log_name]
        for event in events:
            event["batch_key"] = key
            event["event_id"] = f"{key}:E{event['event_ordinal']:02d}"
            event["source_transport_log"] = log_name
            event["transport_log_sha256"] = sha(blob)
            event["categories"], event["classification_basis"] = classify_event(event)
            event["confirmed_case_ids"] = []
            for case in matched_cases:
                if (
                    event["returned_text"].strip()
                    and event["returned_line_start"]
                    and event["returned_line_start"] <= case["line_end"]
                    and event["returned_line_end"] >= case["line_start"]
                ):
                    event["confirmed_case_ids"].append(case["id"])
                    event["categories"] = ["PRIOR_JUDGMENT_OR_CLASSIFICATION"]
                    if (
                        case["id"] == "A_US04_PRIOR_A_CLASSIFICATION"
                        and '"deterministic_fundamental_option"' in event["returned_text"]
                    ):
                        event["categories"].append("POST_A_PRICE_VALUATION_OR_TACTICAL_INPUT_IN_A")
                    event["classification_basis"] = (
                        "Pinned review excerpt reproduced independently; non-null historical values before final response."
                    )
            # Reviewed mixed return: its BUY/SELL literals belong to appended static
            # hypothetical examples, not to the preceding report's historical rows.
            if event["event_id"] == "A-US04:E13":
                assert (
                    event["returned_utf8_sha256"]
                    == "48d98cb99012e75057c9e884621bb6e31704f0bd660f7b0fa3a28ad1460e75e5"
                )
                event["categories"] = ["OTHER_UNBOUND_SOURCE"]
                event["classification_basis"] = (
                    "Content review: report returns validation receipts; appended scripts/m12cn_policy_contract.py lines 1350-1430 contain hypothetical BUY/SELL examples, not old issuer decisions."
                )
            if event["event_id"] in {"A-KR02:E05", "B-KR02:E06", "B-US01:E11"}:
                event["categories"] = ["PATH_ONLY_OR_NO_CONTENT"]
                event["classification_basis"] = (
                    "Reviewed filename-only search output, including .agents/root ZIP paths and diagnostics, not source contents."
                )
            returned = event.pop("returned_text")
            output_path = f"returned-content/{key}/event-{event['event_ordinal']:03d}.txt"
            target = out / output_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(returned)
            event["returned_content_artifact"] = output_path
            event["candidate_source_paths"] = sorted(
                set(PATH.findall(event["command"] + "\n" + returned))
            )
            event["source_path_extraction_scope"] = (
                "Visible literal paths only; glob/recursive command paths are not an exhaustive opened-file ledger."
            )
            source_keys = []
            ref = A_BASE if stage == "A" else BASE
            for path in event["candidate_source_paths"]:
                path = path.removeprefix("./")
                source_key = ref + ":" + path
                source_keys.append(source_key)
                if source_key not in sources:
                    try:
                        content = git(repo, "show", source_key)
                        sources[source_key] = {
                            "commit": ref,
                            "path": path,
                            "sha256": sha(content),
                            "bytes": len(content),
                            "binding": "PINNED_GIT_OBJECT_NOT_FULL_READ_ATTESTATION",
                        }
                    except subprocess.CalledProcessError:
                        sources[source_key] = {
                            "commit": ref,
                            "path": path,
                            "sha256": None,
                            "binding": "MISSING_PINNED_FILE_OR_LITERAL_PATTERN",
                            "gap": "Transcript bytes remain bound; full opened-file bytes not established.",
                        }
            event["source_identity_keys"] = source_keys
            all_events.append(event)
            first = [line[:220] for line in returned.splitlines() if line.strip()][:3]
            matches = [
                line[:450]
                for line in returned.replace('\\"', '"').splitlines()
                if PRIOR_VALUE.search(line)
            ][:4]
            excerpts.extend(
                [
                    f"## {event['event_id']} {','.join(event['categories'])}",
                    f"Lines {event['command_line_start']} / returned {event['returned_line_start']}-{event['returned_line_end']}; {event['status']}; {event['attribution']}",
                    event["command"],
                    "\n".join(first + matches),
                    "",
                ]
            )
        batch_events = [event for event in all_events if event["batch_key"] == key]
        categories = Counter(c for event in batch_events for c in event["categories"])
        batches.append(
            {
                "batch_key": key,
                "stage": stage,
                "market": market,
                "batch": batch,
                "tickers": tickers,
                "source_generation_id": json.loads(
                    (old if stage == "A" else r1)["program-completion.json"]
                )["generation_id"],
                "request_directory": prefix,
                "request_sha256": receipt["request_sha256"],
                "request_file_sha256": request_hashes,
                "transport_log": log_name,
                "transport_log_sha256": sha(blob),
                "visible_exec_events": len(events),
                "categories": dict(categories),
                "confirmed_case_ids": [case["id"] for case in matched_cases],
                "all_visible_events_before_final": all(
                    event["before_final_response"] for event in batch_events
                ),
                "declared_identity": "PASS",
                "bounded_effective_context": "NOT_PROVEN",
                "prior_judgment_observation": "OBSERVED"
                if categories["PRIOR_JUDGMENT_OR_CLASSIFICATION"]
                else "NOT_ESTABLISHED_NOT_A_CLEAN_CERTIFICATE",
                "reuse_for_clean_calibration": "WITHHELD",
                "diagnostic_reuse": "ALLOWED_WITH_EXPOSURE_QUALIFICATION",
                "downstream_dependency": f"B-{market.upper()}{batch:02d}"
                if stage == "A"
                else f"A-{market.upper()}{batch:02d}",
                "effective_context_gap": "System/developer/bootstrap, skill discovery and complete tool inventory were not archived as a final model request.",
            }
        )
    reproduced = []
    for case in confirmed:
        lines = r1[case["log"]].decode().splitlines()
        excerpt = "\n".join(lines[case["line_start"] - 1 : case["line_end"]])
        assert sha(excerpt.encode()) == case["excerpt_sha256"]
        assert all(fragment in excerpt for fragment in case["required_fragments"])
        assert case["line_end"] < max(i + 1 for i, line in enumerate(lines) if line == "codex")
        prefix = (
            "upstream-a/frozen-requests/pass-a"
            if case["stage"] == "A"
            else "frozen-requests/pass-b"
        )
        prompt = r1[f"{prefix}/{case['market']}/batch-{case['batch']:02d}/prompt.txt"].decode()
        assert case["prompt_forbidden_field"] not in prompt
        reproduced.append({**case, "independent_reproduction": "PASS"})
        (out / f"{case['id']}.txt").write_text(excerpt)
    assert len(batches) == 16 and len(all_events) == 156
    for stage in ("A", "B"):
        stage_tickers = [
            ticker for row in batches if row["stage"] == stage for ticker in row["tickers"]
        ]
        assert len(stage_tickers) == len(set(stage_tickers)) == 22
    binding = {
        "sources": [x[1] for x in archives],
        "A_subset_equal_files": 131,
        "original_artifacts_modified": False,
        "original_program_completion_sha256": {
            "R1": sha(r1["program-completion.json"]),
            "M12DC": sha(old["program-completion.json"]),
        },
        "pinned_git_sources": sources,
    }
    write_json(out / "source-binding-manifest.json", binding)
    write_json(
        out / "tool-read-event-matrix.json",
        {
            "scope": "Visible tool commands/returned content, not hidden reasoning or causal attribution",
            "events": all_events,
        },
    )
    write_json(out / "batch-exposure-and-reuse-matrix.json", {"batches": batches})
    write_json(out / "confirmed-exposure-reproduction.json", reproduced)
    write_json(
        out / "original-completion-overlay.json",
        {
            "original_r1_completion": json.loads(r1["program-completion.json"]),
            "original_m12dc_completion": json.loads(old["program-completion.json"]),
            "mechanical_results_preserved": True,
            "declared_input_only_calibration": "WITHHELD",
            "comparison_loader_timing_does_not_bound_worker_tool_reads": True,
        },
    )
    (out / "EVENT_REVIEW.md").write_text("\n".join(excerpts))
    summary = {
        "batch_count": len(batches),
        "visible_exec_markers": len(all_events),
        "confirmed_review_excerpts": len(reproduced),
        "category_event_counts": dict(Counter(c for e in all_events for c in e["categories"])),
        "interleaved_events": sum(e["attribution"] != "UNAMBIGUOUS" for e in all_events),
        "all_events_before_response": all(e["before_final_response"] for e in all_events),
        "model_calls": 0,
        "network_calls": 0,
    }
    write_json(out / "exposure-summary.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.package, args.repo, args.out), indent=2))
