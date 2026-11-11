"""Read broker history as an optional, explicitly dated US-message section."""
from pathlib import Path
from app.services.broker_night_seed_history import load_history,render_broker_history


def us_broker_night_reference(*,cutoff,contract_maturity,history_path=None,instrument_root='KOSPI200'):
    if history_path is None:
        from app.config import get_settings
        history_path=Path(get_settings().data_dir)/'market/krx-night-history/broker-seed-v1/history.json'
    try:
        history=load_history(history_path)
        value=render_broker_history(history,instrument_root=instrument_root,contract_maturity=contract_maturity,cutoff=cutoff)
    except (OSError,ValueError) as exc:
        return dict(text='### 한국 야간선물\n일봉: 자료 부족\n주봉: 자료 부족\n월봉: 자료 부족\n',
            selected=[],available_at_cutoff=False,current_directional=False,source_kind='USER_BROKER_SCREENSHOT',
            reference_fact_ids=[],NO_SEND=True,diagnostic=type(exc).__name__,optional_gap=True)
    heading='### 한국 야간선물 · 과거 차트 참고' if value['selected'] else '### 한국 야간선물'
    return dict(value,text=heading+'\n\n'+value['text'],source_kind='USER_BROKER_SCREENSHOT',
        available_at_cutoff=bool(value['selected']),current_directional=False,
        reference_fact_ids=['broker-chart:'+b['revision_sha256'] for b in value['selected']])
