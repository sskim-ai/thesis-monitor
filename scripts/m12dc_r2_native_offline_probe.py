"""Finite native CLI diagnostics with no auth, inference, or external network."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from scripts.m12dc_r2_offline_exposure_audit import sha, write_json


CLI = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
PINNED_SHA = "c147aa90d34139599711fb568102ceefc6319ca1ac5cb6f4056ca46a1834edd9"
DISABLE = (
    "shell_tool",
    "unified_exec",
    "code_mode",
    "code_mode_host",
    "plugins",
    "apps",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "view_image",
    "image_generation",
    "multi_agent",
    "multi_agent_v2",
    "skill_search",
    "workspace_dependencies",
    "memories",
    "hooks",
    "shell_snapshot",
)


def serialize_existing_probe(out: Path) -> dict:
    """Inspect the exact tested profile, still behind native network denial."""
    data = json.loads((out / "offline-access-control-results.json").read_text())
    debug = next(row for row in data["receipts"] if row["name"] == "offline-requested-prompt-input")
    bounded = next(row for row in data["receipts"] if row["name"] == "native-bounded-approved")
    argv = list(debug["argv"])
    if argv[:2] != [str(CLI), "sandbox"] or bounded["argv"][:4] != [
        str(CLI),
        "sandbox",
        "-P",
        "bounded",
    ]:
        raise ValueError("unexpected_local_probe_command")
    offset = argv.index("debug")
    argv[offset:offset] = [
        "-c",
        bounded["argv"][5],
        "-c",
        'default_permissions="bounded"',
        "-c",
        'approval_policy="never"',
    ]
    scratch = out / "canaries"
    env = {
        "HOME": str(scratch / "empty-home"),
        "CODEX_HOME": str(scratch / "empty-home/.codex"),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "TMPDIR": str(scratch),
        "LANG": "en_US.UTF-8",
    }
    process = subprocess.run(
        argv, env=env, cwd=scratch / "approved-batch", capture_output=True, timeout=30, check=False
    )
    (out / "bounded-effective-prompt-input.json").write_bytes(process.stdout)
    (out / "bounded-effective-prompt-input.stderr").write_bytes(process.stderr)
    result = {
        "argv": argv,
        "returncode": process.returncode,
        "sha256": sha(process.stdout),
        "model_calls": 0,
        "network_disabled_by_outer_native_profile": True,
        "credential_files_provided": 0,
    }
    write_json(out / "bounded-effective-prompt-input-receipt.json", result)
    return result


def probe(out: Path, repo: Path) -> dict:
    if sha(CLI.read_bytes()) != PINNED_SHA:
        raise ValueError("installed_cli_identity_changed")
    out.mkdir(parents=True, exist_ok=False)
    scratch = out / "canaries"
    batch = scratch / "approved-batch"
    home = scratch / "empty-home"
    codex_home = home / ".codex"
    history = scratch / "historical-report.txt"
    sibling = scratch / "sibling-batch" / "output.txt"
    for directory in (batch, codex_home, sibling.parent):
        directory.mkdir(parents=True)
    (batch / "evidence.txt").write_text("APPROVED_BATCH_CANARY\n")
    history.write_text("HISTORICAL_REPORT_CANARY\n")
    sibling.write_text("SIBLING_OUTPUT_CANARY\n")
    (batch / "history-link").symlink_to(history)
    environment = {
        "HOME": str(home),
        "CODEX_HOME": str(codex_home),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "TMPDIR": str(scratch),
        "LANG": "en_US.UTF-8",
    }
    receipts = []

    def run(name: str, argv: list[str], timeout: int = 20) -> dict:
        try:
            result = subprocess.run(
                argv, cwd=batch, env=environment, capture_output=True, timeout=timeout, check=False
            )
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, code = exc.stdout or b"", exc.stderr or b"", None
            timed_out = True
        (out / f"{name}.stdout").write_bytes(stdout)
        (out / f"{name}.stderr").write_bytes(stderr)
        row = {
            "name": name,
            "argv": argv,
            "cwd": str(batch),
            "environment_keys": sorted(environment),
            "credentials_present": False,
            "returncode": code,
            "timeout": timed_out,
            "stdout_sha256": sha(stdout),
            "stderr_sha256": sha(stderr),
        }
        receipts.append(row)
        return row

    for name, args in (
        ("version", ["--version"]),
        ("exec-help", ["exec", "--help"]),
        ("sandbox-help", ["sandbox", "--help"]),
        ("debug-prompt-help", ["debug", "prompt-input", "--help"]),
        ("default-features", ["features", "list"]),
    ):
        run(name, [str(CLI), *args])
    requested = [arg for feature in DISABLE for arg in ("--disable", feature)]
    requested.extend(["--enable", "skip_host_skill_discovery"])
    run("requested-no-tools-features", [str(CLI), *requested, "features", "list"])

    def native_profile(name: str, entries: list[dict]) -> list[str]:
        entries_toml = ",".join(
            json.dumps(row["path"]) + "=" + json.dumps(row["access"]) for row in entries
        )
        config = (
            "permissions." + name + "={filesystem={" + entries_toml + "},network={enabled=false}}"
        )
        return [str(CLI), "sandbox", "-P", name, "-c", config, "-C", str(batch), "--"]

    native = native_profile("allread", [{"path": "/", "access": "read"}])
    platform_roots = [":minimal"]
    bounded = native_profile(
        "bounded",
        [
            *[{"path": path, "access": "read"} for path in platform_roots],
            *[
                {"path": path, "access": "deny"}
                for path in ("/tmp", "/private/tmp", "/var/folders", "/private/var/folders")
            ],
            {"path": str(batch), "access": "read"},
        ],
    )
    targets = {
        "approved": batch / "evidence.txt",
        "historical": history,
        "sibling": sibling,
        "symlink": batch / "history-link",
        "absolute-repo": repo
        / "docs/work-instructions/20260919-m12dc-r2-runtime-input-isolation-and-exposure-accounting-offline-proof.md",
    }
    access = []
    for name, target in targets.items():
        row = run("native-readonly-" + name, [*native, "/bin/cat", str(target)])
        restricted = run("native-bounded-" + name, [*bounded, "/bin/cat", str(target)])
        content = target.read_bytes()
        matches = (out / f"native-readonly-{name}.stdout").read_bytes() == content
        bounded_stdout = (out / f"native-bounded-{name}.stdout").read_bytes()
        bounded_stderr = (out / f"native-bounded-{name}.stderr").read_text()
        access.append(
            {
                "case": name,
                "target": str(target),
                "target_sha256": sha(content),
                "controller_readable": True,
                "worker_native_readonly_readable": row["returncode"] == 0 and matches,
                "returncode": row["returncode"],
                "stdout_matches_target": matches,
                "bounded_returncode": restricted["returncode"],
                "bounded_readable": restricted["returncode"] == 0 and bounded_stdout == content,
                "bounded_denied_by_os": restricted["returncode"] == 1
                and (
                    "Operation not permitted" in bounded_stderr
                    or "Permission denied" in bounded_stderr
                )
                and content not in bounded_stdout,
            }
        )
    # This native sandbox enforces no network while rendering a harmless local debug input.
    # It is a diagnostic serializer only: no `exec`, turn/start, auth, or model request.
    debug_native = native_profile(
        "debugoffline", [{"path": "/", "access": "read"}, {"path": str(scratch), "access": "write"}]
    )
    debug = run(
        "offline-requested-prompt-input",
        [
            *debug_native,
            str(CLI),
            *requested,
            "-c",
            "project_doc_max_bytes=0",
            "-c",
            'web_search="disabled"',
            "debug",
            "prompt-input",
            "SYNTHETIC_OFFLINE_INPUT_CANARY",
        ],
        timeout=30,
    )
    result = {
        "installed_cli_sha256": PINNED_SHA,
        "receipts": receipts,
        "access_tests": access,
        "bounded_platform_roots": platform_roots,
        "original_readonly_mode_is_read_allowlist": False
        if all(row["worker_native_readonly_readable"] for row in access)
        else "NOT_ESTABLISHED_BY_THIS_PROBE",
        "requested_no_tool_features": list(DISABLE),
        "feature_config_not_tool_dispatch_proof": True,
        "prompt_debug_returncode": debug["returncode"],
        "provider_behavior_measured": False,
        "no_tools_dispatch_enforcement": "UNOBSERVABLE_WITH_AVAILABLE_OFFLINE_FEATURE_LIST",
        "network_successes": 0,
        "model_inference_calls": 0,
        "credentials_copied": 0,
        "production_config_changes": 0,
        "new_transport_installed": 0,
        "scope": "Native local command sandbox + installed feature introspection only. No fake tool dispatcher; no provider request.",
    }
    write_json(out / "offline-access-control-results.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--serialize-existing", action="store_true")
    args = parser.parse_args()
    if args.serialize_existing:
        print(json.dumps(serialize_existing_probe(args.out.resolve()), indent=2))
    else:
        result = probe(args.out.resolve(), args.repo.resolve())
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in (
                        "access_tests",
                        "prompt_debug_returncode",
                        "provider_behavior_measured",
                        "model_inference_calls",
                    )
                },
                indent=2,
            )
        )
