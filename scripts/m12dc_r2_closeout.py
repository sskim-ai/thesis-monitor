"""Package the bounded R2 audit without running any model or production owner."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from scripts.m12dc_r2_offline_exposure_audit import A_BASE, BASE, git, sha, write_json


TERMINAL = "M12DC_R2_EXPOSURE_RECONCILED_ISOLATION_MECHANISM_REQUIRES_CHAT"
INSTRUCTION = "61fd6114ddaa5ff9d53d5a4fd719d6562f8d759a"
FILES = [
    "scripts/m12dc_r2_offline_exposure_audit.py",
    "scripts/m12dc_r2_native_offline_probe.py",
    "scripts/m12dc_r2_closeout.py",
    "tests/test_m12dc_r2_offline_exposure_audit.py",
]
OWNERS = [
    "scripts/m12dc_fresh_source_use_two_pass_reproof.py",
    "app/jobs/accepted_decision_v2_runtime.py",
    "app/services/codex_runtime_state_service.py",
    "scripts/m12cv_pass_b_capability_contract.py",
    "scripts/m12cq_two_pass_contract.py",
    "scripts/m12cr_shadow_contract.py",
]


def closeout(repo: Path, out: Path, package: Path, probes: list[Path]) -> dict:
    batches = json.loads((out / "batch-exposure-and-reuse-matrix.json").read_text())["batches"]
    events = json.loads((out / "tool-read-event-matrix.json").read_text())["events"]
    exposure = json.loads((out / "exposure-summary.json").read_text())
    implementation = git(repo, "rev-parse", "HEAD").decode().strip()
    changed = git(repo, "diff", "--name-only", BASE).decode().splitlines()
    assert not any(path.startswith("app/") or path in OWNERS for path in changed)
    identities = []
    for owner in OWNERS:
        actual = (repo / owner).read_bytes()
        baseline = git(repo, "show", BASE + ":" + owner)
        assert actual == baseline
        identities.append(
            {
                "path": owner,
                "baseline_sha256": sha(baseline),
                "current_sha256": sha(actual),
                "unchanged": True,
            }
        )
    write_json(out / "unchanged-runtime-and-policy-owners.json", identities)
    for path in FILES:
        target = out / "audit-code" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / path, target)
    shutil.copytree(package, out / "instruction-package", dirs_exist_ok=True)
    for source in probes:
        target = out / "native-probes" / source.name
        target.mkdir(parents=True, exist_ok=True)
        for path in source.iterdir():
            if path.is_file() and not path.is_symlink():
                shutil.copy2(path, target / path.name)
    latest = probes[-1]
    native = json.loads((latest / "offline-access-control-results.json").read_text())
    prompt = json.loads((latest / "bounded-effective-prompt-input.json").read_text())
    prompt_receipt = json.loads(
        (latest / "bounded-effective-prompt-input-receipt.json").read_text()
    )
    assert prompt_receipt["returncode"] == 0
    assert native["access_tests"][0]["bounded_readable"]
    assert all(
        row["bounded_readable"]
        for row in native["access_tests"]
        if row["case"] in {"historical", "sibling", "symlink"}
    )
    assert next(row for row in native["access_tests"] if row["case"] == "absolute-repo")[
        "bounded_denied_by_os"
    ]
    rendered = "\n".join(
        item.get("text", "") for message in prompt for item in message.get("content", [])
    )
    assert "Denied filesystem reads" in rendered and "<skills_instructions>" in rendered
    current_roots = [repo, *repo.parents, Path.home() / ".codex"]
    root_inventory = []
    for root in dict.fromkeys(current_roots):
        for name in ("AGENTS.md", "AGENTS.override.md"):
            path = root / name
            row = {
                "path": str(path),
                "exists_now": path.is_file(),
                "historical_identity": "NOT_CAPTURED",
            }
            if path.is_file():
                row["current_sha256"] = sha(path.read_bytes())
            root_inventory.append(row)
    skill = ".agents/skills/thesis-monitor-daily-review/SKILL.md"
    skill_identities = {ref: sha(git(repo, "show", ref + ":" + skill)) for ref in (A_BASE, BASE)}
    surface_manifest = {
        "contract": "M12DC_R2_EFFECTIVE_SURFACE_AUDIT_ONLY",
        "historical_model_input_fully_bound": False,
        "known_declared_surfaces": [
            {
                "batch_key": row["batch_key"],
                "category": "DECLARED_FROZEN_INPUT",
                "hashes": row["request_file_sha256"],
            }
            for row in batches
        ],
        "known_additional_surfaces": [
            {
                "event_id": row["event_id"],
                "sha256": row["returned_utf8_sha256"],
                "artifact": row["returned_content_artifact"],
                "categories": row["categories"],
            }
            for row in events
        ],
        "repository_skill_identity": {
            "path": skill,
            "pinned_git_sha256": skill_identities,
            "batch_explicit_content_reads": 15,
        },
        "current_instruction_root_inventory": root_inventory,
        "auto_loaded_system_skill_content_inventory": [
            {
                "relative_path": str(path.relative_to(latest / "canaries/empty-home/.codex")),
                "sha256": sha(path.read_bytes()),
            }
            for path in sorted(
                (latest / "canaries/empty-home/.codex/skills/.system").glob("*/SKILL.md")
            )
        ],
        "system_developer_bootstrap_historical_request": "UNOBSERVABLE_FROM_ARCHIVED_TRANSPORT_LOGS",
        "initial_full_tool_registry_historical_and_proposed": "NOT_EXPORTED_BY_PROMPT_INPUT_DEBUG",
        "skill_discovery_at_historical_start": "NOT_ARCHIVED; 15 explicit later reads observed, no-read batch is not certified",
        "prior_session": "ephemeral + unique namespace requested by runtime; historical full conversation serialization not archived",
        "runtime_auth": "Existing protected symlink owner inspected as code only; not invoked or copied by R2",
        "proposed_prompt_debug_sha256": prompt_receipt["sha256"],
        "proposed_effective_context_semantic_parity_with_old": "NOT_ESTABLISHED; removing repo skills/tools and explicitly adding static definitions changes effective context",
        "allowed_static_contract_bundle_added": False,
        "remaining_gaps": [
            "temporary-file and symlink reads still succeed under tested native profile",
            "requested no-tool features are not a captured complete tool registry or dispatcher proof",
            "bundled system skills remain in serializer",
            "serializer is not a provider-complete Responses envelope or historical request reconstruction",
        ],
    }
    write_json(out / "effective-input-surface-manifest.json", surface_manifest)
    validation_dir = out / "validation"
    validation_dir.mkdir(exist_ok=True)
    venv = Path("/Users/sskim/Codex/thesis-monitor/.venv/bin")
    tests = [
        "tests/test_m12dc_r2_offline_exposure_audit.py",
        "tests/test_m12dc_fresh_source_use_two_pass_reproof.py",
        "tests/test_m12cv_pass_b_capability_contract.py",
        "tests/test_m12cq_two_pass_policy_shadow.py",
        "tests/test_m12cr_shadow_contract.py",
        "tests/test_m12cr_r1_typed_quality_contract.py",
        "tests/test_m12db_model_view_readiness.py",
        "tests/test_m12db_r1_request_composition_closure.py",
    ]
    validation = []
    for name, command in (
        ("focused", [str(venv / "pytest"), "-q", *tests]),
        ("ruff", [str(venv / "ruff"), "check", *FILES]),
        ("diff-check", ["git", "diff", "--check", BASE]),
        ("package-verification", [str(venv / "python"), str(package / "verify_package.py")]),
    ):
        process = subprocess.run(command, cwd=repo, capture_output=True, timeout=120, check=False)
        (validation_dir / f"{name}.stdout").write_bytes(process.stdout)
        (validation_dir / f"{name}.stderr").write_bytes(process.stderr)
        validation.append(
            {
                "name": name,
                "argv": command,
                "returncode": process.returncode,
                "stdout_sha256": sha(process.stdout),
                "stderr_sha256": sha(process.stderr),
            }
        )
        if process.returncode:
            raise ValueError("validation_failed:" + name)
    write_json(
        out / "validation-results.json",
        {
            "commands": validation,
            "new_full_pytest": "NOT_RUN: offline audit-only change; shared runtime unchanged",
            "prior_R1_full_pytest": "4518 passed / 63 skipped (inherited submitted evidence, not an R2 rerun)",
            "CI": "NOT_RUN; no remote push or network",
        },
    )
    assert b"227 passed" in (validation_dir / "focused.stdout").read_bytes()
    binding = json.loads((out / "source-binding-manifest.json").read_text())
    immutable = []
    for source in binding["sources"]:
        actual = sha(Path(source["path"]).read_bytes())
        assert actual == source["sha256"]
        immutable.append(
            {
                "path": source["path"],
                "before_sha256": source["sha256"],
                "after_sha256": actual,
                "unchanged": True,
            }
        )
    write_json(out / "immutable-originals-final-verification.json", immutable)
    write_json(
        out / "safety-counters.json",
        {
            name: 0
            for name in (
                "new_A_calls",
                "new_B_calls",
                "core_calls",
                "judge_calls",
                "repair_calls",
                "provider_calls",
                "external_network_calls",
                "source_refresh",
                "market_refresh",
                "production_code_changes",
                "production_config_changes",
                "production_DB_mutations",
                "send",
                "intent",
                "broker",
                "scheduler_changes",
                "merge",
                "push",
                "deploy",
                "old_outputs_modified",
                "credentials_copied",
            )
        },
    )

    map_lines = [
        "| Batch | Shared subjects | Exec markers | Historical value reads | Context proof |",
        "|---|---|---:|---:|---|",
    ]
    for row in batches:
        map_lines.append(
            f"| {row['batch_key']} | {', '.join(row['tickers'])} | {row['visible_exec_events']} | {row['categories'].get('PRIOR_JUDGMENT_OR_CLASSIFICATION', 0)} | NOT PROVEN |"
        )
    table = "\n".join(map_lines)
    exposed = [
        row["batch_key"]
        for row in batches
        if row["categories"].get("PRIOR_JUDGMENT_OR_CLASSIFICATION")
    ]
    exposure_report = f"""# Runtime Input Exposure Reconciliation

