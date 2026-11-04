"""Source-only KR completed adjusted close via the original exact-price Owner.

No new raw parser or adjustment assumption. An adjusted chart close cannot be
relabeled an independent unadjusted regular close or granted Native authority.
"""
from app.services.completed_session_current_price import project_completed_price
from app.services.unified_snapshot_contract import digest


def project_source_close(**inputs):
    read = inputs['read']
    if read.market != 'kr' or read.api_id != 'ka10081' or not read.adjusted:
        raise ValueError('kr_source_close_original_adjusted_daily_required')
    projection = project_completed_price(**inputs)
    return dict(contract='kr-completed-adjusted-source-close-v1',
        projection=projection.model_dump(mode='json'),projection_sha256=projection.projection_sha256,
        single_capture_binding=digest(dict(plan=projection.source_plan_sha256,
            receipt=projection.source_receipt_sha256,raw=projection.raw_sha256,
            normalized=projection.normalized_sha256)),
        scope='SOURCE_ONLY_NO_NATIVE',
        completed_regular_session_close='UNAVAILABLE_ADJUSTMENT_COMPATIBILITY_UNPROVEN',
        current_price_authority=False,valuation=False,native=False,MarketParent=False)
