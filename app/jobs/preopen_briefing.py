"""One market's local, model-free preopen run. The CLI only records NO_SEND."""

from __future__ import annotations

import argparse
import asyncio
import json
from contextlib import ExitStack
from datetime import datetime, timezone
from os.path import abspath
from pathlib import Path

from app.jobs.unified_market_snapshot import _local_lock, read_local_configuration
from app.services.preopen_base import read_preopen_base
from app.services.preopen_briefing import preopen_window, render_briefing
from app.services.preopen_delivery import deliver_preopen, existing_preopen_preview
from app.services.preopen_sources import collect_preopen_sources
from app.services.production_delivery import destination_fingerprint
from app.services.unified_snapshot_contract import digest


LOCAL_PREVIEW_FINGERPRINT = digest({'destination': 'PREOPEN_LOCAL_NO_SEND'})


def utc_now():
    return datetime.now(timezone.utc)


async def run_preopen(
    market, *, run_roots, preview_root, clock=utc_now, collect=False,
    shared_lease_path=None, settings=None, recipient_fingerprint=LOCAL_PREVIEW_FINGERPRINT,
):
    window = preopen_window(market, clock())
    if window is None:
        return {'status': 'NO_RUN', 'reason': 'OUTSIDE_PREOPEN_WINDOW', 'normal_messages_sent': False}

    delivery_scope = dict(
        root=preview_root, market=market, opening_session=window.opening_session,
        recipient_fingerprint=recipient_fingerprint,
    )
    prior = existing_preopen_preview(**delivery_scope)
    if prior is not None:
        return prior

    base = read_preopen_base(run_roots[market], market, window.base_session)
    source_scope = dict(
        opening_session=window.opening_session, rows=base.rows if base.is_current else (),
        cutoff=window.collection_end, run_roots=run_roots, clock=clock,
        base_cutoff=base.cutoff if base.is_current else None, settings=settings,
    )
    sources = None
    source_status = None
    if collect and clock() < window.collection_end:
        with ExitStack() as lease:
            try:
                if shared_lease_path is None:
                    raise FileNotFoundError
                lease.enter_context(_local_lock(shared_lease_path, existing=True))
            except BlockingIOError:
                source_status = 'LOCK_BUSY'
            except OSError:
                source_status = 'UNAVAILABLE'
            else:
                try:
                    # Each request uses the collector's shared deadline. Completed
                    # observations survive a later source's cutoff or timeout.
                    sources = await collect_preopen_sources(market, **source_scope, enable_network=True)
                except TimeoutError:
                    source_status = 'TIMEOUT'
                except (ImportError, OSError, ValueError):
                    source_status = 'UNAVAILABLE'
    elif collect:
        source_status = 'TIMEOUT'

    if sources is None:
        sources = await collect_preopen_sources(market, **source_scope, enable_network=False)
    if source_status:
        sources['coverage'].append({'topic': 'market', 'provider': 'preopen', 'status': source_status})

    generated_at = clock()
    messages = render_briefing(market, window, base, sources, generated_at)
    return await deliver_preopen(
        **delivery_scope, messages=messages, dry_run=True,
        metadata=dict(
            expected_base_session=window.base_session.isoformat(),
            base_session=base.session.isoformat() if base.session else None,
            base_status=base.status, base_generation_id=base.generation_id,
            base_source_generation_id=base.source_generation_id, base_code_commit=base.code_commit,
            subjects=list(base.subjects),
            base_messages_sha256=base.messages_sha256,
            base_cutoff=base.cutoff.isoformat() if base.cutoff else None,
            base_completed_at=base.completed_at.isoformat() if base.completed_at else None,
            generated_at=generated_at.isoformat(), collection_end=window.collection_end.isoformat(),
            delivery_end=window.delivery_end.isoformat(), within_delivery_window=generated_at < window.delivery_end,
            source_coverage=sources['coverage'], source_requests=sources.get('requests', {}),
            market_observations=[{k: v for k, v in row.items() if k != 'source_url'}
                                 for row in sources['market']],
            event_references={ticker: [{k: v for k, v in event.items() if k != 'url'} for event in events]
                              for ticker, events in sources['events'].items()},
            model_calls=0,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--market', choices=('kr', 'us'), required=True)
    parser.add_argument('--kr-run-root', type=Path, required=True)
    parser.add_argument('--us-run-root', type=Path, required=True)
    parser.add_argument('--preview-root', type=Path, required=True)
    parser.add_argument('--at', type=datetime.fromisoformat, help='Offline replay clock with offset')
    parser.add_argument('--collect', action='store_true', help='Enable existing incremental sources')
    parser.add_argument('--configuration', type=Path, help='Existing regular config for this market')
    args = parser.parse_args()
    if args.at and args.at.utcoffset() is None:
        parser.error('--at requires a timezone offset')
    if args.collect and (args.at or args.configuration is None):
        parser.error('--collect requires the local regular --configuration and a current clock')

    run_roots = {'kr': Path(abspath(args.kr_run_root)), 'us': Path(abspath(args.us_run_root))}
    settings = lease = None
    fingerprint = LOCAL_PREVIEW_FINGERPRINT
    clock = (lambda: args.at) if args.at else utc_now
    if args.configuration is not None and preopen_window(args.market, clock()) is not None:
        from app.config import Settings

        config = read_local_configuration(args.configuration, args.market)
        if not config.enabled or config.one_shot or Path(config.run_root) != run_roots[args.market]:
            parser.error('--configuration must be the enabled regular config for the selected run root')
        lease = config.shared_lease_path
        try:
            settings = Settings(_env_file=config.settings_env_file)
        except (OSError, ValueError):
            # An optional provider credential file cannot prevent the base preview.
            lease = None
        if settings and settings.telegram_chat_id and settings.telegram_bot_token:
            fingerprint = destination_fingerprint(recipient=settings.telegram_chat_id, token=settings.telegram_bot_token)
    result = asyncio.run(run_preopen(
        args.market, run_roots=run_roots, preview_root=Path(abspath(args.preview_root)), clock=clock,
        collect=args.collect, shared_lease_path=lease, settings=settings, recipient_fingerprint=fingerprint,
    ))
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == '__main__':
    main()