## Disposition

R1 role-schema repair and software execution remain PASS at their demonstrated scope: frozen A22 identity, B8/8 and B22 validation. R1 and the original M12DC failed terminal are unchanged. Declared-input-only calibration acceptance is WITHHELD. No economic label was corrected, rated, targeted, or copied into a new candidate.

Implementation base: `{BASE}`. Instruction commit: `{INSTRUCTION}`. R2 audit implementation: `{implementation}`.

## Source binding

- R1 ZIP: `30ba5076bb5785b89ac6e6806e1510f86b772d1dbe24221faa36aaa5bdb2b25c`, 467 payloads verified.
- Original M12DC ZIP: `54428273276e986c8fe1c36be705bed3967e8647290b8ebe3cce70fb643de6e7`, 347 payloads verified.
- All 131 copied upstream-A files equal the complete original archive. The nested whole-report manifest is NOT interpreted as a promise that every old B payload is in the A subset.
- A generation: `20260919-m12dc-fresh-source-use-two-pass-20260919T074953Z-3e1bdeab`.
- B generation: `20260919-m12dc-r1-frozen-a-b-reproof-20260919T090738Z-fac9e4cc`.

## Whole-batch map

{table}

All 16 declared prompt/context/schema identities pass. 156 visible exec markers were inventoried; they are NOT 156 contamination events. 15 batches explicitly received the repository daily-review skill. A-US05 has zero recorded exec events, not proof of an instruction-free context.

