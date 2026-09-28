"""Offline source-policy correction. No provider/model/delivery entry point."""
import argparse
import asyncio
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch
import zipfile

from sqlmodel import Session

from scripts import financial_direction_eligibility as guard
from scripts import r2b_r2_contract as c
from scripts import r2b_r2_preflight as pre
from scripts import r2b_sealed_blind_preflight as io
from scripts.m12ds_r4_offline_capture import capture_payload
from scripts.sealed_cohort_offline_proof import network_guard

R6_SHA = "c2578c352831f5240e83ca6c6d9ac81957adfc89bd0cabe0f38f960f003648a3"
BASE = "ad24ba92e8a7d8494a62c5e90a8321fba9c5230d"
LABEL = "POST_COMPARISON_SOURCE_POLICY_CORRECTED"


class SealedR6:
    def __init__(self, path):
        self.path = path
        if io.sha(path.read_bytes()) != R6_SHA:
            raise ValueError("r6_zip_identity")
        self.archive = zipfile.ZipFile(path)
        self.manifest = self.json("bundle-manifest.json")
        names = self.archive.namelist()
        assert len(names) == len(set(names))
        assert set(names) == {"result/" + n for n in self.manifest} | {"result/bundle-manifest.json"}
        for name, row in self.manifest.items():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
            raw = self.raw(name)
            assert io.sha(raw) == row["sha256"] and len(raw) == row["bytes"]

    def raw(self, name):
        return self.archive.read("result/" + name)

    def json(self, name):
        return json.loads(self.raw(name))

    def execution(self, name):
        return self.json("execution/" + name)


def directional_refs(authority):
    return sorted(r["ref_id"] for r in authority["authority_records"]
                  if r["authority_state"] == "RESOLVED"
                  and "OVERALL_DIRECTION" in r["allowed_uses"]
                  and "OVERALL_DIRECTION" not in r["prohibited_uses"])


def unknown(recovery):
    return dict(decision_mode="UNKNOWN_LIMIT", overall_direction="OBSERVE", new_buyer="OBSERVE", holder="OBSERVE",
                directional_buy_score=None, directional_sell_score=None, confidence=None,
                limitation_reason="ZERO_AUTHORIZED_DIRECTIONAL_EVIDENCE", unknowns=sorted(recovery),
                required_next_evidence=sorted(recovery))


