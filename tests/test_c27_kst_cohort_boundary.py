"""KST assessment-date boundary only; toy cohorts grant no Source rights."""
from dataclasses import replace

import pytest

from tests.test_c22z_dynamic_model_plan import cohort


def dated(cutoff, assessment='2026-11-21', *, market='us', effective=None, available=None):
    base = cohort(us=int(market == 'us'), kr=int(market == 'kr'))
    rows = tuple(replace(row, available_at=available or cutoff) for row in base.subjects)
    return replace(base, assessment_date=assessment, cutoff=cutoff,
                   effective_at=effective or cutoff, subjects=rows)


@pytest.mark.parametrize('cutoff', ['2026-11-20T21:10:06Z', '2026-11-20T23:10:05Z'])
def test_c25_both_real_cutoff_times_allow_kst_date(cutoff):
    value = dated(cutoff)
    assert value.assessment_date == '2026-11-21'
    assert value.cutoff.startswith('2026-11-20T') and value.cutoff.endswith('+00:00')
    assert value.effective_at == value.cutoff == value.subjects[0].available_at
    assert value.planning_only is True


def test_before_kst_midnight_still_rejects_next_day():
    with pytest.raises(ValueError, match='model_cohort_future_assessment'):
        dated('2026-11-20T23:59:59+09:00')


def test_kst_midnight_allows_new_day_without_changing_instant():
    assert dated('2026-11-21T00:00:00+09:00').cutoff == '2026-11-20T15:00:00+00:00'


def test_utc_midnight_keeps_same_kst_assessment_day():
    before = dated('2026-11-20T23:59:59+00:00')
    after = dated('2026-11-21T00:00:00+00:00')
    assert before.assessment_date == after.assessment_date == '2026-11-21'


def test_actual_future_kst_assessment_remains_rejected():
    with pytest.raises(ValueError, match='model_cohort_future_assessment'):
        dated('2026-11-20T23:10:05Z', assessment='2026-11-22')


def test_effective_instant_after_cutoff_remains_rejected():
    with pytest.raises(ValueError, match='model_cohort_effective_after_cutoff'):
        dated('2026-11-20T23:10:05Z', effective='2026-11-20T23:10:06Z')


def test_source_available_instant_after_cutoff_remains_rejected():
    with pytest.raises(ValueError, match='model_cohort_future_availability'):
        dated('2026-11-20T23:10:05Z', available='2026-11-20T23:10:06Z')


def test_naive_cutoff_and_effective_instant_remain_rejected():
    for kwargs in ({'cutoff': '2026-11-20T23:10:05'},
                   {'cutoff': '2026-11-20T23:10:05Z', 'effective': '2026-11-20T23:10:05'}):
        with pytest.raises(ValueError, match='model_cohort_aware_time_required'):
            dated(**kwargs)


def test_kr_cohort_uses_identical_boundary():
    assert dated('2026-11-20T21:10:06Z', market='kr').market_subjects == {'kr': ('KR000',)}
    with pytest.raises(ValueError, match='model_cohort_future_assessment'):
        dated('2026-11-20T14:59:59Z', market='kr')
