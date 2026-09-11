from __future__ import annotations

from app.services.direction_timing_ownership_service import stage_alias_catalogs
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic
from scripts import unknown_field_consistency_offline_review as review


def _core_inventory(ticker: str) -> list[dict[str, object]]:
    return [
        {
            "ticker": ticker,
            "run": run,
            "context_path": f"model-contexts/{run}/DIRECTIONAL_CORE/batch-01",
            "normalized_output_sha256": run.lower().ljust(64, "0"),
        }
        for run in ("FIRST", "A", "B", "C")
    ]


def test_reference_to_alias_covers_every_core_reference_array() -> None:
    owned = synthetic.fictional_owned("SYNTHETIC_ALIAS_AUDIT", market="us")
    candidate = synthetic.fixture_core(owned)
    core_catalog, _ = stage_alias_catalogs(owned)

    aliased = review._reference_to_alias(
        candidate.model_dump(mode="json"), core_catalog.by_ref
    )

    strings = review._all_strings(aliased)
    assert not any(value.startswith("fictional:") for value in strings)
    assert aliased["fundamental_new_buyer"]["confirmation_business_condition_refs"]
    assert aliased["fundamental_holder"]["business_invalidation_condition_refs"]


def test_exposure_registry_reconciliation_is_idempotent() -> None:
    source = {
        "contract": "source-registry-v1",
        "rows": [],
        "all_excluded_issuer_keys": [],
    }
    identities = {
        "NEON": {
            "canonical_issuer_key": "sec:cik:0000087050",
            "market": "us",
        }
    }

    first, first_appended = review._reconcile_exposure_registry(
        source,
        identities,
        _core_inventory("NEON"),
        "generation-one",
    )
    second, second_appended = review._reconcile_exposure_registry(
        first,
        identities,
        _core_inventory("NEON"),
        "generation-one",
    )

    assert first_appended == 1
    assert second_appended == 0
    assert review.canonical_sha256(first["rows"]) == review.canonical_sha256(
        second["rows"]
    )
    assert first["rows"][0]["security_aliases"] == ["NEON"]
    assert first["rows"][0]["whole_cohort_retired"] is True
    assert len(first["rows"][0]["lineage"]) == 4


def test_safe_member_rejects_escape_and_accepts_focused_payload() -> None:
    assert review._safe_member("reports/completion.json")
    assert not review._safe_member("../outside.json")
    assert not review._safe_member("/absolute.json")