def calibration_audits(sealed, out, prepared, cores, a, b):
    """Describe original R6 behavior. No independent labels enter any repair path."""
    contexts, schemas, provenance = {}, {}, {}
    for name in sealed.manifest:
        if not name.startswith("execution/sealed/requests/pass-b/") or not name.endswith("/subject-context.json"):
            continue
        data = sealed.json(name)
        schema_name = name.replace("subject-context.json", "internal-semantic-schema.json")
        schema = sealed.json(schema_name)["properties"].get("decisions", {}).get("properties", {})
        for ticker, ctx in data.items():
            if ticker not in b["accepted"]:
                continue
            contexts[ticker], schemas[ticker] = ctx, schema[ticker]
            provenance[ticker] = {n: sealed.manifest[n]["sha256"] for n in (
                name, schema_name, name.replace("subject-context.json", "prompt.txt"))}

    def choices(schema, axis, field):
        return sorted({v for branch in schema["properties"][axis]["anyOf"]
                       for v in branch["properties"][field]["enum"]})

    rows = []
    for ticker, decision in b["accepted"].items():
        ctx, schema = contexts[ticker], schemas[ticker]
        cap, val, cls = ctx["r2_policy_capability"], ctx["r2_valuation"], a["accepted"][ticker]
        refs = set(decision["supporting_refs"] + decision["contradicting_refs"])
        rows.append(dict(ticker=ticker, decision=decision, archetype=cls["archetype"],
            valuation_regime_tier=cls["valuation_regime_tier"], capability=cap, valuation=val,
            new_buyer_schema=choices(schema, "new_buyer_axis", "new_buyer"),
            holder_schema=choices(schema, "holder_axis", "holder"),
            overall_schema=choices(schema, "overall", "overall_direction"),
            score_bins={branch["properties"]["overall_direction"]["enum"][0]:
                        branch["properties"]["directional_buy_score"]["enum"]
                        for branch in schema["properties"]["overall"]["anyOf"]},
            core_support=[claim for claim in cores["accepted"][ticker]["atomic_claims"] if claim["claim_ref"] in refs],
            core_effects=ctx["r2_core_effects"], provenance=provenance[ticker],
            quality=prepared[ticker]["subject"]["business_evidence_quality_state"],
            security_basis=prepared[ticker]["subject"]["security_valuation_basis_state"],
            data_quality_effect=cls["data_quality_effect"], data_quality_reason=cls["data_quality_reason"],
            data_quality_reason_class=cls["data_quality_reason_class"]))
    common = dict(scope="ORIGINAL_SEALED_R6_DESCRIPTIVE_AUDIT", R6_zip_sha256=R6_SHA,
                  tuning=False, independent_labels_used_as_targets=False, model_calls=0)
    growth = [r for r in rows if r["ticker"] in {"CPNG", "HUT", "WULF"}]
    io.save(out, "execution-growth-downside-calibration-audit.json", dict(common, rows=growth,
        finding="SELL is permitted when verified deterioration exists, not forced. Positive and negative refs permit balanced HOLD. Active risk without verified compensation forces buyer AVOID and restricts Holder to REVIEW. Overall magnitude/weight remains the model's selection within accepted score bins.",
        persistence_owner="r3 axis_capability.sell_eligible permits deterioration OR impairment OR holder_reduce; persistence is not required for comparative deterioration",
        audit_limitation="No causal model experiment; stated reasons and allowed options are observed, hidden reasoning is not inferred."))
    io.save(out, "new-buyer-actionability-audit.json", dict(common,
        counts=dict(Counter(r["decision"]["new_buyer"] for r in rows)),
        limits=b["limits"], rows=[{k:r[k] for k in ("ticker", "decision", "valuation", "security_basis", "new_buyer_schema", "provenance")} for r in rows],
        finding="ATTRACTIVE requires fundamental_valid and compensating_discount. Tactical zones do not substitute. Active material risk without compensation can require AVOID even when valuation is unresolved; WAIT otherwise reflects the recorded reason, not a mandatory portfolio quota."))
    io.save(out, "holder-actionability-audit.json", dict(common,
        counts=dict(Counter(r["decision"]["holder"] for r in rows)), limits=b["limits"],
        rows=[dict(ticker=r["ticker"], holder=r["decision"]["holder"], eligible_schema=r["holder_schema"],
                   holder_reason_class=r["decision"]["holder_reason_class"],
                   risk=r["capability"]["holder_risk"], reduce=r["capability"]["holder_reduce"],
                   core_effects=r["core_effects"], provenance=r["provenance"]) for r in rows],
        finding="ADD is not part of this contract vocabulary. REDUCE requires PERSISTENT_OR_IMPAIRED source-backed materiality; current core schema only provides CONTEXT_ONLY/ACTIVE_MATERIAL_RISK, and current adapter has no realized impairment owner. REDUCE compression is therefore partly a capability/schema restriction, not merely a sample choice. No action added."))
    io.save(out, "directional-score-compression-audit.json", dict(common,
        observed_range=[min(r["decision"]["directional_buy_score"] for r in rows), max(r["decision"]["directional_buy_score"] for r in rows)],
        independent_range_reported_in_instruction=[2, 8], independent_range_verified=False,
        schema_score_union=sorted({score for r in rows for values in r["score_bins"].values() for score in values}),
        rows=[dict(ticker=r["ticker"], score=r["decision"]["directional_buy_score"], direction=r["decision"]["overall_direction"],
                   bins=r["score_bins"], provenance=r["provenance"]) for r in rows],
        finding="Provider schema uses canonical half-point score bins; validator enforces label/score compatibility. Neither imposes the observed 4.5..7.5 sample range. Prompt explicitly separates score from probability, timing and confidence; no score distribution target is specified."))
    io.save(out, "large-cap-descriptive-policy-matrix.json", dict(common,
        rows=[r for r in rows if r["ticker"] in {"GOOGL", "MU", "TSM", "SKHY", "000660", "005930"}],
        future_product_options=[
            dict(option="Retain independent Overall/NewBuyer/Holder axes", tradeoff="Keep thesis direction separate from entry valuation; WAIT may remain common."),
            dict(option="Separate future source/security valuation coverage work", tradeoff="Improve denominators and qualified comparisons without relaxing policy gates."),
            dict(option="Separately authorize downside aggregation policy review", tradeoff="Evaluate severity/persistence weighting generically; no per-ticker target fitting."),
            dict(option="Separately design Holder action vocabulary", tradeoff="ADD/REDUCE require explicit evidence contracts and independent validation before use.")]))
    io.save(out, "source-quality-vs-policy-matrix.json", dict(common,
        rows=[{k:r[k] for k in ("ticker", "quality", "security_basis", "data_quality_effect", "data_quality_reason",
                               "data_quality_reason_class", "valuation", "provenance")} for r in rows],
        finding="Financial quality and security-basis denials remain source constraints. Threshold relaxation cannot repair missing source authority. Model stance conservatism must be separated from these factual gates."))
    return dict(new_buyer=dict(Counter(r["decision"]["new_buyer"] for r in rows)),
                holder=dict(Counter(r["decision"]["holder"] for r in rows)), ordinary_subjects=len(rows))


