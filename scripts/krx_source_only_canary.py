"""Manual bounded source-only canary. No network without --execute."""
import argparse
import asyncio
from datetime import date,datetime,timezone
import json
from pathlib import Path

from app.services.krx_source_only import issue_source_only_parent,collect_source_only


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--dates',nargs='+',type=date.fromisoformat,required=True)
    p.add_argument('--settings-env',type=Path)
    args=p.parse_args()
    if not args.execute:
        print(json.dumps(dict(status='DISABLED_NO_HTTP',dates=[str(d) for d in args.dates],maximum_HTTP=2,retry=0)))
        return
    from app.config import Settings
    settings=Settings(_env_file=args.settings_env) if args.settings_env else Settings()
    now=datetime.now(timezone.utc)
    parent=issue_source_only_parent(root=args.output,run_id='KRX-SOURCE-ONLY-'+now.strftime('%Y%m%dT%H%M%S%fZ'),
        exact_dates=tuple(args.dates),cutoff=now,live_enabled=True)
    result=asyncio.run(collect_source_only(parent,enabled=True,api_key=settings.krx_open_api_key))
    print(json.dumps({k:result.get(k) for k in ('status','physical_HTTP','error','available_at','late_capture','full_market_parent','model_use')}))


if __name__=='__main__':main()
