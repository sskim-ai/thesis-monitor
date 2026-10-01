"""Provider snapshots belong to B calibration, never business direction refs."""

from copy import deepcopy
import re
from typing import Literal

from pydantic import model_validator

from app.services.current_fresh_valuation import CurrentValuationView, valuation_numeric_bindings
from app.services.unified_snapshot_contract import ContractModel, digest

CONTRACT = "provider-valuation-calibration-context-v1"
PROMPT = """The valuation_context block contains atomic provider-latest snapshots, not
same-session recomputation and not a fair-value or discount model. Unknown metric
dates remain unknown. Use it only as additional NewBuyer/Holder valuation context.
Record any selected qualified snapshot refs in new_buyer_valuation_refs or
holder_valuation_refs, separate from business-risk/support refs. Empty is allowed.
Unavailable metrics have no numeric ref. Do not infer fPER, ADR conversion,
fundamental discount or a price target from these multiples alone. Existing
axis capability, risk severity and range policy still govern allowed decisions.
Core and A do not receive this block. Overall rationale, directional refs and
directional score must use business evidence only, never these valuation refs.
Do not repeat exact snapshot numbers in rationale: the bound Valuation renderer
owns numeric display. Never present retrieval time as metric-as-of."""
VALUATION_TERMS = re.compile(
    r"(?<![A-Za-z])(?:PER|PBR|fPER|P/E|P/B)(?![A-Za-z])|주가수익비율|주가순자산비율", re.I
)


class ValuationCalibrationContext(ContractModel):
    contract: Literal["provider-valuation-calibration-context-v1"] = CONTRACT
    ticker: str
    run_id: str
    security_id: str
    valuation_view_sha256: str
    metric_states: tuple[dict, ...]
    facts: dict
    overall_direction_use: Literal[False] = False
    allowed_axes: tuple[Literal["NEW_BUYER", "HOLDER"], ...] = ("NEW_BUYER", "HOLDER")
    context_sha256: str

    @model_validator(mode="after")
    def bound(self):
        if self.context_sha256 != digest(self.model_dump(mode="json", exclude={"context_sha256"})):
            raise ValueError("valuation_context_hash_mismatch")
        if [r["metric"] for r in self.metric_states] != ["PER", "PBR", "fPER"]:
            raise ValueError("valuation_metric_triplet_required")
        expected = {r["fact_ref"] for r in self.metric_states if r["fact_ref"] is not None}
        if expected != set(self.facts):
            raise ValueError("valuation_context_fact_set_mismatch")
        for row in self.metric_states:
            if row["state"] != "QUALIFIED_PROVIDER_LATEST_SNAPSHOT" and (
                row["value"] is not None or row["fact_ref"] is not None
            ):
                raise ValueError("valuation_unavailable_value_leak")
        if any(f["fact"]["overall_direction_use"] is not False for f in self.facts.values()):
            raise ValueError("valuation_direction_permission_leak")
        return self


def calibration_context(view):
    view = CurrentValuationView.model_validate(view)
    bindings = valuation_numeric_bindings(view)
    rows, facts = [], {}
    for metric in view.metrics:
        native = metric.native_snapshot
        qualified = native is not None and native.display_eligible
        ref = bindings[metric.metric]["fact"]["fact_id"] if qualified else None
        if ref:
            facts[ref] = bindings[metric.metric]
        rows.append(
            dict(
                metric=metric.metric,
                state=native.state if native else "UNAVAILABLE_SOURCE_AUTHORITY",
                value=metric.value if qualified else None,
                fact_ref=ref,
                provider=native.provider if native else None,
                provider_field=native.provider_field if native else None,
                retrieval_timestamp=native.retrieval_timestamp.isoformat() if native else None,
                metric_asof=native.metric_asof.isoformat()
                if native and native.metric_asof
                else None,
                caveats=list(native.caveats) if native else [metric.denial_reason],
                snapshot_sha256=native.snapshot_sha256 if native else None,
                overall_direction_use=False,
            )
        )
    values = dict(
        ticker=view.ticker,
        run_id=view.run_id,
        security_id=view.security_id,
        valuation_view_sha256=digest(view.model_dump(mode="json")),
        metric_states=tuple(rows),
        facts=facts,
    )
    canonical = ValuationCalibrationContext.model_construct(**values, context_sha256="").model_dump(
        mode="json", exclude={"context_sha256"}
    )
    return ValuationCalibrationContext.model_validate(
        dict(canonical, context_sha256=digest(canonical))
    ).model_dump(mode="json")


