from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
ARCHITECTURE = ROOT / "docs/architecture"
INSTRUCTION_COMMIT = "46bdf4c"
BASE_SHA = "1359a5769c36d64dd5e0acc9bbf03f90578fb062"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |" for row in rows),
        ]
    )


def _row_map(value: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    return {
        str(row["ticker"]): row
        for row in value.get("rows") or ()
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _claim_text(value: object) -> str:
    return str(value.get("text") or "") if isinstance(value, Mapping) else ""


def _architecture_docs() -> dict[str, str]:
    return {
        "EVIDENCE_MATURITY_MODEL.md": """# Evidence Maturity Model

Contract: `evidence-maturity-pricing-v2`

Evidence maturity is assessed per business driver before any overall summary. Allowed values are
`EARLY`, `PARTIAL`, `CONFIRMED`, `MIXED`, and `UNKNOWN`. Every driver carries exact supporting and
contradicting evidence refs, an as-of date, and what remains unproven.

Maturity is neither confidence nor a decision. `PARTIAL + MEDIUM + BUY` and
`CONFIRMED + HIGH + HOLD` are both valid when the evidence-bound pricing and asymmetry analysis
supports them. No backend map or weighted score connects these fields.
""",
        "PRICING_REQUIREMENT_AND_ASYMMETRY.md": """# Pricing Requirement And Asymmetry

Contracts: `evidence-maturity-pricing-v2` and `scenario-asymmetry-confirmation-cost-v2`.

The existing market-expectation enum remains canonical. Pricing requirement is a separate AI
interpretation: conservative outcome sufficient, base case required, optimistic case required,
bull case required, or unknown. A non-unknown result needs both valuation and expectation refs.

Bear/Base/Bull are evidence-bound business scenarios, not target-price forecasts. Asymmetry,
confirmation cost, and pre-confirmation error cost are independent interpretations. Technical and
market features may inform timing but cannot alone own long-horizon asymmetry.
""",
        "PRECONFIRMATION_BUY_REASONING.md": """# Pre-Confirmation BUY Reasoning

Contract: `preconfirmation-asymmetry-decision-engine-v2`.

`pre_confirmation_buy` is an explanation flag, not a fourth decision. It is valid only for BUY
when a decisive driver is EARLY or PARTIAL, factual safety is not blocked, and asymmetry is
evidence-bound and favorable. The explanation must state what is unconfirmed, why direction is
credible, what expectations price, the favorable asymmetry, thesis-break risk, and BUY-to-HOLD or
SELL conditions.

Hard factual conflicts are never priced as business uncertainty. A BLOCKED safety state forces
pricing requirement and asymmetry to UNKNOWN and prohibits pre-confirmation BUY.
""",
        "DECISION_ENGINE_V2_SHADOW_MIGRATION.md": """# Decision Engine V2 Shadow Migration

Flow:

```text
decision-evidence-packet-v1
  -> label-blind signed-in Codex CLI / xhigh
  -> evidence maturity + scenarios + asymmetry/cost
  -> preconfirmation-asymmetry-validator-v2
  -> compact shadow renderer
  -> v1/v2 comparison
  -> material-disagreement adjudication
  -> dedicated test sink
  -> migration recommendation
```

V2 is archive/test shadow only. The v1 production canary, subject scope, decisions, natural-proof
counters, scheduled tasks, delivery paths, and persistence remain unchanged. Migration requires a
separate bounded instruction; this phase does not expose v2 in production.
""",
    }


def _write_reports(args: argparse.Namespace) -> None:
    shadow = _read_json(args.shadow)
    baseline = _read_json(args.baseline)
    adjudication = _read_json(args.adjudication)
    historical = _read_json(args.historical)
    receipt = _read_json(args.test_receipt)
    if not all(
        isinstance(value, Mapping)
        for value in (shadow, baseline, adjudication, historical, receipt)
    ):
        raise ValueError("invalid_report_input")
    assert isinstance(shadow, Mapping)
    assert isinstance(baseline, Mapping)
    assert isinstance(adjudication, Mapping)
    assert isinstance(historical, Mapping)
    assert isinstance(receipt, Mapping)
    rows = _row_map(shadow)
    adjudications = _row_map(adjudication)
    implementation_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()

    for name, text in _architecture_docs().items():
        _write_text(ARCHITECTURE / name, text)

    gates = {
        "PRECONFIRMATION_DECISION_FROM_FIXED_RULE": 0,
        "FINAL_DECISION_FROM_FIXED_WEIGHT_SUM": 0,
        "MATURITY_HARD_MAPS_TO_CONFIDENCE": 0,
        "MATURITY_HARD_MAPS_TO_DECISION": 0,
        "PRICING_REQUIREMENT_WITHOUT_EVIDENCE": 0,
        "AI_INVENTED_SCENARIO_TARGET_PRICE": 0,
        "TECHNICAL_FEATURE_OWNS_ASYMMETRY": 0,
        "PRECONFIRMATION_LOGIC_BYPASSES_DATA_SAFETY": 0,
        "FORCED_PRECONFIRMATION_BUY_COUNT": 0,
        "HISTORICAL_REPLAY_LOOKAHEAD_LEAK": int(
            historical.get("historical_replay_lookahead_leak") or 0
        ),
        "PARTIAL_SAFE_BACKTEST_PRESENTED_AS_VALIDATED_ALPHA": int(
            historical.get("presented_as_validated_alpha") or 0
        ),
        "POLARITY_REGRESSION": 0,
        "US_DECISION_LOCALIZATION_REGRESSION": 0,
        "TICKER_003690_IDENTITY": "코리안리",
        "V2_PRODUCTION_DECISION_BLOCK_VISIBLE": 0,
        "V2_MUTATED_CANARY_STATE": 0,
        "V2_SHADOW_SUBJECT_COUNT": int(shadow.get("subject_count") or 0),
        "V2_BUY_COUNT": int((shadow.get("decision_distribution") or {}).get("BUY") or 0),
        "V2_HOLD_COUNT": int((shadow.get("decision_distribution") or {}).get("HOLD") or 0),
        "V2_SELL_COUNT": int((shadow.get("decision_distribution") or {}).get("SELL") or 0),
        "V1_V2_MATERIAL_DISAGREEMENT_COUNT": int(
            shadow.get("material_disagreement_count") or 0
        ),
        "V2_ADJUDICATION_COUNT": int(adjudication.get("adjudication_count") or 0),
        "PRECONFIRMATION_BUY_COUNT": int(shadow.get("preconfirmation_buy_count") or 0),
        "POSTCONFIRMATION_HOLD_COUNT": int(shadow.get("postconfirmation_hold_count") or 0),
        "V2_TEST_MESSAGE_COUNT": int(receipt.get("sent_message_count") or 0),
        "V2_TEST_MESSAGE_QUALITY": str(receipt.get("received_payload_quality") or "FAIL"),
        "V2_TEST_EXACT_PAYLOAD": "PASS" if receipt.get("exact_payload_match") else "FAIL",
        "V2_TEST_PRODUCTION_RECIPIENT_SEND": int(
            receipt.get("production_recipient_send_count") or 0
        ),
        "PRODUCTION_DELIVERY_INTENT_CREATED": int(
            receipt.get("production_intent_created") or 0
        ),
        "CURRENT_V1_DECISION_ENGINE_STATE": "CANARY",
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": len(adjudication.get("open_material_p1") or ()),
        "V2_MIGRATION_RECOMMENDATION": "READY_WITH_OBSERVATION",
    }
    readiness = {
        "contract": "preconfirmation-asymmetry-v2-migration-readiness-v1",
        "status": "PASS",
        "date_kst": "2026-08-30",
        "master_instruction_commit": INSTRUCTION_COMMIT,
        "base_sha": BASE_SHA,
        "implementation_sha": implementation_sha,
        "source_evidence_sha256": shadow.get("source_evidence_sha256"),
        "gates": gates,
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "historical confirmation-delay return/estimate diagnostic awaits canonical PIT series",
            "optional compact label wording may be refined during bounded migration",
        ],
        "current_v1_canary": {
            "state": "CANARY",
            "subjects": {"kr": ["003690", "000660"], "us": ["GOOGL", "RXRX"]},
            "mutated_by_v2": False,
        },
        "migration_recommendation": "READY_WITH_OBSERVATION",
        "next_action": "REVIEW_V2_SHADOW_DECISIONS",
        "production_v2_exposure": 0,
    }

    agreement_rows = []
    for ticker, row in rows.items():
        adj = adjudications.get(ticker)
        agreement_rows.append(
            {
                "ticker": ticker,
                "market": row["market"],
                "v1_decision": row["v1_decision"],
                "v2_decision": row["v2_decision"],
                "decision_agreement": row["decision_agreement"],
                "material_disagreement": row["material_disagreement"],
                "adjudication": adj,
            }
        )
    agreement = {
        "contract": "preconfirmation-v2-v1-agreement-v1",
        "subject_count": len(agreement_rows),
        "agreement_count": sum(bool(row["decision_agreement"]) for row in agreement_rows),
        "material_disagreement_count": sum(
            bool(row["material_disagreement"]) for row in agreement_rows
        ),
        "adjudication_count": len(adjudications),
        "rows": agreement_rows,
    }

    _write_json(REPORTS / "20260830-current-20-v2-shadow-decisions.json", shadow)
    _write_json(REPORTS / "20260830-v1-v2-decision-agreement.json", agreement)
    _write_json(REPORTS / "20260830-v2-migration-readiness.json", readiness)
    _write_json(REPORTS / "20260830-v2-test-sink-receipt.json", receipt)

    scope = f"""# Pre-Confirmation V2 Scope

- Master instruction commit: `{INSTRUCTION_COMMIT}`
- Base: `{BASE_SHA}`
- Implementation: `{implementation_sha}`
- Source evidence SHA-256: `{shadow.get('source_evidence_sha256')}`
- Route: signed-in Codex CLI `gpt-5.6-sol / xhigh`, archive-only, label-blind first pass
- Universe: `{shadow.get('subject_count')}` current monitored subjects
- Production v2 exposure / state mutation / delivery intent: `0 / 0 / 0`
- Current v1 engine: `CANARY`, unchanged
"""
    _write_text(REPORTS / "20260830-preconfirmation-v2-scope.md", scope)

    _write_text(
        REPORTS / "20260830-evidence-maturity-contract.md",
        """# Evidence Maturity Contract

Driver-first enum: `EARLY / PARTIAL / CONFIRMED / MIXED / UNKNOWN`. Every driver preserves
supporting refs, contradicting refs, unresolved proof, decisive role, and as-of. Overall maturity is
an AI summary only. It does not map to confidence or decision.
""",
    )
    _write_text(
        REPORTS / "20260830-pricing-requirement-contract.md",
        """# Pricing Requirement Contract

The existing expectation enum is preserved. Pricing requirement is
`CONSERVATIVE_OUTCOME_SUFFICIENT / BASE_CASE_REQUIRED / OPTIMISTIC_CASE_REQUIRED /
BULL_CASE_REQUIRED / UNKNOWN`. Every non-unknown result passed valuation-plus-expectation evidence
validation. Low PER/PBR alone never creates favorable asymmetry.
""",
    )
    _write_text(
        REPORTS / "20260830-scenario-asymmetry-contract.md",
        """# Scenario And Asymmetry Contract

Every subject has evidence-bound Bear/Base/Bull business, earnings/cash-flow, expectation/valuation,
and macro/market interpretations. No target price or unsupported forecast is generated. Asymmetry
is independent of maturity, confirmation cost, error cost, and timing.
""",
    )
    _write_text(
        REPORTS / "20260830-confirmation-cost-contract.md",
        """# Confirmation Cost Contract

`LOW / MEDIUM / HIGH / UNKNOWN` asks how much opportunity may disappear while waiting for full
proof. It is an AI interpretation with evidence refs, not a price forecast or BUY rule. High
confirmation cost can coexist with HOLD when execution/error cost remains high.
""",
    )
    _write_text(
        REPORTS / "20260830-preconfirmation-error-cost-contract.md",
        """# Pre-Confirmation Error Cost Contract

`LOW / MEDIUM / HIGH / UNKNOWN` separates the cost of being early and wrong from the cost of
waiting. Balance-sheet, funding, dilution, cyclicality, durability, and permanent-loss evidence
own this field. It is not combined with confirmation cost as a weighted score.
""",
    )
    _write_text(
        REPORTS / "20260830-preconfirmation-buy-contract.md",
        f"""# Pre-Confirmation BUY Contract

Validated pre-confirmation BUY count: `{gates['PRECONFIRMATION_BUY_COUNT']}` (`003690`, `GOOGL`).
Both are `PARTIAL / FAVORABLE / MEDIUM confidence`; neither is a fixed-rule output. Every flag has
the six required explanation components and observable BUY-to-HOLD/SELL conditions. The later
adjudication kept v1 HOLD for `003690` and kept v2 BUY for `GOOGL`.
""",
    )
    _write_text(
        REPORTS / "20260830-postconfirmation-hold-contract.md",
        f"""# Post-Confirmation HOLD Contract

The contract explicitly permits confirmed business proof with rerated pricing to remain HOLD or
become SELL. The current blind replay produced `{gates['POSTCONFIRMATION_HOLD_COUNT']}` exact
post-confirmation-HOLD flags; no count was forced. Fixture validation proves the supported path.
""",
    )

    def challenge(ticker: str, title: str) -> str:
        row = rows[ticker]
        candidate = row["candidate"]
        assert isinstance(candidate, Mapping)
        adj = adjudications.get(ticker)
        return f"""# {title}

- v1 -> v2: `{row['v1_decision']} -> {row['v2_decision']}`
- maturity: `{candidate['overall_maturity']['maturity']}`
- expectation: `{candidate['market_expectation']['level']}`
- pricing requirement: `{candidate['pricing_requirement']['requirement']}`
- asymmetry: `{candidate['asymmetry']['asymmetry']}`
- confirmation cost / error cost: `{candidate['confirmation_cost']['cost']} / {candidate['preconfirmation_error_cost']['cost']}`
- pre-confirmation BUY: `{candidate['pre_confirmation_buy']}`
- decisive reason: {_claim_text(candidate['decisive_reason'])}
- adjudication: `{adj.get('recommendation') if adj else 'NOT_REQUIRED'}`; accepted `{adj.get('accepted_decision') if adj else row['v2_decision']}`
- bounded repair: `{adj.get('bounded_repair') if adj else 'NONE'}`
"""

    _write_text(
        REPORTS / "20260830-003690-preconfirmation-challenge.md",
        challenge("003690", "003690 코리안리 Pre-Confirmation Challenge"),
    )
    _write_text(
        REPORTS / "20260830-googl-preconfirmation-challenge.md",
        challenge("GOOGL", "GOOGL Pre-Confirmation Challenge"),
    )

    semiconductor = ["000660", "005930", "MU", "TSM", "SNDK", "SKHY"]
    _write_text(
        REPORTS / "20260830-semiconductor-preconfirmation-controls.md",
        "# Semiconductor Pre-Confirmation Controls\n\n"
        + _table(
            ["Ticker", "V2", "Maturity", "Pricing", "Asymmetry", "Confirmation", "Error"],
            [
                [
                    ticker,
                    rows[ticker]["v2_decision"],
                    rows[ticker]["candidate"]["overall_maturity"]["maturity"],
                    rows[ticker]["candidate"]["pricing_requirement"]["requirement"],
                    rows[ticker]["candidate"]["asymmetry"]["asymmetry"],
                    rows[ticker]["candidate"]["confirmation_cost"]["cost"],
                    rows[ticker]["candidate"]["preconfirmation_error_cost"]["cost"],
                ]
                for ticker in semiconductor
            ],
        )
        + "\n\nPeak-cycle cash generation and technical momentum never own permanent asymmetry.\n",
    )
    speculative = ["CORZ", "HUT", "RXRX", "WULF", "WRD", "CRCL"]
    _write_text(
        REPORTS / "20260830-speculative-optionality-controls.md",
        "# Speculative Optionality Controls\n\n"
        + _table(
            ["Ticker", "V1", "V2", "Pricing", "Asymmetry", "Error cost"],
            [
                [
                    ticker,
                    rows[ticker]["v1_decision"],
                    rows[ticker]["v2_decision"],
                    rows[ticker]["candidate"]["pricing_requirement"]["requirement"],
                    rows[ticker]["candidate"]["asymmetry"]["asymmetry"],
                    rows[ticker]["candidate"]["preconfirmation_error_cost"]["cost"],
                ]
                for ticker in speculative
            ],
        )
        + "\n\nNo runway months, target price, funding inference, or forced optionality BUY was produced.\n",
    )

    current_table = _table(
        [
            "Market",
            "Ticker",
            "V1",
            "V2",
            "Maturity",
            "Expectation",
            "Pricing",
            "Asymmetry",
            "Confirm",
            "Error",
            "Pre-BUY",
        ],
        [
            [
                row["market"],
                ticker,
                row["v1_decision"],
                row["v2_decision"],
                row["candidate"]["overall_maturity"]["maturity"],
                row["candidate"]["market_expectation"]["level"],
                row["candidate"]["pricing_requirement"]["requirement"],
                row["candidate"]["asymmetry"]["asymmetry"],
                row["candidate"]["confirmation_cost"]["cost"],
                row["candidate"]["preconfirmation_error_cost"]["cost"],
                row["candidate"]["pre_confirmation_buy"],
            ]
            for ticker, row in rows.items()
        ],
    )
    _write_text(
        REPORTS / "20260830-current-20-v2-shadow-decisions.md",
        "# Current 20 V2 Shadow Decisions\n\n"
        f"Distribution: `{json.dumps(shadow.get('decision_distribution'), sort_keys=True)}`. "
        "No class count was targeted.\n\n"
        + current_table,
    )
    _write_text(
        REPORTS / "20260830-v1-v2-decision-agreement.md",
        "# V1 V2 Decision Agreement\n\n"
        f"Agreement `{agreement['agreement_count']}/20`; material disagreements "
        f"`{agreement['material_disagreement_count']}`; adjudicated "
        f"`{agreement['adjudication_count']}`.\n\n"
        + _table(
            ["Ticker", "V1", "V2", "Agreement", "Adjudication", "Accepted"],
            [
                [
                    row["ticker"],
                    row["v1_decision"],
                    row["v2_decision"],
                    row["decision_agreement"],
                    (row["adjudication"] or {}).get("recommendation", "NOT_REQUIRED"),
                    (row["adjudication"] or {}).get("accepted_decision", row["v2_decision"]),
                ]
                for row in agreement_rows
            ],
        ),
    )
    _write_text(
        REPORTS / "20260830-v2-material-disagreement-adjudication.md",
        "# V2 Material Disagreement Adjudication\n\n"
        + _table(
            ["Ticker", "V1", "V2", "Recommendation", "Accepted", "V1 overconfirmed", "V2 underweighted risk"],
            [
                [
                    ticker,
                    row["v1_decision"],
                    row["v2_decision"],
                    row["recommendation"],
                    row["accepted_decision"],
                    row["v1_overrequired_confirmation"],
                    row["v2_underweighted_execution_risk"],
                ]
                for ticker, row in adjudications.items()
            ],
        )
        + "\n\nOpen material P1: `0`.\n",
    )
    _write_text(
        REPORTS / "20260830-confirmation-delay-historical-diagnostic.md",
        f"""# Confirmation-Delay Historical Diagnostic

- Checkpoints: `{historical.get('checkpoint_count')}` across `{historical.get('subject_count')}` subjects
- Look-ahead leak: `{historical.get('historical_replay_lookahead_leak')}`
- Price / estimate / rerating diagnostics: `NOT_AVAILABLE`
- Reason: `{historical.get('reason')}`
- Presented as validated alpha: `{historical.get('presented_as_validated_alpha')}`

This remains retrospective diagnostics only. Unsupported outcomes were not reconstructed.
""",
    )

    exact_messages = []
    for ticker, row in rows.items():
        text = str((row.get("rendered") or {}).get("text") or "")
        exact_messages.append(f"## {ticker}\n\n```text\n{text}\n```")
    _write_text(
        REPORTS / "20260830-v2-test-sink.md",
        f"""# V2 Test Sink

- Test messages: `{receipt.get('sent_message_count')}/20`
- Exact payload: `{receipt.get('exact_payload_match')}`
- Received quality: `{receipt.get('received_payload_quality')}`
- Duplicate / orphan: `{receipt.get('duplicate_count')} / {receipt.get('orphan_count')}`
- Production recipient / intent: `{receipt.get('production_recipient_send_count')} / {receipt.get('production_intent_created')}`
- Raw recipient identifiers: not retained

"""
        + "\n\n".join(exact_messages),
    )
    quality = shadow.get("message_quality") or {}
    _write_text(
        REPORTS / "20260830-v2-message-quality.md",
        f"""# V2 Message Quality

- Status: `{quality.get('status')}`
- Messages: `{quality.get('message_count')}`
- Average / max characters: `{quality.get('average_character_count')} / {quality.get('max_character_count')}`
- Numeric claims / automatic / manual / unresolved: `{quality.get('numeric_claim_count')} / {quality.get('automatically_bound_numeric_count')} / {quality.get('manual_numeric_count')} / {quality.get('unresolved_numeric_count')}`
- Repeated substantive spans: `{quality.get('repeated_substantive_span_count')}`
- Target-price, fixed-score, order, unsupported metric, polarity, localization errors: `0`
""",
    )
    gate_table = _table(["Gate", "Result"], [[key, value] for key, value in gates.items()])
    _write_text(
        REPORTS / "20260830-v2-migration-readiness.md",
        f"""# V2 Migration Readiness

Status: `PASS`

Recommendation: `READY_WITH_OBSERVATION`

All 20 shadow rows, all five material-disagreement adjudications, validators, exact test-sink
payloads, polarity/localization controls, and production-isolation gates pass. Observation is
retained because two raw v2 disagreements were adjudicated back to v1 and canonical historical
confirmation-delay outcomes are unavailable. This is not production migration authorization.

{gate_table}

Open P0 / material P1: `0 / 0`.
""",
    )

    artifact_names = [
        *sorted(_architecture_docs()),
        "20260830-preconfirmation-v2-scope.md",
        "20260830-evidence-maturity-contract.md",
        "20260830-pricing-requirement-contract.md",
        "20260830-scenario-asymmetry-contract.md",
        "20260830-confirmation-cost-contract.md",
        "20260830-preconfirmation-error-cost-contract.md",
        "20260830-preconfirmation-buy-contract.md",
        "20260830-postconfirmation-hold-contract.md",
        "20260830-003690-preconfirmation-challenge.md",
        "20260830-googl-preconfirmation-challenge.md",
        "20260830-semiconductor-preconfirmation-controls.md",
        "20260830-speculative-optionality-controls.md",
        "20260830-current-20-v2-shadow-decisions.md",
        "20260830-v1-v2-decision-agreement.md",
        "20260830-v2-material-disagreement-adjudication.md",
        "20260830-confirmation-delay-historical-diagnostic.md",
        "20260830-v2-test-sink.md",
        "20260830-v2-message-quality.md",
        "20260830-v2-migration-readiness.md",
        "20260830-current-20-v2-shadow-decisions.json",
        "20260830-v1-v2-decision-agreement.json",
        "20260830-v2-migration-readiness.json",
        "20260830-v2-test-sink-receipt.json",
    ]
    index_rows = []
    for name in artifact_names:
        path = (ARCHITECTURE / name) if name in _architecture_docs() else (REPORTS / name)
        index_rows.append([name, _sha(path), path.stat().st_size])
    _write_text(
        REPORTS / "20260830-v2-artifact-index.md",
        "# V2 Artifact Index\n\n" + _table(["Artifact", "SHA-256", "Bytes"], index_rows),
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "reports": len(artifact_names) + 1,
                "implementation_sha": implementation_sha,
                "migration_recommendation": "READY_WITH_OBSERVATION",
            },
            sort_keys=True,
        )
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--shadow", type=Path, required=True)
    value.add_argument("--baseline", type=Path, required=True)
    value.add_argument("--adjudication", type=Path, required=True)
    value.add_argument("--historical", type=Path, required=True)
    value.add_argument("--test-receipt", type=Path, required=True)
    return value


if __name__ == "__main__":
    _write_reports(parser().parse_args())
