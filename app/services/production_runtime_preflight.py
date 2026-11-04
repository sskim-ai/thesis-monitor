"""Presence-only runtime binding; comments are not environment variables."""
from pathlib import Path

from app.services.unified_runtime_v2 import CONTRACT


def kis_binding(settings, *, required):
    key = settings.kis_app_key
    canonical = settings.kis_app_secret
    legacy = settings.kis_secret_app_key
    if canonical and legacy and canonical.get_secret_value() != legacy.get_secret_value():
        raise ValueError("kis_conflicting_explicit_aliases")
    secret = canonical or legacy
    present = bool(key and key.get_secret_value().strip() and secret and secret.get_secret_value().strip())
    if required and not present:
        raise ValueError("kis_required_active_binding_missing")
    return {"contract": "kis-environment-binding-v1", "present": present,
            "app_key_name": "KIS_APP_KEY" if key else None,
            "app_secret_name": "KIS_APP_SECRET" if canonical else "KIS_SECRET_APP_KEY" if legacy else None,
            "secret_values_exported": False, "comments_are_active": False}


def runtime_preflight(settings, policy):
    if (not settings.unified_snapshot_enabled or settings.unified_snapshot_adapter_version != "production-v1"
            or settings.unified_snapshot_runtime_contract != CONTRACT):
        raise ValueError("production_runtime_disabled_or_version_mismatch")
    # Pydantic model_copy is intentionally not trusted as validation.
    type(policy).model_validate(policy.model_dump(mode="json"))
    destination = settings.unified_snapshot_debug_destination
    if not destination or not Path(destination).is_dir() or Path(destination).is_symlink():
        raise ValueError("configured_debug_destination_unavailable")
    kis = kis_binding(settings, required=policy.market == "kr")
    if not settings.notification_dry_run:
        if (not settings.unified_snapshot_live_delivery_authorized
                or settings.notification_recipient_class != "production"
                or not settings.telegram_bot_token or not settings.telegram_chat_id
                or settings.telegram_chat_id == settings.telegram_test_chat_id):
            raise ValueError("production_delivery_not_explicitly_authorized")
    return {"status": "PASS", "kis": kis, "runtime_contract": CONTRACT,
            "delivery_mode": "DRY_RUN" if settings.notification_dry_run else "LIVE_AUTHORIZED"}
