"""Manual vNext-only CLI. Importing this module does not open a DB or Settings."""
import argparse
import json

from app.services.vnext_runtime import RuntimeConfig, VNextRuntime


def run_reviewed_product(config, ticker, **kwargs):
    """Backend-only manual entry point; JSON cannot supply the review callback."""
    return VNextRuntime(config).research_product(ticker, **kwargs)


def run_no_send_slot(config, **kwargs):
    """Explicit isolated backend capability; no scheduler or JSON Owner input."""
    from app.services.vnext_no_send_runner import run_slot
    return run_slot(config, **kwargs)


def run_manual_research_canary(config, **kwargs):
    """Explicit trusted backend only; no CLI scheduler or public job loader."""
    from app.services.vnext_no_send_runner import run_manual_research
    return run_manual_research(config, **kwargs)


def run_daily_research(config, *, bridge, identity, manual_scope=None,
                       allow_capture=False, allow_primary=False, expected_packet_sha256=None,
                       execution_authority=None, unified_review=None, unified_enabled=False, **kwargs):
    """Join original source, cold consumer and Primary inside the existing host.

    The live bridge is a backend capability. This does not install a schedule,
    grant HTTP/model permission or deserialize public JSON into an Owner.
    """
    from app.services.vnext_daily_bridge import DailyResearchBridge
    if not isinstance(bridge, DailyResearchBridge):
        raise ValueError('daily_bridge_backend_required')
    if kwargs.get('initialization_recovery') is not None and (
            manual_scope is None or allow_capture or not allow_primary):
        raise ValueError('daily_recovery_model_only_no_capture')
    if identity['security'] != bridge.registration['security']['canonical_security_id']:
        raise ValueError('daily_bridge_host_security')
    def operation(controller, gate):
        if (gate['session'] != bridge.session or
                gate['market'] != bridge.registration['security']['country'].lower() or
                manual_scope is not None and (gate['prior_session'] != bridge.prior_session or
                    gate['plan_sha256'] != bridge.request['plan_sha256'])):
            raise ValueError('daily_bridge_host_session_or_plan')
        result = bridge.execute(controller, allow_capture=allow_capture, allow_primary=allow_primary,
            execution_authority=execution_authority, unified_review=unified_review, unified_enabled=unified_enabled)
        if (expected_packet_sha256 is not None and result.get('packet_sha256') is not None
                and result['packet_sha256'] != expected_packet_sha256):
            raise ValueError('daily_bridge_frozen_packet_drift')
        return dict(result, input_identity=identity, send=False)
    if manual_scope is not None:
        return run_manual_research_canary(config, scope=manual_scope, identity=identity,
            operation=operation, **kwargs)
    return run_no_send_slot(config, identity=identity, operation=operation, **kwargs)


def run_unified_no_send(controller, *, packet, owner, mode, output_context, enabled=False):
    """Same callable for dated replay and daily; no model, capture or schedule."""
    from app.services.vnext_unified_dispatch import consume
    return consume(controller,packet=packet,owner=owner,mode=mode,
                   output_context=output_context,enabled=enabled)


def run_daily_no_send(config, **kwargs):
    """Operator entrypoint, default OFF; never installs a scheduler or sender."""
    from app.services.vnext_daily_entrypoint import run_daily
    return run_daily(config, **kwargs)


