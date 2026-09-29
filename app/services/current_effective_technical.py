"""Project the current technical surface; historical safe facts stay audit-only."""
from app.services.ohlcv_feature_engine_service import FeatureStatus
from app.services.unified_snapshot_contract import digest


def project(context, features):
    updates = {}
    for tf, row in features.items():
        original = getattr(context.features, tf)
        by_id = {f.fact_id: f for f in original.facts}
        effective = tuple(by_id[f['fact_id']] for f in row['facts'])
        if [f.model_dump(mode='json') for f in effective] != row['facts']:
            raise ValueError('current_effective_feature_not_owned')
        if (not row['current_role_gate'] or not row['quality']['usable_for_current_reasoning']) and effective:
            raise ValueError('historical_features_in_current_component')
        updates[tf] = original.model_copy(update=dict(facts=effective, safe_feature_count=len(effective),
            status=original.status if effective else FeatureStatus.UNAVAILABLE))
    if all(getattr(context.features, tf) == value for tf, value in updates.items()):
        return context
    packet = context.features.model_copy(update=updates)
    packet = packet.model_copy(update={'packet_sha256': digest(
        {k: v for k, v in packet.model_dump(mode='json').items() if k != 'packet_sha256'})})
    fingerprint = digest(packet.model_dump(mode='json'))
    return context.model_copy(update=dict(features=packet, feature_fingerprint=fingerprint,
        technical_context_id='technical:current-effective:' + digest(dict(
            historical_context_id=context.technical_context_id, feature_fingerprint=fingerprint))))
