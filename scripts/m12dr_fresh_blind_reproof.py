"""Bounded new Core/A/B execution from the M12DR offline source closure.

No old model output is loaded. All output is sealed; stdout is structural only.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
import zipfile

from pydantic import ValidationError

from app.services import accepted_decision_v2_runtime_service as core_owner
from app.services import official_codex_shadow_transport_service as transport
from scripts import m12dc_fresh_source_use_two_pass_reproof as owner
from scripts.m12cn_policy_contract import build_subject_catalog
from scripts.m12co_entry_range_contract import build_subject_candidate_coverage
from scripts.m12cp_valuation_policy_contract import build_subject_policy_matrix
from scripts.m12cq_two_pass_contract import validate_pass_b_transformation
from scripts.m12cr_r1_typed_quality_contract import project_business_evidence_quality, project_security_valuation_basis
from scripts.m12dj_source_authority_preflight import preflight_current_pass_a_cohort
from scripts.m12dk_current_source_authority import freeze_current_source_binding
from scripts.m12dr_financial_source_authority import build_source_authority
from scripts.m12dr_offline_source_closure import read, write, sha


REPO = Path(__file__).resolve().parents[1]
OPERATING = Path("/Users/sskim/Codex/thesis-monitor")
BIN = Path("/Users/sskim/.codex/packages/standalone/releases/0.155.1-aarch64-apple-darwin/bin/codex")
QUALIFICATION = Path("/Users/sskim/Documents/Codex/Reports/20260921-m12de-official-refresh-auth/official-qualification.json")
_BANNED_KEYS = {"previous_assessment", "prior_accepted", "accepted_plan", "model_recommendation",
                "buy_drivers", "sell_drivers", "directional_balance", "overall_axis", "new_buyer_axis",
                "holder_axis", "frozen_pass_a_classification", "deterministic_assessment"}


def now():
    return datetime.now(timezone.utc).isoformat()


def git_state(path):
    return {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip(),
            "status": subprocess.check_output(["git", "status", "--porcelain"], cwd=path, text=True).strip()}


def manifest(path):
    return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob("*")) if p.is_file()}


def code_manifest():
    return {str(p.relative_to(REPO)): sha(p) for directory in ("app", "scripts")
            for p in sorted((REPO / directory).rglob("*")) if p.is_file() and p.suffix in {".py", ".json"}}


def binding():
    return transport.OfficialCodexBinding(
        executable=BIN, executable_sha256="8eaf1ad12fe6bf89b1710330f58900014322c7c5af677e43be116d8ac5fc0a9e",
        version="codex-cli 0.155.1", auth_method="CHATGPT_LOCAL_CONFIRMED", home=os.environ["HOME"],
        codex_home=os.environ.get("CODEX_HOME"), user_config_sha256=None, installation_verified=True,
        qualification_path=QUALIFICATION, qualification_sha256="c31565c76cb9d7fc521d21343ccdd45c9515fd3988683f1dbcee1503107936ab")


class BatchFailure(ValueError):
    pass


class SystemicFailure(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise BatchFailure(code)


def authority_core_schema(context, subjects, authorities):
    """Per-subject refs and narrower directional refs, before seeing any output."""
    schema = core_owner.accepted_v2_fundamental_core_output_schema(context, subjects=subjects)
    definitions = schema["$defs"]
    branches, receipt = [], []
    for index, ticker in enumerate(subjects):
        owned = next(r for r in context.evidence_ownership if r.ticker == ticker)
        refs = sorted(owned.core_ref_ids)
        direction = sorted(r["ref_id"] for r in authorities[ticker]["authority"]["authority_records"]
                           if r["ref_id"] in refs and r["authority_state"] == "RESOLVED"
                           and "OVERALL_DIRECTION" in r["allowed_uses"])
        require(bool(direction), "CORE_DIRECTIONAL_SOURCE_UNAVAILABLE:" + ticker)
        claim_name, driver_name, core_name = (f"M12DR{name}{index}" for name in ("Claim", "Driver", "Core"))
        claim = deepcopy(definitions["EvidenceClaim"])
        claim["properties"]["evidence_refs"]["items"]["enum"] = refs
        driver = deepcopy(claim)
        driver["properties"]["evidence_refs"]["items"]["enum"] = direction
        definitions[claim_name], definitions[driver_name] = claim, driver
        candidate = deepcopy(definitions["AcceptedV2FundamentalCoreCandidate"])
        props = candidate["properties"]
        props["ticker"].update(enum=[ticker], const=ticker)
        for key in ("buy_drivers", "sell_drivers"):
            props[key]["items"] = {"$ref": "#/$defs/" + driver_name}
        props["decisive_reason"] = {"$ref": "#/$defs/" + driver_name}
        holder = deepcopy(definitions["HolderDecisionAxis"])
        holder["properties"]["reason"] = {"$ref": "#/$defs/" + claim_name}
        definitions[f"M12DRHolder{index}"] = holder
        props["holder_axis"] = {"$ref": f"#/$defs/M12DRHolder{index}"}
        definitions[core_name] = candidate
        branches.append({"$ref": "#/$defs/" + core_name})
        receipt.append({"ticker": ticker, "same_subject_core_refs": refs, "directional_refs": direction})
    schema["properties"]["cores"]["items"] = {"anyOf": branches}
    return schema, receipt


class Reproof:
    def __init__(self, root):
        self.root, self.report, self.sealed = root, root / "report", root / "sealed"
        self.snapshot = root / "snapshot"
        self.requests = self.sealed / "requests"
        coverage = read(self.report / "source-coverage.json")
        require(coverage["allow_core_preflight"] and coverage["ready_count"] == coverage["active_count"],
                "FULL_SOURCE_GATE_REQUIRED")
        self.source_gen = coverage["source_generation_id"]
        self.gen = "20260921-m12dr-blind-" + self.source_gen.split("current-", 1)[-1]
        self.contexts = {m: core_owner.AcceptedV2ProductionContext.model_validate(
            read(self.snapshot / f"{m}-context.json")) for m in ("us", "kr")}
        require(all(not c.prior_accepted for c in self.contexts.values()), "PRIOR_MODEL_CONTEXT_FORBIDDEN")
        self.packets = {m: read(self.snapshot / f"{m}-packet.json") for m in self.contexts}
        self.bundles = read(root / "source/quality-inputs.json")
        self.issuers = read(root / "source/issuer-bindings.json")
        self.ledger, self.cores, self.arows, self.brows = [], {}, {}, {}
        self.catalogs, self.subjects, self.chains, self.authorities = {}, {}, {}, {}
        self.typed, self.actx, self.options, self.bctx, self.caps, self.entries = {}, {}, {}, {}, {}, {}
        self.frozen = None

    def verify(self):
        frozen = self.frozen or read(self.report / "execution-freeze.json")
        for path, key in ((REPO, "controller"), (OPERATING, "operating")):
            if git_state(path) != frozen[key]:
                raise SystemicFailure("CODE_OR_OPERATING_DRIFT")
        if code_manifest() != frozen["code"]:
            raise SystemicFailure("CODE_CONTENT_DRIFT")
        for path, key in ((self.snapshot, "snapshot"), (self.root / "source", "source")):
            if manifest(path) != frozen[key]:
                raise SystemicFailure("FROZEN_SOURCE_DRIFT")
        if sha(self.root / "m12dr-live-data-blind-pack.zip") != frozen["blind_zip_sha256"]:
            raise SystemicFailure("BLIND_PACK_DRIFT")
        if shutil.disk_usage(self.root).free < 10 * 1024 ** 3:
            raise SystemicFailure("DISK_BUDGET_BLOCKED")
        transport.validate_binding(binding(), str(BIN))

    def chain(self, ticker, market, atomic):
        ctx = self.contexts[market].model_dump(mode="json")
        cat = build_subject_catalog(context=ctx, ticker=ticker, atomic_claims=atomic)
        ep = next(r for r in ctx["evidence_packets"] if r["ticker"] == ticker)
        ownership = next(r for r in ctx["evidence_ownership"] if r["ticker"] == ticker)
        metadata = [r for r in ep["evidence"] if r["ref_id"] in cat["all_evidence_refs"]]
        sub = build_subject_candidate_coverage(market=market, packet=ep, ownership=ownership)
        sub["decision_evidence"] = metadata
        sub["business_evidence_quality_state"] = project_business_evidence_quality(ep)
        sub["security_valuation_basis_state"] = project_security_valuation_basis(ep)
        sub["directional_disclosure_quality_refs"] = sorted(set(cat["material_disclosure_failure_refs"] + cat["positive_quality_refs"]))
        authority = build_source_authority(
            ticker=ticker, source_generation_id=self.source_gen, source_packet=self.packets[market],
            evidence_packet=ep, catalog=cat, source_metadata=metadata,
            frozen_binding=freeze_current_source_binding(source_generation_id=self.source_gen,
                                                        source_packet=self.packets[market], evidence_packet=ep),
            quality_bundles=self.bundles, issuer_bindings=self.issuers)
        ex = owner.freeze_source_use_input_expectation(
            ticker=ticker, source_generation_id=self.source_gen, execution_generation_id=self.gen,
            catalog=cat, source_metadata=metadata, authority_manifest=authority["authority"])
        projection = owner.build_source_use_projection(
            ticker=ticker, input_generation_id=self.source_gen, execution_generation_id=self.gen,
            catalog=cat, authority_manifest=authority["authority"], current_input_expectation=ex)
        bound = owner.freeze_source_use_binding(projection=projection, authority_manifest=authority["authority"],
                                                current_input_expectation=ex)
        validation = owner.validate_source_use_current_input(
            projection, bound, ex, ticker=ticker, source_generation_id=self.source_gen, execution_generation_id=self.gen,
            catalog=cat, source_metadata=metadata)
        require(validation["status"] == "PASS", "SOURCE_USE_BINDING_FAILED")
        self.catalogs[ticker], self.subjects[ticker], self.authorities[ticker] = cat, sub, authority
        self.chains[ticker] = dict(authority=authority["authority"], expectation=ex, projection=projection,
                                  binding=bound, validation=validation, source_generation_id=self.source_gen,
                                  execution_generation_id=self.gen)
        self.typed[ticker] = dict(business_evidence_quality=sub["business_evidence_quality_state"],
                                  security_valuation_basis=sub["security_valuation_basis_state"],
                                  directional_disclosure_refs=sub["directional_disclosure_quality_refs"])

    def freeze(self):
        require(not (self.report / "execution-freeze.json").exists(), "EXECUTION_ALREADY_FROZEN")
        require(not git_state(REPO)["status"], "IMPLEMENTATION_COMMIT_REQUIRED")
        leaks = []

        def scan(value, path):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in _BANNED_KEYS:
                        leaks.append(path + "." + key)
                    scan(child, path + "." + key)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    scan(child, path + f"[{index}]")

        for market, packet in self.packets.items():
            scan(packet, market)
        write(self.report / "blind-leakage-audit.json", {"status": "FAIL" if leaks else "PASS", "leaks": leaks})
        require(not leaks, "BLIND_AI_LEAKAGE")
        blind = self.root / "m12dr-live-data-blind-pack.zip"
        with zipfile.ZipFile(blind, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for market in self.packets:
                archive.write(self.snapshot / f"{market}-packet.json", f"BLIND_DATA_PACK/{market}-packet.json")
            for name in ("quality-receipts.json", "issuer-business-projection.json", "source-input-binding.json"):
                archive.write(self.report / name, "BLIND_DATA_PACK/" + name)
            archive.writestr("BLIND_DATA_PACK/README.txt", "M12DR facts only. Same M12DQ source snapshot; not a new collection.\n"
                             "Extreme reported values remain cautioned, not recurring profit or a target decision.\n"
                             "Issuer business comparisons do not grant security valuation. Freeze independent judgment before AI reveal.\n")
        blind.with_suffix(".zip.sha256").write_text(sha(blind) + "  " + blind.name + "\n")
        requests = []
        for spec in owner._batch_topology():
            for ticker in spec["subjects"]:
                self.chain(ticker, spec["market"], [])
            ctx = self.contexts[spec["market"]]
            schema, refs = authority_core_schema(ctx, spec["subjects"], self.authorities)
            wire, projection = owner.project_provider_wire_schema(schema)
            require(owner.scan_provider_structured_output_schema(wire)["status"] == "PASS", "CORE_WIRE_SCHEMA_FAILED")
            dest = self.requests / "core" / spec["market"] / f"batch-{spec['batch']:02d}"
            dest.mkdir(parents=True, exist_ok=False)
            prompt = core_owner.accepted_v2_fundamental_core_prompt(ctx, subjects=spec["subjects"])
            prompt += "\nSOURCE_AUTHORITY_BOUNDARY:\n" + json.dumps(refs, ensure_ascii=False)
            prompt += ("\nAll current buy/sell drivers and decisive reasons must cite only that subject's directional_refs. "
                       "Other same-subject refs are context only, not independently directional. "
                       "Reported extreme observations corroborate amounts, not recurrence or normalized margins. "
                       "Unreconciled net income cannot establish recurring core profit or a valuation regime. "
                       "Absolute magnitude or an anomaly warning alone is neither deterioration nor recurring strength. "
                       "Do not target any label or force bullish/bearish interpretation. Do not reparent claims.\n")
            (dest / "prompt.txt").write_text(prompt)
            write(dest / "internal-semantic-schema.json", schema)
            write(dest / "provider-wire-schema.json", wire)
            write(dest / "wire-projection.json", projection)
            write(dest / "authority-ref-catalog.json", refs)
            requests.append({"directory": str(dest), **spec})
        write(self.sealed / "core-request-manifest.json", {"requests": requests, "files": manifest(self.requests / "core")})
        self.frozen = dict(generation_id=self.gen, source_generation_id=self.source_gen, frozen_at=now(),
                           controller=git_state(REPO), operating=git_state(OPERATING), code=code_manifest(),
                           snapshot=manifest(self.snapshot), source=manifest(self.root / "source"),
                           blind_zip_sha256=sha(blind), core_requests=manifest(self.requests / "core"),
                           model="gpt-5.6-sol", effort="xhigh", timeout_seconds=1200,
                           max_calls={"core": 8, "a": 8, "b": 8}, retries=0, fallback=0, judge=0,
                           production_actions=0, source_only_inference_certified=False)
        write(self.report / "execution-freeze.json", self.frozen)
        self.verify()
        print(json.dumps({"preflight": "PASS", "source_ready": 22, "core_requests": len(requests),
                          "blind_sha256": sha(blind), "model_calls": 0}), flush=True)

    def publish(self):
        write(self.report / "model-structural-ledger.json", {"generation_id": self.gen, "source_generation_id": self.source_gen,
                                                           "rows": self.ledger})
        print(json.dumps({"core_accepted": len(self.cores), "a_accepted": len(self.arows), "b_accepted": len(self.brows),
                          "last": self.ledger[-1] if self.ledger else None}), flush=True)

    def transport_failure(self, exc, destination, elapsed):
        if exc.code not in {"TRANSPORT_TIMEOUT", "FINAL_OUTPUT_EMPTY", "FINAL_OUTPUT_MALFORMED", "PROCESS_NONZERO"}:
            raise SystemicFailure(exc.code) from exc
        raise BatchFailure(exc.code) from exc

    def invoke(self, stage, spec, request):
        self.verify()
        src = Path(request["directory"])
        dst = Path("/private/tmp") / self.gen / stage / spec["market"] / f"batch-{spec['batch']:02d}"
        inp = dst / "approved-input"
        inp.mkdir(parents=True, exist_ok=False)
        for name in ("prompt.txt", "provider-wire-schema.json"):
            shutil.copy2(src / name, inp / name)
        reqid = f"{self.gen}-{stage}-{spec['market']}-{spec['batch']:02d}"
        req = transport.OfficialShadowRequest(binding(), reqid, sha(inp / "prompt.txt"), sha(inp / "provider-wire-schema.json"))
        row = self.ledger[-1]
        row.update(status="INVOKING", attempts=1, started_at=now(), prompt_sha256=req.prompt_sha256,
                   schema_sha256=req.schema_sha256)
        self.publish()
        dest = self.sealed / "calls" / stage / spec["market"] / f"batch-{spec['batch']:02d}"
        dest.mkdir(parents=True, exist_ok=False)
        started = time.monotonic()
        try:
            receipt = transport.invoke_official_shadow(codex_bin=str(BIN), prompt=inp / "prompt.txt", schema=inp / "provider-wire-schema.json",
                output=dst / "raw-output.json", log=dst / "events.jsonl", cwd=inp, timeout=1200, state_namespace=reqid, request=req)
            write(dest / "transport-receipt.json", receipt)
        except transport.OfficialShadowError as exc:
            self.transport_failure(exc, dst, time.monotonic() - started)
        finally:
            row.update(completed_at=now(), elapsed_seconds=round(time.monotonic() - started, 3))
            if (dst / "raw-output.json").exists():
                shutil.copy2(dst / "raw-output.json", dest / "raw-output.json")
                row["raw_output_sha256"] = sha(dest / "raw-output.json")
            if (dst / "events.jsonl").exists():
                events, unsafe = [], False
                for line in (dst / "events.jsonl").read_bytes().splitlines():
                    try:
                        event = json.loads(line)
                        kind, item = event.get("type"), event.get("item", {}).get("type")
                        if kind in {"item.started", "item.updated", "item.completed"}:
                            unsafe |= item not in {"reasoning", "agent_message"}
                        else:
                            unsafe |= kind not in {"thread.started", "turn.started", "turn.completed", "turn.failed", "error"}
                        events.append({"type": kind, "item_type": item})
                    except (ValueError, AttributeError):
                        unsafe = True
                write(dest / "sanitized-events.json", {"events": events, "hidden_reasoning_exported": False})
                if unsafe:
                    raise SystemicFailure("UNDECLARED_OR_UNKNOWN_TOOL_EVENT")
        self.verify()
        output = read(dest / "raw-output.json")
        errors = {name: owner.validate_json_schema(output, read(src / name))
                  for name in ("provider-wire-schema.json", "internal-semantic-schema.json")}
        write(dest / "schema-validation.json", errors)
        require(not any(errors.values()), "SCHEMA_REJECT")
        return output, dest

    def bounded(self, stage, spec, callback):
        self.ledger.append(dict(stage=stage, **spec, attempts=0, status="NOT_STARTED"))
        try:
            callback()
            self.ledger[-1]["status"] = "PASS"
        except (BatchFailure, ValidationError) as exc:
            self.ledger[-1].update(status="FAIL", failure_code=str(exc) if isinstance(exc, BatchFailure) else "MODEL_VALIDATION_ERROR")
            write(self.sealed / "failures" / f"{stage}-{spec['market']}-{spec['batch']}.json",
                  {"error_type": type(exc).__name__, "details": traceback.format_exc()})
        finally:
            self.publish()

    def core(self, spec, request):
        output, dest = self.invoke("core", spec, request)
        ctx = self.contexts[spec["market"]]
        batch = core_owner.AcceptedV2FundamentalCoreBatch.model_validate(output)
        errors = list(core_owner.validate_accepted_v2_fundamental_core_batch_scope(batch, ctx, subjects=spec["subjects"]))
        own = {r.ticker: r for r in ctx.evidence_ownership}
        refs = {r["ticker"]: set(r["directional_refs"]) for r in read(Path(request["directory"]) / "authority-ref-catalog.json")}
        for core in batch.cores:
            errors.extend(core_owner.validate_accepted_v2_fundamental_core(core, own[core.ticker]))
            for claim in (*core.buy_drivers, *core.sell_drivers, core.decisive_reason):
                if not claim.evidence_refs or not set(claim.evidence_refs) <= refs[core.ticker]:
                    errors.append("CURRENT_DIRECTION_SOURCE_ENTITLEMENT_FAILED")
        write(dest / "core-validation.json", {"status": "FAIL" if errors else "PASS", "errors": errors})
        require(not errors, "CORE_VALIDATION_REJECT")
        self.cores.update({r.ticker: r for r in batch.cores})

    def before_a(self):
        inputs, direction = [], []
        for spec in owner._batch_topology():
            for ticker in spec["subjects"]:
                atomic = core_owner.accepted_v2_maturity_atomic_claim_catalog_manifest((self.cores[ticker],))["claims"]
                self.chain(ticker, spec["market"], atomic)
                chain = self.chains[ticker]
                inputs.append(dict(ticker=ticker, source_generation_id=self.source_gen, execution_generation_id=self.gen,
                    catalog=self.catalogs[ticker], source_packet=self.subjects[ticker], authority=chain["authority"],
                    projection=chain["projection"], binding=chain["binding"], expectation=chain["expectation"],
                    prohibited_pass_a_source_refs=self.authorities[ticker]["pass_a_visibility_exclusions"]))
                permitted = [ref for ref, record in chain["projection"]["claim_records"].items()
                             if record["authority_state"] == "RESOLVED" and "OVERALL_DIRECTION" in record["allowed_uses"]]
                direction.append({"ticker": ticker, "permitted_atomic_claim_count": len(permitted)})
        gate = preflight_current_pass_a_cohort(inputs, expected_subjects=owner._expected_tickers())
        write(self.sealed / "before-a-preflight.json", gate)
        write(self.report / "future-b-entitlement.json", {"rows": direction, "a_passed": gate["passed_subjects"],
                                                         "status": "PASS" if gate["status"] == "PASS" and all(r["permitted_atomic_claim_count"] for r in direction) else "FAIL"})
        require(gate["status"] == "PASS" and all(r["permitted_atomic_claim_count"] for r in direction),
                "M12DR_FRESH_CORE_DIRECTIONAL_ENTITLEMENT_INCOMPLETE")
        self.actx = gate["model_contexts"]
        write(self.sealed / "fresh-core-freeze.json", {"cores": [r.model_dump(mode="json") for r in self.cores.values()],
                                                       "generation_id": self.gen, "frozen_at": now()})

    def args(self, subjects):
        return dict(subjects=tuple(subjects), catalogs=self.catalogs,
                    source_use_views={t: self.chains[t]["projection"] for t in subjects},
                    source_use_bindings={t: self.chains[t]["binding"] for t in subjects},
                    source_use_expectations={t: self.chains[t]["expectation"] for t in subjects},
                    source_metadata_by_ticker={t: self.subjects[t]["decision_evidence"] for t in subjects},
                    source_generation_id=self.source_gen, execution_generation_id=self.gen, require_source_use=True)

    def receipt(self, path, value):
        write(path, value)
        require(value.get("status") == "PASS", path.stem)

    def identity(self, spec):
        return dict(generation_id=self.gen, packet_id=f"m12dr-{spec['market']}-{spec['batch']}",
                    market=spec["market"], assessment_date=self.contexts[spec["market"]].assessment_date)

    def pass_a(self, spec, request=None):
        req = request if request is not None else owner._request_capture(
            root=self.requests, stage="pass-a", **spec, contexts=self.actx,
            catalogs=self.catalogs, chains=self.chains, generation_id=self.gen, fixture_only=False,
            raw_source_metadata_by_ticker={t: self.subjects[t]["decision_evidence"] for t in spec["subjects"]})
        output, dest = self.invoke("pass-a", spec, req)
        normal, mat = owner.materialize_future_pass_a(output, subjects=tuple(spec["subjects"]), subject_contexts=self.actx)
        self.receipt(dest / "materialization.json", mat)
        envelope = owner.PassABatchOutput.model_validate({"contract": "m12cq-pass-a-archetype-regime-v1",
                                                        **self.identity(spec), "classifications": normal})
        args = self.args(spec["subjects"])
        args["source_catalogs"] = args.pop("catalogs")
        self.receipt(dest / "semantic.json", owner.validate_pass_a_batch(envelope, expected_identity=self.identity(spec),
                                                                        subject_contexts=self.actx, **args))
        self.receipt(dest / "leakage.json", owner.pass_a_output_leak_scan(output))
        write(dest / "accepted.json", normal)
        self.arows.update({r["ticker"]: r for r in normal})

    def before_b(self):
        rows, requests = [], []
        for spec in owner._batch_topology():
            for ticker in spec["subjects"]:
                chain, a = self.chains[ticker], self.arows[ticker]
                selected = owner.select_matrix_option(build_subject_policy_matrix(self.subjects[ticker]), a)
                option, gate = owner.gate_policy_option_for_security_basis(selected, self.typed[ticker]["security_valuation_basis"])
                require(gate["status"] == "PASS", "OPTION_SECURITY_GATE")
                self.options[ticker] = option
                common = dict(catalog=self.catalogs[ticker], source_use_view=chain["projection"], source_use_binding=chain["binding"],
                              source_use_expectation=chain["expectation"], source_generation_id=self.source_gen,
                              execution_generation_id=self.gen, require_source_use=True)
                ctx = owner.build_pass_b_subject_context(context=owner.m12db._source_context(ticker, self.subjects[ticker]),
                                                         ticker=ticker, pass_a=a, policy_option=option, **common)
                ctx.update(business_evidence_quality_state=self.typed[ticker]["business_evidence_quality"],
                           security_valuation_basis_state=self.typed[ticker]["security_valuation_basis"],
                           directional_disclosure_quality_refs=self.typed[ticker]["directional_disclosure_refs"])
                raw = self.subjects[ticker]["decision_evidence"]
                transform = validate_pass_b_transformation(context=ctx, raw_source_metadata=raw,
                                                           **{k: v for k, v in common.items() if k != "require_source_use"})
                require(transform["status"] == "PASS", "RAW_EMITTED_TRANSFORMATION_FAILED")
                emitted = {r["ref_id"]: r for r in ctx["decision_evidence"]}
                conditions = [r for r in raw if r.get("logical_condition") not in (None, "", [], {})]
                require(all(emitted.get(r["ref_id"], {}).get("logical_condition") == r["logical_condition"] for r in conditions),
                        "LOGICAL_CONDITION_SCOPE_LOST")
                cap = owner.build_pass_b_capability_catalog(context=ctx, pass_a=a, policy_option=option, raw_source_metadata=raw, **common)
                ctx["pass_b_capability_catalog"] = cap
                self.bctx[ticker], self.caps[ticker] = ctx, cap
                rows.append({"ticker": ticker, "status": "PASS", "conditions_preserved": len(conditions),
                             "capability_sha256": owner.canonical_sha256(cap)})
            requests.append(owner._request_capture(root=self.requests, stage="pass-b", **spec, contexts=self.bctx,
                catalogs=self.catalogs, chains=self.chains, generation_id=self.gen, fixture_only=False, capabilities=self.caps,
                raw_source_metadata_by_ticker={t: self.subjects[t]["decision_evidence"] for t in spec["subjects"]}))
        require(len(rows) == 22 and len(requests) == 8, "PREB_INCOMPLETE")
        write(self.report / "offline-preb-closure.json", {"status": "PASS", "subjects": rows, "requests": len(requests), "model_calls": 0})
        write(self.sealed / "b-request-freeze.json", {"requests": requests, "files": manifest(self.requests / "pass-b")})
        return requests

    def pass_b(self, spec, request):
        output, dest = self.invoke("pass-b", spec, request)
        args = self.args(spec["subjects"])
        self.receipt(dest / "raw-capability.json", owner.validate_capability_selection(output, capabilities=self.caps, **args))
        normal, norm = owner.normalize_future_pass_b(output, subjects=tuple(spec["subjects"]), catalogs=self.catalogs)
        self.receipt(dest / "normalization.json", norm)
        mat = owner.validate_materialized_pass_b(normal, subjects=tuple(spec["subjects"]), catalogs=self.catalogs,
                                               pass_a_by_ticker=self.arows, policy_options=self.options, capabilities=self.caps)
        self.receipt(dest / "materialized.json", mat)
        envelope = owner.PassBBatchOutput.model_validate({"contract": "m12cq-pass-b-decision-tactical-v1",
                                                         **self.identity(spec), "decisions": normal})
        self.receipt(dest / "semantic.json", owner.validate_pass_b_batch(envelope, expected_identity=self.identity(spec),
                                                                        pass_a_by_ticker=self.arows, **args))
        self.receipt(dest / "typed-quality.json", owner.validate_quality_basis_decision_ownership(normal, catalogs=self.catalogs,
                                                                                                  typed_states=self.typed))
        entries = {r["ticker"]: r["entry_range"] for r in mat["entry_rows"]}
        for row in normal:
            ticker = row["ticker"]
            self.receipt(dest / (ticker + "-final-consistency.json"), owner.validate_new_buyer_consistency(
                decision=row, policy_option=self.options[ticker], entry_range=entries[ticker],
                catalog=self.catalogs[ticker], capability=self.caps[ticker]))
        write(dest / "accepted.json", {"decisions": normal, "entry_rows": mat["entry_rows"]})
        self.brows.update({r["ticker"]: r for r in normal})
        self.entries.update(entries)

    def run(self):
        require(not (self.report / "model-structural-ledger.json").exists(), "NO_RETRY_OR_RESUME_AUTHORIZED")
        self.frozen = read(self.report / "execution-freeze.json")
        self.verify()
        require(manifest(self.requests / "core") == self.frozen["core_requests"], "CORE_REQUEST_DRIFT")
        terminal = "M12DR_RUNTIME_OR_SECURITY_STOP"
        failure = None
        try:
            requests = read(self.sealed / "core-request-manifest.json")["requests"]
            for spec, request in zip(owner._batch_topology(), requests, strict=True):
                self.bounded("core", spec, lambda spec=spec, request=request: self.core(spec, request))
            require(len(self.cores) == 22, "M12DR_CORE_PREFLIGHT_FAILED")
            self.before_a()
            for spec in owner._batch_topology():
                self.bounded("pass-a", spec, lambda spec=spec: self.pass_a(spec))
            require(len(self.arows) == 22, "M12DR_PASS_A_COMPLETED_WITH_BATCH_LOCAL_FAILURES")
            write(self.sealed / "pass-a-freeze.json", {"classifications": self.arows, "frozen_at": now()})
            try:
                requests = self.before_b()
            except (ValueError, KeyError, TypeError) as exc:
                raise BatchFailure("M12DR_OFFLINE_PREB_CLOSURE_FAILED") from exc
            for spec, request in zip(owner._batch_topology(), requests, strict=True):
                self.bounded("pass-b", spec, lambda spec=spec, request=request: self.pass_b(spec, request))
            require(len(self.brows) == 22, "M12DR_PASS_B_COMPLETED_WITH_BATCH_LOCAL_FAILURES")
            final = owner._finalize_rows(pass_a_rows=list(self.arows.values()), pass_b_rows=list(self.brows.values()),
                entry_rows=[{"ticker": t, "entry_range": v} for t, v in self.entries.items()], options=self.options,
                typed=self.typed, source_packets=self.subjects)
            write(self.sealed / "final-results.json", {"generation_id": self.gen, "candidates": final})
            terminal = "M12DR_FRESH_BLIND_CORE_AB_PASS_READY_FOR_CHAT"
        except BatchFailure as exc:
            terminal = str(exc) if str(exc).startswith("M12DR_") else "M12DR_CORE_PREFLIGHT_FAILED"
            failure = type(exc).__name__
            write(self.sealed / "gate-failure.json", {"details": traceback.format_exc()})
        except Exception as exc:
            failure = type(exc).__name__
            write(self.sealed / "runtime-failure.json", {"details": traceback.format_exc()})
        finally:
            write(self.report / "execution-complete.json", {
                "terminal": terminal, "generation_id": self.gen, "source_generation_id": self.source_gen,
                "completed_at": now(), "core_accepted": len(self.cores), "a_accepted": len(self.arows), "b_accepted": len(self.brows),
                "calls": {stage: sum(r["attempts"] for r in self.ledger if r["stage"] == stage)
                          for stage in ("core", "pass-a", "pass-b")},
                "failure_type": failure, "comparison": "NOT_PERFORMED", "production_ready": False,
                "retries": 0, "source_only_inference_certified": False})
            self.publish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "run"))
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    proof = Reproof(args.root)
    proof.freeze() if args.mode == "freeze" else proof.run()


if __name__ == "__main__":
    main()
