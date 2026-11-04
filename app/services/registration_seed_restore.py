"""Restore operator definitions through original models and onboarding, not eligibility."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

from sqlmodel import Session, select
from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.schemas.watchlist import WatchlistItemCreate
from app.services.watchlist_service import add_watchlist_item

TABLES=('watchlistitem','securitymaster','company','investmentthesis')
IDENTITY=('ticker','canonical_company_id','canonical_security_id','exchange','country')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()


def restore_operator_registration(session: Session, primary, comparison, *, expected):
    if set(primary)!=set(TABLES) or set(comparison)!=set(TABLES):
        raise ValueError('registration_seed_four_tables_required')
    if not expected or len(set(expected))!=len(expected):
        raise ValueError('registration_seed_exact_cohort_required')
    if any(session.exec(select(model).limit(1)).first() is not None
           for model in (Company,SecurityMaster,InvestmentThesis,WatchlistItem)):
        raise ValueError('registration_seed_empty_destination_required')
    indices={}
    for label,seed in (('primary',primary),('comparison',comparison)):
        indices[label]={}
        for table in TABLES[:3]:
            rows=seed[table]
            if len({r['ticker'] for r in rows})!=len(rows):
                raise ValueError('registration_seed_duplicate_identity')
            indices[label][table]={r['ticker']:r for r in rows}
    target=set(expected)
    if set(indices['primary']['watchlistitem'])!=target:
        raise ValueError('registration_primary_cohort_mismatch')
    comparison_report={t:dict(extra_subjects=sorted(set(indices['comparison'][t])-target),
        missing_subjects=sorted(target-set(indices['comparison'][t]))) for t in TABLES[:3]}
    result=[]
    for ticker in expected:
        first={t:indices['primary'][t].get(ticker) for t in TABLES[:3]}
        second=indices['comparison']['securitymaster'].get(ticker)
        if not all(first.values()) or second is None:
            result.append(dict(ticker=ticker,status='REGISTRATION_BLOCKED',reason='SEED_IDENTITY_MISSING'));continue
        security=first['securitymaster']
        conflict=[key for key in IDENTITY if security.get(key)!=second.get(key)]
        if conflict:
            result.append(dict(ticker=ticker,status='REGISTRATION_BLOCKED',reason='SEED_IDENTITY_CONFLICT',fields=conflict));continue
        theses=[r for r in primary['investmentthesis'] if r['ticker']==ticker]
        if (not any(r['status']=='active' and r['core_thesis'].strip() for r in theses)
                or len({r['version'] for r in theses})!=len(theses)):
            result.append(dict(ticker=ticker,status='REGISTRATION_BLOCKED',reason='USER_THESIS_MISSING_OR_DUPLICATE'));continue
        if first['watchlistitem']['exchange']!=security['exchange']:
            result.append(dict(ticker=ticker,status='REGISTRATION_BLOCKED',reason='EXCHANGE_BINDING_CONFLICT'));continue
        # Preserve user definitions and identity timestamps. No old observations,
        # readiness receipts, assessments, activation dates or eligibility flags.
        company={k:first['company'][k] for k in ('id','ticker','company_name','exchange','ir_url','filings_url','created_at')}
        security_fields={k:v for k,v in security.items() if k in SecurityMaster.model_fields}
        security_fields['identity_quality']='partial'
        session.add(Company.model_validate(company))
        session.add(SecurityMaster.model_validate(security_fields))
        for thesis in theses:session.add(InvestmentThesis.model_validate(thesis))
        watch=first['watchlistitem']
        item=WatchlistItem(id=watch['id'],ticker=ticker,company_name=watch['company_name'],
            exchange=watch['exchange'],notes=watch.get('notes'),active=False,monitoring_requested=True,
            issuer_type=watch.get('issuer_type'),ordinary_share_identifier=watch.get('ordinary_share_identifier'),
            adr_ratio=watch.get('adr_ratio'),adr_currency=watch.get('adr_currency'),underlying_currency=watch.get('underlying_currency'),
            production_eligible=False,onboarding_state='PENDING_ONBOARDING',
            registration_requested_at=datetime.now(timezone.utc))
        session.add(item);session.flush()
        item=add_watchlist_item(session,WatchlistItemCreate(ticker=ticker,
            company_name=watch['company_name'],exchange=watch['exchange'],notes=watch.get('notes'),active=True))
        if item.production_eligible or item.active or item.activated_at or item.first_eligible_session:
            raise ValueError('registration_seed_unexpected_live_promotion')
        restored_security=session.get(SecurityMaster,security['id'])
        if any(getattr(restored_security,key)!=security[key] for key in IDENTITY):
            raise ValueError('registration_seed_business_identity_changed')
        restored_security.updated_at=SecurityMaster.model_validate(security_fields).updated_at
        session.add(restored_security);session.commit()
        result.append(dict(ticker=ticker,status='REGISTERED_PENDING_ONBOARDING',
            original_registration_id=watch['id'],new_registration_id=item.id,
            canonical_security_id=security['canonical_security_id'],exchange=security['exchange'],
            thesis_versions=len(theses),user_definition_sha256=digest(theses),
            registration_record_sha256=digest(watch),production_eligible=False,
            onboarding_failure_stage=item.onboarding_failure_stage))
    return dict(contract='operator-registration-restore-v1',records=result,
        comparison=comparison_report,counts=dict(Counter(r['status'] for r in result)),
        old_eligibility_imported=False,old_source_or_judgments_imported=False,current_source_authority=False)
