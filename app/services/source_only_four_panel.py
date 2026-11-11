"""Small dated four-panel consumer; never current model or send authority."""
from datetime import datetime
import hashlib
from app.services.broker_night_us_consumer import us_broker_night_reference
from app.services.completed_date_aggregate_flows import CompletedDateAggregateFlows


def render_four_panel(*,us,kr,mu,samsung,history_path,cutoff,contract_maturity,flows=None):
    for value in (us,kr):
        if not value.get('NO_SEND') or hashlib.sha256(value['text'].encode()).hexdigest()!=value['text_sha256']:
            raise ValueError('four_panel_original_message_binding')
    night=us_broker_night_reference(history_path=history_path,cutoff=cutoff,contract_maturity=contract_maturity)
    marker='### 야간선물'
    if us['text'].count(marker)!=1:raise ValueError('four_panel_unique_us_night_slot')
    prefix,old_night=us['text'].split(marker)
    footer='관측일이 다른 자료를 같은 날의 변화로 합성하지 않습니다.'
    if old_night.count(footer)!=1:raise ValueError('four_panel_us_footer_binding')
    us_text=prefix+night['text']+'\n'+footer+'\n'
    kr_text=kr['text'];citations=[]
    if flows is not None:
        if type(flows) is not CompletedDateAggregateFlows or flows.session!=kr['session'] or flows.first_system_available_at>cutoff:
            raise ValueError('four_panel_flow_scope_or_cutoff')
        lines=[]
        for row in flows.market_flows:
            actor={'foreign':'외국인','institution':'기관','retail':'개인'}[row.actor]
            line=f'{row.market} {actor} 집계 수급: {row.net_buy_amount/100_000_000:+,.0f}억원 · {flows.session} · KRX/NXT 통합'
            binding=next(b for b in flows.bindings if b['market']==row.market)
            citations.append(dict(text=line,value_krw=row.net_buy_amount,source_ref=row.source_ref,raw_sha256=binding['raw_sha256'],
                base_dt=binding['base_dt'],received_at=binding['received_at'],provider_document=flows.provider_document))
            lines.append(line)
        missing='집계 수급: 완료일 적격 자료 부족'
        if kr_text.count(missing)!=1:raise ValueError('four_panel_unique_kr_flow_slot')
        kr_text=kr_text.replace(missing,'\n'.join(lines))
    text='# 날짜 명시 4패널 · NO-SEND\n\n'+us_text+'\n## MU · 기존 과거 연구\n'+mu+'\n'+kr_text+'\n## 삼성전자 · 기존 과거 연구\n'+samsung
    return dict(text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        order=['US Market','MU','KR Market','005930'],US_night=night,flow_citations=citations,
        source_messages=dict(us_sha256=us['text_sha256'],kr_sha256=kr['text_sha256']),
        market_judgment=None,new_model_judgment=False,full_market_parent=False,NO_SEND=True,Strict_READY='0/22')
