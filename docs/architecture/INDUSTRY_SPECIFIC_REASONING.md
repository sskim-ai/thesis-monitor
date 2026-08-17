# Industry-Specific Reasoning

Contract: `industry-specific-reasoning-v1`

## Purpose

Industry reasoning translates verified company Facts into an industry-appropriate decision frame.
It does not add data, calculate metrics, replace the renderer, or turn a market theme into company
evidence.

```text
Verified Fact -> Structured Industry Route -> Evidence-Bounded Causal Chain
              -> Valuation Boundary -> Observer / Holder -> Next Confirmation
```

## Responsibility Boundary

- Backend owns Facts, calculations, lineage, taxonomy, and exact numeric values.
- Investment Knowledge v3 supplies the analytical framework and remains unchanged.
- Codex selects supported relationships and identifies missing drivers.
- The validator rejects framework mismatch, missing causal links, and unsupported valuation claims.
- The renderer assembles validated text without calculating or repairing meaning.

## Routing

Primary routing follows this order:

1. verified `knowledge_routing.industry_key` and normalized company taxonomy;
2. verified company industry or sector when the structured route is `general`;
3. verified business units or revenue sources when a future canonical contract supplies them;
4. `general` fallback.

Thesis prose and market themes never select the primary framework. They may appear only as
secondary context. Confidence is `high` for an exact structured classification, `medium` for a
verified broad classification with incomplete business mix, and `low` for general fallback.

## Supported Frameworks

| Framework | Primary causal focus | Valuation boundary |
|---|---|---|
| `memory` | pricing/mix, margin, inventory, CAPEX, FCF | normalized earnings and PBR; low trailing PER alone is insufficient |
| `semiconductor` | product/segment mix, margin, CAPEX, cash conversion | company multiple remains company-level without segment facts |
| `semiconductor_foundry` | utilization, node mix/pricing, packaging, CAPEX, FCF | utilization, margin, cash conversion, ROIC |
| `insurance` | underwriting/investment earnings, ROE, capital | PBR needs ROE, capital, and underwriting quality |
| `transport_logistics` | volume/rate/cost/mix, margin, working capital, OCF | mid-cycle margin and cash conversion |
| `steel_materials` | spread, raw material, utilization, inventory, normalized earnings | PBR and earnings multiple must be read with the cycle |
| `automotive` | volume, ASP, mix, incentives, margin, CAPEX, FCF | margin, FCF, and execution option value |
| `biotech` | cash burn/runway, milestones, probability, financing, dilution | risk-adjusted pipeline; PER is not forced |
| `hpc_crypto_infrastructure` | contracted power, cost, utilization, customer, CAPEX/funding | cash flow, financing, and dilution |
| `epc_construction` | orders/backlog, revenue recognition, project margin, working capital | order value is not earnings |
| `saas` | ARR, NRR, gross margin, leverage, FCF | growth quality and FCF only when those metrics exist |
| `holding_company` | subsidiary value, ownership, net debt, allocation, discount | NAV/SOTP evidence required |
| `general` | revenue, margin, cash flow, balance sheet, valuation/risk | specialized metrics are not synthesized |

## Reasoning Plan

Each stock receives an internal plan with primary and secondary frameworks, confidence, route
evidence, available and selected Fact families, missing drivers, causal chain, valuation framework,
observer focus, holder focus, and next confirmation. This metadata is audit-only and is not shown in
Telegram.

Visible causal claims may reference only approved `supporting_fact_ids`. A verified causal claim
must contain every required middle Fact family. A missing-driver Unknown is valid only when that
driver is actually absent. Short Fact markers use token boundaries, so unrelated paths cannot be
mistaken for ARR, ROE, or PE.

## Guardrails

- Missing middle evidence cannot support a downstream confirmation.
- Memory low trailing PER alone cannot mean cheap.
- Insurance low PBR without ROE or capital cannot mean cheap.
- Biotech is not forced into PER-based valuation.
- EPC orders do not imply margin improvement without project-margin evidence.
- Hyperscaler CAPEX does not confirm a company's revenue or order.
- Insurance cannot use SaaS ARR/NRR reasoning.
- A generic “additional confirmation is needed” Unknown is a quality failure.
- Denied financial families, security identity, economic scope, and typed valuation rules remain
  upstream hard boundaries.

## Archive Evidence

Phase 8.5 uses immutable packets and committed artifacts only. Preview generation performs no
provider call, Telegram send, Pilot update, or production database/archive mutation. It preserves
the original evaluation context and reports specialized-routing gaps rather than inferring a more
specific industry from thesis prose.