def run_manual_source_canary(config, *, source_owner_factory, registry, identity, **kwargs):
    """Trusted producer -> original daily Owner -> original isolated controller.

    Factory executes only inside the admitted supervised child. It must enforce
    its separately frozen transport budget and return a live original Owner.
    This source-only entry never calls a model or fabricates an economic output.
    """
    if not callable(source_owner_factory):
        raise ValueError('backend_source_producer_required')
    from app.services.vnext_daily_research import UseRegistry
    if not isinstance(registry, UseRegistry):
        raise ValueError('live_use_registry_required_before_source')
    def operation(controller, gate):
        owner = source_owner_factory(gate)
        from app.services.vnext_incremental_ingestion import DailyDeltaOwner
        if not isinstance(owner, DailyDeltaOwner):
            raise ValueError('original_delta_and_use_owners_required')
        batch = owner.batch()
        registrations = list(batch['registrations'].values())
        if (gate['kind'] != 'EXISTING_SUBJECT_SUCCESSOR' or len(registrations) != 1
                or registrations[0]['security']['canonical_security_id'] != identity['security']
                or registrations[0]['security']['country'].lower() != gate['market']
                or any(o['payload']['calendar']['session'] != gate['session'] for o in batch['observations'])):
            raise ValueError('manual_source_owner_scope_mismatch')
        ticker = registrations[0]['security']['ticker']
        previous = [o['payload']['calendar']['session'] for o in owner.prior.batch()['observations']
                    if o['ticker'] == ticker and o['field'] in ('completed_close','ohlcv.adjusted_daily')]
        if not previous or max(previous) != gate['prior_session']:
            raise ValueError('manual_source_prior_scope_mismatch')
        result = controller.source(owner=owner, registry=registry)
        return dict(result, send=False, input_identity=identity,
                    primary_new_verified=False, source_only=True)
    return run_manual_research_canary(config, identity=identity, operation=operation, **kwargs)


def main(argv=None):
    p = argparse.ArgumentParser(description='Opt-in no-send vNext research worker')
    p.add_argument('action', choices=('health', 'schema', 'registration', 'coverage', 'sources', 'shadow', 'draft', 'valuation', 'composite', 'composite-draft', 'no-send-observe'))
    p.add_argument('--market', choices=('kr', 'us'))
    p.add_argument('--watermark')
    p.add_argument('--run')
    p.add_argument('--ticker')
    p.add_argument('--market-type')
    p.add_argument('--job-id')
    p.add_argument('--as-of')
    p.add_argument('--runs', nargs='+')
    p.add_argument('--historical-price', nargs=4, metavar=('ARCHIVE','ARCHIVE_SHA256','MEMBER','MEMBER_SHA256'),
                   help='Reviewed historical archive pins; reference only, no Owner issuance')
    p.add_argument('--component-reference',nargs=2,metavar=('MANIFEST','SHA256'),
                   help='Pinned original accounting replay; research only, no Owner issuance')
    args = p.parse_args(argv)
    if args.action == 'no-send-observe':
        if not args.market or not args.watermark:
            p.error('no-send-observe requires --market and --watermark')
        from datetime import datetime, timezone
        from app.services.vnext_no_send_controller import calendar_gate
        result = calendar_gate(args.market, datetime.now(timezone.utc), watermark=args.watermark)
        result.update(runtime='OFF_NOT_TESTED', provider_HTTP=0, model_calls=0,
                      DB_opened=False, backend_capability_required=True)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return
    if args.historical_price and args.action not in ('composite','composite-draft'):
        p.error('historical price only belongs to read-only composite')
    if args.component_reference and args.action not in ('composite','composite-draft'):
        p.error('component reference only belongs to read-only composite')
    runtime = VNextRuntime(RuntimeConfig.from_environment())
    if args.action in ('health', 'schema'):
        result = runtime.state()
    elif args.action == 'registration':
        result = runtime.registration()
    elif args.action == 'coverage':
        result = runtime.coverage()
    elif args.action == 'sources':
        result = runtime.verify_sources(args.run)
    elif args.action == 'shadow':
        result = runtime.shadow(args.run, args.ticker)
    elif args.action == 'draft':
        result = runtime.draft(args.run, args.ticker, job_id=args.job_id)
    elif args.action in ('composite', 'composite-draft'):
        if args.job_id or args.run or not args.as_of or not args.ticker:
            p.error('composite requires --ticker and --as-of; no write job or single --run')
        method = runtime.composite if args.action == 'composite' else runtime.composite_draft
        kwargs = {}
        from app.services.vnext_reference_bundle import load_family
        if args.historical_price:
            from app.services.vnext_historical_price_reference import load_pinned_archive
            kwargs['price_reference'] = load_family(load_pinned_archive, *args.historical_price)
        if args.component_reference:
            from app.services.vnext_component_reference import load_reference
            kwargs['component_reference'] = load_family(load_reference, *args.component_reference)
        result = method(args.ticker, as_of=args.as_of, run_ids=args.runs, **kwargs)
    else:
        result = runtime.valuation(args.run, args.ticker, args.market_type, job_id=args.job_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
