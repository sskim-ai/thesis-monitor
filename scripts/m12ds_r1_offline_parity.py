"""Exhaustive request enum/source-use parity with the unchanged semantic owner."""
from copy import deepcopy

from scripts.m12da_source_use_contract import SourceUse, validate_selected_refs
from scripts import m12dr_fresh_blind_reproof as p


def resolved(schema, node):
    if "$ref" in node:
        result = schema
        for part in node["$ref"].split("/")[1:]:
            result = result[part]
        return resolved(schema, result)
    return node


def offered(schema, prop):
    prop = resolved(schema, prop)
    if prop.get("maxItems") == 0:
        return []
    items = resolved(schema, prop["items"])
    p.require("enum" in items, "UNCONSTRAINED_PASS_A_REF_FIELD")
    return sorted(items["enum"])


def allowed(proof, ticker, refs, use):
    chain = proof.chains[ticker]
    return sorted(ref for ref in refs if validate_selected_refs(
        chain["projection"], refs=[ref], use=use, require_any=True, binding=chain["binding"],
    )["status"] == "PASS")


def semantic(proof, ticker, row):
    # Packet subject shape varies; the frozen canonical topology owns membership.
    market = next(s["market"] for s in p.owner._batch_topology() if ticker in s["subjects"])
    identity = proof.identity({"market": market, "batch": 1})
    envelope = p.owner.PassABatchOutput.model_validate({"contract": "m12cq-pass-a-archetype-regime-v1",
        **identity, "classifications": [{"ticker": ticker, **row}]})
    args = proof.args([ticker])
    args["source_catalogs"] = args.pop("catalogs")
    return p.owner.validate_pass_a_batch(envelope, expected_identity=identity, subject_contexts=proof.actx, **args)


def audit(proof, requests):
    rows = []
    for request in requests:
        directory = p.Path(request["directory"])
        internal, wire = (p.read(directory / name) for name in ("internal-semantic-schema.json", "provider-wire-schema.json"))
        for ticker in request["subjects"]:
            context = proof.actx[ticker]
            registered = sorted(proof.catalogs[ticker]["claim_refs"])
            visible = sorted(context["eligible_claim_refs"])
            arches = allowed(proof, ticker, registered, SourceUse.PASS_A_ARCHETYPE)
            tiers = allowed(proof, ticker, registered, SourceUse.PASS_A_VALUATION_TIER)
            ib = internal["properties"]["classifications"]["properties"][ticker]["anyOf"]
            wb = wire["properties"]["classifications"]["properties"][ticker]["anyOf"]
            fields, available = [], []
            for branch, wire_branch in zip(ib, wb, strict=True):
                props, wp = branch["properties"], wire_branch["properties"]
                tier = props["valuation_regime_tier"]["const"]
                available.append(tier)
                expected_tier = sorted(set(tiers) & set(visible)) if tier != "UNRESOLVED" else []
                if tier == "PREMIUM":
                    expected_tier = sorted(set(expected_tier) & set(context["premium_eligible_claim_refs"]))
                base = dict(archetype="UNRESOLVED", archetype_confidence="LOW",
                    archetype_supporting_claim_refs=sorted(set(arches) & set(visible))[:1],
                    archetype_rationale="Bounded offline reference probe.", valuation_regime_tier=tier,
                    tier_supporting_claim_refs=expected_tier[:1], tier_rationale="Bounded offline reference probe.",
                    data_quality_effect="NONE", data_quality_reason_class="NOT_APPLICABLE",
                    data_quality_reason=None, data_quality_evidence_refs=[], classification_summary="Offline scope validation only.")
                p.require(semantic(proof, ticker, base)["status"] == "PASS", "PARITY_BASE_SEMANTIC_FAILURE")
                for field, required, expected, authority in (
                    ("archetype_supporting_claim_refs", "PASS_A_ARCHETYPE", sorted(set(arches) & set(visible)), arches),
                    ("tier_supporting_claim_refs", "PASS_A_VALUATION_TIER", expected_tier, tiers),
                ):
                    refs, wire_refs = offered(internal, props[field]), offered(wire, wp[field])
                    checks = []
                    for ref in refs:
                        probe = deepcopy(base)
                        probe[field] = [ref]
                        checks.append({"ref": ref, "status": semantic(proof, ticker, probe)["status"]})
                    fields.append({"field": field, "branch": tier, "semantic_role": required,
                        "registered_refs": registered, "authorized_refs": authority, "expected_refs": expected,
                        "schema_refs": refs, "provider_refs": wire_refs, "forbidden_offered": sorted(set(refs) - set(expected)),
                        "eligible_omitted": sorted(set(expected) - set(refs)), "semantic_checks": checks})
                quality = context["data_quality_catalog"]
                for quality_branch, wire_quality in zip(props["directional_data_quality_judgment"]["anyOf"],
                                                       wp["directional_data_quality_judgment"]["anyOf"], strict=True):
                    qp, wqp = quality_branch["properties"], wire_quality["properties"]
                    effect = qp["effect"]["const"]
                    role = {"NONE": None, "DIRECTIONAL_NEGATIVE": "material_disclosure_failure_refs",
                            "DIRECTIONAL_POSITIVE": "positive_quality_refs"}[effect]
                    expected = sorted(set(quality.get(role) or ()) & set(quality.get("evidence_refs") or ())) if role else []
                    refs, wr = offered(internal, qp["evidence_refs"]), offered(wire, wqp["evidence_refs"])
                    checks = []
                    for ref in refs:
                        probe = {**base, "data_quality_effect": effect, "data_quality_reason_class": qp["reason_class"]["const"],
                                 "data_quality_reason": "Observed disclosure evidence.", "data_quality_evidence_refs": [ref]}
                        checks.append({"ref": ref, "status": semantic(proof, ticker, probe)["status"]})
                    fields.append({"field": "directional_data_quality_judgment.evidence_refs", "branch": tier + "/" + effect,
                        "semantic_role": role or "NONE_EMPTY", "source_use_enum": None,
                        "registered_refs": sorted(proof.catalogs[ticker]["all_evidence_refs"]),
                        "authorized_refs": expected, "expected_refs": expected, "schema_refs": refs, "provider_refs": wr,
                        "forbidden_offered": sorted(set(refs) - set(expected)), "eligible_omitted": sorted(set(expected) - set(refs)),
                        "semantic_checks": checks})
            expected_branches = ["UNRESOLVED"]
            if set(tiers) & set(visible):
                expected_branches += ["CONSERVATIVE", "BASE"]
            if set(tiers) & set(visible) & set(context["premium_eligible_claim_refs"]):
                expected_branches += ["PREMIUM"]
            passed = set(available) == set(expected_branches) and all(
                not f["forbidden_offered"] and not f["eligible_omitted"] and f["schema_refs"] == f["provider_refs"]
                and all(c["status"] == "PASS" for c in f["semantic_checks"]) for f in fields)
            rows.append({"ticker": ticker, "fields": fields, "available_branches": available,
                         "expected_branches": expected_branches, "status": "PASS" if passed else "FAIL"})
    return {"contract": "m12ds-r1-pass-a-axis-specific-source-use-schema-parity-v1", "rows": rows,
            "subject_count": len(rows), "passed": sum(r["status"] == "PASS" for r in rows),
            "status": "PASS" if len(rows) == 22 and all(r["status"] == "PASS" for r in rows) else "FAIL"}
