import json

import pytest

from app.services.canonical_source_replay import captured_phase_value, publication_inputs


@pytest.mark.parametrize('status', ['NOT_RUN_OUTSIDE_MARKET_DELTA', 'NOT_RUN', 'PASS', None])
@pytest.mark.parametrize('value', [None, {'value': 123, 'qualified': True}])
def test_skipped_phase_cannot_launder_a_value(tmp_path, status, value):
    outcome = {'phases': {'fred': {'status': status, 'value': value}}}
    with pytest.raises(ValueError, match='SOURCE_PREREQUISITE_NOT_CAPTURED:fred'):
        publication_inputs(tmp_path, {}, outcome, None)


@pytest.mark.parametrize('phase', ['fred', 'eia', 'ecos', 'night'])
def test_missing_phase_is_explicit(tmp_path, phase):
    with pytest.raises(ValueError, match='SOURCE_PREREQUISITE_NOT_CAPTURED:' + phase):
        captured_phase_value(tmp_path, {}, {'phases': {}}, phase)


@pytest.mark.parametrize('state', [
    {'status': 'CAPTURED_NOT_QUALIFIED'},
    {'status': 'CAPTURED_NOT_QUALIFIED', 'value': None},
])
def test_capture_requires_actual_producer_value(tmp_path, state):
    with pytest.raises(ValueError, match='SOURCE_CAPTURE_VALUE_MISSING'):
        captured_phase_value(tmp_path, {}, {'phases': {'night': state}}, 'night')


def test_captured_empty_is_not_skipped_or_qualified(tmp_path):
    state = {'status': 'CAPTURED_NOT_QUALIFIED', 'value': {}}
    (tmp_path / 'phase-night.json').write_text(json.dumps(state))
    assert captured_phase_value(tmp_path, {}, {'phases': {'night': state}}, 'night') == {}


def test_caller_changed_capture_denied(tmp_path):
    state = {'status': 'CAPTURED_NOT_QUALIFIED', 'value': {'probe': []}}
    (tmp_path / 'phase-night.json').write_text(json.dumps(state))
    with pytest.raises(OSError, match='captured_phase_provenance_mismatch'):
        captured_phase_value(tmp_path, {}, {'phases': {'night': {**state, 'value': {'probe': [1]}}}}, 'night')


def test_captured_phase_symlink_denied(tmp_path):
    state = {'status': 'CAPTURED_NOT_QUALIFIED', 'value': {}}
    original = tmp_path / 'original.json'
    original.write_text(json.dumps(state))
    (tmp_path / 'phase-night.json').symlink_to(original)
    with pytest.raises(OSError, match='captured_phase_symlink_denied'):
        captured_phase_value(tmp_path, {}, {'phases': {'night': state}}, 'night')