9 command returns across {len(exposed)} batches contain historical classifications or investment labels: {", ".join(exposed)}. A-US04 also received post-A option metadata. These are call-level exposures shared by every subject in the call, not a finding that each subject copied an old answer. No keyword match and no logged tool use are not clean-context certificates.

## Reproduced and additional observations

1. B-US05 lines 1345-1367: old WULF `prior_accepted_decision: SELL` and distribution returned before final output. Its later HOLD does not undo exposure or prove causal independence.
2. A-US04 lines 1087-1169: old B fixture returns `frozen_pass_a_classification`, archetype/tier/rationale and deterministic option context. These are not fresh A inputs.
3. A-KR02 lines 5551-5607: old `original_new_buyer`, `original_holder`, and Overall fields returned during the shared 005930/010120/012450 call.
4. A-KR02 events 13/14 additionally return non-null old archetypes and rationales from a recursive report query. Individual source-file attribution for those aggregate queries is not recoverable from the output; returned bytes are fully bound.
5. B-KR03 event 11, B-US04 event 6 and B-US05 event 24 read old fixture prompts containing old A classifications. They are not the corresponding current declared R1 B requests. Exact returned-content artifacts and pinned file hashes are recorded.

All inventoried returns precede the final `codex` response marker. Chronology is line-order evidence, not fabricated per-event wall-clock timestamps. Two interleaved commands at B-US05 events 4/5 lack call IDs; their combined returned static content is retained with UNRESOLVED attribution, not assigned in a guessed completion order.