def with_axis_refs(schema, context):
    """Separate optional calibration refs; existing business capabilities unchanged."""
    context = parse_context(context)
    result = deepcopy(schema)
    refs = sorted(context.facts)
    for axis in ("holder", "new_buyer"):
        for branch in result["properties"][axis + "_axis"]["anyOf"]:
            field = axis + "_valuation_refs"
            branch["properties"][field] = dict(
                type="array",
                items=dict(type="string", enum=refs) if refs else dict(type="string"),
                minItems=0,
                maxItems=len(refs),
                uniqueItems=True,
            )
            branch["required"].append(field)
    return result


def require_direction_isolation(value):
    if isinstance(value, dict):
        if "valuation_context" in value:
            raise ValueError("valuation_directional_input_leak")
        for child in value.values():
            require_direction_isolation(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            require_direction_isolation(child)
    elif isinstance(value, str) and any(prefix in value for prefix in ("current-valuation:", "kr-forward-valuation:")):
        raise ValueError("valuation_directional_ref_leak")


def validate_calibration_output(raw, context):
    if context.get('contract') == 'kr-fy1-valuation-calibration-context-v1':
        from app.services.kr_forward_valuation_context import validate_output
        return validate_output(raw, context)
    context = ValuationCalibrationContext.model_validate(context)
    require_direction_isolation(raw["overall"])
    if VALUATION_TERMS.search(raw["overall"]["overall_reason"]):
        raise ValueError("valuation_overall_reason_scope")
    audit = {}
    for axis in ("holder", "new_buyer"):
        row = raw[axis + "_axis"]
        field = axis + "_valuation_refs"
        refs = row[field]
        if (
            not isinstance(refs, list)
            or len(refs) != len(set(refs))
            or not set(refs) <= set(context.facts)
        ):
            raise ValueError("valuation_axis_ref_not_owned")
        rest = {k: v for k, v in row.items() if k != field}
        require_direction_isolation(rest)
        terms = {
            "per": "PER",
            "p/e": "PER",
            "주가수익비율": "PER",
            "pbr": "PBR",
            "p/b": "PBR",
            "주가순자산비율": "PBR",
            "fper": "fPER",
        }
        mentioned = {
            terms[term.casefold()] for term in VALUATION_TERMS.findall(row[axis + "_reason"])
        }
        qualified = {
            r["metric"]: r["fact_ref"] for r in context.metric_states if r["fact_ref"] is not None
        }
        # Unavailable metrics cannot supply refs. A different qualified multiple
        # must not turn a truthful missing-metric caution into a binding error.
        required = {ref for metric, ref in qualified.items() if metric in mentioned}
        if not required <= set(refs):
            raise ValueError("valuation_reason_requires_axis_ref")
        audit[axis] = refs
    return dict(
        status="PASS",
        context_sha256=context.context_sha256,
        selected_refs=audit,
        overall_direction_use=False,
        business_capabilities_modified=False,
    )


def parse_context(context):
    if context.get('contract') == 'kr-fy1-valuation-calibration-context-v1':
        from app.services.kr_forward_valuation_context import KrValuationCalibrationContext
        return KrValuationCalibrationContext.model_validate(context)
    return ValuationCalibrationContext.model_validate(context)


def context_prompt(contexts):
    if any(c.get('valuation_context',{}).get('contract') == 'kr-fy1-valuation-calibration-context-v1'
           for c in contexts.values()):
        from app.services.kr_forward_valuation_context import PROMPT as KR_PROMPT
        return KR_PROMPT
    return PROMPT
