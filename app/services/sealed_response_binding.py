"""Response-owned values for predeclared slots, never new request descriptors."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Literal

import httpx
from pydantic import Field, model_validator

from app.services.bounded_financial_acquisition import (
    dart_selection, exhibit_selection, sec_base, sec_selection,
)
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest, encoded


class SlotNotSelected(ValueError):
    """A sealed optional continuation/document slot has no selected input."""


class ResponseBinding(ContractModel):
    kind: Literal['KIWOOM_CONTINUATION', 'KIWOOM_US_EXCHANGE', 'SEC_PRIMARY', 'SEC_INDEX', 'SEC_EXHIBIT',
                  'DART_NEXT_PAGE', 'DART_STATEMENT']
    parents: tuple[str, ...] = Field(min_length=1, max_length=3)
    policy_json: str
    policy_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    selection_ordinal: int = Field(default=1, ge=1, le=4)
    item_ordinal: int = Field(default=1, ge=1, le=2)
    basis: Literal['CFS', 'OFS'] | None = None

    @model_validator(mode='after')
    def exact_policy(self):
        policy = json.loads(self.policy_json)
        if encoded(policy).decode() != self.policy_json or digest(policy) != self.policy_sha256:
            raise ValueError('binding_policy_identity_mismatch')
        if len(set(self.parents)) != len(self.parents):
            raise ValueError('binding_parent_duplicate')
        expected = 3 if self.kind in {'SEC_EXHIBIT', 'KIWOOM_US_EXCHANGE'} else 2 if self.kind == 'DART_STATEMENT' else 1
        if len(self.parents) != expected:
            raise ValueError('binding_parent_count')
        if (self.kind == 'DART_STATEMENT') != (self.basis is not None):
            raise ValueError('binding_statement_basis')
        if self.kind == 'KIWOOM_CONTINUATION':
            if policy not in ({'rule': 'previous_page_exact_continuation'},
                              {'rule': 'previous_page_exact_continuation', 'inherit_exchange': True}):
                raise ValueError('binding_continuation_policy')
        elif self.kind == 'KIWOOM_US_EXCHANGE':
            if (set(policy) != {'rule', 'symbol', 'exchange_order', 'row_keys'}
                    or policy['rule'] != 'native_exact_symbol_in_exchange_list'
                    or policy['exchange_order'] != ['ND', 'NY', 'NA']
                    or policy['row_keys'] != ['list', 'result_list', 'output', 'data']
                    or not isinstance(policy['symbol'], str) or not policy['symbol']):
                raise ValueError('binding_us_exchange_policy')
        else:
            from app.services.bounded_financial_acquisition import make_plan
            from datetime import datetime
            rebuilt = make_plan(policy['security'], market=policy['market'],
                cutoff=datetime.fromisoformat(policy['cutoff']), run_id=policy['run_id'], all_subjects_fresh=True,
                exact_financial_owner=bool(policy.get('financial_owner_policy')))
            if rebuilt != policy:
                raise ValueError('binding_not_existing_financial_policy')
            market = 'us' if self.kind.startswith('SEC_') else 'kr'
            if policy['market'] != market:
                raise ValueError('binding_policy_market')
            if self.selection_ordinal > policy['limits']['current'] + policy['limits']['prior']:
                raise ValueError('binding_selection_budget')
            if self.kind == 'SEC_EXHIBIT' and self.item_ordinal > policy['limits']['linked_exhibits']:
                raise ValueError('binding_exhibit_budget')
        return self


def binding_owner_hash():
    root = Path(__file__).resolve().parents[2]
    names = ('app/services/sealed_response_binding.py',
             'app/services/bounded_financial_acquisition.py',
             'app/services/sec_current_financial_candidates.py',
             'app/services/sec_financial_snapshot_service.py',
             'app/services/opendart_financial_recovery_service.py')
    return digest({p: sha256_bytes((root / p).read_bytes()) for p in names})


def resolve_response_binding(template, binding, parents):
    """Parents are verified dispatcher artifacts, not values supplied by callers.

    Return the exact public request plus selected metadata. Credentials remain
    redacted; the dispatcher compares the actual wire request after redaction.
    """
    binding = ResponseBinding.model_validate(binding)
    if set(parents) != set(binding.parents):
        raise ValueError('binding_parent_set_mismatch')
    sources = [parents[p] for p in binding.parents]
    request = json.loads(template)
    policy = json.loads(binding.policy_json)
    selected = None
    if binding.kind == 'KIWOOM_US_EXCHANGE':
        found = []
        for exchange, source in zip(policy['exchange_order'], sources, strict=True):
            if source['status'] != 'PASS':
                raise ValueError('binding_exchange_discovery_incomplete')
            req = source['request']
            if (json.loads(req['body']) != {'stex_tp': exchange}
                    or dict(req['headers']).get('api-id') != 'usa10099'):
                raise ValueError('binding_exchange_parent_request')
            payload = json.loads(source['raw'])
            rows = None
            for key in policy['row_keys']:
                value = payload.get(key)
                if isinstance(value, list):
                    rows = value
                    break
                if isinstance(value, dict):
                    rows = next((v for v in value.values() if isinstance(v, list)), None)
                    if rows is not None:
                        break
            if rows is None:
                rows = next((v for v in payload.values() if isinstance(v, list)), [])
            found += [exchange for row in rows if isinstance(row, dict)
                      and str(row.get('stk_cd', '')).upper().replace('.', '-') == policy['symbol'].upper().replace('.', '-')]
        if len(found) != 1:
            raise ValueError('binding_exchange_symbol_not_unique')
        body = json.loads(request['body'])
        if body.get('stk_cd') != policy['symbol']:
            raise ValueError('binding_exchange_subject_mismatch')
        body['stex_tp'] = found[0]
        request['body'] = encoded(body).decode()
        selected = {'symbol': policy['symbol'], 'exchange': found[0]}
    elif binding.kind == 'KIWOOM_CONTINUATION':
        source = sources[0]
        if source['status'] == 'NOT_SELECTED':
            raise SlotNotSelected('ANCESTOR_NO_CONTINUATION')
        if source['status'] != 'PASS':
            raise ValueError('binding_parent_not_successful')
        previous = source['request']
        headers = dict(previous['headers'])
        current_headers = dict(request['headers'])
        if policy.get('inherit_exchange'):
            prior_body, body = json.loads(previous['body']), json.loads(request['body'])
            prior_exchange = prior_body.pop('stex_tp')
            body.pop('stex_tp')
            if body != prior_body or prior_exchange not in {'ND', 'NY', 'NA'}:
                raise ValueError('binding_page_exchange_inheritance_scope')
            request['body'] = previous['body']
        # Only the continuation pair may differ from the preceding page.
        for key in ('cont-yn', 'next-key'):
            headers.pop(key, None)
            current_headers.pop(key, None)
        if ({k: previous[k] for k in ('method', 'url', 'body')} !=
                {k: request[k] for k in ('method', 'url', 'body')} or headers != current_headers):
            raise ValueError('binding_page_request_scope_changed')
        response = source['response_headers']
        payload = json.loads(source['raw'])
        cont = str(response.get('cont-yn') or payload.get('cont-yn') or payload.get('cont_yn') or 'N')
        cursor = str(response.get('next-key') or payload.get('next-key') or payload.get('next_key') or '')
        if cont != 'Y':
            raise SlotNotSelected('NO_CONTINUATION')
        if not cursor or cursor == dict(previous['headers']).get('next-key'):
            raise ValueError('binding_invalid_or_repeated_cursor')
        current_headers.update({'cont-yn': 'Y', 'next-key': cursor})
        request['headers'] = sorted(current_headers.items())
    elif binding.kind.startswith('SEC_'):
        if sources[0]['status'] != 'PASS':
            raise ValueError('binding_parent_not_successful')
        filings = sec_selection(json.loads(sources[0]['raw']), policy)
        if binding.selection_ordinal > len(filings):
            raise SlotNotSelected('NO_SELECTED_FILING')
        if any(s['status'] != 'PASS' for s in sources):
            raise ValueError('binding_parent_not_successful')
        selected = filings[binding.selection_ordinal - 1]
        base = sec_base(policy, selected)
        if binding.kind == 'SEC_PRIMARY':
            request['url'] = base + selected['primaryDocument']
        elif binding.kind == 'SEC_INDEX':
            request['url'] = base + 'index.json'
        else:
            if (sources[1]['request']['url'] != base + 'index.json' or
                    sources[2]['request']['url'] != base + selected['primaryDocument']):
                raise ValueError('binding_exhibit_wrong_filing_parent')
            urls = exhibit_selection(json.loads(sources[1]['raw']), sources[2]['raw'].decode('utf-8', errors='replace'),
                                     policy, selected)
            if binding.item_ordinal > len(urls):
                raise SlotNotSelected('NO_SELECTED_EXHIBIT')
            request['url'] = urls[binding.item_ordinal - 1]
    else:
        first = sources[0]
        if first['status'] != 'PASS':
            raise ValueError('binding_parent_not_successful')
        payload = json.loads(first['raw'])
        if payload.get('status') not in {'000', '013'}:
            raise ValueError('binding_dart_discovery_denied')
        total = int(payload.get('total_page') or 1)
        if not 1 <= total <= policy['limits']['discovery']:
            raise ValueError('binding_dart_discovery_exhausted')
        if binding.kind == 'DART_NEXT_PAGE':
            if total == 1:
                raise SlotNotSelected('NO_SECOND_DISCOVERY_PAGE')
        else:
            rows = payload.get('list', [])
            if total == 2:
                if sources[1]['status'] != 'PASS':
                    raise ValueError('binding_parent_not_successful')
                second = json.loads(sources[1]['raw'])
                if second.get('status') != '000' or int(second.get('total_page') or 1) != total:
                    raise ValueError('binding_dart_discovery_drift')
                rows += second.get('list', [])
            filings = dart_selection(rows, policy)
            if binding.selection_ordinal > len(filings):
                raise SlotNotSelected('NO_SELECTED_FILING')
            role, filing = filings[binding.selection_ordinal - 1]
            selected = dict(asdict(filing), role=role, receipt_date=filing.receipt_date.isoformat())
            url = httpx.URL(request['url'])
            params = dict(url.params)
            params.update(corp_code=policy['issuer'], bsns_year=str(filing.business_year),
                          reprt_code=filing.report_code, fs_div=binding.basis)
            request['url'] = str(url.copy_with(query=None).copy_merge_params(params)).replace('%5BREDACTED%5D', '[REDACTED]')
    return encoded(request).decode(), selected