The original designated post-freeze comparison loader may satisfy its schedule. Its timestamp does not cover these earlier model-initiated file reads. This overlay narrows that claim without editing the original report.

## Classification limits

{json.dumps(exposure["category_event_counts"], indent=2)}

Categories may overlap. APPROVED_STATIC_CONTRACT denotes existing static implementation definitions, not retroactive authorization of repository browsing. Mixed test examples, source definitions, legacy instructions and report metadata remain OTHER/UNDECLARED where attribution is insufficient. A-US04 event 13 was manually checked: BUY/SELL literals in the appended Python examples are not historical issuer judgments. Failed rg/python, empty searches, filename output and wc metadata are separated from received file contents.

`tool-read-event-matrix.json` binds every command, status, return range, return hash, chronology, source candidates and attribution gap. `source-binding-manifest.json` binds available full files to their Git commit, not to a falsely reconstructed read set. Full log copies are retained under `pinned-evidence`; extracted tool content excludes model reasoning. `EVENT_REVIEW.md` is a compact review index, not the complete evidence.
"""
    isolation_report = f"""# Inference Input Isolation Offline Proof

## Terminal

`{TERMINAL}`

Exposure accounting is complete. Input isolation is NOT closed. No model call, provider/source refresh, production edit, push, merge or deployment was performed. The accepted code owners, role enums, final validators and old output bytes are unchanged. R2 adds only standalone offline audit/probe/packaging utilities and tests.

## Actual owner

`scripts/m12dc_fresh_source_use_two_pass_reproof.py::_invoke` verifies frozen prompt/schema/context hashes and calls `app/jobs/accepted_decision_v2_runtime.py::_invoke_signed_in_codex` with `cwd=REPO`.

The runtime invokes installed Codex 0.153.4 with `exec --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox read-only`, model/effort and the JSON schema. `--ignore-rules` concerns execpolicy rules; it is not an AGENTS/skills/file-read exclusion. `--ignore-user-config` skips that config file, not all bootstrap instructions. A unique runtime namespace isolates writable state, not the repository/home read surface. Auth remains in its existing symlink owner; R2 did not invoke it or read credentials.

The CLI binary is pinned at `c147aa90d34139599711fb568102ceefc6319ca1ac5cb6f4056ca46a1834edd9`. Local help, feature list, generated protocol schemas and native probes were used. No online documentation or new runtime dependency was used.

## Native tests, including failures

The audit invokes the installed `codex sandbox -P NAME` with per-call `permissions.NAME` settings and `/bin/cat` on harmless canaries. This is the native dispatcher, not a fabricated stub. The controller separately reads all canaries to compare bytes. All phases and argv/stdout/stderr receipts are preserved under `native-probes/`.

