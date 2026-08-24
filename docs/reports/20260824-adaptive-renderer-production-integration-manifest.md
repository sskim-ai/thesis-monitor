# Adaptive Renderer Future Production Integration Manifest

This manifest is future-only. No item below is activated by this branch.

Proposed call order: production packet -> Free Analyst -> synthesis validator -> Adaptive Renderer -> numeric/semantic/temporal/final-language/runtime-quality validators -> AI-assisted candidate; any hard failure -> deterministic fallback.

Proposed feature flag: `AI_ANALYST_MODE = CURRENT | VNEXT | FREE_ANALYST_SHADOW | FREE_ANALYST_ADAPTIVE`. Current remains unchanged.

Proposed audit fields: `analysis_mode`, `free_analyst_generated`, `synthesis_validation`, `selected_renderer`, `selection_reasons`, `hard_validation`, `fallback_reason`, `final_delivery_mode`.

Required kill switches isolate Free Analyst generation and adaptive selection independently. Renderer decisions must remain auditable, and internal enum names must not enter user text. Delivery remains isolated until the 2026-08-25 natural review and a separate promotion instruction.

- Production import wiring: `0`
- Public schema change: `0`
- Prompt/packet change: `0`
- Telegram send: `0`
- Schedule change: `0`
- Main promotion: `0`
