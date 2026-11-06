"""Read-only dated research view. It issues no source, economic or Native grant.

Selection is over recorded observations, not a replacement financial parser.
Original receipts and typed quality decisions remain necessary inputs. Equal
source lineage is not independent economic corroboration.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
import re

from app.services.vnext_research_store import digest, plain

CONTRACT = 'COMPOSITE_RESEARCH_PACKET_V1'
ALLOWED = {'CURRENT_VALID', 'SOURCE_REFERENCE'}
DENIED = {'POLICY_DENIED', 'MAPPING_CONFLICT', 'MISSING_SOURCE', 'STALE',
          'PROVIDER_LIMIT', 'NOT_ATTEMPTED', 'RESEARCH_UNREVIEWED'}
FIELDS = ('completed_close', 'financial.revenue', 'financial.operating_income',
          'financial.net_income', 'valuation.PER', 'valuation.PBR', 'valuation.FPER',
          'valuation.FY1_EPS', 'technical.reference', 'ohlcv.adjusted_daily',
          'ohlcv.adjusted_weekly', 'ohlcv.adjusted_monthly', 'ohlcv.unadjusted_weekly_valuation')
CONTEXT_FIELDS = ('financial.operating_cashflow', 'financial.operating_cash_flow',
                  'financial.assets', 'financial.liabilities', 'financial.equity',
                  'financial.stockholders_equity', 'financial.debt_including_current',
                  'financial.owners_parent_net_income', 'financial.noncontrolling_interest',
                  'financial.cash_and_cash_equivalents')
PUBLIC_ID = ('ticker', 'canonical_security_id', 'canonical_company_id', 'country',
             'exchange', 'security_type', 'issuer_type', 'cik', 'corp_code',
             'ordinary_share_identifier', 'adr_ratio', 'adr_ratio_source', 'adr_ratio_as_of')


STATE_CONTRACT = 'research-field-state-v1'
REFERENCE_USE = 'PUBLIC_RESEARCH_REFERENCE_ONLY'


def _state_key(item):
    return (item['field'], item.get('allowed_use', REFERENCE_USE),
            json.dumps(item.get('scope', []), sort_keys=True))


def validate_field_state(packet):
    """Reject same-use contradictions before rendering or model consumption."""
    admitted = {_state_key(e) for e in packet['evidence'] if e['status'] in ALLOWED}
    denied = {_state_key(e) for e in packet['evidence'] if e['status'] in DENIED}
    if admitted & denied:
        raise ValueError('PACKET_EVIDENCE_STATE_CONFLICT')
    if any(_state_key(m) in admitted for m in packet.get('missing', [])):
        raise ValueError('PACKET_EVIDENCE_STATE_CONFLICT')
    if packet.get('field_state_contract') == STATE_CONTRACT:
        expected = reduce_field_state({k:v for k,v in packet.items() if k != 'field_states'})
        if packet.get('field_states') != expected['field_states']:
            raise ValueError('PACKET_EVIDENCE_STATE_CONFLICT')


def reduce_field_state(packet):
    """Reconcile absence only; never revoke quality denials or issue new uses.

    Call after qualified evidence changes and before reference-bundle sealing.
    Scope-less legacy missing entries mean the public reference axis only.
    """
    result = deepcopy(packet)
    admitted = {_state_key(e) for e in result['evidence'] if e['status'] in ALLOWED}
    history = result.setdefault('missing_history', [])
    remaining = []
    for missing in result.get('missing', []):
        if _state_key(missing) in admitted:
            if missing['status'] not in ('NOT_ATTEMPTED', 'MISSING_SOURCE'):
                raise ValueError('PACKET_EVIDENCE_STATE_CONFLICT')
            if missing not in history:
                history.append(deepcopy(missing))
        else:
            remaining.append(missing)
    result['missing'] = remaining
    states = defaultdict(list)
    for item in result['evidence']:
        states[_state_key(item)].append(dict(ref=item['ref'], status=item['status'], source_sha=item['source_sha']))
    result['field_states'] = [dict(security=result.get('ticker',result.get('case')), field=k[0],
        use_scope=k[1], scope=json.loads(k[2]), analysis_as_of=result['as_of'],
        observations=sorted(v,key=lambda x:(x['ref'],x['source_sha'],x['status']))) for k,v in sorted(states.items())]
    result['field_state_contract'] = STATE_CONTRACT
    return result


def merge_public_reference(base, source):
    """Merge two original CompositeView results, before reference-bundle sealing.

    This is a projection, not an admission API. Runtime verifies both stores and
    registration identities before calling it. Same-time conflicts fail closed.
    """
    if base['public_security']!=source['public_security'] or base['as_of']!=source['as_of']:
        raise ValueError('public_reference_identity_or_cutoff')
    result=deepcopy(base);groups=defaultdict(list)
    for e in base['evidence']+source['evidence']:groups[_state_key(e)].append(deepcopy(e))
    result['evidence']=[]
    for key,items in sorted(groups.items()):
        items.sort(key=lambda x:(instant(x['reviewed_at']),x['status'] in DENIED,x['source_sha']),reverse=True)
        winner=items[0];peers=[x for x in items if x['reviewed_at']==winner['reviewed_at']]
        if len({digest(x['data']) for x in peers})>1 and not any(x['status'] in DENIED for x in peers):
            winner=dict(winner,status='MAPPING_CONFLICT',conflict_reason='SAME_REVIEW_TIME_DIFFERENT_VALUES')
        result['evidence'].append(winner)
        result.setdefault('source_lineage',[]).extend(items[1:])
    # Preserve an unscoped newer denial over older scoped observations.
    for e in result['evidence']:
        if e.get('scope') and any(x['field']==e['field'] and x.get('allowed_use',REFERENCE_USE)==e.get('allowed_use',REFERENCE_USE) and not x.get('scope') and x['status'] in DENIED
            and instant(x['reviewed_at'])>=instant(e['reviewed_at']) for x in result['evidence']):e['status']='POLICY_DENIED'
    for a in base['source_runs']:
        if any(b['run_id']==a['run_id'] and b!=a for b in source['source_runs']):raise ValueError('source_run_metadata_conflict')
    result['source_runs']=sorted({r['run_id']:r for r in base['source_runs']+source['source_runs']}.values(),key=lambda r:(r['started_at'],r['run_id']))
    if len(result['source_runs'])>16:raise ValueError('composite_run_bound_exceeded')
    result['public_source_snapshot_sha256']=source['snapshot_sha256']
    result['lineage_count']=len({e['lineage_group'] for e in result['evidence'] if e['status'] in ALLOWED})
    result=reduce_field_state(result);result['numeric_catalog']=numeric_catalog(result)
    return result


def instant(value):
    if not isinstance(value, str):
        raise ValueError('explicit_aware_cutoff_required')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('explicit_aware_cutoff_required')
    return dt.astimezone(timezone.utc)


def pick(value, names):
    return {k: value[k] for k in names if k in value}


def public_data(field, p):
    if field.startswith('financial.'):
        if not p.get('fact'):
            return pick(p, ('reason','quality','denials'))
        if field in CONTEXT_FIELDS:
            return dict(p['fact'])
        return pick(p.get('fact', {}), ('fields', 'as_of_date', 'quality_contract', 'quality_receipt_sha256',
                    'projection_sha256', 'interpretation_eligible', 'prose_eligible', 'field_dependency_receipts'))
    if field == 'completed_close':
        return pick(p, ('row', 'currency', 'calendar', 'adjustment', 'price_basis', 'adjusted', 'validator', 'integrity'))
    if field.startswith('ohlcv.'):
        return pick(p, ('rows', 'requested_rows', 'source_exhausted', 'quality_valid', 'reason', 'calendar', 'adjusted', 'source_captured_at'))
    if field.startswith('valuation.'):
        return p.get('snapshot', {})
    if field.startswith('macro.'):
        return pick(p, ('observation', 'full_market_owner'))
    if field == 'technical.reference':
        return dict(availability=p.get('daily_availability', []),
                    adjustment_basis=p.get('packet', {}).get('adjustment_basis'),
                    timeframes={tf: p.get('packet', {}).get(tf, {}) for tf in ('daily', 'weekly', 'monthly')})
    return {}


class CompositeView:
    """One bounded RuntimeStore snapshot, exact CAS verification, no writes."""
    @classmethod
    def from_dated_archive(cls, bundle, *, enabled=False):
        """Separate opt-in reference edge; it does not admit current registration."""
        from app.services.dated_capture_research import dated_archive_view
        return dated_archive_view(bundle, enabled=enabled)

    def __init__(self, store, *, as_of, run_ids=None, tickers=None, kis_multisource_owner=None,
                 reported_context=False, registration_owner=None, registration_generation=None,
                 registration_policy=None):
        self.store, self.cutoff = store, instant(as_of)
        self.reported_context = reported_context
        self.kis_multisource_owner = kis_multisource_owner
        self.as_of = self.cutoff.isoformat()
        intake_identities=None
        self.registration_admission=None
        if registration_owner is not None or registration_generation is not None:
            from app.services.prospective_class_c_owner import source_intake_snapshot
            if not tickers or registration_policy is None:
                raise ValueError('composite_intake_exact_subject_policy_required')
            identities,receipt,_,_=source_intake_snapshot(registration_owner,
                generation_id=registration_generation,subjects=tuple(tickers),policy=registration_policy)
            intake_identities={t:{k:r.get(k) for k in PUBLIC_ID} for t,r in identities.items()}
            self.registration_admission=dict(contract='composite-source-intake-reference-v1',
                registration_sha256=digest(receipt),purpose='RESEARCH_NO_SEND',
                current_production=False,send=False)
        self.raw, self.capture_proofs, self.visiting = {}, {}, set()
        with store.connect() as c:
            runs = c.execute('SELECT run_id,started_at,as_of,status FROM research_run ORDER BY started_at,run_id LIMIT 17').fetchall()
            if len(runs) > 16:
                raise ValueError('composite_run_bound_exceeded')
            known = {r[0] for r in runs}
            if run_ids is not None and (not run_ids or len(run_ids) != len(set(run_ids)) or not set(run_ids) <= known):
                raise ValueError('composite_run_selection')
            self.runs = {r[0]: dict(zip(('run_id', 'started_at', 'as_of', 'status'), r)) for r in runs
                         if (run_ids is None or r[0] in run_ids) and instant(r[1]) <= self.cutoff}
            if not self.runs:
                raise ValueError('no_runs_available_at_cutoff')
            marks = ','.join('?' for _ in self.runs)
            # Public identity only. Do not select notes, user_snapshot or thesis text.
            cols = ','.join('s.' + k for k in PUBLIC_ID)
            if tickers is not None and (not tickers or len(tickers)>500 or len(set(tickers))!=len(tickers)):
                raise ValueError('composite_subject_scope')
            subject_clause = '' if tickers is None else ' AND s.ticker IN ('+','.join('?' for _ in tickers)+')'
            self.identities = intake_identities if intake_identities is not None else {r[0]: dict(zip(PUBLIC_ID, r)) for r in c.execute(
                'SELECT ' + cols + ' FROM securitymaster s JOIN watchlistitem w ON w.ticker=s.ticker WHERE w.active=1'+subject_clause+' ORDER BY s.ticker',tuple(tickers or []))}
            captures = c.execute('SELECT capture_id,run_id,provider,request_key,raw_sha,raw_path,captured_at,receipt_json FROM source_capture WHERE run_id IN ('+marks+') LIMIT 10001', tuple(self.runs)).fetchall()
            # Scoped stock views retain the macro fields already admitted by
            # packet(); an index/ETF reference still has no stock input grant.
            observation_clause = '' if tickers is None else (' AND (ticker IN ('+
                ','.join('?' for _ in tickers)+") OR (ticker='@MARKET:US' AND field LIKE 'macro.%'))")
            self.rows = c.execute('SELECT observation_id,run_id,ticker,field,status,source_sha,payload_json FROM research_observation WHERE run_id IN ('+marks+')'+observation_clause+' ORDER BY run_id,ticker,field,observation_id LIMIT 20001', (*self.runs,*(tickers or []))).fetchall()
        if len(captures) > 10000 or len(self.rows) > 20000 or len(self.identities) > 500:
            raise ValueError('composite_snapshot_bound_exceeded')
        self.captures = defaultdict(list)
        for row in captures:
            self.captures[(row[1], row[4])].append(row)
        self.snapshot_sha = digest(dict(runs=self.runs, identities=self.identities, captures=captures, observations=self.rows))
        if self.registration_admission is not None:
            self.snapshot_sha=digest(dict(source_snapshot=self.snapshot_sha,registration=self.registration_admission))

    def source(self, run, sha, capture_id=None):
        key = (run, sha, capture_id)
        if key in self.capture_proofs:
            return self.capture_proofs[key]
        if key in self.visiting:
            raise ValueError('source_dependency_cycle')
        candidates = self.captures.get((run, sha), [])
        if capture_id is not None:
            candidates = [c for c in candidates if c[0] == capture_id]
        if len(candidates) > 1 and capture_id is None:
            variants = [self.source(run, sha, c[0]) for c in candidates]
            if len({(v['provider'],v['origin_run']) for v in variants}) != 1:
                raise ValueError('source_identity_ambiguous')
            result = dict(min(variants,key=lambda v: instant(v['captured_at'])),
                          receipt_variants=variants,
                          available_at=max(instant(v['available_at']) for v in variants).isoformat())
            self.capture_proofs[key] = result
            return result
        if len(candidates) != 1:
            raise ValueError('source_receipt_missing_or_ambiguous:'+str((run,sha,len(candidates))))
        ident, _, provider, request, _, path, at, text = candidates[0]
        if not re.fullmatch('[0-9a-f]{64}', sha):
            raise ValueError('source_hash_format')
        expected = plain(self.store.path.parent / 'raw' / sha)
        if plain(path) != expected or expected.stat().st_nlink != 1 or expected.stat().st_size > 64*1024**2:
            raise ValueError('source_path_or_size')
        if sha not in self.raw:
            raw = expected.read_bytes()
            if digest(raw) != sha:
                raise ValueError('source_integrity_gap')
            self.raw[sha] = raw
        receipt = json.loads(text)
        if receipt.get('captured_at') != at or instant(at) > self.cutoff:
            raise ValueError('source_time_outside_cutoff')
        self.visiting.add(key)
        origin_run, origin = run, receipt
        parents = []
        if receipt.get('kind') == 'EXPLICIT_HISTORICAL_REUSE':
            original = receipt.get('original_receipt')
            if not original or digest(original) != receipt.get('original_receipt_sha256'):
                raise ValueError('inherited_receipt_hash')
            originals = self.captures.get((receipt['source_run'], sha), [])
            originals = [c for c in originals if digest(json.loads(c[7])) == digest(original)]
            if len(originals) != 1:
                raise ValueError('inherited_receipt_origin')
            parent = self.source(receipt['source_run'], sha, originals[0][0])
            if parent['receipt_sha256'] != digest(original) or parent['captured_at'] != at:
                raise ValueError('inherited_receipt_origin')
            parents.append(parent)
            origin_run = parent['origin_run']
            origin = original
        if origin.get('raw_birth') == 'CURRENT_HTTP':
            if (origin.get('raw_sha256') != sha or origin.get('run_id') != origin_run or
                    origin.get('status') != 200 or origin.get('auth') is True):
                raise ValueError('original_http_receipt_binding')
        proof = dict(capture_id=ident, run_id=run, origin_run=origin_run, provider=provider,
                     raw_sha256=sha, receipt_sha256=digest(receipt), captured_at=at,
                     receipt_kind=origin.get('kind', origin.get('raw_birth', 'UNSPECIFIED')),
                     original_receipt_sha256=digest(origin), request_key=request)
        data = None
        if 'Replay' in provider:
            data = json.loads(self.raw[sha])
            dependencies = []
            for page in data.get('pages', []):
                candidates = self.captures.get((origin_run, page['raw_sha256']), [])
                if data.get('kind') == 'CURRENT_CHART_REPLAY' and len(candidates) > 1:
                    from app.services.vnext_incremental_replay import capture_occurrence
                    selected = capture_occurrence([
                        dict(run_id=origin_run,raw_sha=page['raw_sha256'],capture_id=c[0],
                             receipt=json.loads(c[7])) for c in candidates],
                        origin_run,page['raw_sha256'],captured_at=page['captured_at'],
                        request_body=data['request_body'])
                    dependencies.append((origin_run,page['raw_sha256'],selected['capture_id']))
                else:
                    dependencies.append((origin_run,page['raw_sha256']))
            dependencies += [(origin_run, h) for h in data.get('sources', [])]
            for r in data.get('receipts', []):
                birth = r.get('vnext_source_birth')
                if birth:
                    dependencies.append((birth['run_id'], birth['raw_sha256']))
            if provider == 'FinancialAmountReplay':
                dependencies.append((origin.get('source_generation'), origin.get('original_raw_sha256')))
                supplement = data.get('fact', {}).get('fields', {}).get('documentary_reconciliation')
                if supplement:
                    dependencies += [(supplement['documentary_generation'], supplement[k])
                        for k in ('index_raw_sha256', 'document_raw_sha256')]
            if provider == 'IncrementalDailyReplay':
                if len(data.get('parents',[]))!=2:
                    raise ValueError('incremental_original_parents_required')
                dependencies += [(p['run_id'],p['raw_sha256']) for p in data['parents']]
            for dep in sorted(set(dependencies)):
                parents.append(self.source(*dep))
            if provider == 'IncrementalDailyReplay':
                from app.services.vnext_incremental_ingestion import replay_merge
                a,b=data['parents']
                replay_merge(data,json.loads(self.raw[a['raw_sha256']]),json.loads(self.raw[b['raw_sha256']]))
        def reference(p):
            value = dict(run_id=p['run_id'], raw_sha256=p['raw_sha256'], receipt_sha256=p['receipt_sha256'])
            if len(self.captures.get((p['run_id'],p['raw_sha256']),[])) > 1:
                value['capture_id'] = p['capture_id']
            return value
        proof['dependencies'] = [reference(p) for p in parents]
        if provider=='IncrementalDailyReplay':
            closure={}
            def include(parent):
                key=(parent['run_id'],parent['raw_sha256'])
                if key in closure:
                    if closure[key]['receipt_sha256'] != parent['receipt_sha256']:
                        raise ValueError('incremental_conflicting_capture_occurrence')
                    return
                closure[key]=reference(parent)
                for dep in parent['dependencies']:
                    include(self.source(dep['run_id'],dep['raw_sha256'],dep.get('capture_id')))
            for parent in parents:include(parent)
            proof['dependency_closure']=[closure[k] for k in sorted(closure)]
        proof['available_at'] = max([instant(at), instant(self.runs[run]['started_at'])] +
                                    [instant(p['available_at']) for p in parents]).isoformat()
        if instant(proof['available_at']) > self.cutoff:
            raise ValueError('source_dependency_after_cutoff')
        self.visiting.remove(key)
        self.capture_proofs[key] = proof
        return proof

    def entry(self, row):
        ident, run, ticker, field, status, sha, text = row
        p = json.loads(text)
        proof = self.source(run, sha)
        data = public_data(field, p)
        if p.get('strict_native') is not False or not data:
            raise ValueError('unrecognized_or_authority_bearing_observation')
        if field == 'completed_close' and proof['provider'] in ('Kiwoom', 'ChartReplay'):
            from app.services.vnext_incremental_replay import verify_completed_projection
            capture = next(c for c in self.captures[(run, sha)] if c[0] == proof['capture_id'])
            receipt = json.loads(capture[7])
            if receipt.get('kind') == 'EXPLICIT_HISTORICAL_REUSE':
                receipt = receipt['original_receipt']
            verify_completed_projection(self.identities[ticker], self.raw[sha], receipt, p)
        f = data.get('fields', {})
        if field in CONTEXT_FIELDS:
            if not self.reported_context:
                raise ValueError('reported_context_opt_in_required')
            from app.services.vnext_financial_reuse import verify_reported_context
            capsule = json.loads(self.raw[sha])
            if capsule.get('fact') != p.get('fact') or proof['provider'] != 'FinancialAmountReplay':
                raise ValueError('reported_context_capsule_binding')
            verify_reported_context(p['fact'], self.identities[ticker])
            if (f.get('original_raw_sha256') not in {d['raw_sha256'] for d in proof['dependencies']}
                    or f.get('source_generation') not in {d['run_id'] for d in proof['dependencies']}):
                raise ValueError('reported_context_origin_binding')
            supplement = f.get('documentary_reconciliation')
            if supplement:
                dependencies = {(d['run_id'], d['raw_sha256']) for d in proof['dependencies']}
                if any((supplement['documentary_generation'], supplement[k]) not in dependencies
                       for k in ('index_raw_sha256', 'document_raw_sha256')):
                    raise ValueError('reported_context_documentary_parent_binding')
        if f and (f.get('source_ticker') != ticker or field != 'financial.' + f.get('metric', '')):
            raise ValueError('financial_security_or_field_binding')
        if field.startswith('valuation.') and data.get('contract') == 'kis-reviewed-multisource-research-v1':
            from app.services.vnext_kis_multisource_ingestion import verify_stored
            verify_stored(self.store,self.kis_multisource_owner,row=row,payload=p,
                capsule=json.loads(self.raw[sha]),security=self.identities[ticker],cutoff=self.as_of)
        elif field.startswith('valuation.') and data.get('contract') == 'kis-owner-research-snapshot-v1':
            from app.services.vnext_kis_research import owner_snapshots
            capsule=json.loads(self.raw[sha])
            identity=capsule['security']
            if any(identity.get(k)!=self.identities[ticker].get(k) for k in PUBLIC_ID):
                raise ValueError('kis_composite_security_binding')
            expected=next(s for s in owner_snapshots(capsule,security=identity) if s['metric']==field.split('.')[1])
            if data!=expected:raise ValueError('kis_projection_owner_mismatch')
            if instant(data['qualification_as_of'])>self.cutoff:raise ValueError('future_kis_qualification')
            if instant(data['qualification_as_of']).date()!=self.cutoff.date():status='STALE'
        elif field.startswith('valuation.'):
            from app.services.provider_native_valuation_snapshot import ProviderNativeValuationSnapshot, ProviderNativeForwardValuationSnapshot
            model = ProviderNativeForwardValuationSnapshot if field == 'valuation.FPER' else ProviderNativeValuationSnapshot
            model.model_validate(data)
            if (data.get('raw_sha256') != sha or data.get('requested_security_id') != ticker or
                    data.get('canonical_security_id') != self.identities[ticker]['canonical_security_id']):
                raise ValueError('valuation_source_identity_binding')
            if instant(data['retrieval_timestamp']) > self.cutoff:
                raise ValueError('future_observation_at_cutoff')
            if data.get('display_eligible') is not True:
                status = 'POLICY_DENIED'
        if field.startswith('financial.') and (f or status not in DENIED):
            if not all(f.get(k) for k in ('period_start', 'period_end', 'currency', 'statement_basis', 'source_receipt', 'source_occurrences')):
                raise ValueError('financial_scope_missing')
            source = json.loads(self.raw[sha])
            if 'facts' in source and p['fact'] not in source['facts'] or 'fact' in source and p['fact'] != source['fact']:
                raise ValueError('financial_record_projection_mismatch')
            if 'plan' in source:
                from app.services.reported_comparison_facts import comparative_facts
                from app.services.financial_observation_quality_service import digest as quality_digest
                from app.services.sec_business_field_quality_service import sha as sec_digest
                facts = []
                for bundle in source['projection']['quality_bundles']:
                    quality = bundle['quality']
                    qdigest = sec_digest if bundle['source_inputs']['formal'].get('provider') in ('sec_companyfacts','sec_foreign_filing') else quality_digest
                    if qdigest({k:v for k,v in quality.items() if k != 'receipt_sha256'}) != quality['receipt_sha256']:
                        raise ValueError('recorded_quality_receipt_drift:'+ticker+':'+str(quality.get('contract')))
                    facts.extend(comparative_facts(quality, ticker=ticker, issuer_id=f['issuer_id']))
                if p['fact'] not in facts:
                    raise ValueError('original_financial_quality_replay_denied')
            if data.get('prose_eligible') is False:
                status = 'POLICY_DENIED'
            # Absolute amounts remain one datum and cannot acquire derived uses.
            if f.get('observation_only'):
                if f.get('comparison_eligible') is not False or f.get('valuation_denominator_eligible') is not False or any(k in f for k in ('growth_pct','delta','prior_comparable_value')):
                    raise ValueError('absolute_amount_scope_broadened')
        if field == 'technical.reference':
            original = json.loads(self.raw[sha])
            if p.get('packet') != original.get('packet') or p['packet'].get('ticker') != ticker:
                raise ValueError('technical_projection_binding')
        if field.startswith('ohlcv.'):
            original = json.loads(self.raw[sha])
            if original.get('request_body', {}).get('stk_cd') != ticker.replace('.', '-'):
                raise ValueError('chart_security_binding')
            if original.get('contract')=='owned-incremental-daily-research-v1':
                merged=original['merge']
                if (p.get('selected_rows')!=(merged['rows'] if merged['quality']['valid'] else []) or
                    data.get('rows')!=merged['merged_rows'] or data.get('quality_valid')!=merged['quality']['valid'] or
                    data.get('calendar')!=original['calendar'] or data.get('adjusted')!=original['basis']['adjusted']):
                    raise ValueError('incremental_cold_observation_mismatch')
        dates = [f.get('period_end'), f.get('prior_period_end'), data.get('calendar', {}).get('session')]
        if field.startswith('macro.'):
            ob = data.get('observation', {})
            context = ob.get('raw_payload', {}).get('publication_context', {})
            if context.get('response_sha256') != sha or context.get('display_eligible') is not True:
                status = 'POLICY_DENIED'
            dates.append(ob.get('observed_at'))
        if any(str(d)[:10] > self.cutoff.date().isoformat() for d in dates if d):
            raise ValueError('future_observation_at_cutoff')
        period = (f.get('period_start'), f.get('period_end'), f.get('period_type'), f.get('statement_basis'), f.get('currency')) if f else ()
        lineage = [ticker, f.get('issuer_id'), f.get('source_receipt'), period] if f else [ticker, field, proof['origin_run'], sha]
        # Inherited copies never become newer reviews by virtue of their wrapper.
        review_at = max(instant(proof['captured_at']), instant(self.runs[proof['origin_run']]['started_at']))
        return dict(ref='e'+digest([ticker,field,period,sha])[:24], field=field, status=status,
                    source_sha=sha, data=data, lineage_group='l'+digest(lineage)[:24],
                    scope=list(period), record_id=ident, original_run=proof['origin_run'],
                    recorded_runs=[run], reviewed_at=review_at.isoformat(), provenance=proof,
                    observation_sha256=digest(json.loads(text)),
                    freshness='DATED_REFERENCE_NOT_CURRENT_REQUALIFICATION',
                    allowed_use='PUBLIC_RESEARCH_REFERENCE_ONLY', direction_allowed=False)

    def packet(self, ticker):
        if ticker not in self.identities:
            raise ValueError('not_registered')
        grouped = defaultdict(list)
        excluded = []
        for row in self.rows:
            if row[2] != ticker and not (row[2] == '@MARKET:US' and row[3].startswith('macro.')):
                continue
            if row[3] not in FIELDS and not (self.reported_context and row[3] in CONTEXT_FIELDS) and not row[3].startswith('macro.'):
                continue
            try:
                item = self.entry(row)
            except ValueError as exc:
                if str(exc) not in ('source_time_outside_cutoff','source_dependency_after_cutoff','future_observation_at_cutoff'):
                    raise
                self.visiting.clear()
                excluded.append(dict(field=row[3],record_id=row[0],reason=str(exc)))
                continue
            grouped[(item['field'], tuple(item['scope']))].append(item)
        evidence, superseded = [], []
        for (field, _), variants in sorted(grouped.items(), key=lambda kv: str(kv[0])):
            variants.sort(key=lambda x: (instant(x['reviewed_at']), x['status'] in DENIED, x['source_sha']), reverse=True)
            winner = variants[0]
            peers = [v for v in variants if v['reviewed_at'] == winner['reviewed_at']]
            if len({digest(v['data']) for v in peers}) > 1 and not any(v['status'] in DENIED for v in peers):
                winner = dict(winner, status='MAPPING_CONFLICT', conflict_reason='SAME_REVIEW_TIME_DIFFERENT_VALUES')
            winner['recorded_runs'] = sorted({r for v in variants if v['source_sha'] == winner['source_sha'] for r in v['recorded_runs']})
            winner['collapsed_or_superseded_count'] = len(variants)-1
            evidence.append(winner)
            superseded.extend(dict(field=v['field'], record_id=v['record_id'], source_sha=v['source_sha'],
                                   reason='DUPLICATE_OR_OLDER_REVIEW') for v in variants[1:])
        # An unscoped later field denial may not be bypassed with an older period.
        for item in evidence:
            denials = [e for e in evidence if e['field']==item['field'] and not e['scope'] and e['status'] in DENIED
                       and instant(e['reviewed_at']) >= instant(item['reviewed_at'])]
            if item['scope'] and denials:
                item['status'] = 'POLICY_DENIED'
                item['blocking_refs'] = [d['ref'] for d in denials]
        result = dict(contract=CONTRACT, ticker=ticker, case=ticker, public_security=self.identities[ticker],
                      as_of=self.as_of, source_runs=list(self.runs.values()), snapshot_sha256=self.snapshot_sha,
                      evidence=evidence, superseded=superseded, excluded_after_cutoff=excluded,
                      missing=[dict(field=f,status='MISSING_SOURCE',reason='NO_RECORDED_QUALIFIED_OBSERVATION') for f in FIELDS if not any(e['field']==f for e in evidence)],
                      freshness='MIXED_DATED_SOURCES_NO_CURRENT_OWNER_ISSUANCE',
                      model='OFF', model_execution='NOT_RUN', send=False, strict_ready=False,
                      user_thesis_included=False, holdings_included=False, decision=None,
                      newbuyer=dict(decision=None, authority='NOT_ASSESSED'),
                      holder=dict(decision=None, basis='HYPOTHETICAL_NO_PRIVATE_POSITION'),
                      economic_driver_count=0, independent_corroboration='NOT_ESTABLISHED',
                      lineage_count=len({e['lineage_group'] for e in evidence if e['status'] in ALLOWED}))
        result = reduce_field_state(result)
        for e in evidence:
            if e['data'].get('contract') == 'kis-reviewed-multisource-research-v1':
                result['missing'].append(dict(field='current_fiscal.'+e['data']['metric'],
                    status='NOT_ATTEMPTED',allowed_use='CURRENT_FISCAL_VERIFIED',
                    reason='DATED_RESEARCH_ADMITTED_BUT_CURRENT_FILING_CENSUS_UNVERIFIED'))
        result['numeric_catalog'] = numeric_catalog(result)
        return result


def numeric_catalog(packet):
    """Only original numeric values, always with units, dates and lineage."""
    result = []
    def add(e, path, value, unit, basis, when):
        if type(value) not in (int,float) or not math.isfinite(value) or not all((unit,basis,when)):
            return
        row = dict(ref=e['ref'], field=e['field'], path=path, value=value, unit=unit, basis=basis,
                   as_of=when, source_sha=e['source_sha'], lineage_group=e['lineage_group'])
        result.append(dict(row, catalog_id='c'+digest(row)[:24]))
    for e in packet['evidence']:
        if e['status'] not in ALLOWED:
            continue
        d=e['data'];field=e['field']
        if field.startswith('financial.'):
            f=d['fields'];basis=f['statement_basis']+' '+f['period_type']
            for key in ('current_value','delta','growth_pct','prior_comparable_value'):
                prefix='prior_' if key=='prior_comparable_value' else ''
                when=str(f.get(prefix+'period_start',''))+'/'+str(f.get(prefix+'period_end',''))
                add(e,'fields.'+key,f.get(key),'percent' if key=='growth_pct' else f['currency'],basis,when)
        elif field=='completed_close':
            r=d.get('row',{});key='close' if 'close' in r else 'close_price'
            add(e,'row.'+key,r.get(key),d.get('currency'),d.get('price_basis') or d.get('adjustment') or 'RECORDED_COMPLETED_CLOSE',d.get('calendar',{}).get('session'))
        elif field.startswith('valuation.') and d.get('display_eligible'):
            add(e,'value',d.get('value'),d.get('unit','multiple'),d.get('metric_semantic'),d.get('retrieval_timestamp'))
        elif field.startswith('macro.'):
            ob=d.get('observation',{})
            add(e,'observation.value',ob.get('value'),ob.get('unit'),'OBSERVATION_NOT_PUBLICATION_DATE',ob.get('observed_at'))
        elif field == 'technical.reference':
            for tf in ('daily', 'weekly', 'monthly'):
                part = d.get('timeframes', {}).get(tf, {})
                for f in part.get('facts', []):
                    if f.get('semantic') not in ('close','return_1','return_20','sma_20','sma_200','rsi_14','atr_pct_14') or f.get('dependency_classification') != 'SAFE' or f.get('completed_bar_only') is not True:
                        continue
                    add(e, tf+'.'+f['semantic'], float(f['value']), f.get('unit'), f.get('input_basis'), f.get('as_of'))
    if packet.get('component_reference'):
        from app.services.vnext_component_reference import catalog
        result.extend(catalog(packet['component_reference']))
    if packet.get('research_financial_reference'):
        from app.services.sec_research_source_authority import catalog
        result.extend(catalog(packet['research_financial_reference']))
    return result


def draft(packet, *, price_reference=None, component_reference=None, financial_reference=None,
          historical_valuation_owner=None, kis_source_owner=None, kis_multisource_owner=None):
    validate_field_state(packet)
    if packet.get('contract') != CONTRACT or packet.get('numeric_catalog') != numeric_catalog(packet):
        raise ValueError('composite_numeric_drift')
    if 'kis_source_status' in packet:
        from app.services.vnext_kis_source_state import verify as verify_kis_source
        verify_kis_source(packet,kis_source_owner)
    for item in packet['evidence']:
        if item['data'].get('contract') == 'kis-reviewed-multisource-research-v1':
            from app.services.vnext_kis_multisource import ReviewedMultisourceKIS
            if not isinstance(kis_multisource_owner,ReviewedMultisourceKIS):
                raise ValueError('live_multisource_capability_required')
            kis_multisource_owner.verify(kis_multisource_owner.capsule_for_snapshot(packet['public_security'],item['data']),
                item['data'],security=packet['public_security'],cutoff=packet['as_of'])
    historical = packet.get('historical_price_reference')
    components = packet.get('component_reference')
    if 'reference_bundle' in packet:
        from app.services.vnext_reference_bundle import verify
        verify(packet, price_reference=price_reference, component_reference=component_reference, financial_reference=financial_reference)
    elif packet.get('research_financial_reference'):
        raise ValueError('research_financial_bundle_required')
    elif components:
        from app.services.vnext_component_reference import project
        original = {k:v for k,v in packet.items() if k != 'component_reference'}
        original['numeric_catalog'] = numeric_catalog(original)
        if historical or component_reference is None or components != project(original,component_reference):
            raise ValueError('component_draft_binding')
    if historical and 'reference_bundle' not in packet:
        from app.services.vnext_historical_price_reference import project
        original = {k:v for k,v in packet.items() if k != 'historical_price_reference'}
        if price_reference is None or historical != project(original, price_reference):
            raise ValueError('historical_draft_binding')
    from app.services.vnext_reported_observations import reported_trends, normalization_questions, NO_DRIVER_MEANING
    historical_valuation = None
    if historical_valuation_owner is not None:
        from app.services.vnext_reported_observations import historical_kis_reference
        historical_valuation = historical_kis_reference(historical_valuation_owner,
            security=packet['public_security'],as_of=packet['as_of'])
    return dict(contract='vnext-composite-unsent-draft-v1', input_sha256=digest(packet),
                ticker=packet['ticker'], evidence_as_of=packet['as_of'], numeric_catalog=packet['numeric_catalog'],
                evidence=packet['evidence'], missing=packet['missing'], model='OFF', send=False,
                strict_ready=False, decision=None, newbuyer=packet['newbuyer'],holder=packet['holder'],
                message_status='DATED_SOURCE_CONTEXT_NOT_MODEL_JUDGMENT',
                historical_price_reference=historical,
                component_reference=components,
                research_financial_reference=packet.get('research_financial_reference'),
                historical_valuation_reference=historical_valuation,
                **({'kis_source_status':packet['kis_source_status']} if 'kis_source_status' in packet else {}),
                reported_financial_trend=reported_trends(packet.get('research_financial_reference')),
                earnings_normalization_questions=normalization_questions(packet),
                no_eligible_economic_evidence_meaning=NO_DRIVER_MEANING,
                reference_bundle=packet.get('reference_bundle'),
                warning='Original dates and quality limits apply. No current source requalification or economic judgment.')


def render_draft(result):
    """Concise no-send preview, without inventing NewBuyer or Holder judgments."""
    if (result.get('contract')!='vnext-composite-unsent-draft-v1' or result.get('model')!='OFF'
        or result.get('send') is not False or result.get('decision') is not None):
        raise ValueError('model_off_draft_required')
    lines=[result['ticker']+' | Dated research preview', 'Evidence cutoff: '+result['evidence_as_of'],
           'Model OFF; no NewBuyer or Holder decision issued.', '',
           '| Field | Value | Unit | Basis | Period |', '|---|---:|---|---|---|']
    for n in result['numeric_catalog']:
        value,unit=str(n['value']),n['unit']
        labels={'ifrs-full_InsuranceServiceResult':'보험손익', 'dart_InvestmentIncomeExpenses':'투자손익',
                'ifrs-full_OtherOperatingIncomeExpense':'기타영업손익', 'financial.revenue':'매출',
                'financial.operating_income':'영업이익', 'financial.net_income':'순이익',
                'completed_close':'완료 종가'}
        label=labels.get(n['field'].removeprefix('operating_component.'),n['field'])
        path={'current':'당기','comparison':'비교 분기','fields.current_value':'당기',
              'fields.prior_comparable_value':'비교 기간','fields.growth_pct':'증감률','fields.delta':'증감액'}.get(n['path'],n['path'])
        basis=n['basis']
        if n['field'].startswith('operating_component.') and unit=='KRW':
            from decimal import Decimal
            value,unit=format(Decimal(n['value'])/Decimal(100000000),'.2f'),'억원'
            basis='연결 · 단독 분기 · 과거 연구 참고'
        lines.append('| '+label+' '+path+' | '+value+' | '+unit+' | '+basis+' | '+n['as_of']+' |')
    for e in result['evidence']:
        d=e['data']
        if d.get('contract')=='kis-reviewed-multisource-research-v1':
            lines+=['',d['metric']+' · 날짜가 명시된 KIS 자체 추정 연구 참고 (컨센서스 아님)',
                '예측 기간: '+d['period']+' | 추정자료 기준일: '+d['estimate_date'],
                '원본 수집: '+d['retrieval_timestamp']+' | 회계목록 확인 범위: '+d['fiscal_inventory_as_of'],
                '현재 최신 회계목록 미확인. 현재 가치평가·Strict Financial·Native·투자 방향 사용권 없음.']
            if d.get('price_session'):
                lines.append('FPER 분자: '+str(d['price_value'])+' KRW, '+d['price_session']+' 완료 비수정 종가. 다른 종목에 사용하지 않음.')
    components=result.get('component_reference')
    kis_source=result.get('kis_source_status')
    if kis_source:
        labels={'CURRENT_SOURCE_PRESENT_OWNER_PENDING':'추정자료 원본 있음 · 현재 수치 사용권 검증 대기',
                'CURRENT_SOURCE_EMPTY_AT_RETRIEVAL':'이번 조회에서 제공사 정상 빈 응답 · 영구 미지원 판정 아님',
                'HISTORICAL_REFERENCE_ONLY':'과거 조회 기록 · 현재 재수집 아님',
                'SOURCE_REJECTED':'원본 형식 또는 신원 검증 거절'}
        lines+=['','KIS 원본 상태: '+labels.get(kis_source['state'],kis_source['state']),
                '검증 상태: '+kis_source['state'],
                '원본 조회: '+kis_source['captured_at']+' | 원래 수집 세대: '+kis_source['source_generation']]
        if kis_source.get('estimate_date'):
            lines.append('제공사 추정자료 기준일: '+kis_source['estimate_date'])
        lines.append('원본 확보 여부만 표시합니다. EPS·FPER·매매 방향 사용권은 별도 검증 대상입니다. 기존 관측과 과거 자료는 보존합니다.')
        if kis_source.get('private_durable'):
            lines.append('연구 저장소에 원본·영수증 저장 완료. EPS·FPER 수치 저장 또는 승인과는 별개입니다.')
    if components:
        lines+=['','보고된 보험·투자·기타영업손익은 한 공시의 회계상 구성입니다. 원본 합계 대조 통과; 인과관계와 지속성은 미확인입니다.',
                '과거 연구용 참고이며 현재 Owner·매매 방향·EPS·밸류에이션·이익률 분모 사용권은 발급하지 않았습니다.']
        for account in dict.fromkeys(f['account_id'] for f in components['facts']):
            pair={f['role']:f for f in components['facts'] if f['account_id']==account}
            change=pair['current']['value']-pair['comparison']['value']
            lines.append(pair['current']['account_name']+': '+('증가' if change>0 else '감소' if change<0 else '동일')+' (비교 분기 대비, 독립 신호 아님)')
    history=result.get('historical_price_reference')
    valuation_history=result.get('historical_valuation_reference')
    if valuation_history and valuation_history['facts']:
        if kis_source and kis_source['retrieval_state']=='CURRENT_SOURCE_EMPTY_AT_RETRIEVAL':
            lines.append('이번 빈 응답과 별개로 이전 정상 추정자료는 아래 원래 날짜의 과거 참고로 보존합니다.')
        lines+=['','Historical KIS research, not current valuation:']
        lines.extend(f"{f['metric']}: {f['value']} {f['unit']} | FY1 {f['period']} | {f['as_of']}" for f in valuation_history['facts'])
        lines.append(valuation_history['limitation'])
    financial=result.get('research_financial_reference')
    if financial:
        lines+=['','Historical exact financial source reference only. Financial L3, Native, investment direction and EPS/ADS valuation remain denied.']
        lines.extend('- '+str(v) for v in financial['limitations'])
        trend=result.get('reported_financial_trend') or {}
        for row in trend.get('comparisons',[]):
            lines.append(row['field']+': reported '+row['reported_direction'].lower()+' ('+
                '/'.join(row['current_period'])+' versus '+'/'.join(row['prior_period'])+
                '; same filing, no causal or recurring conclusion).')
        lines.append(result.get('no_eligible_economic_evidence_meaning',''))
    if result.get('earnings_normalization_questions'):
        lines+=['','Research questions, not investment conclusions:']
        lines.extend('- '+q['question'] for q in result['earnings_normalization_questions'])
    if history:
        lines+=['','Historical adjusted chart reference: '+history['session']+' '+history['currency']+'; not an executable order price.']
        names={'support_low':'지지 구간 하단','support_high':'지지 구간 상단','resistance_low':'저항 구간 하단',
               'resistance_high':'저항 구간 상단','chart_invalidation':'차트 시나리오 무효화 참고',
               'current_price_rr':'기준가 손익비 참고','support_entry_rr':'지지 구간 손익비 참고'}
        lines += [names[f['kind']]+': '+str(f['value'])+' '+f['unit'] for f in history['facts']]
        if history['roles_rejected']:
            lines += ['적격 자료가 없는 차트 역할은 표시하지 않았습니다. 자세한 거절 근거는 구조화된 결과에 보존됩니다.']
    if any(f['status']=='DENIED' for f in (result.get('reference_bundle') or {}).get('families',{}).values()):
        lines += ['','일부 추가 참고자료는 원본 검증을 통과하지 못해 제외했습니다. 다른 적격 자료는 유지됩니다.']
    limits=[]
    for e in result['evidence']:
        if e['status'] not in ALLOWED:limits.append(e['field']+': '+e['status']+' '+str(e['data'].get('reason','')))
        limits.extend(e['data'].get('fields',{}).get('limitations',[]))
        limits.extend(e['data'].get('caveats',[]))
    limits.extend(m['field']+': '+m['status'] for m in result['missing'])
    if limits:
        lines+=['','Limits:', '- 일부 자료의 기간·품질·사용 범위에 제한이 있습니다. 누락 자료를 악재나 투자 판단으로 바꾸지 않습니다.',
                '- 항목별 원본 거절 사유는 구조화된 결과의 evidence와 missing에 보존됩니다.']
    return '\n'.join(lines)+'\n'