def recompute(data, ticker, generation):
    cat, sub, chain = pre.subject_inputs(data["view"], data["source_authority"], data["view_receipt"], generation=generation)
    before = data["core_input"]
    obs = c.policy.observations(before["metadata"], chain["authority"], before["frozen_fact_fields"])
    mode = c.decision_mode(data["view"], chain["authority"], obs)
    recovery = c.limitation_catalog(data["view"], chain["authority"]) if mode == "UNKNOWN_LIMIT" else {}
    records = {r["ref_id"]: r for r in before["authority"]["authority_records"]}
    absolute, comparative = [], []
    for row in before["metadata"]:
        record = records[row["ref_id"]]
        if guard.is_financial(record, row):
            bucket = comparative if guard.comparison_eligible(record, before["frozen_fact_fields"].get(row["ref_id"])) else absolute
            bucket.append(row["ref_id"])
    impact = dict(ticker=ticker, directional_refs_before=directional_refs(before["authority"]),
                  directional_refs_after=directional_refs(chain["authority"]), absolute_current_refs=absolute,
                  comparative_refs=comparative, decision_mode_before=data["mode"], decision_mode_after=mode,
                  model_calls=0, source_packet_sha256=c.digest(data["view"]["packet"]))
    impact["refs_removed_from_direction"] = sorted(set(impact["directional_refs_before"]) - set(impact["directional_refs_after"]))
    impact["result_changed"] = data["mode"] != mode
    impact["reason"] = guard.DENIAL if impact["refs_removed_from_direction"] else "UNCHANGED"
    return impact, chain, obs, recovery