| Native configuration | Approved | Historical / sibling / symlink | Absolute repository |
|---|---|---|---|
| Broad read profile | readable | all readable | readable |
| Empty/minimal explicit file list without native platform support | process exit 134 | process exit 134 | process exit 134 |
| `:minimal` plus approved batch | readable | all readable | denied |
| `:minimal`, explicit tmp denies, approved batch | readable | all readable | denied |

An earlier invocation without required `-P` failed argument validation (exit 2). A `file_system` spelling did not establish a supported TOML filesystem policy; subsequent native tests use the actual `filesystem` mapping. Aborted commands are NOT classified as successful access denials. Explicit OS-directory lists were insufficient to start the target process and were not adopted.

The final profile requests `filesystem={{":minimal"="read", "/private/tmp"="deny", "/tmp"="deny", "/private/var/folders"="deny", "/var/folders"="deny", BATCH="read"}}`, network disabled. Its exact rendered environment advertises those deny entries, yet the native local test still reads the three outside-batch tmp targets. This is an observed native behavior gap for this setup, not a proven universal Codex bug or a claimed root cause inside unavailable native source. R2 does NOT connect this profile to the inference runner.

## Tool and instruction surfaces

Installed `shell_tool`, `unified_exec`, code-mode, plugin/app/browser/computer, image, multi-agent, skill-search, memory, hook and other feature controls can be requested off; `skip_host_skill_discovery` and `project_doc_max_bytes=0` are recognized by the inspected runtime. Feature configuration is REQUESTED evidence, not proof that every provider tool/dispatcher is absent.

`debug prompt-input` was executed only on a synthetic string, with an empty no-auth HOME behind the native network-disabled diagnostic sandbox. It returned five message objects: three developer and two user. Even with those feature controls and an empty working context, its developer text includes the five bundled system-skill descriptions. Its bounded-profile output explicitly describes the tmp deny entries. The exact JSON and SHA are retained. It is not the final Responses envelope: no complete tool registry, opaque base-system prompt or provider receipt is exported here. No inference canary was run to fill that gap.

## Evidence levels and controller separation

- PROVEN: pinned source identity; visible tool-content exposure; approved canary readable; absolute repo canary denied by the tested bounded native profile; tmp/sibling/symlink read leakage; requested deny entries present in local serialized environment.
- REQUESTED: feature-level no-tool configuration, bootstrap discovery controls, tmp deny profile. None is promoted to full no-tools/no-history proof.
- UNOBSERVABLE: historical full system/developer/tool envelope, opaque provider behavior, complete auto-loaded context during the old calls and end-to-end enforcement in the canonical exec path.

Controller archive access is required and remains separate. Future inference must not inherit it. No auth material was copied, no original file was deleted/chmodded, and no global or operating configuration changed. No new static analytical definitions were added to production/shadow prompts. If explicit static definitions are later bundled, select only already-approved owner definitions, review and hash them, with no old labels or new policy.

`effective-input-surface-manifest.json` records all known declared files, tool-return hashes, pinned skill identity, current instruction-root inventory and the precise unknowns. It deliberately has `historical_model_input_fully_bound=false`. Hashing only prompt.txt would not repair that gap.

## Verification

227 focused tests passed, including the new offline parser cases and existing source-use/capability/role-schema contracts. Ruff and git diff --check pass. Shared production/runtime/policy owner bytes are identical to R1. Full pytest/CI were not rerun for this standalone offline audit; prior R1 full-suite evidence remains inherited, not restated as new validation.
"""
    reuse_report = f"""# Next Execution and Checkpoint Reuse Decision

## Decision now

Return to Chat with `{TERMINAL}`. Authorized/executed new inference calls: ZERO. No A/B run is queued, scheduled or started. No readiness terminal here authorizes integration or delivery.

## Reuse matrix

{table}

Every A batch feeds the B batch with the same market/ordinal and subject set. `batch-exposure-and-reuse-matrix.json` records these dependencies and exact generations/request hashes. A-US04 and A-KR02 contain observed forbidden-stage/historical input. B-US05 contains old investment labels; B-KR03 and B-US04 contain old classification context. Other calls do not have a bounded effective-input proof, including zero-exec A-US05. No old-label agreement rate is used.

