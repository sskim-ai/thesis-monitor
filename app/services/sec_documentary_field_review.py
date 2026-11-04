"""Source-bound documentary diagnostics, never non-supersession authority.

The parent supplies original replay, not a public reviewer-id or approval JSON.
This process-local capability proves repeatable source/review bindings only.
Semantic review annotations remain attributed producer observations. They cannot
clear purpose denials, issue financial ownership, or enter a numeric catalogue.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import os
import secrets
from weakref import WeakKeyDictionary

from app.services.unified_snapshot_contract import digest

CONTRACT = 'source-bound-correlated-financial-context-v1'
DISPOSITION = 'UNQUALIFIED_DOCUMENTARY_OBSERVATION'
CATEGORIES = {'EXACT_REPORTED_CELL', 'ROUNDED_EXPLANATORY_DISCLOSURE',
              'FORWARD_GUIDANCE', 'UNKNOWN_CONTENT'}
_IDENTITY = ('issuer', 'accession', 'field', 'period_start', 'period_end', 'currency')


def compare_field(exact, disclosure):
    """Check one explicitly scoped claim; no conversion between metric types."""
    result = dict(category=disclosure.get('category', 'UNKNOWN_CONTENT'),
                  status='UNKNOWN_CONTENT', source_use_granted=False)
    if result['category'] not in CATEGORIES:
        raise ValueError('documentary_category_unknown')
    if not disclosure.get('reviewed') or not disclosure.get('source_span'):
        return result
    if any(disclosure.get(k) != exact.get(k) for k in ('issuer', 'accession')):
        return dict(result, status='IDENTITY_MISMATCH')
    if disclosure.get('field') != exact['field']:
        return dict(result, status='OTHER_METRIC_NOT_REPLACEMENT_EVIDENCE')
    if result['category'] == 'FORWARD_GUIDANCE':
        return dict(result, status='FORECAST_NOT_REPORTED_ACTUAL')
    if disclosure.get('revised_period'):
        return dict(result, status='REVISED_PERIOD_UNRESOLVED')
    if any(disclosure.get(k) != exact.get(k) for k in _IDENTITY):
        return dict(result, status='PERIOD_OR_CURRENCY_MISMATCH')
    if disclosure.get('basis') not in (None, 'UNKNOWN', exact.get('basis')):
        return dict(result, status='STATEMENT_BASIS_CONFLICT')
    if result['category'] == 'UNKNOWN_CONTENT':
        return result
    try:
        value, scale, original, original_scale = map(Decimal, map(str,
            (disclosure['value'], disclosure['scale'], exact['value'], exact['scale'])))
        if not all(n.is_finite() for n in (value, scale, original, original_scale)) or min(scale, original_scale) <= 0:
            raise ValueError
        if result['category'] == 'EXACT_REPORTED_CELL':
            same = value * scale == original * original_scale
            status = 'EXACT_EQUAL' if same else 'CONFLICTING_EXACT_FIELD'
        else:
            precision = Decimal(str(disclosure['precision']))
            if not precision.is_finite() or precision <= 0 or precision.normalize().as_tuple().digits != (1,):
                raise ValueError
            same = (original * original_scale / scale).quantize(precision, rounding=ROUND_HALF_UP) == value
            status = 'CONSISTENT_AT_DISCLOSED_PRECISION' if same else 'CONFLICTING_DISCLOSED_FIELD'
    except (KeyError, ValueError, InvalidOperation):
        return dict(result, status='UNIT_VALUE_OR_PRECISION_UNRESOLVED')
    if disclosure.get('basis') in (None, 'UNKNOWN'):
        return dict(result, status='BASIS_UNVERIFIED', numerical_compatibility=status)
    return dict(result, status=status)


def selection_binding(documents, rows, ticker, cutoff):
    return digest(dict(documents=documents, rows=[r.model_dump(mode='json') for r in rows],
                       ticker=ticker, cutoff=cutoff))


class DocumentaryReview:
    __slots__ = ('__weakref__',)


class DocumentaryReviewRegistry:
    """Trusted-parent diagnostic lifetime. Public receipt rehydration is denied."""
    def __init__(self, original_replay):
        if not callable(original_replay):
            raise ValueError('original_source_replay_required')
        self._replay = original_replay
        self._pid = os.getpid()
        self._id = secrets.token_hex(16)
        self._issued = WeakKeyDictionary()

    def _source(self):
        if os.getpid() != self._pid:
            raise ValueError('documentary_parent_process_changed')
        original = self._replay()
        # Replay must return original-parser occurrences and the complete ordered
        # source inventory, including unreviewed assets. No trust from a label.
        inventory = original['inventory']
        ids = [x['id'] for x in inventory]
        if not inventory or len(set(ids)) != len(ids):
            raise ValueError('documentary_inventory_missing_or_duplicate')
        for item in inventory:
            if not all(item.get(k) for k in ('id', 'raw_sha256', 'receipt_sha256', 'source_generation', 'issuer', 'accession', 'url')):
                raise ValueError('documentary_source_binding_missing')
        return original

    def issue(self, review_event):
        original = self._source()
        event = deepcopy(review_event)
        if (event.get('original_replay_sha256') != digest(original)
                or event.get('contract') != CONTRACT
                or event.get('source_use_requested') is not False
                or not event.get('review_generation')):
            raise ValueError('documentary_event_scope_mismatch')
        inventory = {x['id']: x for x in original['inventory']}
        inspected = event['inventory_review']
        if set(inspected) != set(inventory):
            raise ValueError('documentary_inventory_omission')
        for ident, row in inspected.items():
            if row.get('raw_sha256') != inventory[ident]['raw_sha256'] or not row.get('review_evidence_sha256'):
                raise ValueError('documentary_review_source_mismatch')
        disclosures = event['disclosures']
        for row in disclosures:
            item = inventory.get(row.get('source_id'))
            if (not item or row.get('raw_sha256') != item['raw_sha256']
                    or row.get('issuer') != item['issuer'] or row.get('accession') != item['accession']):
                raise ValueError('documentary_disclosure_source_mismatch')
        reports = []
        unread = [k for k, v in inspected.items() if v.get('reviewed') is not True]
        for cell in original['exact_cells']:
            matching = [x for x in disclosures if x.get('field') == cell['field']]
            comparisons = []
            for row in matching:
                item = inventory[row['source_id']]
                if item['issuer'] != cell['issuer'] or item['accession'] != cell['accession']:
                    raise ValueError('documentary_cross_issuer_or_filing')
                # Same-field historical columns remain visible but do not conflict
                # merely because they describe another explicitly reported period.
                if row.get('period_end') != cell['period_end'] and row.get('category') != 'FORWARD_GUIDANCE':
                    if row.get('revised_period') or row.get('period_end', '') > cell['period_end']:
                        state = dict(category=row['category'], status='OTHER_OR_LATER_PERIOD_RETAINED', source_use_granted=False)
                    else:
                        state = dict(category=row['category'], status='OTHER_PERIOD_RETAINED', source_use_granted=False)
                else:
                    state = compare_field(cell, row)
                comparisons.append(dict(source_id=row['source_id'], disclosure=row, comparison=state))
            reports.append(dict(exact=cell,disclosures=comparisons,unread_sources=unread,
                disposition=DISPOSITION,financial_L3='DENIED',non_supersession_authority=False))
        receipt = dict(contract=CONTRACT,registry=self._id,review_generation=event['review_generation'],
            original_replay_sha256=digest(original),review_event_sha256=digest(event),
            selection_binding=original['selection_binding'],source_inventory=original['inventory'],
            fields=reports,disclosures=disclosures,unread_sources=unread,
            disposition=DISPOSITION,source_use_granted=False,financial_L3_granted=False,
            numeric_catalog_insertion_allowed=False,model_input_allowed=False,
            semantic_review_authority='PRODUCER_ANNOTATIONS_NOT_APPROVED_FINANCIAL_POLICY',
            first_break='FIELD_LOCAL_NON_SUPERSESSION_AUTHORITY_NOT_ESTABLISHED')
        receipt['receipt_sha256'] = digest(receipt)
        handle = DocumentaryReview()
        self._issued[handle] = (digest(original),receipt)
        return handle

    def resolve(self, handle, *, documents, rows, ticker, cutoff):
        if type(handle) is not DocumentaryReview or handle not in self._issued:
            raise ValueError('documentary_live_receipt_required')
        original = self._source()
        frozen,receipt = self._issued[handle]
        if digest(original) != frozen or selection_binding(documents,rows,ticker,cutoff) != receipt['selection_binding']:
            raise ValueError('documentary_original_or_selection_changed')
        return deepcopy(receipt)

    def revoke(self, handle):
        if os.getpid() != self._pid or handle not in self._issued:
            raise ValueError('documentary_live_receipt_required')
        del self._issued[handle]
