"""Exact M12DS Core reuse, offline A schema closure, then fresh bounded A8/B8."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import traceback

from scripts import m12dr_fresh_blind_reproof as p
from scripts.m12ds_same_blind_reproof import Reproof as LaunchReproof
from scripts.m12ds_r1_offline_parity import audit

BASE = Path("/Users/sskim/Documents/Codex/Reports/20260921-m12ds-launch-parity")
ACCEPTED = BASE / "user-authorized-continuation-01"
INSTRUCTION = p.REPO / "docs/work-instructions/20260922-m12ds-r1"
REPORT_ZIP = BASE.parents[1] / "thesis-monitor-20260921-m12ds-official-launch-context-parity-repair-same-blind-fresh-core-ab-completion-report.zip"
SUCCESS = "M12DS_R1_PASS_A_SCHEMA_PARITY_FRESH_A8_B8_PASS_READY_FOR_CHAT"


def historical_manifest():
    return {str(path): p.sha(path) for base in (BASE / "report", BASE / "sealed", ACCEPTED / "report", ACCEPTED / "sealed")
            for path in sorted(base.rglob("*")) if path.is_file()}


def stage(root):
    baseline = p.read(INSTRUCTION / "m12ds-r1-baseline.json")["m12ds"]
    p.require(p.sha(REPORT_ZIP) == baseline["report_zip_sha256"], "M12DS_REPORT_IDENTITY")
    complete = p.read(ACCEPTED / "report/execution-complete.json")
    p.require(complete["core_accepted"] == 22 and complete["a_accepted"] == 19 and complete["b_accepted"] == 0, "M12DS_RESULT_IDENTITY")
    p.require(complete["generation_id"] == baseline["execution_generation_id"], "CORE_GENERATION_IDENTITY")
    p.require(not root.exists(), "ROOT_ALREADY_EXISTS")
    for name in ("source", "snapshot", "sealed/requests/core"):
        shutil.copytree(BASE / name, root / name)
    report = root / "report"
    report.mkdir()
    for name in ("source-coverage.json", "source-input-binding.json", "quality-receipts.json", "issuer-business-projection.json",
                 "blind-leakage-audit.json", "host-context.json", "launch-parity.json"):
        shutil.copy2(BASE / "report" / name, report / name)
    for name in ("m12dr-live-data-blind-pack.zip", "m12dr-live-data-blind-pack.zip.sha256"):
        shutil.copy2(BASE / name, root / name)
    p.require(p.sha(root / "m12dr-live-data-blind-pack.zip") == baseline["blind_pack_sha256"], "BLIND_IDENTITY")
    core_requests = p.read(BASE / "sealed/core-request-manifest.json")["requests"]
    bindings = []
    original_rows = p.read(BASE / "report/model-structural-ledger.json")["rows"]
    retry_rows = p.read(ACCEPTED / "report/model-structural-ledger.json")["rows"]
    for spec, request in zip(p.owner._batch_topology(), core_requests, strict=True):
        retry = spec["market"] == "kr" and spec["batch"] == 3
        stage_name, base = ("core-user-retry", ACCEPTED) if retry else ("core", BASE)
        row = next(r for r in (retry_rows if retry else original_rows)
                   if r["stage"] == stage_name and r["market"] == spec["market"] and r["batch"] == spec["batch"])
        source = base / "sealed/calls" / stage_name / spec["market"] / f"batch-{spec['batch']:02d}"
        p.require(row["status"] == "PASS" and p.sha(source / "raw-output.json") == row["raw_output_sha256"], "CORE_RESPONSE_IDENTITY")
        dest = root / "sealed/reused-core" / spec["market"] / f"batch-{spec['batch']:02d}"
        shutil.copytree(source, dest)
        request["directory"] = str(root / Path(request["directory"]).relative_to(BASE))
        p.require(p.sha(Path(request["directory"]) / "prompt.txt") == row["prompt_sha256"], "CORE_PROMPT_IDENTITY")
        bindings.append({**spec, "original_directory": str(source), "raw_output_sha256": row["raw_output_sha256"],
                         "prompt_sha256": row["prompt_sha256"], "core_generation_id": complete["generation_id"]})
    p.write(root / "sealed/core-request-manifest.json", {"requests": core_requests})
    p.write(report / "core-reuse-binding.json", {"bindings": bindings, "core_rerun_calls": 0})
    p.write(report / "preparation-identity.json", {"generation_id": "20260922-m12ds-r1-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "historical_files": historical_manifest(), "blind_sha256": baseline["blind_pack_sha256"],
        "model": "gpt-5.6-sol", "effort": "xhigh", "timeout_seconds": 1200})


class Reproof(LaunchReproof):
    def __init__(self, root):
        p.Reproof.__init__(self, root)
        self.preparation = p.read(self.report / "preparation-identity.json")
        self.gen = self.preparation["generation_id"]
        self.reusing_core = False
        self.frozen = p.read(self.report / "execution-freeze.json") if (self.report / "execution-freeze.json").exists() else None

    def verify(self):
        if self.frozen is None:
            raise p.SystemicFailure("IMPLEMENTATION_NOT_FROZEN")
        p.Reproof.verify(self)
        for key, base in (("core_requests", self.requests / "core"), ("a_requests", self.requests / "pass-a"),
                          ("reused_core", self.sealed / "reused-core"), ("instructions", INSTRUCTION)):
            if p.manifest(base) != self.frozen[key]:
                raise p.SystemicFailure("M12DS_R1_FROZEN_IDENTITY_MISMATCH:" + key)
        if any(p.sha(Path(path)) != value for path, value in self.preparation["historical_files"].items()):
            raise p.SystemicFailure("HISTORICAL_RECEIPT_DRIFT")
        for name, digest in self.frozen["reports"].items():
            if p.sha(self.report / name) != digest:
                raise p.SystemicFailure("OFFLINE_GATE_RECEIPT_DRIFT")
        for name, digest in self.frozen["state_files"].items():
            if p.sha(self.sealed / name) != digest:
                raise p.SystemicFailure("PREPARED_MANIFEST_OR_STATE_DRIFT")
        if (self.sealed / "b-request-freeze.json").exists():
            if p.sha(self.sealed / "b-request-freeze.json") != getattr(self, "b_freeze_sha256", None):
                raise p.SystemicFailure("B_FREEZE_MANIFEST_DRIFT")
            if p.manifest(self.requests / "pass-b") != p.read(self.sealed / "b-request-freeze.json")["files"]:
                raise p.SystemicFailure("B_REQUEST_IDENTITY_DRIFT")

    def invoke(self, stage, spec, request):
        if stage == "core":
            p.require(self.reusing_core, "CORE_RERUN_NOT_AUTHORIZED")
            src = Path(request["directory"])
            dest = self.sealed / "reused-core" / spec["market"] / f"batch-{spec['batch']:02d}"
            output = p.read(dest / "raw-output.json")
            p.require(all(not p.owner.validate_json_schema(output, p.read(src / name)) for name in
                          ("internal-semantic-schema.json", "provider-wire-schema.json")), "CORE_REUSE_SCHEMA_REJECT")
            return output, dest
        p.require(stage in ("pass-a", "pass-b"), "ONLY_A_B_AUTHORIZED")
        return super().invoke(stage, spec, request)

    def load_core(self):
        self.reusing_core = True
        for spec, request in zip(p.owner._batch_topology(), p.read(self.sealed / "core-request-manifest.json")["requests"], strict=True):
            self.core(spec, request)
        self.reusing_core = False
        p.require(len(self.cores) == 22, "CORE_REUSE_INCOMPLETE")
        old = p.read(ACCEPTED / "sealed/fresh-core-freeze.json")["cores"]
        p.require([r.model_dump(mode="json") for r in self.cores.values()] == old, "CORE_ACCEPTED_BYTES_CHANGED")

    def prepare(self):
        self.load_core()
        self.before_a()
        p.require(p.read(self.report / "future-b-entitlement.json") == p.read(ACCEPTED / "report/future-b-entitlement.json"), "FUTURE_B_ENTITLEMENT_DRIFT")
        old_context = p.read(ACCEPTED / "sealed/before-a-preflight.json")["model_contexts"]
        parity = p.owner._a_semantic_parity(self.actx, old_context)
        p.write(self.report / "a-context-substantive-parity.json", parity)
        p.require(parity["status"] == "PASS", "A_CONTEXT_SEMANTIC_DRIFT")
        requests = [p.owner._request_capture(root=self.requests, stage="pass-a", **spec, contexts=self.actx,
            catalogs=self.catalogs, chains=self.chains, generation_id=self.gen, fixture_only=False,
            raw_source_metadata_by_ticker={t: self.subjects[t]["decision_evidence"] for t in spec["subjects"]})
            for spec in p.owner._batch_topology()]
        p.write(self.sealed / "a-request-manifest.json", {"requests": requests})
        result = audit(self, requests)
        p.write(self.report / "pass-a-axis-ref-schema-parity-22.json", result)
        p.require(result["status"] == "PASS", "M12DS_R1_PASS_A_SCHEMA_PARITY_OFFLINE_FAILED")
        self.old_negative_control(requests)
        p.write(self.sealed / "prepared-state.json", {"actx": self.actx, "catalogs": self.catalogs, "subjects": self.subjects,
            "chains": self.chains, "typed": self.typed, "authorities": self.authorities})
        print("M12DS-R1 offline parity PASS: Core reused 22/22; A requests 8/8; model calls=0", flush=True)

    def old_negative_control(self, requests):
        spec = next(s for s in p.owner._batch_topology() if s["market"] == "kr" and s["batch"] == 1)
        raw = p.read(ACCEPTED / "sealed/calls/pass-a/kr/batch-01/raw-output.json")
        normal, mat = p.owner.materialize_future_pass_a(raw, subjects=tuple(spec["subjects"]), subject_contexts=self.actx)
        p.require(mat["status"] == "PASS", "OLD_MATERIALIZATION_CHANGED")
        env = p.owner.PassABatchOutput.model_validate({"contract": "m12cq-pass-a-archetype-regime-v1", **self.identity(spec), "classifications": normal})
        args = self.args(spec["subjects"])
        args["source_catalogs"] = args.pop("catalogs")
        semantic = p.owner.validate_pass_a_batch(env, expected_identity=self.identity(spec), subject_contexts=self.actx, **args)
        old = p.read(ACCEPTED / "sealed/calls/pass-a/kr/batch-01/semantic.json")
        p.require(semantic == old and semantic["status"] == "FAIL", "OLD_RESPONSE_SEMANTIC_CHANGED")
        request = next(r for r in requests if r["market"] == "kr" and r["batch"] == 1)
        schema_rejects = {name: bool(p.owner.validate_json_schema(raw, p.read(Path(request["directory"]) / name)))
                          for name in ("internal-semantic-schema.json", "provider-wire-schema.json")}
        p.require(all(schema_rejects.values()), "OLD_FORBIDDEN_SELECTION_NOT_SCHEMA_REJECTED")
        p.write(self.report / "old-failure-negative-control.json", {"status": "PASS", "old_semantic_unchanged": True,
                "error_count": 1, "schema_rejects": schema_rejects, "candidate_modified": False})

    def freeze(self):
        p.require(not p.git_state(p.REPO)["status"], "IMPLEMENTATION_COMMIT_REQUIRED")
        p.require(not (self.report / "execution-freeze.json").exists(), "ALREADY_FROZEN")
        reports = ["preparation-identity.json", "host-context.json", "core-reuse-binding.json",
                   "pass-a-axis-ref-schema-parity-22.json", "old-failure-negative-control.json",
                   "a-context-substantive-parity.json", "future-b-entitlement.json",
                   "source-core-contract-neutrality.json", "../validation/receipt.json"]
        p.require(p.read(self.report / "source-core-contract-neutrality.json")["status"] == "PASS", "SOURCE_CORE_NEUTRALITY_REQUIRED")
        p.require(all(row["status"] == "PASS" for row in p.read(self.root / "validation/receipt.json").values()), "OFFLINE_REGRESSION_REQUIRED")
        self.frozen = dict(generation_id=self.gen, source_generation_id=self.source_gen,
            controller=p.git_state(p.REPO), operating=p.git_state(p.OPERATING), code=p.code_manifest(),
            snapshot=p.manifest(self.snapshot), source=p.manifest(self.root / "source"),
            blind_zip_sha256=self.preparation["blind_sha256"], instructions=p.manifest(INSTRUCTION),
            core_requests=p.manifest(self.requests / "core"), a_requests=p.manifest(self.requests / "pass-a"),
            reused_core=p.manifest(self.sealed / "reused-core"), reports={n:p.sha(self.report / n) for n in reports},
            state_files={name:p.sha(self.sealed / name) for name in
                         ("prepared-state.json", "a-request-manifest.json", "core-request-manifest.json", "fresh-core-freeze.json")},
            prepared_state_sha256=p.sha(self.sealed / "prepared-state.json"),
            model="gpt-5.6-sol", effort="xhigh", timeout_seconds=1200, max_calls={"core":0,"pass-a":8,"pass-b":8},
            retries=0, fallback=0, judge=0, frozen_at=p.now())
        p.write(self.report / "execution-freeze.json", self.frozen)
        self.verify()
        print("M12DS-R1 execution freeze PASS; A8 complete request hashes frozen", flush=True)

    def run(self):
        p.require(not (self.report / "model-structural-ledger.json").exists(), "ONE_EXECUTION_ONLY")
        self.verify()
        p.require(p.sha(self.sealed / "prepared-state.json") == self.frozen["prepared_state_sha256"], "PREPARED_STATE_DRIFT")
        for name, value in p.read(self.sealed / "prepared-state.json").items():
            setattr(self, name, value)
        # Revalidate exact Core without any inference or changes to historical outputs.
        self.load_core()
        stage, terminal, failure = "pass-a", "M12DS_R1_RUNTIME_OR_SECURITY_STOP", None
        try:
            requests = p.read(self.sealed / "a-request-manifest.json")["requests"]
            for spec, request in zip(p.owner._batch_topology(), requests, strict=True):
                self.bounded(stage, spec, lambda spec=spec, request=request: self.pass_a(spec, request))
            p.require(len(self.arows) == 22, "M12DS_R1_PASS_A_COMPLETED_WITH_BATCH_LOCAL_FAILURES")
            p.write(self.sealed / "pass-a-freeze.json", {"classifications": self.arows, "frozen_at":p.now()})
            stage = "pre-b"
            requests = self.before_b()
            self.b_freeze_sha256 = p.sha(self.sealed / "b-request-freeze.json")
            stage = "pass-b"
            for spec, request in zip(p.owner._batch_topology(), requests, strict=True):
                self.bounded(stage, spec, lambda spec=spec, request=request: self.pass_b(spec, request))
            p.require(len(self.brows) == 22, "M12DS_R1_FRESH_B8_COMPLETED_WITH_BATCH_LOCAL_FAILURES")
            final = p.owner._finalize_rows(pass_a_rows=list(self.arows.values()), pass_b_rows=list(self.brows.values()),
                entry_rows=[{"ticker":t,"entry_range":v} for t,v in self.entries.items()], options=self.options,
                typed=self.typed, source_packets=self.subjects)
            self.verify()
            p.write(self.sealed / "final-results.json", {"generation_id":self.gen,"candidates":final})
            terminal = SUCCESS
        except p.SystemicFailure as exc:
            failure = str(exc)
            p.write(self.sealed / "runtime-failure.json", {"details":traceback.format_exc()})
        except Exception as exc:
            failure = str(exc) if isinstance(exc,p.BatchFailure) else type(exc).__name__
            terminal = {"pass-a":"M12DS_R1_PASS_A_COMPLETED_WITH_BATCH_LOCAL_FAILURES",
                        "pre-b":"M12DS_R1_OFFLINE_PREB_CLOSURE_FAILED",
                        "pass-b":"M12DS_R1_FRESH_B8_COMPLETED_WITH_BATCH_LOCAL_FAILURES"}[stage]
            p.write(self.sealed / "gate-failure.json", {"details":traceback.format_exc()})
        finally:
            p.write(self.report / "execution-complete.json", {"terminal":terminal,"failure_code":failure,
                "generation_id":self.gen,"source_generation_id":self.source_gen,"core_reused":len(self.cores),
                "a_accepted":len(self.arows),"b_accepted":len(self.brows),
                "calls":{s:sum(r["attempts"] for r in self.ledger if r["stage"]==s) for s in ("core","pass-a","pass-b")},
                "retries":0,"fallback":0,"judge":0,"completed_at":p.now(),
                "comparison":"NOT_PERFORMED","production_ready":False,"source_only_inference_certified":False})
            self.publish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("stage","prepare","freeze","run"))
    parser.add_argument("--root",type=Path,required=True)
    args = parser.parse_args()
    if args.mode == "stage":
        stage(args.root)
    else:
        getattr(Reproof(args.root),args.mode)()


if __name__ == "__main__":
    main()
