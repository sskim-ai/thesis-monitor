from app.services.night_futures_visibility_service import (
    SESSION_DATE_CONVENTION_PENDING,
    night_futures_user_facing_visibility,
)


def test_us_night_futures_are_temporarily_suppressed_with_internal_reason() -> None:
    decision = night_futures_user_facing_visibility("us")

    assert decision.visible is False
    assert decision.suppression_reason == SESSION_DATE_CONVENTION_PENDING


def test_non_us_visibility_is_unchanged() -> None:
    decision = night_futures_user_facing_visibility("kr")

    assert decision.visible is True
    assert decision.suppression_reason is None
