"""Structured provider-error classification for future B2 shadow controllers only."""
import json


def request_schema_rejection(events: bytes) -> dict[str, object] | None:
    """Inspect error events after durable capture, never model-message text."""
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if not isinstance(event, dict) or event.get('type') not in {'error', 'turn.failed'}:
            continue
        payload = event.get('error') if event['type'] == 'turn.failed' else event
        if not isinstance(payload, dict):
            continue
        message = payload.get('message')
        if isinstance(message, str):
            try:
                payload = json.loads(message)
            except ValueError:
                continue
        if not isinstance(payload, dict):
            continue
        error = payload.get('error')
        if (type(payload.get('status')) is int and payload['status'] == 400
                and isinstance(error, dict) and error.get('type') == 'invalid_request_error'
                and error.get('code') == 'invalid_json_schema'):
            return dict(failure_kind='REQUEST_SCHEMA_PROVIDER_REJECTED', retry_eligible=False,
                        http_status=400, provider_error_code='invalid_json_schema')
    return None
