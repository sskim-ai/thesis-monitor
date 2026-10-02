"""Compile bounded chart-page slots without inventing continuation values."""
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor
from app.services.sealed_response_binding import ResponseBinding
from app.services.unified_snapshot_contract import digest, encoded


def chart_slots(first, *, maximum_pages):
    first = FreshRequestDescriptor.model_validate(first)
    if first.provider != 'kiwoom' or first.page_ordinal != 1 or (first.response_binding and first.response_binding.kind != 'KIWOOM_US_EXCHANGE'):
        raise ValueError('chart_first_page_literal_required')
    if type(maximum_pages) is not int or not 1 <= maximum_pages <= 100:
        raise ValueError('chart_finite_page_budget_required')
    policy = {'rule': 'previous_page_exact_continuation'}
    if first.response_binding:
        policy['inherit_exchange'] = True
    values = first.model_dump()
    values.update(group_id=first.logical_request_id + ':pages', max_pages=maximum_pages)
    rows = [FreshRequestDescriptor.model_validate(values)]
    for page in range(2, maximum_pages + 1):
        key = first.logical_request_id + ':continuation:' + str(page)
        values = first.model_dump()
        values.update(logical_request_id=key, raw_path=f'raw/{key}/source.body',
            group_id=rows[0].group_id, page_ordinal=page, max_pages=maximum_pages,
            response_binding=ResponseBinding(kind='KIWOOM_CONTINUATION', parents=(rows[-1].logical_request_id,),
                policy_json=encoded(policy).decode(), policy_sha256=digest(policy)))
        rows.append(FreshRequestDescriptor.model_validate(values))
    return tuple(rows)
