from app.services.directional_boundary_resolution_service import normalize_boundary_lean
from app.services.directional_boundary_resolution_service import (
    BOUNDARY_OUTPUT_CONTRACT,
    BoundaryAwareDirectionalCoreCandidate,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
)
from scripts import leverage_hold_sell_boundary_m12ab as m12ab


def test_non_hold_null_and_not_hold_normalize_equally() -> None:
    assert normalize_boundary_lean("SELL", None) == "NOT_HOLD"
    assert normalize_boundary_lean("SELL", "NOT_HOLD") == "NOT_HOLD"
    assert normalize_boundary_lean("BUY", "not-applicable") == "NOT_HOLD"


def test_hold_lean_remains_material() -> None:
    assert normalize_boundary_lean("HOLD", "SELL_LEAN") == "SELL_LEAN"
    assert normalize_boundary_lean("HOLD", "NEUTRAL") == "NEUTRAL"


def test_corrected_m12aa_band_audit() -> None:
    audit = m12ab.corrected_m12aa_audit()

    assert audit["status"] == "PASS"
    assert audit["in_band_minimum_sell_count"] == 2
    assert audit["in_band_hold_sell_lean_count"] == 1
    assert audit["out_of_band_count"] == 0
    assert audit["stable_preference"] == "MIXED_BOUNDARY"


def test_selects_exactly_option_f_without_scoring() -> None:
    options = m12ab.architecture_options()

    assert [row["option"] for row in options if row["decision"] == "SELECTED"] == ["F"]
    assert all("score" not in row for row in options)


def test_required_artifact_names_are_complete_and_unique() -> None:
    assert set(m12ab.SLUGS) == set(range(1, 89))
    assert len(set(m12ab.SLUGS.values())) == 88


def test_experimental_prompt_is_generic_and_keeps_production_prompt_separate() -> None:
    prompt = m12ab._boundary_prompt(
        packet_id="fictional-generation",
        tickers=("FIC",),
        contexts=({"ticker": "FIC", "evidence": []},),
    )

    assert BOUNDARY_OUTPUT_CONTRACT in prompt
    assert "directional-core-output-v1" not in prompt
    assert "ADJACENT_BUCKETS_REASONABLE" in prompt
    assert "less_directional_balance" in prompt
    assert "more_directional_balance" in prompt
    assert "FIC-FIN-05" not in prompt
    assert "900 debt" not in prompt
    assert "40 cash" not in prompt


def test_boundary_evidence_refs_are_alias_constrained() -> None:
    candidate_schema = m12ab.m12.engine.strict_json_schema(
        BoundaryAwareDirectionalCoreCandidate.model_json_schema()
    )
    schema = build_alias_constrained_batch_schema(
        candidate_schema=candidate_schema,
        contract=BOUNDARY_OUTPUT_CONTRACT,
        packet_id="generation",
        aliases_by_ticker={"FIC": ("E01", "E02")},
    )
    candidate = schema["properties"]["candidates"]["items"]["anyOf"][0]
    boundary_ref = candidate["properties"]["adjacent_boundary"]["$ref"]
    boundary_name = boundary_ref.rsplit("/", 1)[-1]
    boundary = schema["$defs"][boundary_name]
    evidence = boundary["properties"]["evidence_refs"]

    assert evidence["items"]["$ref"].endswith("EvidenceAlias")


def test_legacy_production_surfaces_remain_frozen() -> None:
    for path in (
        "app/services/direction_timing_ownership_service.py",
        "app/services/directional_balance_service.py",
        "app/services/daily_monitor_service.py",
        "app/services/daily_digest_renderer.py",
    ):
        assert m12ab._freeze_paths((path,))["status"] == "PASS"
        assert m12ab.BASE_FILE_SHA256[path] == m12ab._file_sha(m12ab.Path(path))


def test_stance_variance_report_preserves_both_audiences() -> None:
    new_buyer = {"status": "MEASURED", "variance_subject_count": 1}
    holder = {"status": "MEASURED", "variance_subject_count": 2}

    audit = m12ab._stance_variance_audit(new_buyer, holder)

    assert audit["status"] == "MEASURED"
    assert audit["new_buyer"] == new_buyer
    assert audit["holder"] == holder


def test_side_effect_firewall_requires_nonempty_zero_integer_counters() -> None:
    assert m12ab._firewall_passes({"production_sends": 0, "db_mutations": 0})
    assert not m12ab._firewall_passes({})
    assert not m12ab._firewall_passes({"production_sends": 1})
    assert not m12ab._firewall_passes({"production_sends": False})
