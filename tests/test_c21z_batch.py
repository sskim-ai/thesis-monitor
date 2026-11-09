import importlib.util,json
from datetime import date
from pathlib import Path
from app.services.dated_multiframe_research import select_historical,period_end

ROOT=Path('/Users/sskim/Documents/Codex/2026-07-04/the')


def test_original_CORZ_mismatch_keeps_last_week_excluded():
    w=json.loads(Path('/private/tmp/c21y-wm-canary-20261109/us-CORZ-weekly/response.body').read_text())['periods']['weekly']
    d=json.loads(Path('/private/tmp/c21x-daily-canary-20261109/us-CORZ/response.body').read_text())['periods']['daily']
    assert w[-1]['date']=='2026-11-02' and w[-1]['close']==11.70
    assert d[-1]['date']=='2026-11-06' and d[-1]['close']==11.76
    assert period_end(date.fromisoformat(w[-1]['date']),'weekly','us')==date(2026,11,6)
    used,excluded,_=select_historical(w,timeframe='weekly',market='us',cutoff=date(2026,11,5))
    assert used[-1]['date']=='2026-10-26' and excluded[-1]['original_label']=='2026-11-02'
    assert w[-1]['close']==11.70


def test_plan_order_budget_reuse_and_calendar_cache():
    path=Path(__file__).resolve().parents[1]/'scripts/native_dwm_batch.py'
    spec=importlib.util.spec_from_file_location('batch',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    plan=module.prepare_plan(ROOT/'maintenance/20261109-c21y/REMAINING_BATCH_PLAN.json')
    assert [b['ticker'] for b in plan[:4]]==['005930','000660','MU','TSM']
    assert len(plan)==20 and sum(b['physical_max'] for b in plan)==655
    assert all(b['ticker'] not in {'047810','CORZ'} for b in plan)
    assert period_end(date(2003,10,1),'monthly','us')==date(2003,10,31)
    assert period_end(date(2003,10,1),'monthly','us')==date(2003,10,31)


def test_actual_TSM_bad_latest_bar_rejected_without_price_repair():
    from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows
    p=Path('/private/tmp/c21z-native22-20261109/us-TSM/daily/response.body')
    bars=json.loads(p.read_text())['periods']['daily']
    inspection=inspect_normalized_ohlcv_rows(bars,timeframe='daily')
    assert not inspection.valid and inspection.invalid_row_count==1
    assert inspection.issues[0].violation=='HIGH_LT_CLOSE'
    assert bars[-1]['date']=='2026-11-06' and bars[-1]['high']==380.72 and bars[-1]['close']==383.5


def test_source_failure_continuation_keeps_failed_roles_and_global_usage():
    path=Path(__file__).resolve().parents[1]/'scripts/native_dwm_batch.py'
    spec=importlib.util.spec_from_file_location('continuation',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    ledger,roles=m.read_history('/private/tmp/c21z-native22-continuation-20261109')
    assert ledger['GETs']==11 and ledger['physical_HTTP']==74 and len(roles)==11
    assert ('TSM','daily') in roles and ('CPNG','daily') in roles
    plan=m.prepare_plan(ROOT/'maintenance/20261109-c21y/REMAINING_BATCH_PLAN.json')
    pending=[(b['ticker'],r['timeframe']) for b in plan for r in b['requests'] if (b['ticker'],r['timeframe']) not in roles]
    assert len(pending)==49 and len(set(pending))==49 and not set(pending)&set(roles)
