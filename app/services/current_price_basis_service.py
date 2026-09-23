"""Shared price-phase/adjustment vocabulary, not an investment decision owner."""
from datetime import date


CONTRACT = 'm12ds-r6-r1-market-source-and-price-basis-closure-v1'
BASES = {
    'intraday': ('INTRADAY', 'RAW', '장중 관측'),
    'adjusted_intraday': ('INTRADAY', 'ADJUSTED', '조정가격 기준 장중 관측'),
    'close': ('CLOSE', 'RAW', '종가'),
    'adjusted_close': ('CLOSE', 'ADJUSTED', '조정 종가'),
}


def price_basis_context(legacy):
    if not isinstance(legacy, str) or legacy not in BASES:
        raise ValueError('accepted_quote_basis_invalid')
    phase, adjustment, _ = BASES[legacy]
    return dict(contract=CONTRACT, phase=phase, adjustment=adjustment, legacy=legacy)


def legacy_price_basis(*, intraday, adjusted):
    if not isinstance(intraday, bool) or not isinstance(adjusted, bool):
        raise ValueError('price_basis_dimensions_invalid')
    return ('adjusted_' if adjusted else '') + ('intraday' if intraday else 'close')


def validate_quote_context(quote, assessment_date):
    if quote.get('contract') != 'current-price-context-v1':
        raise ValueError('accepted_quote_contract_invalid')
    if quote.get('availability') not in {'ready', 'partial'}:
        raise ValueError('accepted_quote_availability_invalid')
    basis = price_basis_context(quote.get('price_basis'))
    if quote.get('price_basis_context') is not None and quote['price_basis_context'] != basis:
        raise ValueError('accepted_quote_basis_binding_invalid')
    try:
        observed, assessed = date.fromisoformat(quote['as_of_date']), date.fromisoformat(assessment_date)
        completed = quote.get('latest_completed_regular_session_date')
        if observed > assessed or (basis['phase'] == 'INTRADAY' and observed != assessed):
            raise ValueError('quote_date_mismatch')
        if basis['phase'] == 'CLOSE' and completed and observed != date.fromisoformat(completed):
            raise ValueError('quote_completed_session_mismatch')
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('accepted_quote_asof_invalid') from exc
    return basis


def price_basis_label(basis):
    if price_basis_context(basis.get('legacy')) != basis:
        raise ValueError('accepted_quote_basis_binding_invalid')
    return BASES[basis['legacy']][2]
