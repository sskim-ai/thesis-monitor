"""Explicit manual canary. Without --live this prints a plan, no Settings/API."""
import argparse,asyncio,json,sys,uuid
from datetime import date,datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


async def execute(args):
    import httpx
    from app.services.ohlcv_client import OhlcvClient
    from app.services.dated_technical_research import safe_endpoint,write_new
    client=OhlcvClient()
    endpoint=safe_endpoint(client.settings.ohlcv_base_url)
    headers={};key=client.settings.ohlcv_api_key or client.settings.action_api_key
    if key:headers['X-API-Key']=key
    # Cost-feature discovery only; no provider call or new authentication layer.
    async with httpx.AsyncClient(base_url=endpoint,headers=headers,
            timeout=client.settings.ohlcv_timeout_seconds,follow_redirects=False) as h:
        response=await h.options('/ohlcv')
    if response.status_code!=200 or response.json().get('research_budget_protocol')!='simple-research-budget-v1':
        raise ValueError('service_cost_patch_not_installed_NO_FINANCIAL_GET_SENT')
    root=Path(args.output)
    if root.exists() or any(p.is_symlink() for p in (root,*root.parents)):raise ValueError('new_plain_output_required')
    root.mkdir(parents=True)
    run_id='c21w-'+uuid.uuid4().hex;observed=datetime.now(timezone.utc)
    total=0;instance=None;results=[]
    for market,symbol in [('kr','047810'),('us','CORZ')]:
        output=root/(market+'-'+symbol)
        try:
            _,receipt=await client.fetch_dated_daily_research(symbol=symbol,market=market,
                history_through=args.history_through,observed_at=observed,output=output,
                run_id=run_id,physical_remaining=44-total,count=300)
        except Exception:
            if not (output/'receipt.json').is_file():raise ValueError('request_failed_without_cost_receipt') from None
            receipt=json.loads((output/'receipt.json').read_text())
        count=receipt.get('physical_cumulative_count');current=receipt.get('budget_instance')
        results.append(receipt)
        if (type(count) is not int or not total<=count<=44 or not current
                or (instance is not None and instance!=current)):
            write_new(root/'SUMMARY.json',json.dumps(dict(status='STOP_COST_UNCONFIRMED',results=results),indent=2).encode())
            raise ValueError('cost_count_or_service_restart_STOP')
        total=count;instance=current
        if receipt.get('HTTP_status')!=200:break
    summary=dict(mode='LIVE_MANUAL_NO_SEND',service_GETs=len(results),physical_HTTP=total,
        models=0,DB=0,send=0,READY='0/22',results=results)
    write_new(root/'SUMMARY.json',json.dumps(summary,ensure_ascii=False,indent=2).encode())
    print(json.dumps(dict(service_GETs=len(results),physical_HTTP=total,
        states=[r['status'] for r in results],output=str(root)),ensure_ascii=False))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live',action='store_true',help='Only after explicit user execution approval')
    p.add_argument('--history-through',required=True,type=date.fromisoformat)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    if not args.live:
        print(json.dumps(dict(mode='PLAN_ONLY_NO_HTTP',symbols=['047810','CORZ'],
            market=['kr','us'],daily_count_max=300,indicator_limit=5,GET_max=2,
            physical_max=44,retries=0,model=0,DB=0,send=0)))
        return
    try:asyncio.run(execute(args))
    except Exception as exc:
        detail=str(exc)
        safe=detail if isinstance(exc,ValueError) and detail.replace('_','').isalnum() else type(exc).__name__
        print('CANARY_STOP: '+safe,file=sys.stderr)
        raise SystemExit(1) from None


if __name__=='__main__':main()
