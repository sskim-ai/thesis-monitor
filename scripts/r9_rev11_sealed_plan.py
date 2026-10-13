"""Historical proof adapter over the canonical finite provider-slot compiler."""
from app.services.canonical_source_plan import compile_slots
from app.services.sealed_fresh_dispatch import ProviderPlan
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import encoded


def compile_plan(*, stock, identities, news_reads, config_identities, rev10_receipt,
                 configured_kr_pages, kr_post_acquisition_completeness_approved, exact_financial_owner=False,
                 valuation_market_types=None, auxiliary_security=None, auxiliary_identity_sha256=None):
    result = compile_slots(stock=stock, identities=identities, news_reads=news_reads,
        config_identities=config_identities, configured_kr_pages=configured_kr_pages,
        kr_post_acquisition_completeness_approved=kr_post_acquisition_completeness_approved,
        exact_financial_owner=exact_financial_owner, valuation_market_types=valuation_market_types,
        auxiliary_security=auxiliary_security, auxiliary_identity_sha256=auxiliary_identity_sha256)
    result['plan'] = ProviderPlan(**result['plan'].model_dump(),
        rev10_receipt_sha256=sha256_bytes(encoded(rev10_receipt) + b'\n'))
    from app.services.completed_price_state import require_plan
    require_plan(result['plan'], stock)
    return result
