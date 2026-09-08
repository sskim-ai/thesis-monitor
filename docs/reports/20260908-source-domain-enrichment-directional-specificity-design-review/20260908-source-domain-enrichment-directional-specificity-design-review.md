# 2026-09-08 M4 Source Domain Enrichment Design Review

## Result

- Status: `M4_COMPLETE`
- Domains closed: `6/6`
- US support: `2 supported / 4 partial / 0 unsupported`
- KR support: `1 supported / 5 partial / 0 unsupported`
- Packet schema: `6 domains require an additive typed extension`
- Universal source gate added: `0`
- Production readiness: `NOT_READY`
- Next scope: `DECISION_EVIDENCE_PACKET_DOMAIN_EXTENSION_IMPLEMENTATION`

## Decision

The existing free/public stack already has strong canonical OCF and PPE-only cash-flow
lineage for a selective US/foreign subset, safe KR period-comparison machinery, and
partial working-capital/sector evidence. KR cash-flow duration, complete debt/liquidity,
trade receivable/payable, and generic non-operating attribution remain selective or
mapping-incomplete. Missing evidence stays Unknown rather than negative.

Current `DecisionEvidenceRef` cannot safely carry financial period type, currency,
entity/statement/attribution basis, direct-versus-derived status, or comparison and
derivation lineage as one typed object. The smallest next change is therefore an
optional `financial_context` schema extension with validators and no producer or prompt
activation. Existing canonical adapters follow only after that contract is frozen.
Directional specificity, any sector-conditional source gate, model validation, and a
fresh real holdout remain later, separately frozen steps.

## Safety

This was an offline design review. Model and provider calls, production database or
notification mutations, sends, merges, deployments, V2/Night Futures changes, and
scheduler resume actions were all zero. The eight approved monitoring paths remained
paused at both observations.