def run(args):
    network = network_guard()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    sealed = SealedR6(args.r6)
    r6_before = io.sha(args.r6.read_bytes())
    prepared = sealed.execution("inputs/stock/prepared-inputs.json")
    cores = sealed.execution("upstream/execution/sealed/core-output-freeze.json")
    a = sealed.execution("sealed/pass-a-output-freeze.json")
    b = sealed.execution("sealed/pass-b-output-freeze.json")
    calibration = calibration_audits(sealed, out, prepared, cores, a, b)
    generation = "20260928-r2b-r7-offline-" + io.now().replace(":", "").replace("+", "_")
    impacts, inventory, affected, corrections, revalidations = [], [], [], {}, []
    for ticker, data in prepared.items():
        impact, chain, obs, recovery = recompute(data, ticker, generation)
        old = cores["accepted"].get(ticker)
        fields = data["core_input"]["frozen_fact_fields"]
        if old:
            for claim in old["atomic_claims"]:
                try:
                    guard.validate_atomic_direction([claim], data["core_input"]["metadata"], chain["authority"], fields)
                except ValueError as exc:
                    inventory.append(dict(ticker=ticker, claim=claim, rejection=str(exc)))
        if impact["result_changed"]:
            if impact["decision_mode_after"] != "UNKNOWN_LIMIT":
                raise ValueError("affected_non_limit_requires_separate_execution_plan")
            affected.append(ticker)
            value = unknown(recovery)
            cap = {k: [] for k in c.DIRECTION_BUCKETS}
            validation = c.validate_unknown(value, mode="UNKNOWN_LIMIT", recovery=recovery, capability=cap)
            corrections[ticker] = dict(decision=value, recovery=recovery, capability=cap)
            io.save(out, "subjects/" + ticker + "-before-after.json", dict(
                before=b["accepted"][ticker], after=value, validation=validation,
                retained_source_fact_fields=fields, observations_after=obs, after_authority=chain["authority"],
                classification=LABEL, not_a_new_model_candidate=True))
        elif old:
            assert obs == old["observations"], "unrelated_observation_regression:" + ticker
            cat, sub, bound = pre.subject_inputs(data["view"], data["source_authority"], data["view_receipt"],
                                                generation=generation, atomic=old["atomic_claims"])
            cap = c.policy.axis_capability(old, bound, cat, sub["decision_evidence"])
            assert cat["atomic_claims"] == old["atomic_claims"]
            # Request contexts are the exact accepted R6 B dependencies; do not rerun A.
            contexts = [sealed.json(n)[ticker] for n in sealed.manifest
                        if n.startswith("execution/sealed/requests/pass-b/") and n.endswith("/subject-context.json")
                        and ticker in sealed.json(n)]
            assert len(contexts) == 1
            previous_cap = contexts[0]["r2_policy_capability"]
            assert {k:v for k,v in cap.items() if k != "source_binding_sha256"} == {
                k:v for k,v in previous_cap.items() if k != "source_binding_sha256"}, "unrelated_capability_regression:" + ticker
            validation = c.policy.validate_decision(b["accepted"][ticker], cap, contexts[0]["r2_valuation"])
            assert validation["status"] == "PASS"
            revalidations.append(dict(ticker=ticker, Core="UNCHANGED", A="UNCHANGED", B="UNCHANGED",
                                      decision_validation=validation, new_source_binding_sha256=cap["source_binding_sha256"]))
        else:
            assert data["mode"] == "UNKNOWN_LIMIT" and not obs
            assert recovery == data["recovery"]
            for stage in (cores, a, b):
                c.validate_unknown(stage["limits"][ticker], mode=data["mode"], recovery=recovery,
                                   capability={k: [] for k in c.DIRECTION_BUCKETS})
            revalidations.append(dict(ticker=ticker, Core="UNCHANGED_LIMIT", A="UNCHANGED_LIMIT", B="UNCHANGED_LIMIT"))
        impacts.append(impact)
        original = data["core_input"]["authority"]
        io.save(out, "source-use/" + ticker + ".json", dict(before=original, after=chain["authority"],
            metadata_unchanged=True, fact_fields_unchanged=True, observations_before=data["core_input"]["observed_propositions"],
            observations_after=obs, current_input_validation=chain["validation"]))
    io.save(out, "absolute-current-direction-impact-matrix.json", impacts)
    io.save(out, "absolute-current-directional-claim-inventory.json", inventory)
    io.save(out, "unaffected-r6-invariance.json", dict(status="PASS", rows=revalidations, R6_zip_sha256=R6_SHA,
        source_hashes=sealed.json("source-identities.json"), original_outputs_rewritten=False))
    messages = sealed.execution("messages/manifest.json")
    new_messages = []

    async def capture():
        for row in messages["messages"]:
            name = row["path"]
            ticker = name.rsplit(".", 1)[0].split("-", 1)[-1]
            raw = sealed.raw("execution/messages/" + name)
            assert io.sha(raw) == row["sha256"]
            if ticker in corrections:
                data = corrections[ticker]
                text = c.render_unknown(ticker, data["decision"], recovery=data["recovery"], capability=data["capability"])
                receipt = await capture_payload(dict(text=text, use_llm=False, type="stock_review",
                                                    market=prepared[ticker]["view"]["market"]))
                raw = receipt["prepared_text"].encode()
                assert io.sha(raw) == receipt["prepared_text_sha256"]
                io.save(out, "messages/receipts/" + name.replace(".txt", ".json"), receipt)
            target = out / "messages" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            new_messages.append(dict(path=name, sha256=io.sha(raw), r6_sha256=row["sha256"],
                                     changed=ticker in corrections, production_sends=0))

    def deny(*args, **kwargs):
        raise AssertionError("production_db_access_forbidden")
    with patch.object(Session, "exec", deny), patch.object(Session, "commit", deny):
        asyncio.run(capture())
    assert len(new_messages) == 24
    io.save(out, "messages/manifest.json", dict(classification=LABEL, messages=new_messages, total=24,
                                               generation_id=generation, original_blind_result=False))
    assert io.sha(args.r6.read_bytes()) == r6_before
    summary = dict(status="OBJECTIVE_OFFLINE_PROOF_PASS", generation_id=generation, classification=LABEL,
        affected=affected, invalid_directional_claims=len(inventory), current_cohort=len(impacts),
        unchanged_subjects=len(revalidations), messages=24, unchanged_messages=sum(not r["changed"] for r in new_messages),
        R6_zip_sha256=R6_SHA, model_calls=0, provider_calls=0, policy_threshold_changes=0,
        Telegram=0, production_db_writes=0, scheduler_mutation=0, deploy=0, remote_push=0,
        source_hashes_unchanged=True, network=network, calibration=calibration)
    io.save(out, "summary.json", summary)
    print(json.dumps(summary))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r6", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
