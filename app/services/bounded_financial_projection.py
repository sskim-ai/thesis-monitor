"""Offline occurrence/projection audit over bounded official response bytes.

Amounts use existing SEC/DART parsers and existing quality decisions. A direction
requires an independently eligible comparable pair, never only a current amount.
"""
from __future__ import annotations

from datetime import date, datetime
from dataclasses import asdict
import json
import math
from pydantic import TypeAdapter

from app.models.financial import FinancialSnapshot
from app.services.financial_freshness_service import evaluate_financial_freshness_records
from app.services.opendart_financial_recovery_service import (
    Filing, FIELD_SPECS, select_field_occurrence,
)
from app.services.kr_financial_lineage_service import opendart_field_lineage, opendart_lineage_records
from app.services.kr_financial_lineage_service import _bounds
from app.services.financial_observation_quality_service import build_reported_observation_quality
from app.services.sec_business_field_quality_service import field_errors
from app.services.sec_financial_snapshot_service import _companyfacts_snapshots
from app.services.sec_foreign_comparison_service import parse_document, occurrence_errors
from app.services.sec_foreign_comparison_service import current_projection
from scripts.m12dr_financial_source_authority import source_quality
from app.services.financial_observation_quality_service import digest as quality_digest
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.bounded_financial_acquisition import sec_selection, dart_selection

METRICS = ("revenue", "operating_income", "net_income")
CONTRACT = "bounded-official-financial-projection-v1"


def paired(current, prior):
    if not current.get("context_eligible") or not prior.get("context_eligible"):
        return False
    keys = ("canonical_company_id", "canonical_security_id", "metric", "semantic", "period_role",
            "statement_basis", "currency", "unit", "unit_scale", "formal_state", "source_provider")
    if any(not current.get(k) or current[k] != prior.get(k) for k in keys):
        return False
    try:
        cs, ce = [date.fromisoformat(current[k]) for k in ("period_start", "period_end")]
        ps, pe = [date.fromisoformat(prior[k]) for k in ("period_start", "period_end")]
        return cs < ce and ps < pe < ce and (ce - cs).days == (pe - ps).days and 330 <= (ce - pe).days <= 400
    except (ValueError, KeyError, TypeError):
        return False


def field_record(plan, *, metric, value, lineage, quality, raw_sha, role):
    value_ok = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    required = ("source_document_id", "source_document_type", "filing_date", "occurrence_id",
                "semantic", "period_start", "period_end", "period_role", "statement_basis", "currency", "unit", "unit_scale")
    errors = list(quality)
    if not value_ok or not all(lineage.get(k) for k in required):
        errors.append("LINEAGE_UNRESOLVED")
    try:
        start, end, filed = [date.fromisoformat(lineage[k]) for k in ("period_start", "period_end", "filing_date")]
        if not start < end <= filed <= date.fromisoformat(plan["cutoff"][:10]):
            errors.append("PERIOD_NOT_COMPARABLE")
    except (KeyError, ValueError, TypeError):
        errors.append("PERIOD_NOT_COMPARABLE")
    if not raw_sha or len(raw_sha) != 64:
        errors.append("raw_artifact_missing")
    security = plan["security"]
    result = {"contract": CONTRACT, "ticker": plan["ticker"], "metric": metric, "value": value,
        "canonical_company_id": security["canonical_company_id"], "canonical_security_id": security["canonical_security_id"],
        "provider_issuer_id": plan["issuer"], "source_provider": plan["provider"],
        "raw_artifact_sha256": raw_sha, "current_prior_role": role, "extractor_version": CONTRACT,
        **lineage, "quality_errors": sorted(set(errors)), "context_eligible": not errors,
        "source_use": "ABSOLUTE_CONTEXT_ELIGIBLE" if not errors else "DENIED",
        "direction_eligible": False, "formal_state": lineage.get("formal_state", "FORMAL")}
    result["normalized_hash"] = digest(result)
    return result


def _raw(directory, artifact, receipts):
    matches = [r for r in receipts if r.get("artifact") == artifact and not r.get("failure_class")]
    if len(matches) != 1:
        raise ValueError("unique_successful_receipt_required")
    raw = (directory / artifact).read_bytes()
    if sha256_bytes(raw) != matches[0]["raw_sha256"]:
        raise ValueError("raw_receipt_hash_mismatch")
    return raw


