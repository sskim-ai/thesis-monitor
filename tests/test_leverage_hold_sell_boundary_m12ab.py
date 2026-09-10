from scripts import leverage_hold_sell_boundary_m12ab as m12ab


def test_non_hold_null_and_not_hold_normalize_equally() -> None:
    assert m12ab.normalize_boundary_lean("SELL", None) == "NOT_HOLD"
    assert m12ab.normalize_boundary_lean("SELL", "NOT_HOLD") == "NOT_HOLD"
    assert m12ab.normalize_boundary_lean("BUY", "not-applicable") == "NOT_HOLD"


def test_hold_lean_remains_material() -> None:
    assert m12ab.normalize_boundary_lean("HOLD", "SELL_LEAN") == "SELL_LEAN"
    assert m12ab.normalize_boundary_lean("HOLD", "NEUTRAL") == "NEUTRAL"


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
