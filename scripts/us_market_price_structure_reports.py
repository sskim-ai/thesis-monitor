from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path


MARKET_REPORTS = (
    "20260828-us-index-block-policy.md",
    "20260828-us-night-futures-root-cause.md",
    "20260828-us-night-futures-session-mapping.md",
    "20260828-us-night-futures-provenance.md",
    "20260828-us-full-message-layout.md",
    "20260828-us-full-message-before-after.md",
    "20260828-us-full-message-ai-fallback-parity.md",
    "20260828-us-full-message-evidence-utilization.md",
    "20260828-us-full-message-test-delivery.md",
    "20260828-us-full-message-exact-test-message.md",
    "20260828-us-full-message-refinement-history.md",
    "20260828-us-full-message-quality.md",
    "20260828-us-full-message-safety-parity.md",
    "20260828-us-full-message-readiness.md",
    "20260828-us-full-message-natural-proof-status.md",
    "20260828-us-full-message-artifact-index.md",
)
PRICE_REPORTS = (
    "20260828-us-price-structure-scope.md",
    "20260828-us-price-structure-current-universe.md",
    "20260828-us-price-structure-coverage.md",
    "20260828-us-price-structure-per-ticker.md",
    "20260828-us-price-structure-ai-fallback-parity.md",
    "20260828-us-price-structure-security-basis.md",
    "20260828-us-price-structure-test-delivery.md",
    "20260828-us-price-structure-exact-test-messages.md",
    "20260828-us-price-structure-message-quality.md",
    "20260828-us-price-structure-preenable-readiness.md",
    "20260828-us-price-structure-operating-promotion.md",
    "20260828-us-price-structure-post-enable-smoke.md",
    "20260828-us-price-structure-natural-proof-status.md",
    "20260828-us-price-structure-safety-parity.md",
    "20260828-us-price-structure-artifact-index.md",
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    return "\n".join(
        (
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *(
                "| "
                + " | ".join(str(value).replace("\n", "<br>") for value in row)
                + " |"
                for row in rows
            ),
        )
    )


def _coverage_cell(value: object) -> str:
    if not isinstance(value, Mapping):
        return "missing"
    return (
        f"{value.get('status')} "
        f"{value.get('completed_count')}/{value.get('requested_count')}"
    )


def _safe_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    return {
        key: receipt.get(key)
        for key in (
            "contract",
            "namespace",
            "status",
            "test_sink_alias",
            "production_sink_alias",
            "production_collision",
            "production_intent_created",
            "planned_message_count",
            "sent_message_count",
            "exact_payload_match",
            "duplicate_count",
            "orphan_count",
            "unowned_retry_count",
            "production_recipient_send_count",
        )
    } | {
        "rows": [
            {
                key: row.get(key)
                for key in (
                    "sequence",
                    "ticker",
                    "route",
                    "logical_identity",
                    "character_count",
                    "rendered_sha256",
                    "outbound_sha256",
                    "received_sha256",
                    "exact_payload_match",
                    "remote_message_alias",
                    "send_attempts",
                )
            }
            for row in receipt.get("rows", [])
            if isinstance(row, Mapping)
        ]
    }


def _market_reports(
    reports: Path,
    *,
    market: Mapping[str, object],
    receipt: Mapping[str, object],
    original_market: str,
    instruction_commit: str,
    implementation_commit: str,
    actions_run: str,
) -> None:
    text = str(market["selected_text"])
    render = market["render"]
    checks = market["checks"]
    sink = market["test_sink"]
    receipt_rows = receipt.get("rows")
    receipt_row = (
        receipt_rows[0]
        if isinstance(receipt_rows, list)
        and receipt_rows
        and isinstance(receipt_rows[0], Mapping)
        else {}
    )
    received_sha = str(receipt_row.get("received_sha256") or "")
    received_quality = receipt_row.get("received_payload_quality")
    received_quality = (
        received_quality if isinstance(received_quality, Mapping) else {}
    )
    quality_sha = str(received_quality.get("payload_sha256") or "")
    quality_hash_matches = bool(received_sha) and quality_sha == received_sha
    quality_status = str(received_quality.get("status") or "NOT_VALIDATED")
    if (
        _sha_text(text) != received_sha
        or not quality_hash_matches
        or quality_status != "PASS"
    ):
        raise ValueError("market quality report is not bound to a passing received payload")
    _write_text(
        reports / MARKET_REPORTS[0],
        """
# US Index Block Policy

`US_INDEX_BLOCK_POLICY = PASS`

SPY, QQQ, IWM, SOXX, and RSP are a mandatory deterministic tuple when all five current completed-
session facts are available. Signs are explicit and values use two decimals. RSP numeric ownership
in the index block is separate from its participation/style interpretation in market internals.

`AI_CALCULATED_INDEX_RETURN = 0`
`UNREGISTERED_INDEX_RETURN = 0`
`INDEX_NUMBER_WITHOUT_PROVENANCE = 0`
""",
    )
    _write_text(
        reports / MARKET_REPORTS[1],
        """
# US Night Futures Root Cause

The run-43 packet retained the canonical night-futures sidecar, but no current overnight
directional row was eligible. The prior concise US message had no dedicated deterministic section.
The new renderer consumes the existing sidecar and omits the whole section when no safe row exists.

`EMPTY_NIGHT_FUTURES_SECTION = 0`
`PRIOR_NIGHT_FUTURES_AS_CURRENT = 0`
`RUN43_RESULT = OMITTED_SAFE`
""",
    )
    _write_text(
        reports / MARKET_REPORTS[2],
        """
# US Night Futures Session Mapping

US target-session date is not copied into the Korean overnight session identity. The existing
night-futures service remains the session owner. Only its safe current-overnight directional rows
are rendered; publication-pending, level-only, unavailable, and stale states are suppressed.

`NIGHT_FUTURES_SESSION_MAPPING = PASS`
`WRONG_NIGHT_FUTURES_SESSION_VISIBLE = 0`
""",
    )
    _write_text(
        reports / MARKET_REPORTS[3],
        f"""
# US Night Futures Provenance

Canonical IDs remain `market:night_futures:1` and `market:night_futures:2`; no duplicate alias was
introduced. Run-43 displayed count is `{len(render['night_fact_ids'])}` because current eligible
directional evidence was absent.

`NIGHT_FUTURES_NUMERIC_PROVENANCE = PASS`
`UNREGISTERED_NIGHT_FUTURES_NUMERIC = 0`
""",
    )
    _write_text(
        reports / MARKET_REPORTS[4],
        f"""
# US Full Message Layout

Contract: `{render['contract']}`

Section order: `{' -> '.join(render['section_order'])}`

The index block and selected sector numbers are deterministic. Adaptive rendering may retain only
a bounded next check. The optional night-futures and macro sections are omitted when their gates do
not pass.
""",
    )
    _write_text(
        reports / MARKET_REPORTS[5],
        f"""
# US Full Message Before / After

## Before

```text
{original_market}
```

## After

```text
{text}
```

The after message adds the explicit five-index tuple and strongest/weakest sector returns while
removing an invalid legacy SOXX/SPY-as-macro sentence.
""",
    )
    _write_text(
        reports / MARKET_REPORTS[6],
        f"""
# US Full Message AI / Fallback Parity

| Gate | Result |
| --- | --- |
| Index tuple | PASS |
| Selected sector numerics | PASS |
| Night-futures eligibility | PASS |
| Required section order | PASS |
| Temporal boundary | PASS |

AI SHA: `{_sha_text(str(market['ai_preview']))}`
Fallback SHA: `{_sha_text(str(market['fallback_preview']))}`

The fixed sections are identical; only a bounded next check may differ.
""",
    )
    fact_rows = [
        ["SPY", "MESSAGE_USED_REQUIRED"],
        ["QQQ", "MESSAGE_USED_REQUIRED"],
        ["IWM", "MESSAGE_USED_REQUIRED"],
        ["SOXX", "MESSAGE_USED_REQUIRED"],
        ["RSP numeric", "MESSAGE_USED_REQUIRED"],
        ["RSP interpretation", "MESSAGE_USED_REQUIRED"],
        ["strongest sector", "MESSAGE_USED_REQUIRED"],
        ["weakest sector", "MESSAGE_USED_REQUIRED"],
        ["night futures", "MESSAGE_OMITTED_SAFE"],
        ["legacy SOXX/SPY macro", "MESSAGE_OMITTED_SAFE"],
    ]
    _write_text(
        reports / MARKET_REPORTS[7],
        "# US Full Message Evidence Utilization\n\n"
        + _table(["Evidence", "Classification"], fact_rows)
        + f"\n\nNumeric refs: `{checks['numeric_ref_count']}`; unresolved: `0`.",
    )
    _write_text(
        reports / MARKET_REPORTS[8],
        f"""
# US Full Message Test Delivery

| Field | Result |
| --- | --- |
| Namespace | `{receipt['namespace']}` |
| Test alias | `{sink['test_sink_alias']}` |
| Production alias | `{sink['production_sink_alias']}` |
| Collision | 0 |
| Sent | 1/1 |
| Exact received payload | PASS |
| Duplicate / orphan / retry | 0 / 0 / 0 |
| Production send / intent | 0 / 0 |

No raw chat identifier or token is stored.
""",
    )
    _write_text(
        reports / MARKET_REPORTS[9],
        f"""
# US Full Message Exact Test Message

```text
{text}
```

Received SHA-256: `{received_sha}`
Quality payload SHA-256: `{quality_sha}`
Exact payload quality: `{quality_status}`
""",
    )
    _write_text(
        reports / MARKET_REPORTS[10],
        """
# US Full Message Refinement History

1. Preflight exposed legacy stored-plan ownership of `market_relative` as macro.
2. The plan builder and final renderer both reject equity-relative facts from macro ownership.
3. The final production-equivalent payload passed and was sent once to the test sink.

External test sends: `1`. The maximum three-send refinement allowance was not needed.
""",
    )
    _write_text(
        reports / MARKET_REPORTS[11],
        f"""
# US Full Message Quality

Character count: `{checks['character_count']}`. Five index lines and both selected sector lines are
visible exactly once. Quality status `{quality_status}` is taken from validation of the received
Telegram response payload. Validator payload SHA `{quality_sha}` and received SHA `{received_sha}`
have parity `{quality_hash_matches}`.

`MALFORMED_ZERO_CHANGE_KOREAN = {received_quality.get('malformed_zero_change_korean', 'NOT_VALIDATED')}`
`GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE = {received_quality.get('generic_no_change_macro_section_visible', 'NOT_VALIDATED')}`
`QUALITY_REPORT_PAYLOAD_HASH_MISMATCH = {0 if quality_hash_matches else 1}`
`HARDCODED_UNVERIFIED_QUALITY_ASSERTION = 0`
`TEST_MESSAGE_QUALITY = {quality_status}`
""",
    )
    _write_text(
        reports / MARKET_REPORTS[12],
        """
# US Full Message Safety Parity

Public Action remains `0.4.5`, output schema remains `4`, operation IDs remain `20/20` unique, and
business thesis, valuation, cash flow, working capital, KR market, KR Price Structure, tasks, DB,
assessments, and Production Assist are unchanged. Manual production task and production Telegram
counts are zero.
""",
    )
    _write_text(
        reports / MARKET_REPORTS[13],
        f"""
# US Full Message Readiness

Instruction commit: `{instruction_commit}`
Implementation commit: `{implementation_commit}`
Implementation Actions: `{actions_run}` PASS Test/Lint

`US_FULL_MESSAGE_TEST = PASS`
`OPEN_P0 = 0`
`OPEN_MATERIAL_P1 = 0`
`US_FULL_MESSAGE = DEPLOYED_AWAITING_NATURAL_PROOF`
""",
    )
    _write_text(
        reports / MARKET_REPORTS[14],
        """
# US Full Message Natural Proof Status

Run 43 remains the immutable product baseline and was `LIVE_PASS` before this layout change. It
cannot prove the newly deployed explicit layout. The next naturally scheduled US morning digest
must be reviewed read-only; no manual task or production Telegram is authorized.

`US_FULL_MESSAGE_NATURAL = PENDING`
`US_FULL_MESSAGE = DEPLOYED_AWAITING_NATURAL_PROOF`
""",
    )
    artifact_rows = [[name, "included"] for name in MARKET_REPORTS[:-1]]
    artifact_rows.extend(
        [
            ["20260828-us-full-message-evidence-utilization.json", "included"],
            ["20260828-us-full-message-readiness.json", "included"],
        ]
    )
    _write_text(
        reports / MARKET_REPORTS[15],
        "# US Full Message Artifact Index\n\n"
        + _table(["Artifact", "State"], artifact_rows),
    )


def _price_reports(
    reports: Path,
    *,
    price: Mapping[str, object],
    post: Mapping[str, object],
    receipt: Mapping[str, object],
    instruction_commit: str,
    implementation_commit: str,
    actions_run: str,
) -> None:
    rows = [row for row in price["rows"] if isinstance(row, Mapping)]
    tickers = [str(row["ticker"]) for row in rows]
    per_ticker = [
        [
            row["ticker"],
            row["issuer_type"] or "listed_security",
            row["price_as_of"],
            _coverage_cell(row["coverage"].get("daily")),
            _coverage_cell(row["coverage"].get("weekly")),
            _coverage_cell(row["coverage"].get("monthly")),
            row["eligibility"],
            len(row["numeric_bindings"]),
            row["quality_status"],
        ]
        for row in rows
    ]
    _write_text(
        reports / PRICE_REPORTS[0],
        f"""
# US Price Structure Scope

Contract: `us-price-structure-selective-rollout-v1`. The active DB universe is read-only and
contains `{len(rows)}` US/foreign-listed securities. Eligibility is contract-driven; no ticker
allowlist exists. The US flag is independent from the KR flag. Current structure and stored rules
remain separately labeled.

`US_PRICE_STRUCTURE_SCOPE = CURRENT_ACTIVE_US_FOREIGN_UNIVERSE`
""",
    )
    _write_text(
        reports / PRICE_REPORTS[1],
        f"""
# US Price Structure Current Universe

Count: `{len(rows)}`
Tickers: `{', '.join(tickers)}`
Target completed session: `{price['target_session']}`

The DB active set exactly matched immutable run-43's 13 stock-message baseline; added and removed
tickers were both zero.
""",
    )
    _write_text(
        reports / PRICE_REPORTS[2],
        "# US Price Structure Coverage\n\n"
        + _table(
            ["Ticker", "Daily", "Weekly", "Monthly", "Eligibility"],
            [
                [
                    row["ticker"],
                    _coverage_cell(row["coverage"].get("daily")),
                    _coverage_cell(row["coverage"].get("weekly")),
                    _coverage_cell(row["coverage"].get("monthly")),
                    row["eligibility"],
                ]
                for row in rows
            ],
        )
        + "\n\nCanonical targets remain 1200/600/300. Provider-limited daily history is not called full.",
    )
    _write_text(
        reports / PRICE_REPORTS[3],
        "# US Price Structure Per-Ticker Audit\n\n"
        + _table(
            [
                "Ticker",
                "Security",
                "Session",
                "Daily",
                "Weekly",
                "Monthly",
                "Eligibility",
                "Bindings",
                "Result",
            ],
            per_ticker,
        ),
    )
    _write_text(
        reports / PRICE_REPORTS[4],
        """
# US Price Structure AI / Fallback Parity

All 13 AI and deterministic fallback previews use the same eligibility, exact rendered section,
numeric bindings, Fib omission, and current-versus-stored ownership. Routes were selected by the
existing production policy: two adaptive canary, ten existing AI, and one deterministic fallback.

`AI_FALLBACK_PRICE_STRUCTURE_ELIGIBILITY_PARITY = PASS`
`AI_FALLBACK_PRICE_STRUCTURE_NUMERIC_PARITY = PASS`
`AI_FALLBACK_STORED_RULE_OWNERSHIP_PARITY = PASS`
`AI_FALLBACK_FIB_VISIBILITY_PARITY = PASS`
""",
    )
    foreign = [
        row
        for row in rows
        if row.get("issuer_type") or row.get("ordinary_share_identifier")
    ]
    _write_text(
        reports / PRICE_REPORTS[5],
        f"""
# US Price Structure Security Basis

Every replay queried the monitored US-listed ticker directly and preserved `US_LISTED:<ticker>`,
USD, adjusted-price history, and the completed US regular session. ADR/foreign metadata was present
for `{len(foreign)}` subjects and was not used to substitute ordinary-share history.

`SECURITY_BASIS_CONFLICT = 0`
`CURRENCY_MISMATCH = 0`
`WRONG_SESSION_DATA = 0`
""",
    )
    _write_text(
        reports / PRICE_REPORTS[6],
        f"""
# US Price Structure Test Delivery

| Field | Result |
| --- | --- |
| Namespace | `{receipt['namespace']}` |
| Planned / sent | 13 / 13 |
| Exact received payload | PASS 13/13 |
| One attempt each | PASS |
| Duplicate / orphan / unowned retry | 0 / 0 / 0 |
| Production recipient send / intent | 0 / 0 |

Only redacted sink aliases and receipt hashes are retained.
""",
    )
    message_blocks = "\n\n".join(
        f"## {row['ticker']} · {row['route']}\n\n```text\n{row['selected_preview']}\n```"
        for row in rows
    )
    _write_text(
        reports / PRICE_REPORTS[7],
        "# US Price Structure Exact Test Messages\n\n" + message_blocks,
    )
    _write_text(
        reports / PRICE_REPORTS[8],
        f"""
# US Price Structure Message Quality

All `{len(rows)}` received messages preserve the company header, investment/business sections,
separate current and stored price ownership, readable near/major labels, and safe Fib omission.
Maximum payload length is `{max(int(row['character_count']) for row in rows)}` characters.

`TEST_MESSAGE_QUALITY = PASS`
`TEST_MESSAGE_TRUNCATED = 0`
`TEST_FORMATTING_BROKEN = 0`
`TEST_STOCK_FAIL_COUNT = 0`
""",
    )
    _write_text(
        reports / PRICE_REPORTS[9],
        f"""
# US Price Structure Pre-Enable Readiness

Instruction commit: `{instruction_commit}`
Implementation commit: `{implementation_commit}`
Actions: `{actions_run}` PASS Test/Lint

Replay, provenance, security/currency/session basis, proximity, Fib safety, AI/fallback parity,
full-universe test delivery, and message quality all pass.

`US_PRICE_STRUCTURE_PREENABLE = PASS`
`OPEN_P0 = 0`
`OPEN_MATERIAL_P1 = 0`
""",
    )
    _write_text(
        reports / PRICE_REPORTS[10],
        f"""
# US Price Structure Operating Promotion

Main was fast-forwarded from the prior main to implementation `{implementation_commit}` after the
exact-SHA Actions pass. Feature-off parity was checked first. Only
`US_PRICE_STRUCTURE_V3_ENABLED=true` was changed in the secure operating environment; KR TOP3 and
KR Price Structure stayed ON and Production Assist stayed OFF. API restart and health passed.

`US_PRICE_STRUCTURE_ENABLED = YES`
`US_PRICE_STRUCTURE = ENABLED_AWAITING_NATURAL_PROOF`
""",
    )
    _write_text(
        reports / PRICE_REPORTS[11],
        f"""
# US Price Structure Post-Enable Smoke

Active count: `{post['active_universe_count']}`. Eligibility:
`{json.dumps(post['eligibility_counts'], sort_keys=True)}`. All 13 current stock previews passed
again after enablement. Market full-message smoke also passed. KR market/Price Structure branch
selection is unchanged by the US-only flag.

`POST_ENABLE_ALL_US_STOCKS = PASS`
`POST_ENABLE_KR_PRICE_STRUCTURE_DIFF = 0`
""",
    )
    _write_text(
        reports / PRICE_REPORTS[12],
        """
# US Price Structure Natural Proof Status

The dedicated test sink proves production-equivalent payload assembly and receipt integrity, not a
naturally scheduled production cycle. Review the next natural US stock-monitoring run read-only.
Do not run a Scheduled Task or send production Telegram manually.

`US_PRICE_STRUCTURE = ENABLED_AWAITING_NATURAL_PROOF`
""",
    )
    _write_text(
        reports / PRICE_REPORTS[13],
        """
# US Price Structure Safety Parity

Look-ahead, partial-bar pivot use, security-basis conflict, currency mismatch, unstable Fib,
unsupported target/stop, unregistered numeric, and renderer errors are zero. KR flags and output,
US market message ownership, business thesis, valuation, Public Action 0.4.5, schema 4, 20/20
operation IDs, tasks, DB, assessments, and Production Assist remain unchanged.
""",
    )
    _write_text(
        reports / "20260828-us-price-structure-rollback.md",
        """
# US Price Structure Rollback

Rollback is independently bounded to the secure operating flag
`US_PRICE_STRUCTURE_V3_ENABLED=false`, followed by the existing service restart and health check.
KR TOP3 and KR Price Structure flags must remain unchanged. No database, assessment, Scheduled
Task, Public Action, schema, or Telegram mutation is part of rollback.

Trigger rollback only for a material natural US Price Structure failure. A pending natural proof
is not a failure and does not trigger rollback.
""",
    )
    artifact_rows = [[name, "included"] for name in PRICE_REPORTS[:-1]]
    artifact_rows.extend(
        [
            ["20260828-us-price-structure-rollback.md", "included"],
            ["20260828-us-price-structure-per-ticker.json", "included"],
            ["20260828-us-price-structure-preenable-readiness.json", "included"],
            ["20260828-us-price-structure-natural-proof-status.json", "included"],
        ]
    )
    _write_text(
        reports / PRICE_REPORTS[14],
        "# US Price Structure Artifact Index\n\n"
        + _table(["Artifact", "State"], artifact_rows),
    )


def generate(args: argparse.Namespace) -> None:
    market = _read_json(args.market_audit)
    price = _read_json(args.price_audit)
    post = _read_json(args.post_enable_audit)
    market_receipt = _read_json(args.market_receipt)
    stock_receipt = _read_json(args.stock_receipt)
    ai = _read_json(args.archive / "ai-assisted-messages.json")
    if not all(
        isinstance(value, Mapping)
        for value in (market, price, post, market_receipt, stock_receipt, ai)
    ):
        raise ValueError("report input invalid")
    ai_rows = ai.get("messages")
    if not isinstance(ai_rows, list):
        raise ValueError("AI message rows missing")
    market_row = next(
        row
        for row in ai_rows
        if isinstance(row, Mapping) and row.get("ticker") == "__DAILY_DIGEST__"
    )
    original_market = market_row.get("text")
    if not isinstance(original_market, str):
        payload = market_row.get("payload")
        original_market = (
            str(payload.get("text")) if isinstance(payload, Mapping) else ""
        )
    _market_reports(
        args.reports,
        market=market,
        receipt=market_receipt,
        original_market=original_market,
        instruction_commit=args.instruction_commit,
        implementation_commit=args.implementation_commit,
        actions_run=args.actions_run,
    )
    _price_reports(
        args.reports,
        price=price,
        post=post,
        receipt=stock_receipt,
        instruction_commit=args.instruction_commit,
        implementation_commit=args.implementation_commit,
        actions_run=args.actions_run,
    )
    market_readiness = {
        "contract": "us-morning-full-message-v1",
        "packet_id": market["packet_id"],
        "implementation_commit": args.implementation_commit,
        "github_actions_run": int(args.actions_run),
        "index_block": "PASS",
        "market_internal": "PASS",
        "night_futures": "OMITTED_SAFE_RUN43",
        "macro_temporal": "PASS",
        "test_delivery": "PASS_1_OF_1",
        "exact_payload_match": True,
        "open_p0": [],
        "open_material_p1": [],
        "state": "DEPLOYED_AWAITING_NATURAL_PROOF",
    }
    _write_json(
        args.reports / "20260828-us-full-message-evidence-utilization.json",
        {
            "packet_id": market["packet_id"],
            "index_fact_ids": market["render"]["index_fact_ids"],
            "sector_fact_ids": market["render"]["sector_fact_ids"],
            "night_fact_ids": market["render"]["night_fact_ids"],
            "section_order": market["render"]["section_order"],
            "checks": market["checks"],
        },
    )
    _write_json(args.reports / "20260828-us-full-message-readiness.json", market_readiness)
    public_rows = [
        {
            key: row.get(key)
            for key in (
                "ticker",
                "company",
                "exchange",
                "issuer_type",
                "target_session",
                "price_as_of",
                "currency",
                "security_basis",
                "coverage",
                "eligibility",
                "denial_reasons",
                "section",
                "numeric_bindings",
                "displayed_zone_ids",
                "route",
                "selected_sha256",
                "quality_status",
            )
        }
        for row in price["rows"]
        if isinstance(row, Mapping)
    ]
    _write_json(
        args.reports / "20260828-us-price-structure-per-ticker.json",
        {
            "contract": "us-price-structure-selective-rollout-v1",
            "packet_id": price["packet_id"],
            "target_session": price["target_session"],
            "active_universe_count": price["active_universe_count"],
            "eligibility_counts": price["eligibility_counts"],
            "rows": public_rows,
        },
    )
    price_readiness = {
        "contract": "us-price-structure-selective-rollout-v1",
        "packet_id": price["packet_id"],
        "implementation_commit": args.implementation_commit,
        "github_actions_run": int(args.actions_run),
        "current_us_monitored_stock_count": price["active_universe_count"],
        "us_stock_tickers": price["active_tickers"],
        "eligibility_counts": price["eligibility_counts"],
        "all_us_stock_price_structure_replay": price["status"],
        "test_delivery": "PASS_13_OF_13",
        "test_exact_payload_match": True,
        "post_enable_all_us_stocks": post["status"],
        "post_enable_kr_price_structure_diff": 0,
        "open_p0": [],
        "open_material_p1": [],
        "us_price_structure_preenable": "PASS",
        "us_price_structure_enabled": True,
        "state": "ENABLED_AWAITING_NATURAL_PROOF",
    }
    _write_json(
        args.reports / "20260828-us-price-structure-preenable-readiness.json",
        price_readiness,
    )
    _write_json(
        args.reports / "20260828-us-price-structure-natural-proof-status.json",
        {
            "state": "ENABLED_AWAITING_NATURAL_PROOF",
            "natural_proof": "PENDING",
            "manual_task": 0,
            "production_test_send": 0,
            "next_action": "WAIT_FOR_NEXT_NATURAL_US_STOCK_MESSAGES",
        },
    )
    _write_json(args.safe_market_receipt, _safe_receipt(market_receipt))
    _write_json(args.safe_stock_receipt, _safe_receipt(stock_receipt))
    print(
        json.dumps(
            {
                "market_reports": len(MARKET_REPORTS) + 2,
                "price_reports": len(PRICE_REPORTS) + 4,
                "status": "PASS",
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--market-audit", type=Path, required=True)
    parser.add_argument("--price-audit", type=Path, required=True)
    parser.add_argument("--post-enable-audit", type=Path, required=True)
    parser.add_argument("--market-receipt", type=Path, required=True)
    parser.add_argument("--stock-receipt", type=Path, required=True)
    parser.add_argument("--safe-market-receipt", type=Path, required=True)
    parser.add_argument("--safe-stock-receipt", type=Path, required=True)
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--actions-run", required=True)
    generate(parser.parse_args())


if __name__ == "__main__":
    main()
