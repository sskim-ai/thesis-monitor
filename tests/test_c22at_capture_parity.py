"""Retained-cutoff controls using only a synthetic database."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.services import minimal_class_c_export as export
from app.services.unified_snapshot_contract import digest
from tests.test_c22an_registration_and_cohorts import synthetic_campaign


def test_full22_not_kr8_and_drift_never_rebinds_historical_cutoff(tmp_path, monkeypatch):
    fixture = synthetic_campaign(tmp_path, monkeypatch)
    fixture.now[0] = datetime(2026, 11, 12, 8, 14, tzinfo=timezone.utc)
    old = export.capture_authorized_class_c(fixture.permission)
    _, reference = export.captured_private_snapshot(old)
    fixture.now[0] += timedelta(hours=2)
    permission = replace(fixture.permission, event_id='synthetic-new')
    current = export.capture_authorized_class_c(permission)
    _, actual = export.captured_private_snapshot(current)
    pin = digest(reference)
    assert actual['cutoff'] != reference['cutoff']
    assert export.captured_source_cutoff(current,reference_capture=reference,retained_capture_sha256=pin)==reference['cutoff']
    kr = export.capture_authorized_class_c(replace(permission,subjects=tuple(t for t in permission.subjects if t.isdigit())))
    with pytest.raises(ValueError,match='exact_original_rows'):
        export.captured_source_cutoff(kr,reference_capture=reference,retained_capture_sha256=pin)
    for keys in (('source_identity','inode'),('private_export','schema_sha256'),
                 ('private_export','serializer_sha256'),('original_rows_sha256',)):
        altered = deepcopy(reference)
        target = altered if len(keys)==1 else altered[keys[0]]
        target[keys[-1]] = '0'*64
        with pytest.raises(ValueError,match='receipt_pin_changed'):
            export.captured_source_cutoff(current,reference_capture=altered,retained_capture_sha256=pin)
        with pytest.raises(ValueError,match='exact_original_rows'):
            export.captured_source_cutoff(current,reference_capture=altered,retained_capture_sha256=digest(altered))
    with pytest.raises(ValueError,match='unissued_capture'):
        export.captured_source_cutoff(export.CapturedClassC(),reference_capture=reference,retained_capture_sha256=pin)
