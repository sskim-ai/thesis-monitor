"""Receipt-bound all-source materialization, with external network disabled."""
from pathlib import Path

from app.services.unified_full_source_cohort import FreshFullSourceRunSeed, compose_full_source
from app.services.unified_snapshot_contract import digest


from app.services.canonical_source_replay import read  # noqa: E402,F401


from app.services.canonical_source_replay import bound  # noqa: E402,F401


from app.services.canonical_source_replay import require_sealed_body  # noqa: E402,F401


from app.services.canonical_source_replay import stock_inputs  # noqa: E402,F401


from app.services.canonical_source_replay import aggregate  # noqa: E402,F401


from app.services.canonical_source_replay import market_inputs  # noqa: E402,F401


from app.services.canonical_source_replay import publication_inputs  # noqa: E402,F401


def whole_inputs(root, frozen, outcome, policy, completed_close_sources=None):
    from app.services.canonical_source_inputs import build_source_replay_inputs
    from app.services.unified_full_source_cohort import FreshKRSourceRunSeed, FreshUSSourceRunSeed
    seed_type = (FreshUSSourceRunSeed if frozen.get('scope') == 'US14_ONLY' else
                 FreshKRSourceRunSeed if frozen.get('scope') == 'KR8_ONLY' else FreshFullSourceRunSeed)
    def binding_factory(**values):
        return seed_type(proof_mode='AD_HOC_LIVE_SOURCE_PROOF',
            packet_scope='LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION', **values)
    return build_source_replay_inputs(root, frozen, outcome, policy,
        binding_factory=binding_factory, completed_close_sources=completed_close_sources,
        stock_reader=stock_inputs, market_reader=market_inputs, publication_reader=publication_inputs)


def replay_twice(root, frozen, outcome, policy):
    args = whole_inputs(root, frozen, outcome, policy)
    first, second = compose_full_source(**args), compose_full_source(**args)
    if first != second:
        raise ValueError('whole_source_replay_drift')
    from app.services.whole_source_code_owner_registry import replay_identity_receipt
    identity = replay_identity_receipt(Path(__file__).resolve().parents[1], seed=args['seed'],
        metadata=args['composition_metadata'], first=first, second=second)
    from app.services.provider_valuation_calibration_context import calibration_context
    def contexts(whole):
        return {t: calibration_context(s['valuation_view']) for packet in whole['packets'].values()
            for t, s in packet['stocks'].items()}
    first_contexts, second_contexts = contexts(first), contexts(second)
    if first_contexts != second_contexts:
        raise ValueError('valuation_b_context_replay_drift')
    return args, first, dict(first_sha256=digest(first), second_sha256=digest(second), replay_equal=True,
                            code_owner_registry_identity=identity,
                            valuation_b_context_sha256=digest(first_contexts))
