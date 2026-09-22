"""M12DS host-authorized parent, unchanged official child and financial semantics."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import traceback

from scripts import m12dr_fresh_blind_reproof as previous
from scripts import m12ds_launch_context as launch
from scripts.m12dr_offline_source_closure import read, sha, write

IDENTITY = "M12DS_CONTINUATION_FROM_M12DR_SOURCE_AND_BLIND_NO_MODEL_OUTPUT_REUSE"


def setup(root):
    previous.require(not (root / "report/launch-freeze.json").exists(), "ALREADY_FROZEN")
    previous.require(read(root / "report/launch-parity.json")["status"] == "PASS", "LAUNCH_PARITY_REQUIRED")
    launch.immutable_baseline()
    previous.require(not previous.git_state(previous.REPO)["status"], "IMPLEMENTATION_COMMIT_REQUIRED")
    for name in ("snapshot", "source"):
        shutil.copytree(launch.BASE / name, root / name)
    for name in ("source-coverage.json", "source-input-binding.json", "quality-receipts.json", "issuer-business-projection.json", "blind-leakage-audit.json"):
        shutil.copy2(launch.BASE / "report" / name, root / "report" / name)
    # Preserve the opaque blind archive byte-for-byte; never open or regenerate it.
    for name in ("m12dr-live-data-blind-pack.zip", "m12dr-live-data-blind-pack.zip.sha256"):
        shutil.copy2(launch.BASE / name, root / name)
    requests = root / "sealed/requests"
    shutil.copytree(launch.BASE / "sealed/requests/core", requests / "core")
    rows = []
    for item in read(launch.BASE / "sealed/core-request-manifest.json")["requests"]:
        relative = Path(item["directory"]).relative_to(launch.BASE / "sealed/requests/core")
        rows.append({**item, "directory": str(requests / "core" / relative)})
    write(root / "sealed/core-request-manifest.json", {"requests": rows, "files": previous.manifest(requests / "core")})
    policy = read(launch.INSTRUCTION / "m12ds-launch-canary.json")
    dest = requests / "canary"
    dest.mkdir()
    prompt = ("Tiny launch-context canary. Use only this input, no tools or external data. "
              "Return the exact nonce, integer sum of left and right, label LAUNCH_CONTEXT_OK, "
              "and external_data_used false. Return only the JSON object.\n"
              + previous.json.dumps(policy["input"], sort_keys=True) + "\n")
    (dest / "prompt.txt").write_text(prompt)
    schema = {"type": "object", "additionalProperties": False,
              "required": ["nonce", "sum", "label", "external_data_used"],
              "properties": {"nonce": {"type": "string", "enum": [policy["input"]["nonce"]]},
                             "sum": {"type": "integer"}, "label": {"type": "string", "enum": ["LAUNCH_CONTEXT_OK"]},
                             "external_data_used": {"type": "boolean"}}}
    for name in ("provider-wire-schema.json", "internal-semantic-schema.json"):
        write(dest / name, schema)
    previous.require(not previous.owner.validate_json_schema(policy["expected_output"], schema), "CANARY_SCHEMA_INVALID")
    old = read(launch.BASE / "report/execution-freeze.json")
    previous.require(previous.manifest(requests / "core") == old["core_requests"], "M12DS_CORE_REQUEST_IDENTITY_DRIFT")
    freeze = {"identity": IDENTITY, "frozen_at": previous.now(),
              "canary_generation_id": "20260921-m12ds-canary-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
              "source_generation_id": old["source_generation_id"], "source": previous.manifest(root / "source"),
              "snapshot": previous.manifest(root / "snapshot"), "core_requests": old["core_requests"],
              "canary_requests": previous.manifest(dest), "blind_zip_sha256": old["blind_zip_sha256"],
              "controller": previous.git_state(previous.REPO), "operating": previous.git_state(previous.OPERATING),
              "code": previous.code_manifest(), "instructions": previous.manifest(launch.INSTRUCTION),
              "launch_parity_sha256": sha(root / "report/launch-parity.json"),
              "model": "gpt-5.6-sol", "effort": "xhigh", "timeout_seconds": 1200,
              "retries": 0, "fallback": 0, "judge": 0, "repair": 0,
              "max_calls": {"canary": 1, "core": 8, "pass-a": 8, "pass-b": 8},
              "launch_path": "Reproof.invoke -> unchanged invoke_official_shadow", "child_sandbox": "read-only"}
    write(root / "report/launch-freeze.json", freeze)
    print("M12DS freeze PASS: same blind/source/Core request bytes; model_calls=0", flush=True)


class Reproof(previous.Reproof):
    def __init__(self, root):
        super().__init__(root)
        self.frozen = read(root / "report/launch-freeze.json")
        self.gen = self.frozen["canary_generation_id"]
        self.canary_passed = False

    def verify(self):
        try:
            super().verify()
            previous.require(previous.manifest(launch.INSTRUCTION) == self.frozen["instructions"], "INSTRUCTION_DRIFT")
            previous.require(sha(self.report / "launch-parity.json") == self.frozen["launch_parity_sha256"], "LAUNCH_PARITY_DRIFT")
            previous.require(previous.manifest(self.requests / "core") == self.frozen["core_requests"], "M12DS_CORE_REQUEST_IDENTITY_DRIFT")
            previous.require(previous.manifest(self.requests / "canary") == self.frozen["canary_requests"], "CANARY_REQUEST_DRIFT")
            launch.immutable_baseline()
        except (previous.BatchFailure, previous.transport.OfficialShadowError, AssertionError) as exc:
            raise previous.SystemicFailure(str(exc)) from exc

    def transport_failure(self, exc, destination, elapsed):
        log = destination / "events.jsonl"
        err = destination / "events.jsonl.stderr"
        kind = launch.known_failure(exc.code, elapsed=elapsed, events=log.read_bytes() if log.exists() else b"",
            final_exists=(destination / "raw-output.json").exists(), stderr=err.read_text() if err.exists() else "")
        if kind:
            raise previous.SystemicFailure(kind) from exc
        super().transport_failure(exc, destination, elapsed)

    def invoke(self, stage, spec, request):
        context = launch.context_receipt()
        host = read(self.report / "host-context.json")
        allowed = context["state_access"]["effective_open_readwrite_without_write"]
        allowed &= context["uid"] == host["uid"] and context["gid"] == host["gid"]
        allowed &= context["safe_environment"] == host["safe_environment"]
        if not allowed:
            raise previous.SystemicFailure("HOST_LAUNCH_CONTEXT_DRIFT")
        write(self.report / "launch-contexts" / f"{stage}-{spec['market']}-{spec['batch']}.json", context)
        result = super().invoke(stage, spec, request)
        runtime = Path("/private/tmp") / self.gen / stage / spec["market"] / f"batch-{spec['batch']:02d}"
        write(self.report / "launch-contexts" / f"{stage}-{spec['market']}-{spec['batch']}-child-cwd.json",
              {"request_cwd": str(runtime / "approved-input"), "access": launch.path_access(runtime / "approved-input"),
               "child_sandbox": "read-only", "state_namespace": f"{self.gen}-{stage}-{spec['market']}-{spec['batch']:02d}"})
        stderr = (runtime / "events.jsonl.stderr").read_text().lower()
        if any(s in stderr for s in ("attempt to write a readonly database", "unknownissuer", "invalid peer certificate")):
            raise previous.SystemicFailure("OFFICIAL_RUNTIME_WARNING_RECURRED")
        if "failed to initialize in-process app-server client" in stderr:
            raise previous.SystemicFailure("APP_SERVER_INITIALIZATION_FAILURE")
        return result

    def bounded(self, stage, spec, callback):
        try:
            return super().bounded(stage, spec, callback)
        except previous.SystemicFailure as exc:
            self.ledger[-1].update(status="SYSTEMIC_STOP", failure_code=str(exc))
            self.publish()
            raise

    def canary(self):
        spec = {"market": "synthetic", "batch": 1, "subjects": []}
        request = {"directory": str(self.requests / "canary")}

        def callback():
            output, dest = self.invoke("canary", spec, request)
            expected = read(launch.INSTRUCTION / "m12ds-launch-canary.json")["expected_output"]
            previous.require(output == expected, "CANARY_SEMANTIC_REJECT")
            self.receipt(dest / "semantic.json", {"status": "PASS", "exact_output": True})
            self.canary_passed = True

        self.bounded("canary", spec, callback)
        write(self.report / "canary-complete.json", {"status": "PASS" if self.canary_passed else "FAIL",
              "generation_id": self.gen, "calls": 1, "core_calls": 0, "retries": 0, "completed_at": previous.now()})
        previous.require(self.canary_passed, "M12DS_LAUNCH_CANARY_FAILED")

    def run(self):
        previous.require(not (self.report / "model-structural-ledger.json").exists(), "ONE_EXECUTION_ONLY")
        terminal, failure = "M12DS_RUNTIME_OR_SECURITY_STOP", None
        stage = "canary"
        try:
            self.verify()
            self.canary()
            self.gen = "20260921-m12ds-blind-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + self.frozen["controller"]["head"][:8]
            self.frozen = {**self.frozen, "generation_id": self.gen, "canary_completed_at": previous.now(),
                           "canary_receipt_sha256": sha(self.report / "canary-complete.json")}
            write(self.report / "execution-freeze.json", self.frozen)
            stage = "core"
            requests = read(self.sealed / "core-request-manifest.json")["requests"]
            for spec, request in zip(previous.owner._batch_topology(), requests, strict=True):
                self.bounded(stage, spec, lambda spec=spec, request=request: self.core(spec, request))
            previous.require(len(self.cores) == 22, "M12DS_CORE_COMPLETED_WITH_BATCH_LOCAL_FAILURES")
            stage = "entitlement"
            self.before_a()
            stage = "pass-a"
            for spec in previous.owner._batch_topology():
                self.bounded(stage, spec, lambda spec=spec: self.pass_a(spec))
            previous.require(len(self.arows) == 22, "M12DS_PASS_A_COMPLETED_WITH_BATCH_LOCAL_FAILURES")
            write(self.sealed / "pass-a-freeze.json", {"classifications": self.arows, "frozen_at": previous.now()})
            stage = "pre-b"
            requests = self.before_b()
            stage = "pass-b"
            for spec, request in zip(previous.owner._batch_topology(), requests, strict=True):
                self.bounded(stage, spec, lambda spec=spec, request=request: self.pass_b(spec, request))
            previous.require(len(self.brows) == 22, "M12DS_PASS_B_COMPLETED_WITH_BATCH_LOCAL_FAILURES")
            final = previous.owner._finalize_rows(pass_a_rows=list(self.arows.values()), pass_b_rows=list(self.brows.values()),
                entry_rows=[{"ticker": t, "entry_range": v} for t, v in self.entries.items()], options=self.options,
                typed=self.typed, source_packets=self.subjects)
            self.verify()
            write(self.sealed / "final-results.json", {"generation_id": self.gen, "candidates": final})
            terminal = "M12DS_SAME_BLIND_FRESH_CORE_AB_PASS_READY_FOR_CHAT"
        except previous.SystemicFailure as exc:
            failure = str(exc)
            write(self.sealed / "runtime-failure.json", {"details": traceback.format_exc()})
        except Exception as exc:
            failure = str(exc) if isinstance(exc, previous.BatchFailure) else type(exc).__name__
            terminals = {"canary": "M12DS_LAUNCH_CANARY_FAILED", "core": "M12DS_CORE_COMPLETED_WITH_BATCH_LOCAL_FAILURES",
                         "entitlement": "M12DS_FRESH_CORE_DIRECTIONAL_ENTITLEMENT_INCOMPLETE",
                         "pass-a": "M12DS_PASS_A_COMPLETED_WITH_BATCH_LOCAL_FAILURES", "pre-b": "M12DS_OFFLINE_PREB_CLOSURE_FAILED",
                         "pass-b": "M12DS_PASS_B_COMPLETED_WITH_BATCH_LOCAL_FAILURES"}
            terminal = terminals[stage]
            write(self.sealed / "gate-failure.json", {"details": traceback.format_exc()})
        finally:
            write(self.report / "execution-complete.json", {"terminal": terminal, "failure_code": failure,
                "generation_id": self.gen, "source_generation_id": self.source_gen, "identity": IDENTITY,
                "canary_passed": self.canary_passed, "core_accepted": len(self.cores), "a_accepted": len(self.arows),
                "b_accepted": len(self.brows), "calls": {s: sum(r["attempts"] for r in self.ledger if r["stage"] == s)
                    for s in ("canary", "core", "pass-a", "pass-b")}, "completed_at": previous.now(),
                "comparison": "NOT_PERFORMED", "production_ready": False, "retries": 0, "source_only_inference_certified": False})
            self.publish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "run"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    setup(args.root) if args.mode == "freeze" else Reproof(args.root).run()


if __name__ == "__main__":
    main()
