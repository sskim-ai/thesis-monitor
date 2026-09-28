"""Manual opt-in REV11 sealed acquisition and source replay; never a scheduled job."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from zoneinfo import ZoneInfo

import httpx
from sqlmodel import Session, create_engine

from app.config import Settings
from app.models.security import SecurityMaster
from app.services.fresh_source_run_contract import validate_local_seed
from app.services.sealed_fresh_dispatch import ProviderPlan, SealedDispatcher
from app.services.unified_class_c_owners import project_local_seed
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_acquisition import StockPlan, UNIVERSE, ROLES, make_reads
from app.services.unified_stock_event_input import make_read
from app.services.ohlcv_client import PERIOD_COUNTS, PRICE_STRUCTURE_PERIOD_COUNTS, OHLCV_PROVIDER_REQUEST_LIMIT
from scripts.r9_rev11_sealed_plan import compile_plan
from scripts.r9_rev11_provider_inventory import MAX_KR_REQUEST_PAGES
from scripts.r9_rev11_collect import acquire_all
from scripts.unified_adapter_preflight import current_universe
from scripts.r9_phase_a_gate import code_fingerprints

ROOT = Path(__file__).resolve().parents[1]
PROVIDERS = frozenset({'local','local+openfigi','canonical_local','kiwoom','kiwoom_rest','ohlcv_analyst','sec_edgar',
    'sec_companyfacts','sec_foreign_filing','sec_official_identity','opendart','fred','eia','ecos',
    'krx_night_futures','google_news_rss','naver_news'})
POLICY = UnifiedSourcePolicy(PROVIDERS)
REV10_ROOT_FILE_SHA256 = '8f2508cdb874a089cddc21c0ad50cc485f9d2063388249d5df68fb7d37d59e4c'
REV10_ROOT_RECEIPT_SHA256 = '1fd9656d434312def42bf4d61874f96916223d2c934ac51ce009f1c2447fb44c'


def read(path):
    return json.loads(path.read_bytes())


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def credentials(s):
    return dict(kiwoom=[s.kiwoom_app_key,s.kiwoom_secret_key],sec_edgar=[s.sec_user_agent],opendart=[s.opendart_api_key],
        fred=[s.fred_api_key],eia=[s.eia_api_key],ecos=[s.ecos_api_key],krx_night_futures=[s.krx_open_api_key],
        google_news_rss=['NO_CREDENTIAL_REQUIRED'],naver_news=[s.naver_client_id,s.naver_client_secret])


def exact_rev10_receipt(path):
    raw = path.read_bytes()
    receipt = json.loads(raw)
    if (sha256_bytes(raw) != REV10_ROOT_FILE_SHA256
            or receipt.get('receipt_sha256') != REV10_ROOT_RECEIPT_SHA256
            or digest({k:v for k,v in receipt.items() if k != 'receipt_sha256'}) != REV10_ROOT_RECEIPT_SHA256):
        raise ValueError('rev10_exact_receipt_required')
    return receipt


def static_official_identity():
    path = ROOT/'docs/reports/20260815-phase7-2-6-skhy-official-identity-evidence.json'
    raw = path.read_bytes()
    if sha256_bytes(raw) != 'e1b5ec547e2974b75d9b33869172ff136e34105777f3f37476b310afe8ca3064':
        raise ValueError('official_static_identity_changed')
    return json.loads(raw)


def freeze(args):
    from scripts.sealed_cohort_offline_proof import network_guard
    network_guard()
    if args.output.exists() or git('status','--porcelain'):
        raise ValueError('new_output_clean_exact_commit_required')
    head = git('rev-parse','HEAD')
    validation = read(args.validation)
    if validation.get('status') != 'PASS' or validation.get('head') != head:
        raise ValueError('exact_head_full_validation_required')
    root_receipt = exact_rev10_receipt(args.rev10_receipt)
    args.output.mkdir(mode=0o700,parents=True)
    native_path = args.output/'native-owner.json'
    subprocess.run([sys.executable,'-m','scripts.unified_stock_source_worker','inspect','--owner-root',str(args.native_owner),
        '--output',str(native_path)],check=True,cwd=ROOT)
    native = read(native_path)
    if not native['owner_clean'] or not native['credentials_present'] or not native['live_provider']:
        raise ValueError('native_owner_not_ready')
    s = Settings(_env_file=args.operating/'.env')
    config = credentials(s)
    if not all(all(values) for values in config.values()):
        raise ValueError('configured_credential_missing')
    at = datetime.now(timezone.utc)
    db = args.operating/'data/thesis_monitor.sqlite3'
    universe = current_universe(db,at)
    def connect():
        conn=sqlite3.connect(f'{db.as_uri()}?mode=ro',uri=True)
        conn.execute('PRAGMA query_only=ON')
        return conn
    engine=create_engine('sqlite://',creator=connect)
    counts={}
    for m in UNIVERSE:
        enabled=s.us_price_structure_v3_enabled if m=='us' else s.kr_price_structure_v3_enabled
        configured=PRICE_STRUCTURE_PERIOD_COUNTS if enabled else PERIOD_COUNTS
        counts[m]={role:PERIOD_COUNTS['weekly'] if not adjusted else
            max(min(configured[period],OHLCV_PROVIDER_REQUEST_LIMIT),300 if period=='monthly' else 700)
            for role,(period,adjusted) in ROLES.items()}
    from sqlmodel import select
    with Session(engine) as session:
        records=[r.model_dump(mode='json') for r in session.exec(select(SecurityMaster)).all()
                 if r.ticker in {t for ts in UNIVERSE.values() for t in ts}]
        identities={r['ticker']:r for r in records}
        run='rev11-live-'+at.strftime('%Y%m%dT%H%M%SZ')
        stock=StockPlan(run_id=run,acquisition_id=run+':stock',frozen_at=at,
            instruction_sha=git('rev-parse','fe909d26'),implementation_sha=head,universe_sha256=digest(universe),
            reads=make_reads(universe,identities,at=at,counts=counts),
            **{k:native[k] for k in ('owner_head','owner_files','settings_sha256','request_environment_sha256')})
        for market in UNIVERSE:
            local=project_local_seed(session,market=market,session_key=next(r.latest_completed_session for r in stock.reads if r.market==market),cutoff=at,policy=POLICY)
            validate_local_seed(local)
            durable_json(args.output/f'class-c/local-{market}.json',local,exclusive=True)
    engine.dispose()
    official=static_official_identity()
    durable_json(args.output/'static/official-security-identity.json',official,exclusive=True)
    news=[make_read(security=identities[t],market=m,run_id=run,lookback_days=s.monitor_lookback_days,security_records=records)
          for m,ts in UNIVERSE.items() for t in ts]
    hashes={k:digest(v) for k,v in config.items()}
    result=compile_plan(stock=stock,identities=identities,news_reads=news,config_identities=hashes,
        rev10_receipt=root_receipt,configured_kr_pages=s.kiwoom_rest_max_pages,kr_post_acquisition_completeness_approved=True)
    plan=result.pop('plan')
    admission=plan.admission(rev10_receipt=root_receipt,owners=result['owners'],config_identities=hashes,
        credential_presence={k:all(v) for k,v in config.items()})
    if not admission['live_dispatch_allowed']:
        raise ValueError('final_provider_plan_gap')
    from app.macro.providers.market import MARKET_SYMBOLS
    sessions={m:next(r.latest_completed_session for r in stock.reads if r.market==m) for m in UNIVERSE}
    us=[dict(role='us_market:'+symbol,symbol=symbol,market='us',provider='ohlcv_analyst',response_provider='kiwoom',
        period='daily',adjusted=True,session_date=sessions['us'],max_requests=1,
        params=dict(symbol=symbol,market='US',periods='daily',count=2,include_indicators='false',indicator_limit=0,adjusted='true')) for symbol in MARKET_SYMBOLS]
    frozen=dict(**result,generation_id=run,frozen_at=at.isoformat(),query_kst_date=at.astimezone(ZoneInfo('Asia/Seoul')).date().isoformat(),
        plan=plan.model_dump(mode='json'),stock_plan=stock.model_dump(mode='json'),security_records=records,native_owner=native,
        native_owner_root=str(args.native_owner),us_market_symbols=list(MARKET_SYMBOLS),us_market_reads=us,sessions=sessions,
        kr_local_cap=min(s.kiwoom_rest_max_pages,MAX_KR_REQUEST_PAGES),ohlcv_source_url=s.ohlcv_base_url.rstrip('/')+'/ohlcv',
        config_identities=hashes,settings_sha256=digest(s.model_dump(mode='json')),code=code_fingerprints(),
        validation_sha256=sha256_bytes(args.validation.read_bytes()),rev10_receipt=root_receipt,
        protected_input_hashes={str(p.relative_to(args.output)):sha256_bytes(p.read_bytes()) for p in args.output.rglob('*.json')},
        execution_mode='AD_HOC_LIVE_REQUALIFICATION',model_policy='EXISTING_OFFICIAL_SOL_XHIGH_CONTRACT_NO_FALLBACK',
        production_side_effects=0)
    durable_json(args.output/'r9-rev11-final-provider-plan.json',frozen,exclusive=True)
    durable_json(args.output/'r9-rev11-provider-role-coverage.json',result['role_coverage'],exclusive=True)
    durable_json(args.output/'preflight.json',dict(admission,implementation=head,final_plan_sha256=digest(frozen)),exclusive=True)
    print(json.dumps(dict(status=admission['status'],generation_id=run,descriptors=len(plan.descriptors),provider_calls=0)),flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['freeze','acquire','replay'])
    for name in ('output','operating','native-owner','validation','rev10-receipt'):
        p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    if args.mode=='freeze':
        freeze(args)
        return
    frozen=read(args.output/'r9-rev11-final-provider-plan.json')
    preflight=read(args.output/'preflight.json')
    def guard():
        s=Settings(_env_file=args.operating/'.env')
        if (digest(frozen)!=preflight['final_plan_sha256'] or read(args.output/'r9-rev11-final-provider-plan.json')!=frozen
                or code_fingerprints()!=frozen['code'] or digest(s.model_dump(mode='json'))!=frozen['settings_sha256']
                or git('rev-parse','HEAD')!=preflight['implementation'] or git('status','--porcelain')):
            raise SourceSafetyStop('frozen_code_config_plan_drift')
        for name,sha in frozen['protected_input_hashes'].items():
            if sha256_bytes((args.output/name).read_bytes())!=sha:
                raise SourceSafetyStop('frozen_static_input_drift')
    guard()
    if args.mode=='acquire':
        s=Settings(_env_file=args.operating/'.env')
        config=credentials(s)
        run=SealedDispatcher(plan=ProviderPlan.model_validate(frozen['plan']),root=args.output/'dispatch',
            rev10_receipt=frozen['rev10_receipt'],owners=frozen['owners'],config_identities={k:digest(v) for k,v in config.items()},
            credential_presence={k:all(v) for k,v in config.items()},secrets=tuple(v for values in config.values() for v in values))
        class Guarded(httpx.AsyncHTTPTransport):
            async def handle_async_request(self,request):
                guard()
                return await super().handle_async_request(request)
        asyncio.run(acquire_all(root=args.output,frozen=frozen,settings=s.model_copy(update={'macro_provider_timeout_seconds':600,
            'ohlcv_timeout_seconds':600}),dispatcher=run,inner=Guarded(retries=0),policy=POLICY,guard=guard))
    else:
        from scripts.sealed_cohort_offline_proof import network_guard
        from scripts.r9_rev11_replay import replay_twice
        network_guard()
        outcome=read(args.output/'acquisition-outcome.json')
        try:
            _args,whole,receipt=replay_twice(args.output,frozen,outcome,POLICY)
            durable_json(args.output/'whole-source.json',whole,exclusive=True)
            from scripts.r9_rev11_market_qualification import qualify_markets
            coverage = qualify_markets(whole)
            durable_json(args.output/'market-source-qualification.json',coverage,exclusive=True)
            if any(row['status'] != 'PASS' for row in coverage.values()):
                raise ValueError('SOURCE_PARTIAL:mandatory_market_display_coverage')
            durable_json(args.output/'source-qualification.json',dict(status='PASS',**receipt,
                NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=True, COMPLETE_SOURCE_ADAPTER_QUALIFIED=True),exclusive=True)
        except Exception as exc:
            durable_json(args.output/'source-qualification.json',dict(status='SOURCE_PARTIAL',error_class=type(exc).__name__,reason=str(exc)),exclusive=True)
            raise


if __name__=='__main__':
    main()
