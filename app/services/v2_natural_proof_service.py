from __future__ import annotations

from dataclasses import asdict, dataclass


V2_NATURAL_PROOF_CONTRACT = "explicit-v2-natural-proof-v1"


@dataclass(frozen=True)
class ExplicitV2NaturalProofCounts:
    ai_accepted_total: int
    ai_market_sent: int
    explicit_v2_stock_accepted: int
    explicit_v2_stock_sent: int
    pilot_ai_assisted_sent: int
    deterministic_fallback_sent: int
    duplicate_sent: int


def evaluate_explicit_v2_natural_proof(
    counts: ExplicitV2NaturalProofCounts,
    *,
    expected_stock_count: int,
) -> dict[str, object]:
    checks = {
        "ai_market_sent": counts.ai_market_sent == 1,
        "explicit_v2_stock_accepted": (
            counts.explicit_v2_stock_accepted == expected_stock_count
        ),
        "explicit_v2_stock_sent": counts.explicit_v2_stock_sent == expected_stock_count,
        "pilot_ai_assisted_sent": counts.pilot_ai_assisted_sent == 0,
        "deterministic_fallback_sent": counts.deterministic_fallback_sent == 0,
        "duplicate_sent": counts.duplicate_sent == 0,
    }
    return {
        "contract": V2_NATURAL_PROOF_CONTRACT,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "expected_stock_count": expected_stock_count,
        "counts": asdict(counts),
        "checks": checks,
    }
