# Track B — Accepted Delivery Queue / Retry / Fallback Repair

Create one authoritative persisted AI-delivery lifecycle.

Key requirements:
- analysis reuse cannot erase pending delivery
- accepted delivery must survive process exit/restart
- retry must discover the same pending rows recorded at acceptance
- AI sent cancels fallback eligibility
- rejected candidate generations are never sendable
- fallback after lost pending state is forbidden
- exactly once: AI9/fallback0 or AI0/fallback9, never both

Use generic generation/run/market identity, not ticker/path allowlists.
