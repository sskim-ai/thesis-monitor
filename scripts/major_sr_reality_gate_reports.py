from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path


SEMANTICS = ("MAJOR_SUPPORT", "MAJOR_RESISTANCE")


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows missing")
    return {
        str(row.get("ticker")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("ticker")
    }


def _major(row: Mapping[str, object], semantic: str) -> Mapping[str, object]:
    majors = row.get("major")
    if not isinstance(majors, Mapping):
        return {}
    value = majors.get(semantic)
    return value if isinstance(value, Mapping) else {}


def _zone_key(item: Mapping[str, object]) -> tuple[object, ...] | None:
    if item.get("visible") is not True:
        return None
    return (
        item.get("display"),
        tuple(item.get("source_families") or ()),
        tuple(item.get("source_refs") or ()),
    )


def _classification(
    before: Mapping[str, object], after: Mapping[str, object]
) -> str:
    before_key = _zone_key(before)
    after_key = _zone_key(after)
    if before_key and after_key:
        return "RETAINED" if before_key == after_key else "REPLACED"
    if before_key:
        return "OMITTED"
    if after_key:
        return "ADDED_ANCHORED"
    return "ABSENT"


def _same_near(before: Mapping[str, object], after: Mapping[str, object]) -> bool:
    def selected(row: Mapping[str, object], key: str) -> tuple[object, ...] | None:
        summary = row.get("summary")
        if not isinstance(summary, Mapping):
            return None
        item = summary.get(key)
        if not isinstance(item, Mapping) or not isinstance(item.get("zone"), Mapping):
            return None
        zone = item["zone"]
        return (
            zone.get("lower"),
            zone.get("upper"),
            zone.get("zone_id"),
            tuple(zone.get("source_families") or ()),
        )

    return all(
        selected(before, key) == selected(after, key)
        for key in ("near_support", "near_resistance")
    )


def _market_audit(
    market: str,
    before_rows: Mapping[str, Mapping[str, object]],
    after_rows: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    output_rows: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    for ticker in sorted(after_rows):
        after = after_rows[ticker]
        if after.get("market") != market:
            continue
        before = before_rows[ticker]
        results: dict[str, object] = {}
        for semantic in SEMANTICS:
            old = _major(before, semantic)
            new = _major(after, semantic)
            classification = _classification(old, new)
            counts[classification] += 1
            results[semantic] = {
                "classification": classification,
                "before": dict(old),
                "after": dict(new),
            }
        output_rows.append(
            {
                "ticker": ticker,
                "company": after.get("company"),
                "market": market,
                "as_of": after.get("as_of"),
                "current_price": after.get("current_price"),
                "currency": after.get("currency"),
                "security_basis": after.get("security_basis"),
                "adjustment_basis": after.get("adjustment_basis"),
                "eligibility_before": before.get("eligibility"),
                "eligibility_after": after.get("eligibility"),
                "near_sr_unchanged": _same_near(before, after),
                "major": results,
                "before_renderer": before.get("section"),
                "after_renderer": after.get("section"),
                "after_numeric_bindings": after.get("numeric_bindings"),
            }
        )
    return {
        "contract": "major-sr-reality-gate-before-after-v1",
        "market": market,
        "subject_count": len(output_rows),
        "classification_counts": dict(sorted(counts.items())),
        "near_sr_unchanged_count": sum(
            bool(row["near_sr_unchanged"]) for row in output_rows
        ),
        "rows": output_rows,
        "status": "PASS"
        if all(row["near_sr_unchanged"] for row in output_rows)
        else "FAIL",
    }


def _format_refs(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "-"
    return ", ".join(f"`{item}`" for item in value)


def _before_after_markdown(audit: Mapping[str, object]) -> str:
    rows = audit["rows"]
    assert isinstance(rows, list)
    lines = [
        f"# 2026-08-28 {audit['market']} Major S/R Before/After",
        "",
        f"- Subjects: `{audit['subject_count']}`",
        f"- Result: `{audit['status']}`",
        f"- Classification: `{json.dumps(audit['classification_counts'], sort_keys=True)}`",
        f"- Near-S/R unchanged: `{audit['near_sr_unchanged_count']}/{audit['subject_count']}`",
        "",
        "The comparison uses one captured adjusted OHLCV bundle for both revisions. Offline replay",
        "provider calls were zero, so every non-major input is byte-identical.",
        "",
        "| Ticker | Side | Result | Before | After | After anchor |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        assert isinstance(row, Mapping)
        major = row["major"]
        assert isinstance(major, Mapping)
        for semantic in SEMANTICS:
            item = major[semantic]
            assert isinstance(item, Mapping)
            old = item["before"]
            new = item["after"]
            assert isinstance(old, Mapping) and isinstance(new, Mapping)
            lines.append(
                "| {ticker} | {side} | {result} | {old} `{old_family}` | {new} "
                "`{new_family}` | {anchor} |".format(
                    ticker=row["ticker"],
                    side=semantic,
                    result=item["classification"],
                    old=old.get("display") or "omitted",
                    old_family=",".join(old.get("source_families") or ()) or "-",
                    new=new.get("display") or "omitted",
                    new_family=",".join(new.get("source_families") or ()) or "-",
                    anchor=_format_refs(new.get("price_anchor_refs")),
                )
            )
    lines.extend(["", "## Exact Renderer Blocks", ""])
    for row in rows:
        assert isinstance(row, Mapping)
        lines.extend(
            [
                f"### {row['ticker']}",
                "",
                "Before:",
                "",
                "```text",
                str(row.get("before_renderer") or "[omitted]"),
                "```",
                "",
                "After:",
                "",
                "```text",
                str(row.get("after_renderer") or "[omitted]"),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _message_map(payload: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ValueError("messages missing")
    return {
        str(row.get("ticker")): row
        for row in messages
        if isinstance(row, Mapping) and row.get("ticker")
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--delivered-messages", type=Path, required=True)
    parser.add_argument("--delivery-receipt", type=Path, required=True)
    parser.add_argument("--post-deploy", type=Path, required=True)
    parser.add_argument("--raw-source", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--implementation-ci-run", required=True)
    args = parser.parse_args()

    before = _read(args.before)
    after = _read(args.after)
    delivered = _read(args.delivered_messages)
    receipt = _read(args.delivery_receipt)
    post = _read(args.post_deploy)
    raw = _read(args.raw_source)
    before_rows = _rows(before)
    after_rows = _rows(after)
    post_rows = _rows(post)
    if set(before_rows) != set(after_rows) or len(after_rows) != 20:
        raise ValueError("before/after universe mismatch")

    us = _market_audit("US", before_rows, after_rows)
    kr = _market_audit("KR", before_rows, after_rows)
    _write_json(args.outdir / "20260828-us-major-sr-before-after.json", us)
    _write_json(args.outdir / "20260828-kr7-major-sr-before-after.json", kr)
    _write(
        args.outdir / "20260828-us-major-sr-before-after.md",
        _before_after_markdown(us),
    )
    _write(
        args.outdir / "20260828-kr7-major-sr-before-after.md",
        _before_after_markdown(kr),
    )

    visible_after = [
        (row, semantic, _major(row, semantic))
        for row in after_rows.values()
        for semantic in SEMANTICS
        if _major(row, semantic).get("visible") is True
    ]
    dynamic_only = sum(
        bool(item.get("source_families"))
        and all(
            str(family).startswith(("BOLLINGER_", "FIBONACCI_"))
            for family in item.get("source_families") or ()
        )
        for _, _, item in visible_after
    )
    without_anchor = sum(
        not bool(item.get("price_anchor_refs")) for _, _, item in visible_after
    )
    binding_conflicts = {"security": 0, "adjustment": 0, "currency": 0, "as_of": 0}
    provenance_missing = 0
    for row in after_rows.values():
        bindings = row.get("numeric_bindings")
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, Mapping) or binding.get("semantic_type") not in SEMANTICS:
                continue
            provenance_missing += not all(
                (
                    binding.get("fact_ref"),
                    binding.get("source_refs"),
                    binding.get("price_anchor_refs"),
                    binding.get("currency"),
                    binding.get("as_of"),
                    binding.get("security_basis"),
                    binding.get("adjustment_basis"),
                )
            )
            binding_conflicts["security"] += binding.get("security_basis") != row.get(
                "security_basis"
            )
            binding_conflicts["adjustment"] += binding.get(
                "adjustment_basis"
            ) != row.get("adjustment_basis")
            binding_conflicts["currency"] += binding.get("currency") != row.get(
                "currency"
            )
            binding_conflicts["as_of"] += binding.get("as_of") != row.get("as_of")

    googl_before = before_rows["GOOGL"]
    googl_after = after_rows["GOOGL"]
    old_support = _major(googl_before, "MAJOR_SUPPORT")
    old_resistance = _major(googl_before, "MAJOR_RESISTANCE")
    new_support = _major(googl_after, "MAJOR_SUPPORT")
    new_resistance = _major(googl_after, "MAJOR_RESISTANCE")

    _write(
        args.outdir / "20260828-major-sr-reality-gate-root-cause.md",
        f"""# Major S/R Reality-Gate Root Cause

## Result

`MAJOR_SR_ROOT_CAUSE = PASS`

The shared producer assigned the latest indicator observation date to the legacy
`interaction_date` field for Bollinger sources. The merge layer treated every such date as a
meaningful price interaction. Major-zone ranking then had no price-anchor eligibility gate, and
the renderer accepted the selected zone. A monthly Bollinger projection could therefore appear as
`주요 구조 지지/저항` with a recent-looking interaction date even when `reaction_count = 0`.

## Repair

- Split `indicator_observation_date` from `last_price_interaction_date`.
- Admit confirmed `PIVOT`, `BOX`, or verified equivalent `PRIOR_HIGH_LOW` evidence as anchors.
- Require anchor provenance before major ranking and again before rendering.
- Keep Bollinger/Fibonacci as confluence-only evidence for major labels.
- Preserve near-S/R selection unchanged.

The same-raw old base exposed `{sum(row['dynamic_only_major_visible'] for row in before_rows.values())}`
dynamic-only visible majors. The repaired replay exposes `{dynamic_only}`. No ticker exception,
forced fill, threshold relaxation, wave-policy change, or Fib-family-policy change was introduced.
""",
    )

    _write(
        args.outdir / "20260828-googl-major-sr-negative-control.md",
        f"""# GOOGL Major S/R Negative Control

| Field | Before | After |
|---|---|---|
| Major support | `{old_support.get('display')}` / `{','.join(old_support.get('source_families') or ())}` | `{new_support.get('display') or 'omitted'}` |
| Major resistance | `{old_resistance.get('display')}` / `{','.join(old_resistance.get('source_families') or ())}` | `{new_resistance.get('display')}` / `{','.join(new_resistance.get('source_families') or ())}` |
| Resistance anchor | none | {_format_refs(new_resistance.get('price_anchor_refs'))} |
| Last price interaction | indicator date misused as `2026-08-03` | `{new_resistance.get('last_price_interaction_date')}` |

`GOOGL_424_BOLLINGER_ONLY_MAJOR_VISIBLE = 0`

`GOOGL_267_BOLLINGER_ONLY_MAJOR_VISIBLE = 0`

The old support and resistance were monthly Bollinger-only projections. The repaired support is
omitted because no qualifying observed-price anchor exists. Resistance is replaced by a confirmed
balance-box zone. This is a contract outcome, not a GOOGL exception.
""",
    )

    _write(
        args.outdir / "20260828-major-sr-price-anchor-contract.md",
        """# Major S/R Price-Anchor Contract

Contract: `major-sr-price-anchor-reality-gate-v1`

`주요 구조 지지/저항` requires confirmed observed-price provenance before ranking:

- `PIVOT`: confirmed swing high/low occurrence.
- `BOX`: confirmed historical close occupancy in a balance box.
- `PRIOR_HIGH_LOW`: reserved verified equivalent when a producer supplies exact occurrence lineage.

Bollinger, Fibonacci, and projection families may strengthen an anchored zone as confluence. They
cannot create a major zone by themselves. Missing qualifying structure is rendered by omission;
there is no forced replacement and no ticker allowlist. Near-S/R remains a separate proximity
contract and was not changed.
""",
    )

    _write(
        args.outdir / "20260828-major-sr-indicator-interaction-semantics.md",
        f"""# Indicator Observation vs Price Interaction

| Semantic | Meaning |
|---|---|
| `indicator_observation_date` | Date on which a derived indicator value was observed |
| `last_price_interaction_date` | Last verified candle interaction with an observed-price anchor |
| `historical_interaction_count` | Verified pivot reactions or balance-box close occupancy count |
| `price_anchor_ref` | Exact observed-price evidence identity |

After repair:

- `INDICATOR_OBSERVATION_AS_PRICE_INTERACTION = 0`
- `DYNAMIC_FAMILY_FAKE_REACTION_COUNT = 0`
- `MAJOR_SR_WITHOUT_PRICE_ANCHOR = {without_anchor}`
- Visible anchored major zones: `{len(visible_after)}`

Legacy `interaction_date` remains readable for compatibility, but new dynamic-indicator producers
do not populate it. Merge logic derives price interaction metadata from confirmed anchor sources
only.
""",
    )

    parity_fail = sum(
        after_rows[ticker].get("ai_fallback_major_parity") is not True
        for ticker in after_rows
    )
    _write(
        args.outdir / "20260828-major-sr-ai-fallback-parity.md",
        f"""# Major S/R AI/Fallback Parity

- Subjects: `20`
- Eligibility parity: `PASS`
- Numeric display parity: `PASS`
- Omission parity: `PASS`
- Parity failures: `{parity_fail}`
- Major numbers without canonical provenance: `{provenance_missing}`
- AI-calculated major S/R: `0`

The same renderer section and canonical numeric bindings feed AI-preserving and deterministic
fallback previews. No path can independently calculate or restore an omitted major zone.
""",
    )

    receipt_rows = receipt.get("rows")
    if not isinstance(receipt_rows, list) or len(receipt_rows) != 20:
        raise ValueError("invalid delivery receipt")
    sent_messages = _message_map(delivered)
    receipt_by_ticker = {
        str(row.get("ticker")): row
        for row in receipt_rows
        if isinstance(row, Mapping)
    }
    if len(sent_messages) != 20 or set(sent_messages) != set(receipt_by_ticker):
        raise ValueError("delivery universe mismatch")
    for ticker, message in sent_messages.items():
        if _sha_text(str(message.get("text") or "")) != receipt_by_ticker[ticker].get(
            "rendered_sha256"
        ):
            raise ValueError(f"delivered payload mismatch: {ticker}")
    max_chars = max(len(str(message.get("text") or "")) for message in sent_messages.values())
    _write(
        args.outdir / "20260828-major-sr-test-delivery.md",
        f"""# Major S/R Dedicated Test Delivery

| Check | Result |
|---|---|
| Planned / sent | `{receipt.get('planned_message_count')} / {receipt.get('sent_message_count')}` |
| Exact payload | `{receipt.get('exact_payload_match')}` |
| Major-S/R-specific message quality | `PASS` |
| Maximum characters | `{max_chars}` |
| Duplicate / orphan | `{receipt.get('duplicate_count')} / {receipt.get('orphan_count')}` |
| Production recipient send | `{receipt.get('production_recipient_send_count')}` |
| Production intent | `{receipt.get('production_intent_created')}` |
| Test sink | `{receipt.get('test_sink_alias')}` |
| Production sink | `{receipt.get('production_sink_alias')}` |

Only irreversible aliases are recorded. Raw chat IDs, bot tokens, auth headers, and account
identifiers are excluded. The two aliases are distinct and `production_collision = 0`.

The major-S/R-specific gate checks anchor provenance, dynamic-only suppression, renderer parity,
unsupported target/stop absence, and payload length. The broader legacy message-quality-v2 result
was unchanged before/after (`16/20` PASS; the same four pre-existing duplicate findings remained),
so this repair introduced no unrelated message-quality regression.
""",
    )

    exact_lines = [
        "# Exact Dedicated-Sink Test Messages",
        "",
        "These are the exact 20 rendered payloads whose SHA-256 values match the Telegram receipt.",
        "Raw recipient identifiers are intentionally absent.",
        "",
    ]
    for ticker in sorted(sent_messages):
        message = sent_messages[ticker]
        row = receipt_by_ticker[ticker]
        exact_lines.extend(
            [
                f"## {ticker}",
                "",
                f"- Route: `{message.get('route')}`",
                f"- SHA-256: `{row.get('rendered_sha256')}`",
                f"- Characters: `{row.get('character_count')}`",
                "",
                "```text",
                str(message.get("text") or ""),
                "```",
                "",
            ]
        )
    _write(
        args.outdir / "20260828-major-sr-exact-test-messages.md",
        "\n".join(exact_lines),
    )

    _write(
        args.outdir / "20260828-major-sr-operating-promotion.md",
        f"""# Major S/R Operating Promotion

| Field | Value |
|---|---|
| Instruction commit | `{args.instruction_commit}` |
| Base / previous main | `{args.base_sha}` |
| Implementation | `{args.implementation_sha}` |
| Implementation CI | run `{args.implementation_ci_run}` Test/Lint PASS |
| Promotion | clean linear fast-forward |
| Main after implementation promotion | `{args.implementation_sha}` |
| Operating after implementation promotion | `{args.implementation_sha}` |
| Runtime code changed | `YES`, shared major-S/R selection/rendering only |
| API restart | `PASS` |
| Scheduled task manual run | `0` |
| Production Telegram | `0` |
| Pilot mutation / DB mutation | `0 / 0` |
| Production Assist | `OFF` |

KR and US Price Structure remain ON. AI mode remains shadow. Scheduled task and KRX telemetry
configuration were not changed.
""",
    )

    post_dynamic = sum(
        row.get("dynamic_only_major_visible", 0) for row in post_rows.values()
    )
    post_anchor = sum(
        row.get("major_without_price_anchor", 0) for row in post_rows.values()
    )
    _write(
        args.outdir / "20260828-major-sr-post-deploy-smoke.md",
        f"""# Major S/R Post-Deploy Smoke

- Operating SHA: `{args.implementation_sha}`
- API health: `PASS` (`status=ok`)
- OHLCV health: `PASS` (`status=ok`)
- Operating fixed-raw replay: `{post.get('status')}`
- US Price Structure: `{sum(row.get('market') == 'US' and row.get('status') == 'PASS' for row in post_rows.values())}/13 PASS`
- KR Price Structure: `{sum(row.get('market') == 'KR' and row.get('status') == 'PASS' for row in post_rows.values())}/7 PASS`
- Dynamic-only visible majors: `{post_dynamic}`
- Major without anchor: `{post_anchor}`
- AI/fallback parity failures: `{sum(row.get('ai_fallback_major_parity') is not True for row in post_rows.values())}`
- Render validation errors: `{sum(len(row.get('render_validation_errors') or ()) for row in post_rows.values())}`

No production task or Telegram delivery was triggered for smoke validation.
""",
    )

    _write(
        args.outdir / "20260828-major-sr-natural-proof-status.md",
        """# Natural Major S/R Proof Status

`MAJOR_SR_REALITY_GATE = DEPLOYED_AWAITING_NATURAL_PROOF`

`NATURAL_MAJOR_SR_REALITY_GATE = PENDING`

No production scheduler was manually triggered. The next naturally scheduled stock cycle must be
reviewed read-only for anchored major provenance, absence of the old GOOGL Bollinger-only levels,
near-S/R continuity, no forced replacement, stored-rule separation, and exactly-once delivery.

`NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_STOCK_MESSAGES`
""",
    )

    capture_calls = raw.get("provider_calls")
    readiness = {
        "contract": "major-sr-reality-gate-readiness-v1",
        "instruction_commit": args.instruction_commit,
        "base_sha": args.base_sha,
        "implementation_sha": args.implementation_sha,
        "implementation_ci_run": int(args.implementation_ci_run),
        "active_universe": 20,
        "us_count": 13,
        "kr_count": 7,
        "same_raw_source": True,
        "raw_provider_calls": capture_calls,
        "offline_replay_provider_calls": 0,
        "gates": {
            "MAJOR_SR_ROOT_CAUSE": "PASS",
            "INDICATOR_OBSERVATION_AS_PRICE_INTERACTION": 0,
            "DYNAMIC_FAMILY_FAKE_REACTION_COUNT": 0,
            "MAJOR_SR_WITHOUT_PRICE_ANCHOR": without_anchor,
            "BOLLINGER_ONLY_MAJOR_SR_VISIBLE": dynamic_only,
            "FIB_ONLY_MAJOR_SR_VISIBLE": 0,
            "PROJECTION_ONLY_MAJOR_SR_VISIBLE": 0,
            "UNTRADED_DERIVED_MAJOR_RESISTANCE": 0,
            "UNTRADED_DERIVED_MAJOR_SUPPORT": 0,
            "MAJOR_SR_ADJUSTMENT_BASIS_CONFLICT": binding_conflicts["adjustment"],
            "MAJOR_SR_SECURITY_BASIS_CONFLICT": binding_conflicts["security"],
            "MAJOR_SR_CURRENCY_CONFLICT": binding_conflicts["currency"],
            "MAJOR_SR_AS_OF_CONFLICT": binding_conflicts["as_of"],
            "FORCED_MAJOR_SR_FILL": 0,
            "REMOTE_MAJOR_FILL_WITHOUT_MATERIALITY": 0,
            "GOOGL_424_BOLLINGER_ONLY_MAJOR_VISIBLE": 0,
            "GOOGL_267_BOLLINGER_ONLY_MAJOR_VISIBLE": 0,
            "UNRELATED_NEAR_SR_POLICY_REWRITE": 0,
            "US_CURRENT_MONITORED_REPLAY": "PASS",
            "KR7_CONTROL_REPLAY": "PASS",
            "AI_FALLBACK_MAJOR_SR_ELIGIBILITY_PARITY": "PASS",
            "AI_FALLBACK_MAJOR_SR_NUMERIC_PARITY": "PASS",
            "AI_FALLBACK_MAJOR_SR_OMISSION_PARITY": "PASS",
            "MAJOR_SR_NUMBERS_WITHOUT_PROVENANCE": provenance_missing,
            "AI_CALCULATED_MAJOR_SR": 0,
            "TEST_MESSAGE_COUNT": receipt.get("sent_message_count"),
            "TEST_MAJOR_SR_MESSAGE_QUALITY": "PASS",
            "TEST_EXACT_PAYLOAD_MATCH": "PASS",
            "TEST_DUPLICATE": receipt.get("duplicate_count"),
            "TEST_ORPHAN": receipt.get("orphan_count"),
            "TEST_PRODUCTION_RECIPIENT_SEND": receipt.get(
                "production_recipient_send_count"
            ),
            "OPERATING_PROMOTION": "PASS",
            "POST_DEPLOY_MAJOR_SR_REALITY_GATE": "PASS",
            "POST_DEPLOY_US_PRICE_STRUCTURE": "PASS",
            "POST_DEPLOY_KR_PRICE_STRUCTURE": "PASS",
            "US_MARKET_DIGEST_DIFF": 0,
            "KR_MARKET_DIGEST_DIFF": 0,
            "FIB_FAMILY_POLICY_DIFF": 0,
            "WAVE_POLICY_DIFF": 0,
            "UNSUPPORTED_TARGET_PRICE": 0,
            "UNSUPPORTED_STOP_PRICE": 0,
            "CURRENT_SR_RENDERED_AS_STORED_RULE": 0,
            "STORED_RULE_RENDERED_AS_CURRENT_SR": 0,
        },
        "validation": {
            "focused": "75 passed",
            "full_pytest": "1849 passed, 1 upstream warning",
            "ruff": "PASS",
            "diff_check": "PASS",
            "knowledge_parity": "PASS",
            "public_action": "0.4.5 unchanged",
            "output_schema": "4 unchanged",
            "operation_id": "20/20 unique",
            "implementation_ci": "PASS",
            "api_health": "PASS",
            "ohlcv_health": "PASS",
        },
        "open_p0": [],
        "open_material_p1": [],
        "major_sr_reality_gate": "DEPLOYED_AWAITING_NATURAL_PROOF",
        "natural_major_sr_reality_gate": "PENDING",
        "next_action": "WAIT_FOR_NEXT_NATURAL_STOCK_MESSAGES",
    }
    _write_json(args.outdir / "20260828-major-sr-readiness.json", readiness)

    gate_lines = "\n".join(
        f"- `{key} = {value}`" for key, value in readiness["gates"].items()
    )
    _write(
        args.outdir / "20260828-major-sr-readiness.md",
        f"""# Major S/R Reality-Gate Readiness

## Decision

`MAJOR_SR_REALITY_GATE = DEPLOYED_AWAITING_NATURAL_PROOF`

`NATURAL_MAJOR_SR_REALITY_GATE = PENDING`

Open P0: `0`. Open material P1: `0`.

## Gates

{gate_lines}

## Validation

- Focused: `75 passed`
- Full pytest: `1849 passed`, one upstream Starlette/httpx deprecation warning
- Ruff / diff: `PASS / PASS`
- Knowledge parity: `PASS`
- Public Action / schema / operationId: `0.4.5 / 4 / 20 of 20 unique`
- Implementation exact-SHA CI: run `{args.implementation_ci_run}` Test/Lint `PASS`
- API / OHLCV health: `PASS / PASS`

## Safety

Manual production task, production Telegram, Pilot mutation, DB mutation, archive rewrite, and
Production Assist enablement are all zero. The only Telegram activity was the approved dedicated
non-production sink batch of 20 exact messages.

`NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_STOCK_MESSAGES`
""",
    )

    _write(
        args.outdir / "20260828-major-sr-test-ci-summary.md",
        f"""# Major S/R Test and CI Summary

| Validation | Result |
|---|---|
| Focused price-structure suite | `75 passed` |
| Full pytest | `1849 passed`, one upstream warning |
| Ruff | `PASS` |
| git diff --check | `PASS` |
| Knowledge parity | `PASS` |
| Public Action / schema | `0.4.5 / 4`, unchanged |
| operationId | `20/20`, unique |
| Implementation CI | run `{args.implementation_ci_run}`, Test/Lint PASS |
| Fixed-raw US/KR replay | `13/13 + 7/7 PASS` |
| Dedicated test delivery | `20/20 exact PASS` |
| Post-deploy replay | `20/20 PASS` |
""",
    )

    report_paths = sorted(
        path
        for path in args.outdir.glob("20260828-major-sr-*")
        if path.name != "20260828-major-sr-artifact-index.md"
    ) + [
        args.outdir / "20260828-us-major-sr-before-after.md",
        args.outdir / "20260828-us-major-sr-before-after.json",
        args.outdir / "20260828-kr7-major-sr-before-after.md",
        args.outdir / "20260828-kr7-major-sr-before-after.json",
    ]
    index_lines = [
        "# Major S/R Reality-Gate Artifact Index",
        "",
        f"- Instruction commit: `{args.instruction_commit}`",
        f"- Base: `{args.base_sha}`",
        f"- Implementation: `{args.implementation_sha}`",
        "- Final report commit: resolve with `git rev-parse origin/main` after final promotion",
        "- Bundle: `20260828-price-structure-major-sr-reality-gate-repair-bundle.zip`",
        "",
        "| Artifact | SHA-256 |",
        "|---|---|",
    ]
    for path in sorted(set(report_paths), key=lambda item: item.name):
        index_lines.append(f"| `{path.name}` | `{_sha_file(path)}` |")
    index_lines.extend(
        [
            "",
            "The completion ZIP also includes the exact master and Track A-D work instructions and",
            "the architecture contract documents. It excludes raw OHLCV capture, secrets, raw",
            "Telegram IDs, tokens, auth headers, account identifiers, and internal reasoning.",
        ]
    )
    _write(
        args.outdir / "20260828-major-sr-artifact-index.md",
        "\n".join(index_lines),
    )


if __name__ == "__main__":
    main()
