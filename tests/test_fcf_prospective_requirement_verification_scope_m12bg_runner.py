from __future__ import annotations

from scripts import fcf_prospective_requirement_verification_scope_m12bg as runner


def test_m12bg_report_contract_is_complete_and_unique() -> None:
    assert len(runner.REPORT_SLUGS) == 141
    assert len(set(runner.REPORT_SLUGS)) == len(runner.REPORT_SLUGS)
    assert runner.NUMBERS["repository-provenance"] == 1
    assert runner.NUMBERS["program-completion"] == 141


def test_m12bg_model_and_reuse_contract_are_frozen() -> None:
    assert runner.MODEL == "gpt-5.6-sol"
    assert runner.EFFORT == "xhigh"
    assert runner.M12BD_GENERATION_ID == (
        "20260911-m12ai-fictional-20260913T113957Z-07ac29f97bc6"
    )
    assert runner.M12BF_SHADOW_GENERATION_ID == (
        "20260911-m12ai-shadow-20260913T141850Z-fdfcb99c8668"
    )


def test_m12bg_does_not_hardcode_active_universe_count() -> None:
    assert runner._unique_tickers(("A", "B"), subject="fixture") == ("A", "B")


def test_m12bg_requires_a_new_shadow_generation() -> None:
    assert "new-shadow-generation-manifest" in runner.REPORT_SLUGS
    assert "m12bf-context01-four-candidate-offline-replay" in runner.REPORT_SLUGS
    assert "m12bd-complete-fictional-offline-reaudit" in runner.REPORT_SLUGS
