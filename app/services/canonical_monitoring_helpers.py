"""Pure source-view and output-boundary helpers shared with proof callers."""
from collections.abc import Mapping
from copy import deepcopy
from app.services.unified_stock_acquisition import UNIVERSE as POPULATION
from app.services.canonical_monitoring_io import require

def _batch_topology() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for market in ("us", "kr"):
        subjects = POPULATION[market]
        for offset in range(0, len(subjects), 3):
            rows.append(
                {
                    "market": market,
                    "batch": offset // 3 + 1,
                    "subjects": subjects[offset : offset + 3],
                }
            )
    require(len(rows) == 8, "batch_topology_not_8")
    return rows

def _source_context(ticker: str, row: Mapping[str, object]) -> dict[str, object]:
    metadata = deepcopy(list(row.get("decision_evidence") or ()))
    return {
        "ticker": ticker,
        "decision_evidence": deepcopy(metadata),
        "evidence_packets": [{"ticker": ticker, "evidence": deepcopy(metadata)}],
        "current_price": deepcopy(row.get("current_price")),
        "tactical_candidates": deepcopy(row.get("tactical_candidates") or []),
        "security_valuation_basis_state": deepcopy(row.get("security_valuation_basis_state") or {}),
    }

def pass_a_output_leak_scan(output: Mapping[str, object]) -> dict[str, object]:
    forbidden = (
        "current price",
        "technical",
        "entry range",
        "new buyer",
        "holder",
        "현재가",
        "기술적",
        "진입가",
        "진입 범위",
        "신규 매수",
        "보유자",
    )
    hits: list[dict[str, str]] = []

    def visit(value: object, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                visit(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, f"{path}[{index}]")
        elif isinstance(value, str):
            folded = value.casefold()
            for token in forbidden:
                if token.casefold() in folded:
                    hits.append({"path": path, "token": token})

    visit(output, "$output")
    return {
        "contract": "m12cs-pass-a-output-price-technical-language-scan-v1",
        "forbidden_tokens": list(forbidden),
        "hits": hits,
        "hit_count": len(hits),
        "status": "PASS" if not hits else "FAIL",
    }