def verify_capture(plan, acquisition, directory, receipts):
    logical = {}
    for receipt in receipts:
        if receipt['plan_sha256'] != digest(plan) or not 1 <= receipt['attempt'] <= 3:
            raise ValueError('receipt_plan_or_attempt_mismatch')
        name = receipt['logical_id'].split(':')[-1]
        frozen = json.loads((directory / (name + '.plan.json')).read_bytes())
        if (digest(frozen) != receipt['request_sha256'] or frozen['plan_sha256'] != digest(plan)
                or frozen['logical_id'] != receipt['logical_id'] or frozen['stage'] != receipt['stage']
                or frozen.get('filing') != receipt.get('filing')):
            raise ValueError('receipt_request_binding_mismatch')
        attempts = logical.setdefault(receipt['logical_id'], [])
        if receipt['attempt'] != len(attempts)+1 or (attempts and attempts[-1]['request_sha256'] != receipt['request_sha256']):
            raise ValueError('receipt_retry_identity_mismatch')
        attempts.append(receipt)
    if len(logical) > plan['maximum_logical_requests'] or len(receipts) > plan['maximum_HTTP_attempts']:
        raise ValueError('receipt_budget_exceeded')
    discovery = [r for r in receipts if r['stage']=='discovery' and not r['failure_class']]
    if plan['provider']=='sec_edgar':
        if len(discovery)!=1:
            raise ValueError('discovery_receipt_missing')
        selected=sec_selection(json.loads(_raw(directory,discovery[0]['artifact'],receipts)),plan)
    else:
        rows=[]
        for index,r in enumerate(discovery,1):
            if r.get('page')!=index:
                raise ValueError('discovery_page_gap')
            payload=json.loads(_raw(directory,r['artifact'],receipts))
            if int(payload.get('total_page') or 1) > len(discovery):
                raise ValueError('OPENDART_DISCOVERY_BOUND_EXHAUSTED')
            rows.extend(payload.get('list',[]))
        if not discovery:
            raise ValueError('discovery_receipt_missing')
        selected=[{'role':role,**asdict(f),'receipt_date':f.receipt_date.isoformat()} for role,f in dart_selection(rows,plan)]
    if acquisition['selected_filings'] != selected:
        raise ValueError('selected_filing_discovery_replay_mismatch')
    for doc in acquisition['documents']:
        receipt=next((r for r in receipts if r.get('artifact')==doc['artifact']),None)
        if not receipt or receipt.get('filing')!=doc['filing'] or receipt['stage'] not in {'document','statement'}:
            raise ValueError('document_receipt_filing_mismatch')
        frozen=json.loads((directory/(receipt['logical_id'].split(':')[-1]+'.plan.json')).read_bytes())
        if doc.get('url') and frozen['url']!=doc['url']:
            raise ValueError('document_receipt_url_mismatch')
        _raw(directory,doc['artifact'],receipts)


