"""Finite native diagnostics and non-launchable worker plan. No inference entry point."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Literal
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, ValidationError

from scripts.m12dc_r2_native_offline_probe import CLI, DISABLE, PINNED_SHA


BASE = "493171183e7687f7fabb742062166bbb3e5518ab"
R1 = "fac9e4cccb7a2e274cf358c79b6973c3434fd2ad"
INSTRUCTION = "a8809fc15177ea84145899024f2d3657ada0d731"
R2_SHA = "4b7f65abb9ac754ecbfbc5541f9d2d44ae3d9cda49428652b3a92659eb4f2166"
OWNER_PATHS = (
    "scripts/m12dc_fresh_source_use_two_pass_reproof.py",
    "app/jobs/accepted_decision_v2_runtime.py",
    "app/services/codex_runtime_state_service.py",
    "app/services/codex_network_transport_service.py",
    "app/services/accepted_decision_v2_runtime_service.py",
    "scripts/m12cr_shadow_contract.py",
    "scripts/m12cv_pass_b_capability_contract.py",
    "scripts/m12cq_two_pass_contract.py",
)
DENIED_TMP_ROOTS = ("/tmp", "/private/tmp", "/var/folders", "/private/var/folders")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def native_prefix(name: str, cwd: Path, entries: dict[str, str]) -> list[str]:
    fs = ",".join(json.dumps(key) + "=" + json.dumps(value) for key, value in entries.items())
    setting = f"permissions.{name}={{filesystem={{{fs}}},network={{enabled=false}}}}"
    return [str(CLI), "sandbox", "-P", name, "-c", setting, "-C", str(cwd), "--"]


def read_outcome(code: int | None, stdout: bytes, stderr: bytes, expected: bytes) -> str:
    if code == 0 and stdout == expected:
        return "EXACT_BYTES_RETURNED"
    if (
        code == 1
        and not stdout
        and any(marker in stderr for marker in (b"Operation not permitted", b"Permission denied"))
    ):
        return "OS_PERMISSION_DENIED"
    return "INCONCLUSIVE_PROCESS_OR_READ_FAILURE"


def worker_plan(batch: Path, private_tmp: Path, home: Path, excluded: list[Path]) -> dict:
    batch, private_tmp, home = (p.resolve(strict=True) for p in (batch, private_tmp, home))
    if (
        batch == private_tmp
        or batch.is_relative_to(private_tmp)
        or private_tmp.is_relative_to(batch)
    ):
        raise ValueError("private_tmp_must_be_disjoint_from_approved_input")
    for path in excluded:
        resolved = path.resolve(strict=True)
        if any(resolved.is_relative_to(root) for root in (batch, private_tmp, home)):
            raise ValueError("controller_data_inside_worker_root")
    return {
        "mechanism": "F_DIAGNOSTIC_ONLY_AFTER_N_OBSERVABILITY_GAP",
        "executable": False,
        "cwd": str(batch),
        "environment": {
            "HOME": str(home),
            "CODEX_HOME": str(home / ".codex"),
            "TMPDIR": str(private_tmp),
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "LANG": "en_US.UTF-8",
        },
        "native_prefix": native_prefix(
            "bounded",
            batch,
            {":minimal": "read", **dict.fromkeys(DENIED_TMP_ROOTS, "deny"), str(batch): "read"},
        ),
        "requested_feature_disables": list(DISABLE),
        "requested_discovery": {"skip_host_skill_discovery": True, "project_doc_max_bytes": 0},
        "excluded_realpaths": [str(p.resolve()) for p in excluded],
        "launch_denial": "native_tool_dispatch_and_canonical_transport_binding_unproven",
        "credentials": "NONE_PROVIDED; existing protected auth owner not invoked",
    }


def request_artifacts(batch: Path) -> dict:
    class SyntheticAcknowledgment(BaseModel):
        model_config = ConfigDict(extra="forbid")
        ack: Literal["CURRENT_INPUT_R3"]

    evidence = {"kind": "synthetic-operational-canary", "value": "CURRENT_INPUT_R3"}
    schema = SyntheticAcknowledgment.model_json_schema()
    prompt = "Offline preparation only. Current synthetic evidence: " + json.dumps(evidence) + "\n"
    write_json(batch / "evidence.json", evidence)
    write_json(batch / "provider-wire-schema.json", schema)
    (batch / "prompt.txt").write_text(prompt)
    SyntheticAcknowledgment.model_validate({"ack": "CURRENT_INPUT_R3"})
    try:
        SyntheticAcknowledgment.model_validate({"ack": "WRONG"})
    except ValidationError:
        pass
    else:
        raise AssertionError("invalid_synthetic_output_accepted")
    return {
        "scope": "synthetic preparation and local JSON schema only; not a provider output acceptance",
        "files": {
            name: sha((batch / name).read_bytes())
            for name in ("prompt.txt", "evidence.json", "provider-wire-schema.json")
        },
        "positive_local_schema": "PASS",
        "negative_local_schema": "REJECTED",
        "financial_definitions_added": [],
    }


def capture_existing_invocation(repo: Path, out: Path, batch: Path, env: dict) -> dict:
    """Execute existing Python preparation to its spawn boundary, then abort.

    Readiness/state are substituted only for call-site observation. This is not a
    fake no-tools dispatcher or evidence of native/provider enforcement.
    """
    from app.jobs import accepted_decision_v2_runtime as runtime

    class CaptureStop(BaseException):
        pass

    captured = {}

    def stop_spawn(argv, **kwargs):
        data = kwargs["stdin"].read()
        captured.update(
            argv=argv,
            cwd=str(kwargs["cwd"]),
            environment=kwargs["env"],
            stdin_sha256=sha(data.encode()),
            timeout=kwargs["timeout"],
            schema_sha256=sha(Path(argv[argv.index("--output-schema") + 1]).read_bytes()),
        )
        raise CaptureStop

    state = SimpleNamespace(
        contract="OFFLINE_CAPTURE_STUB_ONLY",
        namespace_hash="SYNTHETIC_NAMESPACE",
        ownership="SYNTHETIC",
        mode="0700",
        sqlite_wal_probe="NOT_RUN",
        signed_in_auth_reference="NOT_PROVIDED",
        environment=lambda: dict(env),
    )
    with (
        patch.object(runtime, "_runtime_state_root", return_value=out / "nonexecuted-state"),
        patch.object(runtime, "prepare_codex_runtime_state", return_value=state),
        patch.object(
            runtime,
            "codex_tls_environment",
            side_effect=lambda value: SimpleNamespace(
                environment=value, trust_source="NOT_RUN", ca_bundle_path=None
            ),
        ),
        patch.object(
            runtime,
            "probe_codex_network_readiness",
            return_value=SimpleNamespace(
                contract="OFFLINE_CAPTURE_STUB_ONLY",
                ready=True,
                attempts=0,
                resolved_address_count=0,
                failure_type=None,
            ),
        ),
        patch.object(runtime.subprocess, "run", side_effect=stop_spawn),
    ):
        try:
            runtime._invoke_signed_in_codex(
                codex_bin=str(CLI),
                prompt=batch / "prompt.txt",
                output=out / "never-output.json",
                log=out / "capture-only.log",
                schema=batch / "provider-wire-schema.json",
                cwd=batch,
                timeout=30,
                state_namespace="r3:offline-capture:no-inference",
            )
        except CaptureStop:
            pass
        else:
            raise AssertionError("capture_boundary_not_reached")
    assert captured and not (out / "never-output.json").exists()
    source = (repo / "app/jobs/accepted_decision_v2_runtime.py").read_text()
    function = next(
        n
        for n in ast.parse(source).body
        if isinstance(n, ast.FunctionDef) and n.name == "_invoke_signed_in_codex"
    )
    params = [arg.arg for arg in function.args.kwonlyargs]
    result = {
        "captured": captured,
        "existing_keyword_parameters": params,
        "method": "actual Python owner executed to intercepted subprocess.run; all state/auth/network preparation substituted",
        "native_exec_launched": False,
        "actual_cwd_prompt_schema_binding": True,
        "environment_injected_at_stub_only": True,
        "profile_and_tool_controls_supported_by_existing_signature": False,
        "actual_isolated_invoke_path_bound": False,
        "reason": "shared owner fixes --sandbox read-only and creates state environment internally; no per-call permissions/tools/env parameter",
        "proposed_adapter": "Non-launchable profile plan only. Do not replace CLI with a shim or modify the shared production owner in R3.",
    }
    write_json(out / "actual-callsite-capture.json", result)
    return result


def run_proof(repo: Path, out: Path, source_zip: Path) -> dict:
    assert sha(CLI.read_bytes()) == PINNED_SHA, "installed_cli_drift"
    assert sha(source_zip.read_bytes()) == R2_SHA, "source_zip_drift"
    out.mkdir(parents=True, exist_ok=False)
    root = out / "canaries"
    batch, home = root / "approved", root / "empty-home"
    scratch = root / "worker-private-tmp"
    for path in (batch, home / ".codex", scratch, root / "controller", root / "sibling"):
        path.mkdir(parents=True, exist_ok=False)
    outside_tmp = out / "outside-worker-tmp.txt"
    external = repo / f".m12dc-r3-canary-{out.name}"
    if external.exists():
        raise FileExistsError(external)
    external.write_text("ABSOLUTE_REPO_SYNTHETIC_R3\n")
    targets = {
        "approved": batch / "input.txt",
        "internal_scratch": scratch / "scratch.txt",
        "history": root / "controller/history.txt",
        "sibling": root / "sibling/output.txt",
        "separate_tmp_root": outside_tmp,
        "absolute_repo": external,
        "home_file": home / "private-user-canary.txt",
    }
    for name, target in targets.items():
        if name != "absolute_repo":
            target.write_text(f"SYNTHETIC_{name.upper()}_R3\n")
    targets["symlink_escape"] = batch / "history-link"
    targets["symlink_escape"].symlink_to(targets["history"])
    positive = request_artifacts(batch)
    plan = worker_plan(
        batch,
        scratch,
        home,
        [targets[x] for x in ("history", "sibling", "separate_tmp_root", "absolute_repo")],
    )
    write_json(out / "shadow-profile-plan.json", plan)
    receipts = []

    def native_run(name: str, argv: list[str], env: dict) -> dict:
        if argv[:2] != [str(CLI), "sandbox"] or "network={enabled=false}" not in argv[5]:
            raise ValueError("offline_native_boundary_required")
        command = argv[argv.index("--") + 1 :]
        if command[0] == str(CLI):
            if not ("debug" in command and "prompt-input" in command) and command[-1] != "--help":
                raise ValueError("non_diagnostic_cli_command_forbidden")
        elif command[0] != "/bin/cat":
            raise ValueError("native_probe_command_not_allowed")
        try:
            completed = subprocess.run(
                argv, cwd=batch, env=env, capture_output=True, timeout=30, check=False
            )
            stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code = error.stdout or b"", error.stderr or b"", None
        for suffix, data in (("stdout", stdout), ("stderr", stderr)):
            (out / f"{name}.{suffix}").write_bytes(data)
        row = {
            "name": name,
            "argv": argv,
            "cwd": str(batch.resolve()),
            "environment": env,
            "returncode": code,
            "stdout_sha256": sha(stdout),
            "stderr_sha256": sha(stderr),
            "stdout_file": f"{name}.stdout",
            "stderr_file": f"{name}.stderr",
        }
        receipts.append(row)
        write_json(out / "native-receipts.json", receipts)
        return row

    layouts = []
    try:
        prefix = plan["native_prefix"]
        for layout, tmp in (("R2_COLOCATED", root), ("PRIVATE_WORKER_TMP", scratch)):
            env = {**plan["environment"], "TMPDIR": str(tmp.resolve())}
            rows = []
            for name, target in targets.items():
                data = target.read_bytes()
                receipt = native_run(f"{layout}-{name}", [*prefix, "/bin/cat", str(target)], env)
                rows.append(
                    {
                        "case": name,
                        "requested_path": str(target),
                        "realpath": str(target.resolve()),
                        "target_sha256": sha(data),
                        "controller_exists_and_exact_read": True,
                        "is_symlink": target.is_symlink(),
                        "receipt": receipt["name"],
                        "outcome": read_outcome(
                            receipt["returncode"],
                            (out / receipt["stdout_file"]).read_bytes(),
                            (out / receipt["stderr_file"]).read_bytes(),
                            data,
                        ),
                    }
                )
            layouts.append(
                {
                    "layout": layout,
                    "TMPDIR": env["TMPDIR"],
                    "same_cwd_and_argv_policy": True,
                    "tests": rows,
                }
            )
            write_json(out / "native-layout-comparison.json", layouts)

        # Serializer runs are controller diagnostics, not model tool execution.
        # Their outer read scope permits controlled marker discovery; the bounded
        # proposed policy is serialized inside and never misreported as dispatch.
        markers = {
            "project": "PROJECT_BOOTSTRAP_MARKER_R3",
            "parent": "PARENT_BOOTSTRAP_MARKER_R3",
            "home": "HOME_BOOTSTRAP_MARKER_R3",
            "skill": "PROJECT_SKILL_MARKER_R3",
        }
        (batch / "AGENTS.md").write_text(markers["project"] + "\n")
        (root / "AGENTS.md").write_text(markers["parent"] + "\n")
        (home / ".codex/AGENTS.md").write_text(markers["home"] + "\n")
        skill = batch / ".agents/skills/synthetic-offline-marker"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: synthetic-offline-marker\ndescription: PROJECT_SKILL_MARKER_R3\n---\nOffline marker only.\n"
        )
        diagnostic = native_prefix("diagnostic", batch, {"/": "read", str(root.resolve()): "write"})
        env = dict(plan["environment"])
        feature_flags = [a for item in DISABLE for a in ("--disable", item)]
        common = [
            "-c",
            prefix[5],
            "-c",
            'default_permissions="bounded"',
            "-c",
            'approval_policy="never"',
            "-c",
            'web_search="disabled"',
        ]
        surfaces = []
        for name, controls in (
            ("discovery-default", []),
            (
                "discovery-bounded",
                [
                    *feature_flags,
                    "--enable",
                    "skip_host_skill_discovery",
                    "-c",
                    "project_doc_max_bytes=0",
                ],
            ),
        ):
            row = native_run(
                name,
                [
                    *diagnostic,
                    str(CLI),
                    *common,
                    *controls,
                    "debug",
                    "prompt-input",
                    (batch / "prompt.txt").read_text(),
                ],
                env,
            )
            text = (out / row["stdout_file"]).read_text()
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            surfaces.append(
                {
                    "name": name,
                    "returncode": row["returncode"],
                    "json_type": type(parsed).__name__,
                    "message_count": len(parsed) if isinstance(parsed, list) else None,
                    "markers_present": {k: value in text for k, value in markers.items()},
                    "approved_input_present": "CURRENT_INPUT_R3" in text,
                    "full_tool_registry_captured": False,
                    "provider_envelope_captured": False,
                }
            )
        for name, args in (
            ("debug-help", ["debug", "--help"]),
            ("debug-app-server-help", ["debug", "app-server", "--help"]),
        ):
            native_run(name, [*diagnostic, str(CLI), *args], env)
        write_json(out / "bootstrap-surface-comparison.json", surfaces)
        invocation = capture_existing_invocation(repo, out, batch, env)
        policy_hashes = {}
        for name in OWNER_PATHS:
            path = repo / name
            expected = subprocess.check_output(["git", "-C", str(repo), "show", f"{R1}:{name}"])
            assert path.read_bytes() == expected, name
            policy_hashes[name] = sha(expected)
        result = {
            "base": BASE,
            "work_instruction_commit": INSTRUCTION,
            "binary_sha256": PINNED_SHA,
            "source_r2_sha256": R2_SHA,
            "source_r2_evidence_reaudited": False,
            "mechanism_N": {
                "status": "UNPROVEN",
                "reason": "installed partial serializer/help lacks complete resolved tool registry and no-network synthetic dispatch interface; no version-matched native registry source found in inspected app resources",
                "synthetic_tool_dispatch_attempts": 0,
                "configuration_not_enforcement": True,
            },
            "mechanism_F": {"status": "LOCAL_TOPOLOGY_DIAGNOSTIC_ONLY", "layouts": layouts},
            "bootstrap_surfaces": surfaces,
            "receipts": receipts,
            "request_positive_control": positive,
            "actual_isolated_invoke_path_bound": invocation["actual_isolated_invoke_path_bound"],
            "unchanged_owner_sha256": policy_hashes,
            "terminal": "M12DC_R3_SUPPORTED_RUNTIME_BOUNDARY_UNAVAILABLE_REQUIRES_SEPARATE_DECISION",
            "safety": {
                key: 0
                for key in (
                    "model_calls",
                    "provider_calls",
                    "synthetic_inference_calls",
                    "external_network_calls",
                    "source_refresh",
                    "production_changes",
                    "credential_reads",
                    "credential_copies",
                    "merge",
                    "push",
                    "deploy",
                    "scheduler_changes",
                    "send",
                    "original_output_changes",
                )
            },
        }
        write_json(out / "offline-proof.json", result)
        return result
    finally:
        external.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    args = parser.parse_args()
    result = run_proof(args.repo.resolve(), args.out.resolve(), args.source_zip.resolve())
    print(
        json.dumps(
            {k: result[k] for k in ("terminal", "mechanism_F", "bootstrap_surfaces", "safety")},
            indent=2,
        )
    )
