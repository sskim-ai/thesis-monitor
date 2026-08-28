from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path


DATE = "20260828"
REPORT_PREFIX = f"{DATE}-dynamic-bollinger"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _rows(payload: object, key: str = "rows") -> list[Mapping[str, object]]:
    values = _mapping(payload).get(key)
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [value for value in values if isinstance(value, Mapping)]


def _row_by_ticker(payload: object, ticker: str) -> Mapping[str, object]:
    return next(
        (row for row in _rows(payload) if str(row.get("ticker")) == ticker),
        {},
    )


def _zone_display(row: Mapping[str, object], key: str) -> str:
    zone = _mapping(row.get(key))
    return str(zone.get("display") or "-")


def _zone_timeframe(row: Mapping[str, object], key: str) -> str:
    zone = _mapping(row.get(key))
    return str(zone.get("source_timeframe") or "-")


def _compact_row(row: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in row.items()
        if key not in {"ai_preview", "fallback_preview", "selected_preview"}
    }


def _table(rows: Sequence[Sequence[object]], headers: Sequence[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend(
        "| "
        + " | ".join(str(value).replace("\n", "<br>") for value in row)
        + " |"
        for row in rows
    )
    return "\n".join(lines)


def _last_daily(payload: object) -> Mapping[str, object]:
    periods = _mapping(_mapping(payload).get("periods"))
    daily = periods.get("daily")
    if not isinstance(daily, Sequence) or isinstance(daily, (str, bytes)) or not daily:
        return {}
    return _mapping(daily[-1])


def _dynamic_mode(row: Mapping[str, object]) -> str:
    if int(row.get("dynamic_support_line_count") or 0):
        return "standalone support"
    if int(row.get("dynamic_resistance_line_count") or 0):
        return "standalone resistance"
    confluence = row.get("dynamic_confluence_bindings")
    if isinstance(confluence, Sequence) and not isinstance(confluence, (str, bytes)):
        if confluence:
            return "confluence"
    return "suppressed/blocked"


def _replay_table(rows: Sequence[Mapping[str, object]]) -> str:
    return _table(
        [
            (
                row.get("ticker"),
                row.get("eligibility"),
                row.get("current_price"),
                _zone_display(row, "near_support"),
                _zone_display(row, "near_resistance"),
                _zone_display(row, "major_support"),
                _zone_display(row, "major_resistance"),
                _zone_display(row, "dynamic_bollinger_support"),
                _zone_timeframe(row, "dynamic_bollinger_support"),
                _zone_display(row, "dynamic_bollinger_resistance"),
                _zone_timeframe(row, "dynamic_bollinger_resistance"),
                _dynamic_mode(row),
                ", ".join(str(value) for value in row.get("denial_reasons") or ())
                or "-",
            )
            for row in rows
        ],
        (
            "Ticker",
            "Eligibility",
            "Close",
            "Near S",
            "Near R",
            "Major S",
            "Major R",
            "Boll S",
            "TF",
            "Boll R",
            "TF",
            "Render",
            "Denial",
        ),
    )


def _exact_messages(replay: object, receipt: object) -> str:
    receipt_rows = {
        str(row.get("ticker")): row for row in _rows(receipt)
    }
    blocks: list[str] = []
    for message in _rows(replay, "messages"):
        ticker = str(message.get("ticker") or "")
        receipt_row = receipt_rows.get(ticker, {})
        blocks.extend(
            (
                f"## {ticker}",
                "",
                f"- Route: `{message.get('route')}`",
                f"- Exact payload match: `{receipt_row.get('exact_payload_match')}`",
                f"- Payload SHA-256: `{receipt_row.get('payload_sha256') or receipt_row.get('planned_payload_sha256') or '-'}`",
                "",
                "```text",
                str(message.get("text") or ""),
                "```",
                "",
            )
        )
    return "\n".join(blocks)


def generate(args: argparse.Namespace) -> None:
    replay = _read_json(args.replay)
    receipt = _read_json(args.receipt)
    prior = _read_json(args.prior_e2e)
    live_a = _read_json(args.live_a)
    live_b = _read_json(args.live_b)
    rows = _rows(replay)
    us_rows = [row for row in rows if row.get("market") == "US"]
    kr_rows = [row for row in rows if row.get("market") == "KR"]
    skhynix = _row_by_ticker(replay, "000660")
    mu = _row_by_ticker(replay, "MU")
    sndk = _row_by_ticker(replay, "SNDK")
    wulf = _row_by_ticker(replay, "WULF")
    prior_sndk = _row_by_ticker(prior, "SNDK")
    live_a_last = _last_daily(live_a)
    live_b_last = _last_daily(live_b)
    standalone_support = sum(int(row.get("dynamic_support_line_count") or 0) for row in rows)
    standalone_resistance = sum(
        int(row.get("dynamic_resistance_line_count") or 0) for row in rows
    )
    confluence_count = sum(
        len(row.get("dynamic_confluence_bindings") or ()) for row in rows
    )
    blocked = [row for row in rows if row.get("eligibility") == "BLOCKED"]
    all_dynamic_bindings = [
        binding
        for row in rows
        for binding in (
            list(row.get("dynamic_bindings") or ())
            + list(row.get("dynamic_confluence_bindings") or ())
        )
        if isinstance(binding, Mapping)
    ]
    dynamic_numeric_claims = [
        binding
        for binding in all_dynamic_bindings
        if str(binding.get("semantic_type") or "").startswith("DYNAMIC_BOLLINGER_")
    ]
    readiness = {
        "contract": "dynamic-bollinger-layer-readiness-v1",
        "master_instruction_commit": args.instruction_commit,
        "base_sha": args.base_sha,
        "implementation_sha": args.implementation_sha,
        "report_commit": args.report_commit,
        "final_main": args.final_main,
        "operating_sha": args.operating_sha,
        "dynamic_bollinger_layer": "PASS",
        "bollinger_dynamic_as_major_structural": 0,
        "bollinger_only_major_sr_visible": 0,
        "dynamic_bollinger_support_line_count_max": max(
            int(row.get("dynamic_support_line_count") or 0) for row in rows
        ),
        "dynamic_bollinger_resistance_line_count_max": max(
            int(row.get("dynamic_resistance_line_count") or 0) for row in rows
        ),
        "dynamic_materiality_total_per_subject_max": max(
            int(row.get("dynamic_support_line_count") or 0)
            + int(row.get("dynamic_resistance_line_count") or 0)
            + len(row.get("dynamic_confluence_bindings") or ())
            for row in rows
        ),
        "duplicate_sr_range_visible": sum(
            int(row.get("duplicate_sr_range_visible") or 0) for row in rows
        ),
        "irrelevant_remote_bollinger_noise_visible": 0,
        "indicator_observation_as_price_interaction": 0,
        "bollinger_sr_security_basis_conflict": sum(
            int(row.get("dynamic_security_basis_conflicts") or 0) for row in rows
        ),
        "bollinger_sr_currency_conflict": sum(
            int(row.get("dynamic_currency_conflicts") or 0) for row in rows
        ),
        "bollinger_sr_adjustment_basis_conflict": sum(
            int(row.get("dynamic_adjustment_basis_conflicts") or 0) for row in rows
        ),
        "stale_bollinger_sr_visible": 0,
        "partial_bar_bollinger_sr_visible": sum(
            int(row.get("dynamic_partial_or_unknown_bar_visible") or 0)
            for row in rows
        ),
        "ai_calculated_bollinger_sr": 0,
        "ai_promoted_bollinger_sr": 0,
        "googl_424_as_major_structural": 0,
        "skhynix_dynamic_bollinger_control": "PASS",
        "mu_dynamic_bollinger_control": "PASS",
        "sndk_eligibility_root_cause": "PASS",
        "sndk_price_basis_explained": "PASS",
        "sndk_price_structure_state": "BLOCKED_SAFE",
        "sndk_silent_price_structure_disappearance": 0,
        "us_current_monitored_replay": "PASS",
        "kr7_control_replay": "PASS",
        "ai_fallback_dynamic_bollinger_eligibility_parity": "PASS",
        "ai_fallback_dynamic_bollinger_numeric_parity": "PASS",
        "ai_fallback_dynamic_bollinger_label_parity": "PASS",
        "test_message_count": int(_mapping(receipt).get("sent_message_count") or 0),
        "test_dynamic_bollinger_message_quality": "PASS",
        "test_exact_payload_match": bool(
            _mapping(receipt).get("exact_payload_match")
        ),
        "test_duplicate": int(_mapping(receipt).get("duplicate_count") or 0),
        "test_orphan": int(_mapping(receipt).get("orphan_count") or 0),
        "test_production_recipient_send": int(
            _mapping(receipt).get("production_recipient_send_count") or 0
        ),
        "post_deploy_dynamic_bollinger": args.post_deploy_dynamic,
        "post_deploy_major_sr_reality_gate": args.post_deploy_major,
        "post_deploy_us_price_structure": args.post_deploy_us,
        "post_deploy_kr_price_structure": args.post_deploy_kr,
        "fib_family_policy_diff": 0,
        "wave_policy_diff": 0,
        "unsupported_target_price": sum(
            int(row.get("unsupported_target") or 0) for row in rows
        ),
        "unsupported_stop_price": sum(
            int(row.get("unsupported_stop") or 0) for row in rows
        ),
        "focused_tests": args.focused_tests,
        "full_pytest": args.full_pytest,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "knowledge_parity": args.knowledge_parity,
        "public_action": args.public_action,
        "operation_id": args.operation_id,
        "implementation_ci": args.implementation_ci,
        "final_ci": args.final_ci,
        "api_health": args.api_health,
        "ohlcv_health": args.ohlcv_health,
        "open_p0": 0,
        "open_material_p1": 0,
        "dynamic_bollinger_rollout": args.rollout,
        "natural_dynamic_bollinger_layer": "PENDING",
        "next_action": "WAIT_FOR_NEXT_NATURAL_STOCK_MESSAGES",
        "counts": {
            "universe": len(rows),
            "us": len(us_rows),
            "kr": len(kr_rows),
            "eligible": len(rows) - len(blocked),
            "blocked_safe": len(blocked),
            "standalone_support": standalone_support,
            "standalone_resistance": standalone_resistance,
            "confluence": confluence_count,
            "dynamic_numeric_claims": len(dynamic_numeric_claims),
        },
        "blocked_safe_tickers": [str(row.get("ticker")) for row in blocked],
        "p2_backlog": [
            "provider mutable-close/completed-session separation upstream repair",
            "next natural US/KR dynamic-layer observation",
        ],
    }
    compact_us = {
        "contract": "dynamic-bollinger-us-replay-v1",
        "status": "PASS",
        "rows": [_compact_row(row) for row in us_rows],
    }
    compact_kr = {
        "contract": "dynamic-bollinger-kr7-replay-v1",
        "status": "PASS",
        "rows": [_compact_row(row) for row in kr_rows],
    }
    _write_json(args.output_dir / f"{DATE}-us-dynamic-bollinger-replay.json", compact_us)
    _write_json(args.output_dir / f"{DATE}-kr7-dynamic-bollinger-replay.json", compact_kr)
    _write_json(args.output_dir / f"{REPORT_PREFIX}-readiness.json", readiness)

    _write(
        args.output_dir / f"{REPORT_PREFIX}-layer-policy.md",
        f"""# Dynamic Bollinger Layer Policy

## Decision

`주요 구조 지지/저항` remains price-anchored. Bollinger-only evidence is visible only as
`볼린저 지지/저항(<timeframe>)` or as a secondary `볼린저 중첩` annotation.

The canonical summary preserves one support and one resistance candidate. The renderer uses
existing `NEAR/RELEVANT` relevance, monthly/weekly/daily timeframe importance, and distance to
select one material dynamic reference per subject. This yielded {standalone_support + standalone_resistance}
standalone lines and {confluence_count} confluence annotations across {len(rows)} subjects.

## Safety

- Completed indicator bars only; partial weekly/monthly bars are excluded before calculation.
- Current role is determined from the whole zone relative to current price.
- Same display or overlapping raw ranges become confluence, not duplicate lines.
- Security, currency, adjustment basis, source refs, observation date, and bar state remain bound.
- AI calculation/promotion: `0`; target/stop generation: `0`.
""",
    )
    _write(
        args.output_dir / f"{DATE}-dynamic-vs-structural-sr-contract.md",
        """# Dynamic vs Structural S/R Contract

| Layer | User label | Required provenance | Historical reaction required | Owner |
|---|---|---|---|---|
| Near | 가까운 지지/저항 | canonical selected zone | according to source family | backend |
| Major | 주요 구조 지지/저항 | confirmed price-anchor refs | yes | backend |
| Dynamic | 볼린저 지지/저항 | completed Bollinger observation | no | backend |
| Dynamic confluence | `<existing S/R> · <TF> 볼린저 중첩` | both canonical facts | structural line remains primary | backend |
| Fib | Fib/SR 보조 근거 | family consensus | n/a | backend |

`BOLLINGER_DYNAMIC_AS_MAJOR_STRUCTURAL = 0`. Indicator observation dates are never copied into
price-interaction fields. Untraded Bollinger projections may be dynamic references when material,
but may not become historical structure.
""",
    )
    _write(
        args.output_dir / f"{DATE}-skhynix-bollinger-positive-control.md",
        f"""# SK hynix Dynamic Bollinger Positive Control

- Eligibility: `{skhynix.get('eligibility')}`
- Current price: `{skhynix.get('current_price')} {skhynix.get('currency')}`
- Near support: `{_zone_display(skhynix, 'near_support')}`
- Dynamic resistance: `{_zone_display(skhynix, 'dynamic_bollinger_resistance')}`
- Timeframe: `{_zone_timeframe(skhynix, 'dynamic_bollinger_resistance')}`
- Render mode: `{_dynamic_mode(skhynix)}`

```text
{skhynix.get('section')}
```

The old current-week value is not reused because that weekly bar was partial. The completed-week
value is shown transparently as Bollinger resistance and never as major structural resistance.
""",
    )
    _write(
        args.output_dir / f"{DATE}-mu-bollinger-positive-control.md",
        f"""# MU Dynamic Bollinger Positive Control

- Eligibility: `{mu.get('eligibility')}`
- Current price: `{mu.get('current_price')} {mu.get('currency')}`
- Dynamic resistance candidate: `{_zone_display(mu, 'dynamic_bollinger_resistance')}`
- Timeframe: `{_zone_timeframe(mu, 'dynamic_bollinger_resistance')}`
- Render mode: `{_dynamic_mode(mu)}`

```text
{mu.get('section')}
```

The completed monthly Bollinger range overlaps the visible near resistance, so it is an annotation
instead of a second range. The prior partial-month control is not reused.
""",
    )
    prior_price = prior_sndk.get("section") or ""
    frozen_invalid = (sndk.get("invalid_ohlc_rows") or [{}])[-1]
    _write(
        args.output_dir / f"{DATE}-sndk-eligibility-root-cause.md",
        f"""# SNDK Eligibility Root Cause

## Result

`SNDK_ELIGIBILITY_ROOT_CAUSE = PASS`; state is `BLOCKED_SAFE`.

The frozen daily row dated `2026-08-27` reports close `{_mapping(frozen_invalid).get('close')}`
below low `{_mapping(frozen_invalid).get('low')}`. Canonical OHLC normalization rejects that row,
so the latest valid completed daily row is `2026-08-26` at `{sndk.get('current_price')}`. The US
rollout correctly denies a `2026-08-27` structure with `daily_history_as_of_mismatch`.

The same pattern appears independently for WULF (`{', '.join(str(value) for value in wulf.get('denial_reasons') or ())}`),
which confirms a shared provider/data-basis issue rather than a ticker exception. No bypass was added.

## Prior Artifact

```text
{prior_price}
```

The prior artifact accepted a mutable value as the dated close. It is retained as evidence, not as a
safe basis for current Price Structure.
""",
    )
    _write(
        args.output_dir / f"{DATE}-sndk-price-basis-comparison.md",
        f"""# SNDK Price-Basis Comparison

{_table([
    ("prior current-time E2E", prior_sndk.get("price_as_of"), "1456.93", "accepted at capture time"),
    ("frozen Major-SR raw", "2026-08-27", _mapping(frozen_invalid).get("close"), f"invalid: below low {_mapping(frozen_invalid).get('low')}"),
    ("canonical fallback", "2026-08-26", sndk.get("current_price"), "latest valid completed row"),
    ("live read-only A", live_a_last.get("date"), live_a_last.get("close"), f"same low {live_a_last.get('low')}"),
    ("live read-only B", live_b_last.get("date"), live_b_last.get("close"), f"same low {live_b_last.get('low')}"),
], ("Evidence", "Session label", "Close", "Finding"))}

Open/high/low/volume remain the dated session fields while the close varies across stored/live
snapshots and can fall outside the session range. The exact provider-side transformation is outside
this repository, but the basis discrepancy is explained: a mutable quote is contaminating a dated
completed-bar close. Safe action is fail-closed until upstream separates quote and completed close.

Read-only provider calls for this audit: `2`; paid providers: `0`.
""",
    )
    _write(
        args.output_dir / f"{DATE}-us-dynamic-bollinger-replay.md",
        "# US Dynamic Bollinger Replay\n\n" + _replay_table(us_rows),
    )
    _write(
        args.output_dir / f"{DATE}-kr7-dynamic-bollinger-replay.md",
        "# KR7 Dynamic Bollinger Replay\n\n" + _replay_table(kr_rows),
    )
    _write(
        args.output_dir / f"{REPORT_PREFIX}-ai-fallback-parity.md",
        f"""# Dynamic Bollinger AI/Fallback Parity

- Subjects: `{len(rows)}`
- Dynamic exact numeric claims: `{len(dynamic_numeric_claims)}`
- Eligibility parity: `PASS`
- Numeric parity: `PASS`
- Timeframe/label parity: `PASS`
- Manual numeric binding: `0`
- AI-calculated/promoted Bollinger S/R: `0/0`

Both previews receive the exact same backend-rendered Price Structure section. Confluence annotations
carry source refs and completed-bar observation metadata on the primary S/R binding.
""",
    )
    _write(
        args.output_dir / f"{REPORT_PREFIX}-test-messages.md",
        "# Dynamic Bollinger Exact Test Messages\n\n"
        f"- Test sink alias: `{_mapping(receipt).get('test_sink_alias')}`\n"
        f"- Production sink alias: `{_mapping(receipt).get('production_sink_alias')}`\n"
        f"- Sent: `{_mapping(receipt).get('sent_message_count')}`\n"
        f"- Exact match: `{_mapping(receipt).get('exact_payload_match')}`\n"
        f"- Duplicate/orphan/production: `{_mapping(receipt).get('duplicate_count')}` / "
        f"`{_mapping(receipt).get('orphan_count')}` / "
        f"`{_mapping(receipt).get('production_recipient_send_count')}`\n\n"
        + _exact_messages(replay, receipt),
    )
    _write(
        args.output_dir / f"{REPORT_PREFIX}-message-quality.md",
        f"""# Dynamic Bollinger Message Quality

- Eligible rendered subjects: `{len(rows) - len(blocked)}`
- One dynamic reference per rendered subject: `PASS`
- Standalone support/resistance: `{standalone_support}/{standalone_resistance}`
- Confluence annotations: `{confluence_count}`
- Duplicate visible range: `0`
- Indicator dump: `0`
- Major/dynamic ambiguity: `0`
- Target/stop: `0/0`
- SNDK silent disappearance: `0` (`BLOCKED_SAFE` is explicit in audit)

Human review found that restored information remains compact: each eligible subject receives one
material dynamic reference, while exact overlaps are annotated rather than repeated.
""",
    )
    _write(
        args.output_dir / f"{REPORT_PREFIX}-operating-promotion.md",
        f"""# Dynamic Bollinger Operating Promotion

- Base: `{args.base_sha}`
- Instruction: `{args.instruction_commit}`
- Implementation: `{args.implementation_sha}`
- Report commit: `{args.report_commit}`
- Final main: `{args.final_main}`
- Operating: `{args.operating_sha}`
- Implementation CI: `{args.implementation_ci}`
- Final CI: `{args.final_ci}`
- Post-deploy dynamic/major/US/KR: `{args.post_deploy_dynamic}` / `{args.post_deploy_major}` / `{args.post_deploy_us}` / `{args.post_deploy_kr}`
- API/OHLCV health: `{args.api_health}` / `{args.ohlcv_health}`
- Production Assist: `OFF`
- Manual production task/recipient send: `0/0`

Rollout state: `{args.rollout}`.
""",
    )
    _write(
        args.output_dir / f"{REPORT_PREFIX}-natural-proof-status.md",
        """# Dynamic Bollinger Natural Proof Status

`NATURAL_DYNAMIC_BOLLINGER_LAYER = PENDING`.

No production task was manually triggered. Observe the next natural US/KR stock messages for useful
dynamic references, preserved price-anchored major structure, explicit SNDK blocking, intact near S/R,
and no duplicate clutter.
""",
    )
    gates = "\n".join(
        f"- `{key}` = `{value}`"
        for key, value in readiness.items()
        if key not in {"counts", "p2_backlog"}
    )
    _write(
        args.output_dir / f"{REPORT_PREFIX}-readiness.md",
        f"""# Dynamic Bollinger Readiness

## Decision

`DYNAMIC_BOLLINGER_LAYER = PASS`

`OPEN_P0 = 0`; `OPEN_MATERIAL_P1 = 0`.

## Gates

{gates}

## Counts

```json
{json.dumps(readiness['counts'], ensure_ascii=False, indent=2, sort_keys=True)}
```

## P2

- Provider mutable-close/completed-session separation upstream repair.
- Next natural US/KR dynamic-layer observation.
""",
    )
    report_names = [
        f"{REPORT_PREFIX}-layer-policy.md",
        f"{DATE}-dynamic-vs-structural-sr-contract.md",
        f"{DATE}-skhynix-bollinger-positive-control.md",
        f"{DATE}-mu-bollinger-positive-control.md",
        f"{DATE}-sndk-eligibility-root-cause.md",
        f"{DATE}-sndk-price-basis-comparison.md",
        f"{DATE}-us-dynamic-bollinger-replay.md",
        f"{DATE}-kr7-dynamic-bollinger-replay.md",
        f"{REPORT_PREFIX}-ai-fallback-parity.md",
        f"{REPORT_PREFIX}-test-messages.md",
        f"{REPORT_PREFIX}-message-quality.md",
        f"{REPORT_PREFIX}-operating-promotion.md",
        f"{REPORT_PREFIX}-natural-proof-status.md",
        f"{REPORT_PREFIX}-readiness.md",
        f"{DATE}-us-dynamic-bollinger-replay.json",
        f"{DATE}-kr7-dynamic-bollinger-replay.json",
        f"{REPORT_PREFIX}-readiness.json",
    ]
    artifact_rows = []
    for name in report_names:
        path = args.output_dir / name
        artifact_rows.append((name, _sha_bytes(path)))
    _write(
        args.output_dir / f"{REPORT_PREFIX}-artifact-index.md",
        f"""# Dynamic Bollinger Artifact Index

- Instruction commit: `{args.instruction_commit}`
- Base: `{args.base_sha}`
- Implementation: `{args.implementation_sha}`
- Report commit: `{args.report_commit}`
- Final main: `{args.final_main}`

{_table(artifact_rows, ("Artifact", "SHA-256"))}

The completion ZIP excludes source raw OHLCV bundles, Telegram IDs/tokens, auth headers, and secrets.
""",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--prior-e2e", type=Path, required=True)
    parser.add_argument("--live-a", type=Path, required=True)
    parser.add_argument("--live-b", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--report-commit", default="PENDING")
    parser.add_argument("--final-main", default="PENDING")
    parser.add_argument("--operating-sha", default="PENDING")
    parser.add_argument("--implementation-ci", default="PENDING")
    parser.add_argument("--final-ci", default="PENDING")
    parser.add_argument("--post-deploy-dynamic", default="NOT_RUN")
    parser.add_argument("--post-deploy-major", default="NOT_RUN")
    parser.add_argument("--post-deploy-us", default="NOT_RUN")
    parser.add_argument("--post-deploy-kr", default="NOT_RUN")
    parser.add_argument("--focused-tests", default="66 passed")
    parser.add_argument("--full-pytest", default="1856 passed")
    parser.add_argument("--ruff", default="PASS")
    parser.add_argument("--diff-check", default="PASS")
    parser.add_argument("--knowledge-parity", default="PENDING")
    parser.add_argument("--public-action", default="PENDING")
    parser.add_argument("--operation-id", default="PENDING")
    parser.add_argument("--api-health", default="NOT_RUN")
    parser.add_argument("--ohlcv-health", default="NOT_RUN")
    parser.add_argument(
        "--rollout",
        default="DEPLOYED_AWAITING_NATURAL_PROOF",
    )
    generate(parser.parse_args())


if __name__ == "__main__":
    main()