def project(plan, acquisition, directory, receipts):
    if acquisition["plan_sha256"] != digest(plan):
        raise ValueError("financial_plan_binding_mismatch")
    verify_capture(plan,acquisition,directory,receipts)
    snapshots, witnesses, denied = [], {}, []
    filings = acquisition["selected_filings"]
    created = datetime.fromisoformat(plan["cutoff"])
    if plan["provider"] == "sec_edgar":
        artifact = acquisition.get("companyfacts_artifact")
        if artifact:
            raw = _raw(directory, artifact, receipts)
            payload = json.loads(raw)
            if str(payload.get("cik", "")).lstrip('0') != plan["issuer"].lstrip('0'):
                raise ValueError("issuer_mismatch")
            selected = {f["accessionNumber"]: f for f in filings}
            document_ids = {d["filing"]["accessionNumber"] for d in acquisition["documents"]}
            for row in _companyfacts_snapshots(payload, plan["ticker"]):
                filing = selected.get(row.source_filing_id)
                if not filing or row.source_filing_id not in document_ids:
                    continue
                if row.normalization_method:
                    denied.append({"field": "all", "reason": "DERIVED_PERIOD_NOT_IN_REPORTED_SCOPE", "filing": row.source_filing_id})
                    continue
                row.unit_scale = 1
                row.created_at = created
                row.id = len(snapshots) + 1
                snapshots.append(row)
                witnesses[row.id] = {"raw_sha": sha256_bytes(raw), "filing": filing,
                    "fields": {r["field"]: r for r in json.loads(row.raw_financial_fields) if r.get("field") in METRICS}}
        # Preserve foreign statement occurrences, but do not disguise them as
        # Company Facts. Their separate existing owner must qualify each cell.
        foreign, foreign_rows = [], []
        for document in acquisition["documents"]:
            filing = document["filing"]
            if filing["form"].split('/')[0] not in {"6-K", "20-F"}:
                continue
            raw = _raw(directory, document["artifact"], receipts)
            occurrences = parse_document(raw.decode('utf-8', errors='replace'), issuer_cik=plan["issuer"],
                    accession=filing["accessionNumber"], document_type=filing["form"], filing_date=filing["filingDate"],
                    source_url=document["url"], raw_payload=raw)
            for occurrence in occurrences:
                foreign.append({"occurrence": occurrence,
                    "errors": occurrence_errors(occurrence, date.fromisoformat(plan["cutoff"][:10])),
                    "packet_consumption": "SEPARATE_FOREIGN_OWNER_NOT_COMPANYFACTS"})
            current = current_projection(occurrences)
            if current:
                end = date.fromisoformat(current['period_end'])
                foreign_rows.append(FinancialSnapshot(ticker=plan['ticker'], period=end.isoformat(),
                    financial_period_end=end, financials_as_of=end, filing_date=date.fromisoformat(filing['filingDate']),
                    source_filing_id=filing['accessionNumber'], source=document['url'], provider='sec_foreign_filing',
                    currency=current['currency'], period_scope='single-quarter', unit_scale=1, created_at=created,
                    raw_financial_fields=json.dumps([{'field':'foreign_business_occurrences','occurrences':occurrences}]),
                    **{k: current.get(k) for k in ('revenue','operating_income')}))
    else:
        foreign, foreign_rows = [], []
        for filing_data in filings:
            role = filing_data["role"]
            filing = Filing(**{**{k: v for k, v in filing_data.items() if k != "role"},
                               "receipt_date": date.fromisoformat(filing_data["receipt_date"])})
            rows_by_basis, raw_hashes = {}, {}
            for document in acquisition["documents"]:
                info = document["filing"]
                if info["receipt_no"] != filing.receipt_no:
                    continue
                raw = _raw(directory, document["artifact"], receipts)
                rows = json.loads(raw).get("list", [])
                if any(str(r.get("rcept_no")) != filing.receipt_no or str(r.get("corp_code")) != plan["issuer"]
                       or str(r.get("bsns_year")) != str(filing.business_year)
                       or str(r.get("reprt_code")) != filing.report_code
                       or (r.get("fs_div") and r["fs_div"] != info["basis"]) for r in rows):
                    denied.append({"field": "all", "reason": "STATEMENT_RESPONSE_FILING_IDENTITY_MISMATCH", "filing": filing.receipt_no})
                    continue
                rows_by_basis[info["basis"]] = rows
                raw_hashes[info["basis"]] = sha256_bytes(raw)
            fields, values, lineages = {}, {}, []
            for metric in METRICS:
                selection = select_field_occurrence(rows_by_basis, FIELD_SPECS[metric])
                if selection.status != 'selected' or selection.row is None:
                    denied.append({"field": metric, "filing": filing.receipt_no,
                        "reason": selection.reason or "FIELD_ABSENT"})
                    continue
                lineage = opendart_field_lineage(selection.row, logical_field=metric,
                    report_code=filing.report_code, source_column='thstrm_amount', selected=True,
                    requested_fs_div=selection.basis)
                fields[metric] = {"lineage": lineage, "raw_sha": raw_hashes[selection.basis]}
                lineages.extend(opendart_lineage_records(selection.row, logical_field=metric,
                    report_code=filing.report_code, selected=True, requested_fs_div=selection.basis))
                values[metric] = lineage.get('amount')
            if not fields:
                continue
            tuples = {(r['lineage'].get('amount_period_start'), r['lineage'].get('amount_period_end'),
                       r['lineage'].get('statement_basis'), r['lineage'].get('currency')) for r in fields.values()}
            if len(tuples) != 1:
                denied.append({"field": "all", "reason": "LINEAGE_OR_COMPATIBLE_TUPLE_MISMATCH", "filing": filing.receipt_no})
                continue
            lineage = next(iter(fields.values()))['lineage']
            if not lineage.get('amount_period_end'):
                continue
            end = date.fromisoformat(lineage['amount_period_end'])
            row = FinancialSnapshot(ticker=plan['ticker'], id=len(snapshots)+1, created_at=created,
                period=end.isoformat(), fiscal_year=filing.business_year, period_type={'11013':'Q1','11012':'Q2','11014':'Q3','11011':'FY'}[filing.report_code],
                period_scope='annual' if filing.report_code == '11011' else 'single-quarter',
                is_cumulative=filing.report_code == '11011', currency=lineage.get('currency'), unit_scale=1,
                fs_div=lineage.get('fs_div'), source='OpenDART', provider='opendart',
                source_filing_id=filing.receipt_no, filing_date=filing.receipt_date, reported_date=filing.receipt_date,
                financial_period_end=end, financials_as_of=end,
                raw_financial_fields=json.dumps(lineages), **values)
            snapshots.append(row)
            witnesses[row.id] = {'fields': fields, 'filing': filing_data, 'role': role}
    snapshots.sort(key=lambda r:(r.financial_period_end or date.min,r.filing_date or date.min),reverse=True)
    freshness, _, validated = evaluate_financial_freshness_records([], snapshots, as_of=created.date())
    records, quality_bundles = [], []
    ordered = sorted([*validated, *foreign_rows], key=lambda r: (r.financial_period_end or date.min, r.filing_date or date.min), reverse=True)
    freshness, _, _ = evaluate_financial_freshness_records([],ordered,as_of=created.date())
    expected_periods = [f['reportDate'] for f in filings if f.get('role')=='current' and f.get('reportDate')]
    if plan['provider']=='opendart':
        for filing in filings:
            if filing['role']=='current':
                _,_,end=_bounds(year=filing['business_year'],report_code=filing['report_code'],
                    statement_type='IS',amount_role='current',amount_variant='standalone')
                if end:
                    expected_periods.append(end.isoformat())
    current_gap = bool(expected_periods and (not ordered or str(ordered[0].financial_period_end)<max(expected_periods)))
    if current_gap:
        denied.append({'field':'all','reason':'LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION'})
    stale = freshness.full_financial_freshness=='stale'
    if stale:
        denied.append({'field':'all','reason':'EXISTING_FINANCIAL_FRESHNESS_STALE'})
    # Only the latest selected formal period can authorize current comparison.
    for row in ordered:
        if current_gap or stale:
            continue
        if row.financial_period_end != ordered[0].financial_period_end:
            continue
        if row.provider == 'sec_companyfacts':
            peers = [r for r in ordered if r.provider == row.provider and r.source_filing_id == row.source_filing_id
                     and 330 <= (row.financial_period_end - r.financial_period_end).days <= 400]
            comparison = peers[0].model_dump(mode='json') if len(peers) == 1 else None
        else:
            comparison = None
        inputs = {'ticker': plan['ticker'], 'cutoff': plan['cutoff'][:10], 'formal': row.model_dump(mode='json'),
            'comparison': comparison, 'preliminary': None,
            'foreign_candidates': [r.model_dump(mode='json') for r in foreign_rows]}
        bundle = {'source_inputs': inputs, 'source_inputs_sha256': quality_digest(inputs),
            'source_generation_id': plan['run_id']}
        quality_bundles.append({**bundle, 'quality': source_quality(bundle)})
    for row in validated:
        witness = witnesses[row.id]
        for metric in METRICS:
            source = witness['fields'].get(metric)
            if not source:
                continue
            errors = list(field_errors(row, metric))
            if row.provider == 'opendart':
                owned_quality = build_reported_observation_quality(formal=row, preliminary=None,
                    ticker=plan['ticker'], cutoff=created.date())
                errors.extend(owned_quality['fields']['current.' + metric]['hard_denial_reasons'])
            if plan['provider'] == 'sec_edgar':
                scope = 'ANNUAL' if row.period_scope == 'annual' else 'SINGLE_QUARTER' if row.period_scope == 'single-quarter' else None
                lineage = {'source_document_id': source.get('source_document_id'), 'source_document_type': source.get('source_document_type'),
                    'filing_date': source.get('source_filing_date'), 'occurrence_id': source.get('source_row_identity'),
                    'semantic': str(source.get('taxonomy')) + ':' + str(source.get('concept')),
                    'period_start': source.get('period_start'), 'period_end': source.get('period_end'),
                    'period_role': scope, 'fiscal_year': row.fiscal_year, 'statement_basis': 'sec_companyfacts_entity_wide',
                    'fiscal_year_basis':'SOURCE_FILING_REPORTED_FY', 'source_fiscal_period_label':row.period_type,
                    'formal_state':'OFFICIAL_PROVISIONAL' if source.get('source_document_type','').startswith('6-K') else 'FORMAL',
                    'currency': source.get('currency'), 'unit': source.get('unit'), 'unit_scale': 1,
                    'source_reported_value': source.get('source_reported_value'), 'original_lineage': source}
                role = witness['filing']['role'] if source.get('period_end') == witness['filing'].get('reportDate') else 'comparative'
                raw_sha = witness['raw_sha']
            else:
                original = source['lineage']
                if not original.get('lineage_verified'):
                    errors.append('LINEAGE_UNRESOLVED')
                lineage = {'source_document_id': original.get('source_filing'), 'source_document_type': witness['filing']['report_code'],
                    'filing_date': row.filing_date.isoformat(), 'occurrence_id': original.get('source_row_identity'),
                    'semantic': original.get('account_id'), 'period_start': original.get('amount_period_start'),
                    'period_end': original.get('amount_period_end'), 'period_role': {'single_quarter':'SINGLE_QUARTER','full_year':'ANNUAL','year_to_date_cumulative':'CUMULATIVE_YTD'}.get(original.get('amount_period_type')),
                    'statement_basis': original.get('statement_basis'), 'currency': original.get('currency'),
                    'unit': original.get('currency'), 'unit_scale': 1, 'fiscal_year': row.fiscal_year,
                    'source_reported_value': original.get('amount'), 'original_lineage': original}
                role, raw_sha = witness['role'], source['raw_sha']
            records.append(field_record(plan, metric=metric, value=getattr(row, metric), lineage=lineage,
                quality=errors, raw_sha=raw_sha, role=role))
    comparisons = []
    for metric in METRICS:
        candidates = [r for r in records if r['metric'] == metric]
        if not candidates:
            continue
        latest_end = max(r['period_end'] or '' for r in candidates)
        latest = [r for r in candidates if r['period_end'] == latest_end]
        # Conflicting current observations are not resolved by largest value.
        if len({(r['value'], r['semantic'], r['period_start'], r['statement_basis'], r['currency']) for r in latest}) != 1:
            denied.append({'field': metric, 'reason': 'AMBIGUOUS_CURRENT_OCCURRENCE'})
            continue
        current = max(latest, key=lambda r: (r['filing_date'], r['source_document_id']))
        peers = [r for r in candidates if paired(current, r)]
        if not peers:
            denied.append({'field': metric, 'reason': 'PERIOD_NOT_COMPARABLE'})
            continue
        prior_end = max(r['period_end'] for r in peers)
        peers = [r for r in peers if r['period_end'] == prior_end]
        if len({r['value'] for r in peers}) != 1:
            denied.append({'field': metric, 'reason': 'AMBIGUOUS_PRIOR_OCCURRENCE'})
            continue
        prior = max(peers, key=lambda r: (r['filing_date'], r['source_document_id']))
        comparisons.append({'metric': metric, 'current_ref': current['normalized_hash'], 'prior_ref': prior['normalized_hash'],
            'direction': 'higher' if current['value'] > prior['value'] else 'lower' if current['value'] < prior['value'] else 'unchanged',
            'direction_eligible': True, 'scope': 'observed_metric_relation_not_investment_verdict'})
    return {'contract': CONTRACT, 'ticker': plan['ticker'], 'plan_sha256': digest(plan),
        'snapshots': [r.model_dump(mode='json') for r in validated], 'fields': records,
        'comparison_candidates': [{**c, 'direction_eligible':False,
            'reason':'REQUIRES_EXISTING_COMPARISON_OWNER'} for c in comparisons],
        'comparisons': [c for b in quality_bundles if b['quality']['status']=='PASS'
            for c in b['quality']['comparative_observations']],
        'denials': denied, 'foreign_occurrences': foreign,
        'quality_bundles': quality_bundles,
        'freshness': TypeAdapter(dict).dump_python(asdict(freshness),mode='json'), 'latest_selected_period_unavailable':current_gap,
        'context_eligible': any(r['context_eligible'] for r in records),
        'direction_eligible': any(b['quality']['status'] == 'PASS' for b in quality_bundles),
        'valuation_eligible': False, 'production_persistence': False}
