import pytest

from tests.historical_scope_descendant_fixture import (
    CALENDAR_PATH,
    require_exact_calendar_descendant,
)


def test_exact_reviewed_cache_bytes_remain_required():
    require_exact_calendar_descendant()


def test_path_is_not_an_unrestricted_scope_exemption():
    from pathlib import Path

    raw = (Path(__file__).resolve().parents[1] / CALENDAR_PATH).read_bytes()
    with pytest.raises(AssertionError, match="unreviewed_calendar_descendant"):
        require_exact_calendar_descendant(raw + b"\n")
