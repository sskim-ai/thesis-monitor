from copy import deepcopy

import pytest
import httpx

from app.services.market_delta_acquisition import market_only_plan, require_market_delta
from app.services.sealed_fresh_dispatch import wire_identity
from test_r9_rev11_sealed_dispatch import descriptor, plan


def fixture():
    rows = []
    for key, role in [
        ("kiwoom:auth", "kiwoom:credential_exchange"),
        ("us_market:SPY", "us_market:SPY"),
        ("kr_market:KOSPI:ka20001", "kr_market:KOSPI:ka20001"),
        ("stock:MU", "stock:MU"),
    ]:
        rows.append(
            descriptor(
                key,
                provider="kiwoom",
                role_id=role,
                consumer_role=role,
                request_json=wire_identity(
                    httpx.Request(
                        "POST", "https://api.kiwoom.com/oauth2/token", json={"fixture_scope": key}
                    )
                ),
            )
        )
    full = plan(*rows, mandatory_roles=tuple(d.role_id for d in rows))
    limited, scope = market_only_plan(full)
    frozen = dict(generation_id=limited.generation_id, market_delta=scope)
    return full, limited, frozen


def test_market_delta_preserves_descriptors_and_does_not_claim_stock():
    full, limited, frozen = fixture()
    assert require_market_delta(frozen, limited) == frozenset(("kr-market", "us-market"))
    assert all(d in full.descriptors for d in limited.descriptors)
    assert len(full.descriptors) == 4 and len(limited.descriptors) == 3
    assert frozen["market_delta"]["stock_acquisition"] == "NOT_RUN"
    assert require_market_delta({}, full) is None


@pytest.mark.parametrize(
    "mutation", ["generation", "plan", "hash", "phase", "cohort", "nonmarket", "wrong_provider"]
)
def test_market_delta_rejects_scope_drift(mutation):
    full, limited, frozen = fixture()
    frozen = deepcopy(frozen)
    if mutation == "generation":
        frozen["generation_id"] = "other"
    elif mutation == "plan":
        limited = full
    elif mutation == "hash":
        frozen["market_delta"]["descriptors_sha256"] = "0" * 64
    elif mutation == "phase":
        frozen["market_delta"]["phases"].append("stocks")
    elif mutation == "cohort":
        frozen["scope"] = "US14_ONLY"
    else:
        data = limited.model_dump(mode="json")
        if mutation == "nonmarket":
            data["descriptors"].append(full.descriptors[-1].model_dump(mode="json"))
        else:
            data["descriptors"][1] = descriptor("us_market:SPY").model_dump(mode="json")
        limited = type(limited).model_validate(data)
        from app.services.unified_snapshot_contract import digest

        frozen["market_delta"]["restricted_plan_sha256"] = limited.plan_sha256
        frozen["market_delta"]["descriptors_sha256"] = digest(data["descriptors"])
    with pytest.raises(ValueError):
        require_market_delta(frozen, limited)
