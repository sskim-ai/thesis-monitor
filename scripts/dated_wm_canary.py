"""Manual W/M-only canary; default prints the plan without reading Settings."""
import argparse,asyncio,json,sys,uuid
from datetime import date,datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


async def execute(args):
    import httpx
    from app.services.ohlcv_client import OhlcvClient
    from app.services.dated_technical_research import safe_endpoint,write_new
    from app.services.dated_multiframe_research import fetch_wm,assemble
    root=Path(args.output)
    if root.exists() or any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('new_plain_output_required')
    root.mkdir(parents=True)
    client=OhlcvClient();endpoint=safe_endpoint(client.settings.ohlcv_base_url)
    headers={};key=client.settings.ohlcv_api_key or client.settings.action_api_key
    if key:headers['X-API-Key']=key
    async with httpx.AsyncClient(base_url=endpoint,headers=headers,
            timeout=client.settings.ohlcv_timeout_seconds,follow_redirects=False) as h:
        response=await h.options('/ohlcv')
    feature=response.json() if response.status_code==200 else {}
    if (feature.get('research_budget_protocol')!='simple-research-budget-v1'
            or feature.get('GET_max')!=4 or feature.get('physical_max')!=44
            or not {'weekly','monthly'}<=set(feature.get('periods',[]))):
        raise ValueError('WM_cost_patch_not_installed_NO_FINANCIAL_GET_SENT')
    run_id='c21y-'+uuid.uuid4().hex;observed=datetime.now(timezone.utc)
    total=0;instance=None;receipts=[];combined=[];status='LIVE_WM_TECHNICAL_CONSUMED_NO_SEND'
    try:
        for market,symbol in [('kr','047810'),('us','CORZ')]:
            daily=Path(args.daily_root)/(market+'-'+symbol)
            cutoff=date.fromisoformat(json.loads((daily/'receipt.json').read_text())['actual_historical_as_of'])
            sources={}
            for tf in ['weekly','monthly']:
                output=root/(market+'-'+symbol+'-'+tf)
                try:
                    bars,receipt=await fetch_wm(client,symbol=symbol,market=market,timeframe=tf,
                        observed_at=observed,analysis_cutoff=cutoff,output=output,run_id=run_id,remaining=44-total)
                except Exception:
                    if (output/'receipt.json').is_file():receipts.append(json.loads((output/'receipt.json').read_text()))
                    raise
                receipts.append(receipt)
                count=receipt.get('physical_cumulative_count');current=receipt.get('budget_instance')
                if (type(count) is not int or not total<=count<=44 or not current
                        or (instance is not None and instance!=current)):
                    raise ValueError('cost_count_or_service_restart_STOP')
                receipt['physical_delta']=count-total;total=count;instance=current
                sources[tf]=(bars,receipt)
            combined.append(assemble(client,daily_root=daily,wm_sources=sources,symbol=symbol,
                market=market,observed_at=observed,output=root/(market+'-'+symbol+'-combined')))
    except Exception:
        status='FAILED_NO_RETRY';raise
    finally:
        summary=dict(status=status,service_GETs=len(receipts),physical_HTTP=total,run_id=run_id,
            model=0,DB=0,send=0,READY='0/22',receipts=receipts,combined=combined)
        write_new(root/'SUMMARY.json',json.dumps(summary,ensure_ascii=False,indent=2).encode())
        print(json.dumps(dict(status=status,service_GETs=len(receipts),physical_HTTP=total,output=str(root))))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live',action='store_true')
    p.add_argument('--daily-root',required=True);p.add_argument('--output',required=True)
    args=p.parse_args()
    if not args.live:
        print(json.dumps(dict(mode='PLAN_ONLY_NO_HTTP',symbols=['047810','CORZ'],
            periods={'weekly':700,'monthly':300},GET_max=4,physical_max=44,retries=0,
            daily_refetch=False,model=0,DB=0,send=0)))
        return
    try:asyncio.run(execute(args))
    except Exception as exc:
        detail=str(exc)
        safe=detail if isinstance(exc,ValueError) and detail.replace('_','').isalnum() else type(exc).__name__
        print('WM_CANARY_STOP: '+safe,file=sys.stderr);raise SystemExit(1) from None


if __name__=='__main__':main()
