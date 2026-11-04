"""Offline occurrence/projection audit over bounded official response bytes.

Amounts use existing SEC/DART parsers and existing quality decisions. A direction
requires an independently eligible comparable pair, never only a current amount.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from dataclasses import asdict, replace
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
from app.services.sec_foreign_comparison_service import occurrence_errors
from app.services.sec_foreign_comparison_service import current_projection
from scripts.m12dr_financial_source_authority import source_quality
from app.services.financial_observation_quality_service import digest as quality_digest
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.bounded_financial_acquisition import (
    sec_selection, dart_selection, sec_base, exhibit_identities, exhibit_selection, AcquisitionDenied,
)
from app.services.sec_fpi_financial_purpose import classify_document, select_economic_period, candidate_inventory, FINANCIAL
from app.services.bounded_fpi_followup import verify_followup

METRICS = ("revenue", "operating_income", "net_income")
CONTRACT = "bounded-official-financial-projection-v1"
# Process-local producer provenance, rebuilt by original sealed-input replay.
# A public projection/hash cannot populate this registry.
_ORIGINAL_PROJECT_REPLAYS = {}
# Exact standard concept extension on the opt-in reported-field route only.
# Existing occurrence selection, lineage and quality owners remain unchanged.
REPORTED_FIELD_SPECS = {**FIELD_SPECS, 'revenue': replace(FIELD_SPECS['revenue'],
    account_ids=(*FIELD_SPECS['revenue'].account_ids, 'ifrs-full_insurancerevenue'))}


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
        same = cs < ce and ps < pe < ce and (ce - cs).days == (pe - ps).days and 330 <= (ce - pe).days <= 400
        if same:
            return True
        from app.services.issuer_fiscal_week_policy import annual_comparability
        def fiscal(row):
            return {**row, 'issuer': row['provider_issuer_id']}
        return bool(annual_comparability(fiscal(current), fiscal(prior), current.get('issuer_fiscal_policy')))
    except (ValueError, KeyError, TypeError):
        return False


def field_record(plan, *, metric, value, lineage, quality, raw_sha, role, allow_instant=False):
    value_ok = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    required = ("source_document_id", "source_document_type", "filing_date", "occurrence_id",
                "semantic", "period_start", "period_end", "period_role", "statement_basis", "currency", "unit", "unit_scale")
    errors = list(quality)
    if not value_ok or not all(lineage.get(k) for k in required):
        errors.append("LINEAGE_UNRESOLVED")
    try:
        start, end, filed = [date.fromisoformat(lineage[k]) for k in ("period_start", "period_end", "filing_date")]
        period_ok = start < end or (allow_instant and start == end and lineage.get('period_role') == 'point_in_time')
        if not period_ok or not end <= filed <= date.fromisoformat(plan["cutoff"][:10]):
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


def reported_context_fields(plan, acquisition, directory, receipts, *, expected_projection,
                            project_options=None, documentary_input=None, extended_sec_fields=False):
    """Opt-in absolute CF/BS occurrences through the original capture boundary.

    This does not add metrics to the comparative/Native owner. In particular,
    Without an explicit admitted supplement, DART interim CF remains denied.
    """
    from pathlib import Path
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('reported_context_plain_source_directory_required')
    for receipt in receipts:
        names = [receipt['logical_id'].split(':')[-1]+'.plan.json']
        if receipt.get('artifact'): names.append(receipt['artifact'])
        for name in names:
            path = directory/name
            if Path(name).name != name or path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
                raise ValueError('reported_context_external_or_aliased_source')
    actual = project(plan, acquisition, directory, receipts, **(project_options or {}))
    if actual != expected_projection:
        raise ValueError('original_financial_projection_drift')
    fields, denied = [], []
    current = [f for f in acquisition['selected_filings'] if f.get('role') == 'current']
    if len(current) != 1:
        return dict(fields=[], denied=[dict(metric='all', reason='UNIQUE_CURRENT_FILING_REQUIRED')])
    filing = current[0]
    if plan['provider'] == 'sec_edgar':
        # Foreign statements keep their separate, existing basis/period owner.
        if filing.get('form') not in ('10-Q', '10-K') or not acquisition.get('companyfacts_artifact'):
            return dict(fields=[], denied=[dict(metric='all', reason='FOREIGN_CONTEXT_FIELD_SCOPE_NOT_QUALIFIED')])
        raw = _raw(directory, acquisition['companyfacts_artifact'], receipts)
        payload = json.loads(raw)
        if str(payload.get('cik', '')).lstrip('0') != plan['issuer'].lstrip('0'):
            raise ValueError('issuer_mismatch')
        concepts = {
            'NetCashProvidedByUsedInOperatingActivities': ('operating_cashflow', 'duration'),
            'NetIncomeLoss': ('owners_parent_net_income', 'duration'),
            'Assets': ('assets', 'instant'), 'Liabilities': ('liabilities', 'instant'),
            'StockholdersEquity': ('stockholders_equity', 'instant'),
            'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities': ('debt_including_current', 'instant'),
        }
        if extended_sec_fields:
            concepts.update({
                'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest': ('equity', 'instant'),
                'MinorityInterest': ('noncontrolling_interest', 'instant'),
                'CashAndCashEquivalentsAtCarryingValue': ('cash_and_cash_equivalents', 'instant'),
            })
        for concept, (metric, kind) in concepts.items():
            groups = {}
            units = payload.get('facts', {}).get('us-gaap', {}).get(concept, {}).get('units', {})
            for unit, items in units.items():
                for ordinal, item in enumerate(items):
                    if item.get('accn') != filing['accessionNumber'] or item.get('end') != filing['reportDate']:
                        continue
                    key = (item.get('start'), item.get('end'), unit)
                    groups.setdefault(key, []).append((ordinal, item))
            if not groups:
                denied.append(dict(metric=metric, reason='EXACT_CURRENT_OCCURRENCE_ABSENT'))
            for (start, end, unit), candidates in groups.items():
                errors = []
                if len(candidates) != 1:
                    denied.append(dict(metric=metric, reason='AMBIGUOUS_EXACT_OCCURRENCE', period=[start, end]))
                    continue
                ordinal, item = candidates[0]
                if (item.get('form') != filing['form'] or item.get('filed') != filing['filingDate']
                        or not isinstance(item.get('fy'), int) or isinstance(item.get('fy'), bool)
                        or item.get('fp') not in ('Q1', 'Q2', 'Q3', 'FY')):
                    errors.append('FILING_OR_FISCAL_METADATA_MISMATCH')
                if unit != 'USD':
                    errors.append('UNSUPPORTED_CONTEXT_CURRENCY')
                if (kind == 'instant' and start is not None) or (kind == 'duration' and not start):
                    errors.append('DURATION_INSTANT_MISMATCH')
                role = 'point_in_time' if kind == 'instant' else 'reported_duration'
                if kind == 'duration' and item.get('fp') in ('Q1', 'Q2', 'Q3', 'FY') and start == f"{item.get('fy')}-01-01":
                    expected_end = {'Q1': '03-31', 'Q2': '06-30', 'Q3': '09-30', 'FY': '12-31'}[item['fp']]
                    if end == f"{item['fy']}-{expected_end}":
                        role = 'full_year' if item['fp'] == 'FY' else 'year_to_date_cumulative'
                elif kind == 'duration':
                    try:
                        if (date.fromisoformat(end)-date.fromisoformat(start)).days in range(70, 101):
                            role = 'reported_quarter_duration'
                    except (ValueError, TypeError):
                        errors.append('PERIOD_UNRESOLVED')
                lineage = dict(source_document_id=item.get('accn'), source_document_type=item.get('form'),
                    filing_date=item.get('filed'), occurrence_id=f'facts.us-gaap.{concept}.units.{unit}[{ordinal}]',
                    semantic='us-gaap:'+concept, period_start=start if kind == 'duration' else end,
                    period_end=end, period_role=role, period_kind=kind,
                    statement_basis='sec_companyfacts_entity_wide', currency=unit, unit=unit, unit_scale=1,
                    exact_source_occurrence=deepcopy(item), fiscal_year=item.get('fy'), fiscal_period=item.get('fp'),
                    consolidation_explicitly_proven=False, accounting_standard='US-GAAP')
                fields.append(field_record(plan, metric=metric, value=item.get('val'), lineage=lineage,
                    quality=errors, raw_sha=sha256_bytes(raw), role='current', allow_instant=True))
    elif plan['provider'] == 'opendart':
        from app.services.opendart_financial_recovery_service import FieldSpec, select_basis_occurrence
        docs = [d for d in acquisition['documents'] if d['filing'].get('receipt_no') == filing['receipt_no']
                and d['filing'].get('basis') == 'CFS']
        if len(docs) != 1:
            return dict(fields=[], denied=[dict(metric='all', reason='EXACT_CONSOLIDATED_DOCUMENT_REQUIRED')])
        raw = _raw(directory, docs[0]['artifact'], receipts)
        payload = json.loads(raw); rows = payload.get('list', [])
        if payload.get('status') != '000' or any(
                str(r.get('rcept_no')) != filing['receipt_no'] or str(r.get('corp_code')) != plan['issuer']
                or str(r.get('bsns_year')) != str(filing['business_year']) or r.get('reprt_code') != filing['report_code']
                or r.get('fs_div') not in (None, '', 'CFS') for r in rows):
            raise ValueError('STATEMENT_RESPONSE_FILING_IDENTITY_MISMATCH')
        specs = {k: FIELD_SPECS[k] for k in ('assets', 'equity', 'operating_cash_flow')}
        specs['liabilities'] = FieldSpec('liabilities', ('ifrs-full_liabilities',), (), ('BS',))
        recovered = None
        if documentary_input is not None:
            from app.services.opendart_financial_recovery_service import promote_recovered_fields
            original_filing = Filing(**{**{k:filing[k] for k in Filing.__dataclass_fields__},
                'receipt_date':date.fromisoformat(filing['receipt_date'])})
            recovered = promote_recovered_fields(original_filing, {'CFS':rows},
                documentary_input=documentary_input, documentary_context=dict(security=plan['security'],
                    original_raw=raw, source_generation=plan['run_id'], source_cutoff=plan['cutoff']))
        for metric, spec in specs.items():
            # Exact taxonomy only; no alias guess or separate-statement fallback.
            spec = replace(spec, account_aliases=())
            selection = select_basis_occurrence(rows, spec, basis='CFS')
            documentary_lineage = (recovered['fields'][metric]['lineage']
                if recovered and metric == 'operating_cash_flow' else None)
            if selection.status != 'selected' and documentary_lineage is None:
                reason = recovered['fields'][metric]['reason'] if recovered and metric == 'operating_cash_flow' else selection.reason
                denied.append(dict(metric=metric, reason=reason, status=selection.status,
                    raw_artifact_sha256=sha256_bytes(raw), candidates=list(selection.candidates)))
                continue
            row = selection.row or selection.candidates[0]
            lineage = documentary_lineage or opendart_field_lineage(row, logical_field=metric, report_code=filing['report_code'],
                source_column=spec.source_column, selected=True, requested_fs_div='CFS')
            errors = [] if lineage['lineage_verified'] else [lineage['denial_reason']]
            if row.get('account_detail') not in (None, '-'): errors.append('DIMENSIONAL_CONTEXT_NOT_TOTAL')
            witness = dict(source_document_id=filing['receipt_no'], source_document_type=filing['report_code'],
                filing_date=filing['receipt_date'], occurrence_id=lineage['source_row_identity'],
                semantic=row['account_id'], period_start=lineage['amount_period_start'],
                period_end=lineage['amount_period_end'], period_role=lineage['amount_period_type'],
                period_kind='instant' if row['sj_div'] == 'BS' else 'duration',
                statement_basis=lineage['statement_basis'], currency=lineage['currency'], unit=lineage['currency'], unit_scale=1,
                exact_source_occurrence=deepcopy(row), original_lineage=lineage,
                fiscal_year=filing['business_year'], fiscal_period=filing['report_code'],
                consolidation_explicitly_proven=True, accounting_standard='IFRS')
            if documentary_lineage:
                witness['documentary_reconciliation'] = deepcopy(lineage['documentary_reconciliation'])
            fields.append(field_record(plan, metric=metric, value=lineage['amount'], lineage=witness,
                quality=errors, raw_sha=sha256_bytes(raw), role='current', allow_instant=True))
    else:
        denied.append(dict(metric='all', reason='UNSUPPORTED_ORIGINAL_PROVIDER'))
    result = dict(fields=fields, denied=denied, original_projection_sha256=digest(actual),
                  security=deepcopy(plan['security']), source_generation=plan['run_id'], source_cutoff=plan['cutoff'])
    frozen = deepcopy((plan, acquisition, receipts, expected_projection, project_options))
    def replay_context():
        p, a, r, expected, options = deepcopy(frozen)
        return reported_context_fields(p, a, directory, r, expected_projection=expected, project_options=options,
            documentary_input=documentary_input, extended_sec_fields=extended_sec_fields)
    _ORIGINAL_PROJECT_REPLAYS[('reported-context', digest(result))] = replay_context
    return result


def replay_original_context(projection_sha256):
    replay = _ORIGINAL_PROJECT_REPLAYS.get(('reported-context', projection_sha256))
    if replay is None:
        raise ValueError('reported_context_original_replay_required')
    result = replay()
    if digest(result) != projection_sha256:
        raise ValueError('reported_context_original_replay_changed')
    return result


def comparison_applicability(projection):
    """Grade comparison availability, not financial health, from replayed fields.

    Only an absent prior occurrence is currently qualified here. Incompatible
    or erroneous prior data stays blocked until its own absence owner exists.
    """
    projection = {k: v for k, v in projection.items()
                  if k not in {'comparison_applicability', 'statement_scope_audit'}}
    result = dict(contract='reported-comparison-applicability-v1',
        state='QUALITY_EXPECTED_OWNER_OUTPUT_MISSING', current_field_hashes=[],
        reasons=[], direction_eligible=False)
    if projection.get('purpose_reconciliation') is not None:
        result['reasons'] = ['AUXILIARY_PURPOSE_CURRENT_GENERATION_USE_NOT_AUTHORIZED']
        result['projection_sha256'] = digest(projection)
        result['receipt_sha256'] = digest(result)
        return result
    if projection['comparisons']:
        result.update(state='QUALITY_RECORD_PRESENT')
    else:
        from app.services.sec_financial_source_completeness import UNAVAILABLE
        complete = projection.get('source_completeness') or {}
        if (complete.get('state') == UNAVAILABLE and complete.get('bounded_plan_complete') is True
                and not complete.get('reasons') and not projection['fields'] and not projection['quality_bundles']
                and complete.get('receipt_sha256') == digest({k: v for k, v in complete.items() if k != 'receipt_sha256'})
                and complete.get('documents_sha256') == digest(projection['fpi_purpose']['documents'])):
            result.update(state='QUALITY_NOT_APPLICABLE_NO_DIRECTIONAL_COMPARISON',
                reasons=[UNAVAILABLE], source_completeness_sha256=complete['receipt_sha256'])
            result['projection_sha256'] = digest(projection)
            result['receipt_sha256'] = digest(result)
            return result
        fields = projection['fields']
        current = [r for r in fields if r['current_prior_role'] == 'current']
        allowed = {'PERIOD_NOT_COMPARABLE', 'FIELD_ABSENT', 'account_not_found'}
        bad = [r for r in projection['denials'] if r['reason'] not in allowed]
        eligible = (current and len(current) == len(fields)
            and all(r['context_eligible'] and not r['quality_errors'] for r in current)
            and all(r['normalized_hash'] == digest({k: v for k, v in r.items()
                                                   if k != 'normalized_hash'}) for r in current)
            and len({r['metric'] for r in current}) == len(current)
            and not projection['comparison_candidates'] and not bad
            and not projection['latest_selected_period_unavailable']
            and projection['freshness']['full_financial_freshness'] == 'current'
            and projection['quality_bundles'])
        # A replayed comparison owner must explicitly diagnose missing prior
        # input. An empty comparison list alone never proves non-applicability.
        for bundle in projection['quality_bundles']:
            quality = source_quality(bundle)
            eligible = eligible and quality == bundle['quality'] and not quality['comparative_observations']
            for field in current:
                q = quality['fields'].get('current.' + field['metric'], {})
                prior = quality['fields'].get('comparison.' + field['metric'], {})
                eligible = (eligible and not q.get('hard_denial_reasons') and q.get('prose_eligible')
                    and 'missing_comparison' in prior.get('hard_denial_reasons', [])
                    and set(prior['hard_denial_reasons']) <= {'missing_comparison', 'exact_sec_occurrence_missing'})
        if eligible:
            result.update(state='QUALITY_NOT_APPLICABLE_NO_DIRECTIONAL_COMPARISON',
                current_field_hashes=sorted(r['normalized_hash'] for r in current),
                reasons=['PRIOR_OCCURRENCE_ABSENT_WITHIN_BOUNDED_OWNER'])
        else:
            result['reasons'] = ['NO_PROVEN_CONTEXT_ONLY_COMPARISON_ABSENCE']
    result['projection_sha256'] = digest(projection)
    result['receipt_sha256'] = digest(result)
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
    if plan.get('financial_owner_policy') and '6-K' in plan['forms']:
        inventory = candidate_inventory(json.loads(_raw(directory, discovery[0]['artifact'], receipts)), plan)
        if acquisition.get('current_candidate_plan') != inventory['current_financial_plan']:
            raise ValueError('current_fpi_candidate_plan_replay_mismatch')
    for doc in acquisition['documents']:
        receipt=next((r for r in receipts if r.get('artifact')==doc['artifact']),None)
        if not receipt or receipt.get('filing')!=doc['filing'] or receipt['stage'] not in {'document','statement'}:
            raise ValueError('document_receipt_filing_mismatch')
        frozen=json.loads((directory/(receipt['logical_id'].split(':')[-1]+'.plan.json')).read_bytes())
        if doc.get('url') and frozen['url']!=doc['url']:
            raise ValueError('document_receipt_url_mismatch')
        _raw(directory,doc['artifact'],receipts)


def reconcile_fragment_denials(plan, acquisition, directory, receipts):
    original = acquisition.get('denials', [])
    proven, diagnostics, remaining = 0, [], []
    for filing in acquisition['selected_filings']:
        primary = sec_base(plan, filing) + filing['primaryDocument']
        docs = [d for d in acquisition['documents'] if d['filing'] == filing]
        captured = next((d for d in docs if d['url'] == primary), None)
        indexes = [r for r in receipts if r['stage'] == 'index' and r.get('filing') == filing and not r['failure_class']]
        if not captured or len(indexes) != 1:
            continue
        try:
            index = json.loads(_raw(directory, indexes[0]['artifact'], receipts))
            html = _raw(directory, captured['artifact'], receipts).decode('utf-8', errors='replace')
            aliases = exhibit_identities(index, html, plan, filing)
            fragments = [r for r in aliases if '#' in r['original_url']]
            closed = bool(fragments) and all(r['already_captured_primary'] for r in fragments)
            proven += int(closed)
            try:
                exhibits = exhibit_selection(index, html, plan, filing)
                if set(exhibits) - {d['url'] for d in docs}:
                    remaining.append('SEC_LINKED_EXHIBIT_NOT_CAPTURED')
            except AcquisitionDenied as exc:
                remaining.append(str(exc))
            diagnostics.append({'filing': filing, 'aliases': aliases, 'closed_same_document_only': closed,
                'primary_sha256': sha256_bytes(_raw(directory, captured['artifact'], receipts)), 'new_calls': 0})
        except (AcquisitionDenied, ValueError):
            diagnostics.append({'filing': filing, 'closed_same_document_only': False})
    expected = original.count('SEC_DOCUMENT_SOURCE_SCOPE_DENIED')
    effective = ([d for d in original if d != 'SEC_DOCUMENT_SOURCE_SCOPE_DENIED'] + sorted(set(remaining))
                 if expected and proven == expected else list(original))
    return {'original_denials': original, 'effective_denials': effective,
        'resolved_count': expected if expected and proven == expected else 0, 'diagnostics': diagnostics}


def project(plan, acquisition, directory, receipts, *, followup_directory=None, phase2=None, field_semantics=False, coverage_window=None, statement_scope_audit=False, statement_basis_policy=None, basis_execution_generation=None, purpose_reconciliation=None, current_purpose_intake=None, quarter_period_policy=None):
    plan, acquisition, receipts = deepcopy((plan, acquisition, receipts))
    options = deepcopy(dict(followup_directory=followup_directory, phase2=phase2,
        field_semantics=field_semantics, coverage_window=coverage_window,
        statement_scope_audit=statement_scope_audit, statement_basis_policy=statement_basis_policy,
        basis_execution_generation=basis_execution_generation, quarter_period_policy=quarter_period_policy))
    # Live capabilities remain references; neither public JSON nor deepcopy
    # may reconstruct their issuing owner.
    capabilities = dict(purpose_reconciliation=purpose_reconciliation,
                        current_purpose_intake=current_purpose_intake)

    def replay():
        return _project(deepcopy(plan), deepcopy(acquisition), directory, deepcopy(receipts),
                        **deepcopy(options), **capabilities)

    result = replay()
    key = (digest(plan), digest(acquisition), digest(result))
    _ORIGINAL_PROJECT_REPLAYS[key] = replay
    return result


def replay_original_projection(*, plan, acquisition, projection):
    """Require original producer issuance and recheck raw bytes/comparisons.

    Restarts require the caller to replay the sealed inputs through ``project``;
    loading a stored projection or selected envelope is not an authority grant.
    """
    key = (digest(plan), digest(acquisition), digest(projection))
    replay = _ORIGINAL_PROJECT_REPLAYS.get(key)
    if replay is None:
        raise ValueError('selected_financial_original_project_required')
    rebuilt = replay()
    if rebuilt != projection:
        raise ValueError('selected_financial_original_project_changed')
    from app.services.bounded_financial_stock_owner import reported_comparisons
    facts, _ = reported_comparisons(plan, rebuilt)
    return facts


def _project(plan, acquisition, directory, receipts, *, followup_directory=None, phase2=None, field_semantics=False, coverage_window=None, statement_scope_audit=False, statement_basis_policy=None, basis_execution_generation=None, purpose_reconciliation=None, current_purpose_intake=None, quarter_period_policy=None):
    if plan.get('financial_owner_policy') not in {None, 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'}:
        raise ValueError('unknown_exact_financial_owner_policy')
    if acquisition["plan_sha256"] != digest(plan):
        raise ValueError("financial_plan_binding_mismatch")
    verify_capture(plan,acquisition,directory,receipts)
    if quarter_period_policy is not None:
        from app.services.sec_reported_quarter_period import POLICY as QUARTER_POLICY
        if (quarter_period_policy != QUARTER_POLICY or not field_semantics
                or plan.get('financial_owner_policy') != 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'
                or plan['provider'] != 'sec_edgar' or '6-K' not in plan['forms']):
            raise ValueError('source_bound_quarter_route_not_authorized')
    quarter_sources = {}
    purpose_review = None
    current_review = None
    if purpose_reconciliation is not None and current_purpose_intake is not None:
        raise ValueError('purpose_diagnostic_and_current_routes_exclusive')
    if current_purpose_intake is not None:
        from app.services.current_financial_purpose_intake import resolve
        if not field_semantics or plan.get('financial_owner_policy') != 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1' or '6-K' not in plan['forms']:
            raise ValueError('current_purpose_wrong_financial_route')
        current_review = resolve(current_purpose_intake, plan=plan, acquisition=acquisition, receipts=receipts)
    if purpose_reconciliation is not None:
        from app.services.sec_fpi_purpose_reconciliation import resolve
        if not field_semantics or plan.get('financial_owner_policy') != 'EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1' or '6-K' not in plan['forms']:
            raise ValueError('purpose_reconciliation_wrong_financial_route')
        purpose_review = resolve(purpose_reconciliation, plan=plan, acquisition=acquisition, receipts=receipts)
    snapshots, witnesses, denied = [], {}, []
    scope_audits, basis_receipts = [], []
    if statement_basis_policy is not None:
        from app.services.sec_fpi_statement_basis_owner import POLICY
        if (statement_basis_policy != POLICY or not basis_execution_generation
                or plan['provider'] != 'sec_edgar' or not field_semantics
                or not plan.get('financial_owner_policy') or '6-K' not in plan['forms']):
            raise ValueError('sec_fpi_basis_route_not_authorized')
    elif basis_execution_generation is not None:
        raise ValueError('sec_fpi_basis_execution_without_policy')
    filings = list(acquisition["selected_filings"])
    created = datetime.fromisoformat(plan["cutoff"])
    followup, inventory, uncaptured, second, window = None, None, [], None, None
    exact_owner = bool(plan.get('financial_owner_policy'))
    fiscal_policies = {}
    if plan["provider"] == "sec_edgar":
        source_documents = [{**d, 'raw': _raw(directory, d['artifact'], receipts)} for d in acquisition['documents']]
        if exact_owner:
            from app.services.issuer_fiscal_week_policy import extract_policy
            for doc in source_documents:
                if doc['filing']['form'].split('/')[0] == '10-K' and doc['url'].endswith('/' + doc['filing']['primaryDocument']):
                    fiscal_policies[doc['filing']['accessionNumber']] = extract_policy(doc['raw'], issuer=plan['issuer'], filing=doc['filing'])
        if '6-K' in plan['forms']:
            discovery = next(r for r in receipts if r['stage'] == 'discovery' and not r['failure_class'])
            discovery_raw = _raw(directory, discovery['artifact'], receipts)
            inventory = candidate_inventory(json.loads(discovery_raw), plan)
            if followup_directory is not None:
                followup = verify_followup(plan, discovery_raw, acquisition['documents'], followup_directory)
                source_documents.extend(followup['documents'])
                selected = {f['accessionNumber']: f for f in filings}
                selected.update({f['accessionNumber']: f for f in followup['plan']['candidates']})
                filings = list(selected.values())
            if phase2 is not None:
                from app.services.fpi_discovered_exhibit_phase2 import verify_phase2
                if followup is None:
                    raise ValueError('phase2_requires_verified_phase1')
                second = verify_phase2(plan, phase2['source'], phase2['directory'])
                if second['plan']['phase1_plan_sha256'] != digest(followup['plan']) or second['plan']['phase1_receipts_sha256'] != followup['receipt_sha256']:
                    raise ValueError('phase2_consumed_phase1_mismatch')
                source_documents.extend(second['documents'])
            if coverage_window is not None:
                from app.services.fpi_coverage_window import verify_window
                first_urls = {sec_base(plan, f) + f['primaryDocument'] for f in followup['plan']['candidates']}
                followup['captured_window_documents'] = [d for d in source_documents if d['url'] in first_urls
                    and d['url'] not in {r['url'] for r in followup['documents']}]
                window = verify_window(plan, discovery_raw, acquisition['documents'], followup, second, **coverage_window)
                source_documents.extend(window['documents'])
                filings.extend(window['plan']['candidates'])
            captured = {d['url'] for d in source_documents}
            uncaptured = [f for f in inventory['inspection_window']
                          if sec_base(plan, f) + f['primaryDocument'] not in captured]
            if plan.get('fpi_candidate_contract'):
                # Excluding a source from the fetch budget does not prove that
                # it is nonfinancial or irrelevant to a newer-period claim.
                uncaptured.extend(r['filing'] for r in inventory['current_financial_plan']['outside_bound']
                                  if sec_base(plan, r['filing']) + r['filing']['primaryDocument'] not in captured)
            if window:
                uncaptured.extend(window['uncaptured'])
        artifact = acquisition.get("companyfacts_artifact")
        if artifact and not (exact_owner and '6-K' in plan['forms']):
            raw = _raw(directory, artifact, receipts)
            payload = json.loads(raw)
            if str(payload.get("cik", "")).lstrip('0') != plan["issuer"].lstrip('0'):
                raise ValueError("issuer_mismatch")
            selected = {f["accessionNumber"]: f for f in filings}
            document_ids = {d["filing"]["accessionNumber"] for d in source_documents}
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
        foreign, foreign_rows, purpose_documents = [], [], []
        for document in source_documents:
            filing = document["filing"]
            if filing["form"].split('/')[0] not in {"6-K", "20-F"}:
                continue
            raw = document['raw']
            if quarter_period_policy:
                from app.services.sec_reported_quarter_period import source_record
                quarter_sources.update(source_record(raw,issuer_cik=plan['issuer'],accession=filing['accessionNumber'],
                    document_type=filing['form'],filing_date=filing['filingDate'],source_url=document['url']))
            context_documents = []
            if exact_owner and document['url'] != sec_base(plan, filing) + filing['primaryDocument']:
                context_documents = [d for d in source_documents if d['filing'] == filing
                    and d['url'] == sec_base(plan, filing) + filing['primaryDocument']]
            purpose = classify_document(raw, url=document['url'], filing=filing, plan=plan,
                                        context_documents=context_documents,quarter_period_policy=quarter_period_policy)
            purpose_documents.append(purpose)
            if statement_scope_audit:
                from app.services.sec_foreign_statement_scope import inspect_scopes
                scope_audits.append(inspect_scopes(raw, issuer_cik=plan['issuer'],
                    filing=filing, source_url=document['url'], cutoff=plan['cutoff'],quarter_period_policy=quarter_period_policy))
            occurrences = purpose['occurrences']
            for occurrence in occurrences:
                foreign.append({"occurrence": occurrence,
                    "errors": occurrence_errors(occurrence, date.fromisoformat(plan["cutoff"][:10]),source_documents=quarter_sources),
                    "packet_consumption": "SEPARATE_FOREIGN_OWNER_NOT_COMPANYFACTS"})
            if statement_basis_policy is not None:
                from app.services.sec_fpi_statement_basis_owner import select_basis, selected_occurrences
                basis=select_basis(raw,plan=plan,filing=filing,source_url=document['url'],
                    policy=statement_basis_policy,execution_generation=basis_execution_generation,quarter_period_policy=quarter_period_policy)
                basis_receipts.append(basis)
                # Keep all original observations in the audit graph; only exact
                # policy-qualified scope cells may enter the accepting projector.
                occurrences=selected_occurrences(basis)
            role = 'single-quarter'
            current = current_projection(occurrences, inline_currency_pair=exact_owner,source_documents=quarter_sources)
            if field_semantics and current is None:
                role = 'half-year'
                current = current_projection(occurrences, required_role=role, inline_currency_pair=exact_owner,source_documents=quarter_sources)
            if exact_owner:
                choices = [(r, current_projection(occurrences, required_role=r, inline_currency_pair=True,source_documents=quarter_sources))
                           for r in ('single-quarter', 'half-year', 'annual')]
                choices = [(r, value) for r, value in choices if value]
                if choices:
                    role, current = max(choices, key=lambda pair: (pair[1]['period_end'],
                        {'single-quarter': 3, 'half-year': 2, 'annual': 1}[pair[0]]))
            if current and purpose['purpose'] in FINANCIAL:
                end = date.fromisoformat(current['period_end'])
                foreign_rows.append(FinancialSnapshot(ticker=plan['ticker'], period=end.isoformat(),
                    financial_period_end=end, financials_as_of=end, filing_date=date.fromisoformat(filing['filingDate']),
                    source_filing_id=filing['accessionNumber'], source=document['url'], provider='sec_foreign_filing',
                    currency=current['currency'], period_scope=role, unit_scale=1, created_at=created,
                    raw_financial_fields=json.dumps([{'field':'foreign_business_occurrences','occurrences':occurrences}]),
                    **{k: current.get(k) for k in ('revenue','operating_income')}))
                if role in {'half-year', 'annual'}:
                    foreign_rows[-1].is_cumulative = True
                    foreign_rows[-1].period_type = role
        if field_semantics:
            from app.services.sec_fpi_financial_purpose import bind_nonfinancial_embedded_assets
            bind_nonfinancial_embedded_assets(purpose_documents,
                [d for d in source_documents if d['filing']['form'].split('/')[0] in {'6-K', '20-F'}], plan)
        if exact_owner and '6-K' in plan['forms']:
            from app.services.fpi_filing_document_graph import build_graph, bind_graph, document_slot_plan, terminal_slots, frozen_slot_accounting
            indexes, slot_plans = {}, []
            for filing in filings:
                matches = [r for r in receipts if r['stage']=='index' and r.get('filing')==filing and not r['failure_class']]
                if len(matches) != 1:
                    continue
                raw_index = _raw(directory, matches[0]['artifact'], receipts)
                indexes[filing['accessionNumber']] = dict(payload=json.loads(raw_index), raw_sha256=sha256_bytes(raw_index))
                primary = next((d for d in source_documents if d['url']==sec_base(plan,filing)+filing['primaryDocument']), None)
                if primary:
                    slot_plans.append(document_slot_plan(json.loads(raw_index), primary['raw'].decode('utf-8',errors='replace'), plan, filing))
            if acquisition.get('document_slot_plans') is not None and acquisition['document_slot_plans'] != slot_plans:
                raise ValueError('fpi_document_slot_plan_replay_mismatch')
            document_graph = build_graph(documents=purpose_documents, source_documents=source_documents, indexes=indexes, plan=plan)
            bind_graph(purpose_documents, document_graph)
            slot_accounting = [terminal_slots(s, acquisition['documents'], receipts) for s in slot_plans]
            if acquisition.get('document_slot_accounting') is not None and acquisition['document_slot_accounting'] != slot_accounting:
                raise ValueError('fpi_document_slot_accounting_replay_mismatch')
            frozen_slots = frozen_slot_accounting(plan, filings, slot_plans, receipts)
            if acquisition.get('frozen_slot_accounting') is not None and acquisition['frozen_slot_accounting'] != frozen_slots:
                raise ValueError('fpi_frozen_slot_accounting_replay_mismatch')
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
                selection = select_field_occurrence(rows_by_basis, REPORTED_FIELD_SPECS[metric])
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
    foreign_purpose = plan['provider'] == 'sec_edgar' and '6-K' in plan['forms']
    purpose_selection = None
    if foreign_purpose:
        if field_semantics:
            from app.services.sec_fpi_field_selection import select_fields
            ordered, purpose_selection = select_fields(purpose_documents, foreign_rows, ticker=plan['ticker'], cutoff=plan['cutoff'],
                uncaptured=uncaptured, allow_inline_annual=exact_owner, purpose_reconciliation=purpose_reconciliation,
                current_purpose_intake=current_purpose_intake,source_documents=quarter_sources)
        else:
            purpose_selection = select_economic_period(purpose_documents, uncaptured=uncaptured)
        if purpose_selection['status'] != 'PASS' and inventory['exhaustion_reason']:
            purpose_selection['denial_reasons'].append(inventory['exhaustion_reason'])
        expected_periods = [purpose_selection['period_end']] if purpose_selection['period_end'] else []
        denied.extend({'field': 'all', 'reason': reason} for reason in purpose_selection['denial_reasons'])
    current_gap = bool(expected_periods and (not ordered or max(str(r.financial_period_end) for r in ordered)<max(expected_periods)))
    if purpose_selection and purpose_selection['status'] != 'PASS':
        current_gap = True
    if current_gap:
        denied.append({'field':'all','reason':'LATEST_SELECTED_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION'})
    if exact_owner and ordered:
        freshness, _, _ = evaluate_financial_freshness_records([], ordered, as_of=created.date())
    stale = freshness.full_financial_freshness=='stale'
    if stale:
        denied.append({'field':'all','reason':'EXISTING_FINANCIAL_FRESHNESS_STALE'})
    # Only the latest selected formal period can authorize current comparison.
    for row in ordered:
        if current_gap or stale:
            continue
        if not (field_semantics and foreign_purpose) and row.financial_period_end != ordered[0].financial_period_end:
            continue
        if purpose_selection and row.source_filing_id not in purpose_selection['source_accessions']:
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
        if exact_owner:
            inputs.update(exact_annual_owner=True, issuer_fiscal_policy=fiscal_policies.get(row.source_filing_id))
        if field_semantics and foreign_purpose:
            from app.services.sec_fpi_field_selection import POLICY
            inputs['foreign_period_policy'] = POLICY
            derived_hashes = {o['source_payload_sha256'] for r in foreign_rows
                for record in json.loads(r.raw_financial_fields) for o in record.get('occurrences', [])
                if o.get('period_source_proof')}
            if derived_hashes:
                inputs['foreign_source_documents'] = {h: quarter_sources[h] for h in sorted(derived_hashes)}
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
                if exact_owner and row.source_filing_id in fiscal_policies:
                    lineage['issuer_fiscal_policy'] = fiscal_policies[row.source_filing_id]
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
    result = {'contract': CONTRACT, 'ticker': plan['ticker'], 'plan_sha256': digest(plan),
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
    if foreign_purpose:
        result['fpi_purpose'] = {'documents': purpose_documents, 'selection': purpose_selection,
            'uncaptured_window': uncaptured, 'candidate_inventory': inventory}
        result['acquisition_denial_reconciliation'] = reconcile_fragment_denials(plan, acquisition, directory, receipts)
        if field_semantics:
            from app.services.sec_fpi_field_selection import reconcile_historical_denials
            result['acquisition_denial_reconciliation'] = reconcile_historical_denials(
                result['acquisition_denial_reconciliation'], purpose_documents, purpose_selection)
        if followup:
            result['fpi_followup'] = {k: v for k, v in followup.items() if k not in {'documents', 'captured_window_documents'}}
        if second:
            result['fpi_phase2'] = {k: v for k, v in second.items() if k != 'documents'}
            phase2_denials = sorted({r['reason'] for r in second['denials']} | {
                r['reason'] for r in second['plan']['excluded'] if r['reason'] == 'FPI_PHASE2_EXHIBIT_BOUND_EXHAUSTED'})
            if second['unattempted']:
                phase2_denials.append('FPI_PHASE2_PLANNED_REQUESTS_UNATTEMPTED')
            result['acquisition_denial_reconciliation']['effective_denials'] = sorted(set(
                result['acquisition_denial_reconciliation']['effective_denials'] + phase2_denials))
            if not second['plan']['exact_requests'] and purpose_selection['status'] != 'PASS':
                result['denials'].append({'field': 'all', 'reason': 'NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_PHASE1_AND_NO_PHASE2_ELIGIBLE_EXHIBIT'})
        if window:
            result['fpi_coverage_window'] = {k: v for k, v in window.items() if k != 'documents'}
            if purpose_selection['status'] != 'PASS' and window['final_coverage_exhausted']:
                result['denials'].extend({'field': 'all', 'reason': r} for r in (
                    'NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_TWO_BOUNDED_WINDOWS', 'FPI_FINANCIAL_PURPOSE_COVERAGE_EXHAUSTED_FINAL'))
            if window.get('phase2'):
                result['acquisition_denial_reconciliation']['effective_denials'].extend(
                    r['reason'] for r in window['phase2']['denials'])
                if window['phase2']['unattempted']:
                    result['acquisition_denial_reconciliation']['effective_denials'].append('FPI_PHASE2_PLANNED_REQUESTS_UNATTEMPTED')
        if exact_owner:
            from app.services.sec_financial_source_completeness import completeness, field_completeness
            result['fpi_document_graph'] = document_graph
            result['fpi_document_slot_plans'] = slot_plans
            result['fpi_document_slot_accounting'] = slot_accounting
            result['fpi_frozen_slot_accounting'] = frozen_slots
            result['source_completeness'] = completeness(plan=plan, acquisition=acquisition,
                inventory=inventory, documents=purpose_documents, uncaptured=uncaptured,
                acquisition_denials=result['acquisition_denial_reconciliation']['effective_denials'])
            result['financial_field_completeness'] = field_completeness(purpose_selection, purpose_documents,
                result['source_completeness'])
    if current_review is not None:
        result['current_purpose_intake'] = current_review
        result['source_completeness']['current_purpose_applicability_sha256'] = current_review['receipt_sha256']
        result['source_completeness']['receipt_sha256'] = digest({k: v for k, v in result['source_completeness'].items() if k != 'receipt_sha256'})
        result['financial_field_completeness'] = field_completeness(purpose_selection, purpose_documents, result['source_completeness'])
    if purpose_review is not None:
        result['purpose_reconciliation'] = purpose_review
        result['direction_eligible'] = False
        result['source_completeness']['auxiliary_purpose_reconciliation_sha256'] = purpose_review['receipt_sha256']
        result['source_completeness']['current_generation_eligible'] = False
        result['source_completeness']['receipt_sha256'] = digest({k: v for k, v in result['source_completeness'].items() if k != 'receipt_sha256'})
        result['financial_field_completeness'] = field_completeness(purpose_selection, purpose_documents, result['source_completeness'])
    if exact_owner:
        result['issuer_fiscal_policies'] = fiscal_policies
    if field_semantics:
        result['comparison_applicability'] = comparison_applicability(result)
    if statement_basis_policy is not None:
        result['statement_basis_owner']=dict(contract='sec-fpi-statement-basis-replay-v1',
            policy=statement_basis_policy,execution_generation=basis_execution_generation,
            plan_sha256=digest(plan),acquisition_sha256=digest(acquisition),
            original_receipts_sha256=digest(receipts),documents=basis_receipts,
            source_use_eligible=False,valuation_eligible=False,direction_eligible=False)
        result['comparison_applicability']=comparison_applicability(result)
    if statement_scope_audit:
        # Applicability ignores diagnostics; whole-projection owner hashes still bind them.
        result['statement_scope_audit'] = dict(contract='foreign-statement-scope-replay-audit-v1',
            plan_sha256=digest(plan), acquisition_sha256=digest(acquisition),
            original_receipts_sha256=digest(receipts), documents=scope_audits,
            selected_basis=None, source_use_eligible=False, direction_eligible=False)
    return result
