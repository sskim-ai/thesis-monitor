"""Predeclared seven-axis comparison; disagreement is not an accuracy failure."""
from copy import deepcopy

from app.services.unified_snapshot_contract import digest
from scripts.strict_blind_contract import AXES, require

AUTHORITY = dict(contract="strict-blind-seven-axis-comparison-v1", axes=list(AXES),
    classes=["EXACT_MATCH", "COMPATIBLE_DIFFERENCE", "MATERIAL_DISAGREEMENT", "NOT_COMPARABLE"],
    equal="EXACT_MATCH", unequal="MATERIAL_DISAGREEMENT", missing="NOT_COMPARABLE",
    compatible_pairs=[], historical_aliases={}, agreement_threshold=None)
ACCEPTANCE = dict(contract="strict-blind-seven-axis-acceptance-v1",
    source_binding_errors=0, contract_semantic_errors=0, incomplete_subjects=0,
    economic_agreement_threshold=None, production_promotion_authorized=False)


def valid_value(value, values):
    return any(type(value) is type(expected) and value == expected for expected in values)


def compare(blind, monitoring, *, binding_receipts, semantic_receipts, authority, acceptance):
    require(authority == AUTHORITY and acceptance == ACCEPTANCE, "COMPARISON_POLICY_DRIFT")
    require(blind and set(blind) == set(monitoring) == set(binding_receipts) == set(semantic_receipts),
        "COMPARISON_COHORT_GAP")
    rows, binding_errors, semantic_errors = [], [], []
    for ticker, left in blind.items():
        right = monitoring[ticker]
        identity = ("generation", "source_generation_id", "ticker", "security_id", "subject_sha256")
        binding = dict(blind_sha256=digest(left), monitoring_sha256=digest(right))
        if (any(left.get(k) != right.get(k) for k in identity)
                or left.get("ticker") != ticker or binding_receipts[ticker].get("status") != "PASS"
                or any(binding_receipts[ticker].get(k) != v for k, v in binding.items())):
            binding_errors.append(ticker)
        if (set(left.get("axes", {})) != set(AXES) or set(right.get("axes", {})) != set(AXES)
                or semantic_receipts[ticker].get("status") != "PASS"
                or any(semantic_receipts[ticker].get(k) != v for k, v in binding.items())):
            semantic_errors.append(ticker)
        axes = {}
        for axis, values in AXES.items():
            a = left.get("axes", {}).get(axis, {}).get("judgment")
            b = right.get("axes", {}).get(axis, {}).get("judgment")
            # No BUY/ATTRACTIVE alias and no compatible-pair mapping are invented.
            classification = ("NOT_COMPARABLE" if not valid_value(a, values) or not valid_value(b, values)
                else "EXACT_MATCH" if a == b else "MATERIAL_DISAGREEMENT")
            axes[axis] = dict(blind=a, monitoring=b, classification=classification)
        rows.append(dict(ticker=ticker, axes=axes, blind_sha256=digest(left), monitoring_sha256=digest(right),
            binding_receipt_sha256=digest(binding_receipts[ticker]), semantic_receipt_sha256=digest(semantic_receipts[ticker])))
    incomplete = sum(any(a["classification"] == "NOT_COMPARABLE" for a in r["axes"].values()) for r in rows)
    return dict(contract=AUTHORITY["contract"], authority_sha256=digest(authority),
        acceptance_sha256=digest(acceptance), rows=rows,
        SOURCE_BINDING=dict(status="FAIL" if binding_errors else "PASS", errors=binding_errors),
        CONTRACT_SEMANTICS=dict(status="FAIL" if semantic_errors else "PASS", errors=semantic_errors),
        ECONOMIC_JUDGMENT=dict(disagreements=sum(a["classification"] == "MATERIAL_DISAGREEMENT"
            for r in rows for a in r["axes"].values()), agreement_threshold=None, correctness_proven=False),
        incomplete_subjects=incomplete,
        status="PASS" if not (binding_errors or semantic_errors or incomplete) else "FAIL")


def validate_comparison(result, authority, acceptance):
    if authority != AUTHORITY or acceptance != ACCEPTANCE:
        return False
    if (result.get("authority_sha256") != digest(authority)
            or result.get("acceptance_sha256") != digest(acceptance)
            or result.get("status") != "PASS" or not result.get("rows")
            or result.get("incomplete_subjects") != 0
            or result.get("SOURCE_BINDING") != dict(status="PASS", errors=[])
            or result.get("CONTRACT_SEMANTICS") != dict(status="PASS", errors=[])):
        return False
    rows = result["rows"]
    if len({r["ticker"] for r in rows}) != len(rows):
        return False
    for row in rows:
        if set(row["axes"]) != set(AXES):
            return False
        for axis, values in AXES.items():
            r = row["axes"][axis]
            if not valid_value(r["blind"], values) or not valid_value(r["monitoring"], values):
                return False
            expected = "EXACT_MATCH" if r["blind"] == r["monitoring"] else "MATERIAL_DISAGREEMENT"
            if r["classification"] != expected:
                return False
    economic = deepcopy(result["ECONOMIC_JUDGMENT"])
    return economic == dict(disagreements=sum(a["classification"] == "MATERIAL_DISAGREEMENT"
        for row in rows for a in row["axes"].values()), agreement_threshold=None, correctness_proven=False)
