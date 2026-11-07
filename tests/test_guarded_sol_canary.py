import pytest

from maintenance.guarded_sol_canary import run_stage


def arguments():
    def forbidden(*args, **kwargs):
        raise AssertionError('No backend or model operation permitted')
    return dict(binding=None, config=None, packet={}, registry=None, source_loader=forbidden,
                economic_loader=forbidden, valuation_analysis_owner=None, request={}, knowledge='',
                approval=forbidden, account_lease=forbidden, session=None, prior_session=None, out=None)


def test_default_off_before_all_backend_access():
    with pytest.raises(ValueError, match='default_off'):
        run_stage(**arguments())


def test_unapproved_stage_never_reaches_source_or_host():
    values = arguments(); values.update(approval=lambda request: False, enabled=True)
    with pytest.raises(ValueError, match='fresh_request_grant'):
        run_stage(**values)
