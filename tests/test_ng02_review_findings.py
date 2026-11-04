"""Independent-review-triggered diagnostics; strict requested boundary expectations."""

import pytest
from app.services.fresh_source_run_contract import validate_local_seed
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_local_seed_bridge import local_owner
from test_unified_stock_owner import source as source_fixture


@pytest.mark.parametrize(
    "roles", [{}, {"universe": {"records": [], "eligible": False}}]
)
def test_empty_local_roles_are_not_positive_admission(roles):
    with pytest.raises(ValueError):
        validate_local_seed(
            {
                "contract": "unified-local-seed-projection-v1",
                "denials": [],
                "roles": roles,
            }
        )


@pytest.mark.parametrize(
    "mutation", ["target_session_before_first_eligible", "wrong_country"]
)
def test_reprojection_needs_exact_temporal_and_country_authority(mutation):
    s = source_fixture.__wrapped__()
    d = s["local_seed"]
    if mutation == "target_session_before_first_eligible":
        d["roles"]["universe"]["records"][0]["record"]["first_eligible_session"] = (
            "2026-09-26"
        )
    else:
        d["roles"]["security_identity"]["records"][0]["record"]["country"] = "KR"
    for part in d["roles"].values():
        part["version"] = digest(part["records"])
    with pytest.raises(ValueError):
        for role in d["roles"]:
            local_owner(
                role=role, market="us", session_key="2026-09-25", policy=s["policy"]
            ).project_and_validate(encoded(d), s["plan"].frozen_at)
