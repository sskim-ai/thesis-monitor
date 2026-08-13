# Knowledge Guide

## Problem

Investment safety and chart interpretation need different contracts. Merging them would let chart
examples override accounting, valuation, share-basis, and monitoring safeguards.

## Decision

Maintain two separate canonical Knowledge files and byte-identical Codex mirrors.

| Knowledge | Canonical source | Runtime mirror | Version | SHA-256 |
|---|---|---|---:|---|
| Investment | `investment-thesis-analysis-monitoring-knowledge-v3.md` | `.agents/skills/thesis-monitor-daily-review/references/investment-thesis-analysis-monitoring-knowledge.md` | 3.0 | `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Chart | `stock-chart-value-analysis-knowledge-v1.md` | `.agents/skills/thesis-monitor-daily-review/references/stock-chart-value-analysis-knowledge-v1.md` | 1.0 | `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |

The Custom GPT upload artifact for Investment Knowledge is `docs/custom_gpt_knowledge_ko.md`.

## Why

Investment Knowledge owns business, industry, earnings, valuation, market expectations, macro, risk,
and monitoring safety. Chart Knowledge owns interpretation of already-validated price structure,
OHLCV, supply, and new-observer versus holder context.

## Rejected Alternative

Do not concatenate the chart manual into Investment Knowledge v3, copy either full Knowledge body
into `SKILL.md`, or sync an archived v2/current source into runtime.

## Safety Constraint and Precedence

```text
Backend verified fact/calculation
  > Investment Knowledge v3 safety
  > OHLCV Analyst validated output
  > Chart Knowledge interpretation
  > examples
```

Codex loads routed sections through `knowledge-index.md` and `chart-knowledge-index.md`. Missing packet
facts remain Unknown even when Knowledge says they are analytically useful. Chart fair-value, target,
stop, or indicator examples do not authorize Codex calculations.

## Validation

Runtime manifests are:

- `.agents/skills/thesis-monitor-daily-review/references/knowledge-manifest.json`
- `.agents/skills/thesis-monitor-daily-review/references/chart-knowledge-manifest.json`

Checksum tests must pass before deployment. Investment Knowledge changes require a new Knowledge and
analysis-policy cohort; Chart Knowledge changes require their own version and runtime checksum update.

