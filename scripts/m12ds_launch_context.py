"""Safe, offline parent-launch evidence and narrow startup classification."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import tempfile

from scripts import m12dr_fresh_blind_reproof as previous
from scripts.m12dr_offline_source_closure import read, sha, write

CONTRACT = "m12ds-official-codex-launch-context-parity-v1"
KNOWN_GOOD = Path("/Users/sskim/Documents/Codex/Reports/20260921-m12dm-qualified-transport-canary")
BASE = Path("/Users/sskim/Documents/Codex/Reports/20260921-m12dr-quality-isolation/reproof")
INSTRUCTION = previous.REPO / "docs/work-instructions/20260921-m12ds"
HELPER = "app/services/official_codex_shadow_transport_service.py"
STARTUP_WINDOW_SECONDS = 5
SAFE_MARKERS = ("CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED", "CODEX_THREAD_ID", "CODEX_INTERNAL_ORIGINATOR_OVERRIDE")


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def path_access(path, *, open_existing=False, probe_directory=False):
    path = path.resolve()
    st = path.stat()
    result = {"path_sha256": digest(str(path)), "uid": st.st_uid, "gid": st.st_gid,
              "mode": oct(stat.S_IMODE(st.st_mode)), "read_access_advisory": os.access(path, os.R_OK),
              "write_access_advisory": os.access(path, os.W_OK)}
    if open_existing:
        # Open without truncation, SQLite, or write calls; never mutate state bytes.
        try:
            fd = os.open(path, os.O_RDWR)
            os.close(fd)
            result["effective_open_readwrite_without_write"] = True
        except OSError as exc:
            result.update(effective_open_readwrite_without_write=False, access_errno=exc.errno)
    if probe_directory:
        try:
            with tempfile.TemporaryFile(dir=path) as stream:
                stream.write(b"M12DS launch access probe\n")
                stream.flush()
            result["effective_temporary_write"] = True
        except OSError as exc:
            result.update(effective_temporary_write=False, access_errno=exc.errno)
    return result


def context_receipt():
    policy = read(INSTRUCTION / "m12ds-launch-context-parity-contract.json")
    names = sorted(set(policy["safe_env_inventory"] + list(SAFE_MARKERS) + [
        "http_proxy", "https_proxy", "all_proxy", "no_proxy", "GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", "NIX_SSL_CERT_FILE"]))
    env = {key: {"present": key in os.environ, "sha256": digest(os.environ[key]) if key in os.environ else None}
           for key in names}
    home = Path(os.environ["HOME"])
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
    state = codex_home / "state_5.sqlite"
    ancestry, pid = [], os.getpid()
    try:
        for _ in range(5):
            line = subprocess.check_output(["ps", "-p", str(pid), "-o", "pid=,ppid=,comm="], text=True, stderr=subprocess.DEVNULL).strip()
            parts = line.split(None, 2)
            if len(parts) != 3:
                break
            ancestry.append({"pid": int(parts[0]), "ppid": int(parts[1]), "executable": parts[2]})
            pid = int(parts[1])
            if not pid:
                break
    except (OSError, subprocess.CalledProcessError):
        ancestry.append({"status": "PROCESS_METADATA_ACCESS_DENIED"})
    return {"contract": CONTRACT, "at": previous.now(), "uid": os.geteuid(), "gid": os.getegid(),
            "cwd": str(Path.cwd().resolve()), "cwd_access": path_access(Path.cwd(), probe_directory=True),
            "home_access": path_access(home), "codex_home_access": path_access(codex_home),
            "tmp_access": path_access(Path(os.environ.get("TMPDIR", tempfile.gettempdir())), probe_directory=True),
            "state_path": str(state), "state_access": path_access(state, open_existing=True),
            "state_parent": path_access(state.parent), "safe_environment": env, "ancestry": ancestry,
            "state_db_write_calls": 0, "state_permissions_modified": False}


def known_failure(code, *, elapsed, events, final_exists, stderr):
    """Only typed pre-dispatch failures escalate; ordinary timeout/nonzero stays local."""
    lowered = stderr.lower()
    if any(marker in lowered for marker in ("unknownissuer", "invalid peer certificate", "certificate verify failed")):
        return "CERTIFICATE_TRUST_FAILURE"
    if code != "PROCESS_NONZERO" or events.strip() or final_exists or not 0 <= elapsed <= STARTUP_WINDOW_SECONDS:
        return None
    if "attempt to write a readonly database" in lowered:
        return "OFFICIAL_STATE_DB_READONLY"
    if "failed to initialize in-process app-server client" in lowered and "operation not permitted" in lowered:
        return "APP_SERVER_INITIALIZATION_PERMISSION_DENIED"
    return None


def immutable_baseline():
    instruction = read(INSTRUCTION / "m12ds-baseline.json")
    freeze = read(BASE / "report/execution-freeze.json")
    archives = BASE.parents[2]
    for pattern, expected in (
        ("thesis-monitor-20260921-m12dr-*-report.zip", instruction["m12dr"]["report_zip_sha256"]),
        ("thesis-monitor-20260921-m12dm-*-report.zip", instruction["known_good_official_runtime"]["source_report_zip_sha256"]),
    ):
        matches = list(archives.glob(pattern))
        assert len(matches) == 1 and sha(matches[0]) == expected, "Baseline archive drift"
    assert sha(BASE / "m12dr-live-data-blind-pack.zip") == instruction["m12dr"]["blind_pack_sha256"]
    for section, root in (("snapshot", BASE / "snapshot"), ("source", BASE / "source"),
                          ("core_requests", BASE / "sealed/requests/core")):
        assert previous.manifest(root) == freeze[section], section + " identity drift"
    assert not list((BASE / "sealed/calls").rglob("raw-output.json")), "M12DR output must be empty"
    assert read(BASE / "report/execution-complete.json")["core_accepted"] == 0
    previous.transport.validate_binding(previous.binding(), str(previous.BIN))
    helper = previous.REPO / HELPER
    old = subprocess.check_output(["git", "show", "4a700efe205ee46e0c14e31b5e29590bb0d5788f:" + HELPER], cwd=previous.REPO)
    assert hashlib.sha256(old).hexdigest() == sha(helper), "Known-good helper drift"
    changed = [name for name, expected in freeze["code"].items() if sha(previous.REPO / name) != expected]
    assert changed in ([], ["scripts/m12dr_fresh_blind_reproof.py"]), "Unapproved semantic change"
    return {"status": "PASS", "blind_sha256": sha(BASE / "m12dr-live-data-blind-pack.zip"),
            "source_generation_id": freeze["source_generation_id"], "core_request_file_count": len(freeze["core_requests"]),
            "core_request_manifest_sha256": sha(BASE / "sealed/core-request-manifest.json"),
            "helper_sha256": sha(helper), "binary_sha256": sha(previous.BIN),
            "qualification_sha256": sha(previous.QUALIFICATION), "permitted_runner_changes": changed}


def parity(root):
    restricted = read(root / "report/restricted-context.json")
    host = read(root / "report/host-context.json")
    good = read(KNOWN_GOOD / "report/canary-complete.json")
    started = read(KNOWN_GOOD / "report/canary-started.json")
    baseline = immutable_baseline()
    assert good["process_exit_0"] and good["exact_semantic_pass"]
    assert good["unknown_events"] == good["prohibited_tool_events"] == 0
    persistent = not host["state_access"]["effective_open_readwrite_without_write"]
    same_fs = all(host["state_access"][key] == restricted["state_access"][key] for key in ("path_sha256", "uid", "gid", "mode"))
    if persistent:
        category = "PERSISTENT_CODEX_STATE_PERMISSION_DEFECT"
    elif same_fs and not restricted["state_access"]["effective_open_readwrite_without_write"]:
        category = "PARENT_LAUNCH_CONTEXT_RESTRICTED"
    else:
        category = "UNRESOLVED_LAUNCH_CONTEXT"
    env_drift = []
    for item in read(KNOWN_GOOD / "report/canary-request-freeze.json")["environment_fingerprint"]:
        if host["safe_environment"][item["name"]] != {k: item[k] for k in ("present", "sha256")}:
            env_drift.append(item["name"])
    assert not env_drift, "Known-good proxy/custom CA environment drift"
    receipt = {"contract": CONTRACT, "status": "PASS" if category == "PARENT_LAUNCH_CONTEXT_RESTRICTED" else "FAIL",
               "primary_category": category, "baseline": baseline, "state_owner_mode_unchanged_between_contexts": same_fs,
               "known_good_execution_context": started["execution_context"], "known_good_elapsed_seconds": good["elapsed_seconds"],
               "known_good_parent_uid_gid_ancestry": "NOT_RECORDED_IN_HISTORICAL_RECEIPT",
               "prior_parent_context_not_reconstructed": True, "environment_drift": env_drift,
               "repair": "HOST_AUTHORIZED_PARENT_ONLY_CHILD_FLAGS_UNCHANGED", "state_db_mutation": 0,
               "canary_required": True, "model_calls": 0}
    signed = subprocess.run(["/usr/bin/codesign", "-dv", "--verbose=2", str(previous.BIN)], capture_output=True, text=True, check=False)
    receipt["codesign"] = {"exit_code": signed.returncode, "identity": [line for line in signed.stderr.splitlines()
        if line.startswith(("Identifier=", "TeamIdentifier=", "Authority=", "Format="))]}
    receipt["qualified_runtime"] = {"version": previous.binding().version, "auth_method": previous.binding().auth_method,
        "command_prefix": list(previous.transport.COMMAND_PREFIX), "timeout_seconds": 1200,
        "historical_state_namespace": read(KNOWN_GOOD / "report/canary-request-freeze.json")["request_id"]}
    receipt["prior_child_cwd_current_metadata"] = {}
    for label, path in (("known_good", Path("/private/tmp/thesis-monitor-m12dm-20260921/canary/approved-input")),
                        ("failed", Path("/private/tmp/20260921-m12dr-blind-20260921T125717Z-d9907928/core/us/batch-01/approved-input"))):
        receipt["prior_child_cwd_current_metadata"][label] = path_access(path) if path.exists() else {"status": "NO_LONGER_PRESENT"}
    write(root / "report/launch-parity.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("restricted", "host", "parity"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "parity":
        result = parity(args.root)
        print(result["primary_category"], result["status"])
    else:
        write(args.root / "report" / f"{args.mode}-context.json", context_receipt())
        print(args.mode + " context captured; model_calls=0; state_db_writes=0")


if __name__ == "__main__":
    main()