Original checkpoint bytes, schemas, receipts and deterministic source material remain useful for software regression, arithmetic/provenance checks and qualified diagnostic comparison. They are not deleted or changed to FAIL. Their clean source-isolated calibration reuse is withheld, not declared equivalent merely from hash or schema success. We did not rerun financial reconciliation or impose expected labels.

## Minimum defensible next scope

1. Recommended immediate next task: bounded OFFLINE native/no-tools mechanism closure, zero real-issuer calls. Resolve the discrepancy between advertised tmp denies and actual native reads; obtain a complete tool registry/dispatch proof and an explicit hashed instruction bundle. Do not expand platform allowlists until tests show the intended boundary. No auth/provider topology change is authorized here.
2. Preferred existing-runtime alternative: feature-level no-tools mode only after proving all file/shell/browser/MCP/connector paths absent, not merely disabled in a feature listing. The current local prompt serializer does not supply that proof. The native per-call permission profile is an alternative only after the tested tmp/symlink gap is closed and controller/bootstrap reads are accounted for.
3. If an opaque provider behavior cannot be established offline, ask Chat for a separately scoped, single synthetic canary after local closure. This is a proposal, not authorization; zero such calls occurred here. No real data, label, repair model or majority voting is needed to test an input boundary.
4. After the boundary and effective static bundle are frozen, Chat may choose a limited diagnostic cohort or a complete clean 22-subject proof. A real clean full-cohort claim would require new A8 followed by new B8 under one newly frozen generation because no old A effective context is certified and the proposed instruction/tool bundle differs. That conditional maximum of 16 calls is NOT an automatic rerun instruction. A targeted A-US04/A-KR02 and dependent B experiment could study those exposures but cannot certify all 22 as clean. B-only reuse of A22 does not fix the observed A exposures.

The known financial facts, source-use definitions, schemas, model/effort, deterministic options and validators remain locked. A changed effective instruction bundle must be recorded as a new experimental context, not disguised as an economic-only label correction. Future timeout/retry rules need their own frozen execution scope; this task changes none.

## Closure boundary

No causal claim that a historical label determined a new label; no claim that all outputs are wrong. R1 mechanical closure is preserved. Exact next-call budget and checkpoint use return to Chat. Monitoring, DB, warnings, notifications, production scheduler, merge, push and deploy remain untouched.
"""
    for name, content in (
        ("RUNTIME_INPUT_EXPOSURE_RECONCILIATION.md", exposure_report),
        ("INFERENCE_INPUT_ISOLATION_OFFLINE_PROOF.md", isolation_report),
        ("NEXT_EXECUTION_AND_CHECKPOINT_REUSE_DECISION.md", reuse_report),
    ):
        (out / name).write_text(content)
    completion = {
        "terminal": TERMINAL,
        "completed_at": datetime.now(UTC).isoformat(),
        "base_commit": BASE,
        "work_instruction_commit": INSTRUCTION,
        "implementation_commit": implementation,
        "local_only": True,
        "batch_count": 16,
        "visible_exec_markers": 156,
        "historical_value_read_events": 9,
        "historical_value_exposed_batches": exposed,
        "new_model_calls": 0,
        "input_isolation_closed": False,
        "original_mechanical_success_preserved": True,
        "source_only_calibration_acceptance": "WITHHELD",
        "next_execution_authorized": False,
        "deployment_authorized": False,
        "focused_tests": 227,
        "ruff": "PASS",
        "diff_check": "PASS",
    }
    write_json(out / "program-completion.json", completion)
    (out / "README.md").write_text(
        "# M12DC-R2 Offline Audit\n\nStart with the three top-level reports. Runtime input isolation remains unproven; no new inference was performed. Original results are preserved. Machine appendices bind sources, event content, native probes and validation. No artifact authorizes a rerun or production change.\n"
    )
    return completion


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--probe", required=True, action="append", type=Path)
    args = parser.parse_args()
    print(json.dumps(closeout(args.repo.resolve(), args.out, args.package, args.probe), indent=2))
