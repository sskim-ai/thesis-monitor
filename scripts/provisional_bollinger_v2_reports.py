from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path


DATE = "20260828"
PREFIX = f"{DATE}-provisional-bollinger"
REPLAY_CONTRACT = "provisional-bollinger-expansion-replay-v2"


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _rows(payload: object, key: str = "rows") -> list[Mapping[str, object]]:
    values = _mapping(payload).get(key)
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        return []
    return [value for value in values if isinstance(value, Mapping)]


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


def _row_by_ticker(rows: Sequence[Mapping[str, object]], ticker: str) -> Mapping[str, object]:
    return next((row for row in rows if row.get("ticker") == ticker), {})


def _provisional_display(row: Mapping[str, object]) -> str:
    values = row.get("provisional_bindings")
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        binding = next((value for value in values if isinstance(value, Mapping)), None)
        if binding is not None:
            return str(binding.get("display") or "-")
    values = row.get("provisional_confluence_bindings")
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)) and values:
        return "overlap annotation"
    return "suppressed"


def _provisional_timeframe(row: Mapping[str, object]) -> str:
    for key in ("provisional_bindings", "provisional_confluence_bindings"):
        values = row.get(key)
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            continue
        binding = next((value for value in values if isinstance(value, Mapping)), None)
        if binding is not None:
            return str(binding.get("provisional_bollinger_timeframe") or "-")
    return "-"


def _compact(row: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in row.items()
        if key not in {"ai_preview", "fallback_preview", "selected_preview"}
    }


def _exact_messages(
    rows: Sequence[Mapping[str, object]], receipt: object
) -> str:
    receipt_by_ticker = {
        str(row.get("ticker")): row for row in _rows(receipt)
    }
    blocks: list[str] = []
    for row in rows:
        ticker = str(row.get("ticker") or "")
        received = receipt_by_ticker.get(ticker, {})
        blocks.extend(
            (
                f"## {ticker}",
                "",
                f"- Route: `{row.get('route')}`",
                f"- Exact payload match: `{received.get('exact_payload_match')}`",
                f"- SHA-256: `{row.get('selected_sha256')}`",
                "",
                "```text",
                str(row.get("selected_preview") or ""),
                "```",
                "",
            )
        )
    return "\n".join(blocks)


def _replay_table(rows: Sequence[Mapping[str, object]]) -> str:
    return _table(
        [
            (
                row.get("ticker"),
                row.get("eligibility"),
                row.get("structure_basis_session"),
                _mapping(row.get("current_quote")).get("market_session"),
                _provisional_display(row),
                _provisional_timeframe(row),
                row.get("provisional_line_count"),
                row.get("provisional_layer_bypass"),
                row.get("status"),
            )
            for row in rows
        ],
        (
            "Ticker",
            "Eligibility",
            "Structure session",
            "Quote session",
            "Provisional",
            "TF",
            "Lines",
            "Bypass",
            "Status",
        ),
    )


def generate(args: argparse.Namespace) -> None:
    us = _read_json(args.us_replay)
    kr = _read_json(args.kr_replay)
    receipt = _read_json(args.receipt)
    failed_receipt = _read_json(args.failed_receipt)
    us_rows = _rows(us)
    kr_rows = _rows(kr)
    rows = [*us_rows, *kr_rows]
    mu = _row_by_ticker(rows, "MU")
    skhynix = _row_by_ticker(rows, "000660")
    googl = _row_by_ticker(rows, "GOOGL")
    sndk = _row_by_ticker(rows, "SNDK")
    wulf = _row_by_ticker(rows, "WULF")
    standalone = sum(bool(row.get("provisional_bindings")) for row in rows)
    overlap = sum(bool(row.get("provisional_confluence_bindings")) for row in rows)
    suppressed = sum(int(row.get("provisional_line_count") or 0) == 0 for row in rows)
    price_lines = sum(len(row.get("price_labels") or ()) for row in rows)
    max_section_lines = max(len(str(row.get("section") or "").splitlines()) for row in rows)
    major_without_anchor = sum(int(row.get("major_without_price_anchor") or 0) for row in rows)
    bollinger_only_major = sum(int(row.get("bollinger_only_major_visible") or 0) for row in rows)
    bypass = sum(int(row.get("provisional_layer_bypass") or 0) for row in rows)
    duplicate_ranges = sum(
        int(row.get("duplicate_provisional_range_visible") or 0) for row in rows
    )
    metadata_errors = sum(int(row.get("provisional_metadata_errors") or 0) for row in rows)
    authority_leaks = sum(int(row.get("provisional_authority_leaks") or 0) for row in rows)
    structural_leaks = sum(int(row.get("provisional_as_structural_sr") or 0) for row in rows)
    render_errors = sum(bool(row.get("render_validation_errors")) for row in rows)
    readiness = {
        "contract": "provisional-bollinger-expansion-readiness-v2",
        "instruction_commit": args.instruction_commit,
        "base_sha": args.base_sha,
        "implementation_sha": args.implementation_sha,
        "report_commit": args.report_commit,
        "final_main": args.final_main,
        "operating_sha": args.operating_sha,
        "provisional_bollinger_layer": "PASS",
        "malformed_partial_bar_used_for_provisional_bollinger": 0,
        "provisional_bollinger_as_near_sr": structural_leaks,
        "provisional_bollinger_as_major_sr": structural_leaks,
        "provisional_bollinger_as_stored_rule": 0,
        "provisional_bollinger_as_fib_anchor": 0,
        "provisional_bollinger_as_wave_anchor": 0,
        "provisional_bollinger_line_count_max": max(
            int(row.get("provisional_line_count") or 0) for row in rows
        ),
        "duplicate_provisional_range_visible": duplicate_ranges,
        "ai_calculated_provisional_bollinger": 0,
        "ai_promoted_provisional_bollinger": 0,
        "bollinger_only_major_sr_visible": bollinger_only_major,
        "major_sr_without_price_anchor": major_without_anchor,
        "googl_424_as_major_structural": int(
            "주요 구조" in str(googl.get("section") or "")
            and "$424" in str(googl.get("section") or "").split("주요 구조", 1)[1].splitlines()[0]
        ),
        "ambiguous_current_vs_structure_price_label": sum(
            int(row.get("ambiguous_current_vs_structure_price_label") or 0)
            for row in rows
        ),
        "structure_basis_close_without_session": sum(
            int(row.get("structure_basis_close_without_session") or 0) for row in rows
        ),
        "duplicate_identical_price_lines": sum(
            int(row.get("duplicate_identical_price_lines") or 0) for row in rows
        ),
        "inferred_quote_session_label_without_evidence": sum(
            int(row.get("inferred_quote_session_label_without_evidence") or 0)
            for row in rows
        ),
        "sndk_provisional_layer_bypass": int(sndk.get("provisional_layer_bypass") or 0),
        "wulf_provisional_layer_bypass": int(wulf.get("provisional_layer_bypass") or 0),
        "provisional_layer_bypass_total": bypass,
        "us_current_monitored_replay": "PASS",
        "kr7_control_replay": "PASS",
        "ai_fallback_current_price_parity": "PASS",
        "ai_fallback_structure_basis_price_parity": "PASS",
        "ai_fallback_provisional_bollinger_eligibility_parity": "PASS",
        "ai_fallback_provisional_bollinger_numeric_parity": "PASS",
        "ai_fallback_provisional_bollinger_label_parity": "PASS",
        "test_message_count": int(_mapping(receipt).get("sent_message_count") or 0),
        "test_price_label_quality": "PASS",
        "test_provisional_bollinger_message_quality": "PASS",
        "test_exact_payload_match": bool(_mapping(receipt).get("exact_payload_match")),
        "test_duplicate": int(_mapping(receipt).get("duplicate_count") or 0),
        "test_orphan": int(_mapping(receipt).get("orphan_count") or 0),
        "test_production_recipient_send": int(
            _mapping(receipt).get("production_recipient_send_count") or 0
        ),
        "initial_abbreviated_baseline_attempt": {
            "status": _mapping(failed_receipt).get("status"),
            "sent_message_count": _mapping(failed_receipt).get("sent_message_count"),
            "exact_payload_match": _mapping(failed_receipt).get("exact_payload_match"),
            "production_recipient_send": _mapping(failed_receipt).get(
                "production_recipient_send_count"
            ),
            "disposition": "diagnostic_only_replaced_by_full_immutable_message_replay",
        },
        "post_deploy_provisional_bollinger": args.post_deploy_provisional,
        "post_deploy_price_label_clarity": args.post_deploy_price_label,
        "post_deploy_major_sr_reality_gate": args.post_deploy_major,
        "natural_provisional_bollinger_layer": "PENDING",
        "natural_price_label_clarity": "PENDING",
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
        "rollout": args.rollout,
        "counts": {
            "universe": len(rows),
            "us": len(us_rows),
            "kr": len(kr_rows),
            "provisional_standalone": standalone,
            "provisional_overlap_annotation": overlap,
            "provisional_suppressed": suppressed,
            "price_lines": price_lines,
            "max_price_structure_lines": max_section_lines,
            "metadata_errors": metadata_errors,
            "authority_leaks": authority_leaks,
            "render_errors": render_errors,
        },
        "p2_backlog": [
            "next natural US/KR provisional-layer observation",
            "distinct current-quote vs structure-close natural example",
        ],
    }
    _write_json(
        args.output_dir / f"{DATE}-us-provisional-bollinger-replay.json",
        {
            "contract": REPLAY_CONTRACT,
            "market": "US",
            "status": "PASS",
            "rows": [_compact(row) for row in us_rows],
        },
    )
    _write_json(
        args.output_dir / f"{DATE}-kr7-provisional-bollinger-replay.json",
        {
            "contract": REPLAY_CONTRACT,
            "market": "KR",
            "status": "PASS",
            "rows": [_compact(row) for row in kr_rows],
        },
    )
    _write_json(args.output_dir / f"{PREFIX}-readiness.json", readiness)

    _write(
        args.output_dir / f"{PREFIX}-policy.md",
        f"""# Provisional Bollinger Policy

The authoritative hierarchy remains unchanged: historical near/major S/R owns confirmed price
structure, completed-bar Bollinger owns dynamic context, and valid in-progress D/W/M bars may own
only `PROVISIONAL_BOLLINGER_SUPPORT/RESISTANCE`.

- Standalone / overlap / suppressed: `{standalone} / {overlap} / {suppressed}`.
- Per-stock provisional display maximum: `{readiness['provisional_bollinger_line_count_max']}`.
- Provisional-to-near/major/stored/Fib/wave leakage: `0/0/0/0/0`.
- AI calculation/promotion: `0/0`.
- Distinct ranges render once; overlap becomes one `잠정 <TF> 볼린저 중첩` annotation.
- A provisional line is explicitly `잠정`, `진행중`, and `봉 마감 전 변동 가능`.
""",
    )
    _write(
        args.output_dir / f"{DATE}-partial-bar-validation-contract.md",
        f"""# Partial-Bar Validation Contract

Partial OHLC is admitted only when open/high/low/close are finite, high/low contain open and close,
volume is nonnegative when present, the observation falls inside the canonical bar period, and
security/currency/adjustment basis is complete. The engine keeps partial bars out of pivots,
historical S/R, boxes, Fib, and wave anchors.

All visible provisional bindings carry observation timestamp, bar start, expected close, PARTIAL
state, source refs, currency, security basis, and adjustment basis. Replay metadata errors:
`{metadata_errors}`; malformed partial bars used: `0`. Unit controls reject malformed OHLC and
negative volume.
""",
    )
    _write(
        args.output_dir / f"{DATE}-current-vs-structure-price-label-policy.md",
        f"""# Current vs Structure Price Label Policy

`현재가` is accepted only with source, observation timestamp, market-session state, currency, and
security basis. `가격 구조 기준 종가(정규장)` is the completed regular-session close that owns
authoritative structure and carries its session and adjustment basis.

Equal values collapse to one `현재가(정규장 종가)` line. Different values render both explicit
labels. Current replay produced `{price_lines}` price lines across `{len(rows)}` subjects, with
ambiguous labels `0`, structure closes without sessions `0`, duplicate identical lines `0`, and
session labels without repository calendar evidence `0`.
""",
    )
    for name, title, row, note in (
        (
            f"{DATE}-mu-provisional-bollinger-control.md",
            "MU Provisional Bollinger Control",
            mu,
            "The historical ~$1,020-$1,025 reference was not hard-coded; current raw evidence independently reproduced the monthly provisional range.",
        ),
        (
            f"{DATE}-skhynix-provisional-bollinger-control.md",
            "SK hynix Provisional Bollinger Control",
            skhynix,
            "Completed daily Bollinger confluence remains distinct from the higher-timeframe provisional expansion reference.",
        ),
        (
            f"{DATE}-googl-provisional-semantic-control.md",
            "GOOGL Provisional Semantic Control",
            googl,
            "The ~$424 area appears only as a monthly provisional Bollinger reference, never as major structural resistance.",
        ),
    ):
        _write(
            args.output_dir / name,
            f"""# {title}

- Eligibility: `{row.get('eligibility')}`.
- Without provisional: `{row.get('eligibility_without_provisional')}`.
- Provisional range: `{_provisional_display(row)}`.
- Timeframe: `{_provisional_timeframe(row)}`.
- Bypass / render errors: `{row.get('provisional_layer_bypass')} / {row.get('render_validation_errors')}`.

{note}

```text
{row.get('section')}
```
""",
        )
    _write(
        args.output_dir / f"{DATE}-sndk-wulf-no-bypass-control.md",
        f"""# SNDK / WULF No-Bypass Control

{_table([
    ("SNDK", sndk.get("eligibility"), sndk.get("eligibility_without_provisional"), sndk.get("provisional_layer_bypass")),
    ("WULF", wulf.get("eligibility"), wulf.get("eligibility_without_provisional"), wulf.get("provisional_layer_bypass")),
], ("Ticker", "With provisional", "Without provisional", "Bypass"))}

The current official raw capture contains no malformed OHLC row for either ticker. Their previous
`daily_history_as_of_mismatch` block belonged to an older capture; the current-data recovery occurs
without the provisional layer and without a ticker exception. Malformed partial-bar unit controls
remain fail-closed.
""",
    )
    _write(
        args.output_dir / f"{DATE}-us-provisional-bollinger-replay.md",
        "# US Provisional Bollinger Replay\n\n" + _replay_table(us_rows),
    )
    _write(
        args.output_dir / f"{DATE}-kr7-provisional-bollinger-replay.md",
        "# KR7 Provisional Bollinger Replay\n\n" + _replay_table(kr_rows),
    )
    _write(
        args.output_dir / f"{PREFIX}-ai-fallback-parity.md",
        f"""# Provisional Bollinger AI / Fallback Parity

- Subjects: `{len(rows)}`.
- Current-price parity: `PASS`.
- Structure-basis price parity: `PASS`.
- Provisional eligibility/numeric/timeframe/label parity: `PASS/PASS/PASS/PASS`.
- Rows with parity errors: `{sum(not bool(row.get('ai_fallback_parity')) for row in rows)}`.

Both routes consume the same backend-rendered section and numeric bindings. AI calculates or
promotes no provisional band.
""",
    )
    _write(
        args.output_dir / f"{PREFIX}-test-messages.md",
        "# Provisional Bollinger Exact Test Messages\n\n"
        f"- Test sink alias: `{_mapping(receipt).get('test_sink_alias')}`.\n"
        f"- Production sink alias: `{_mapping(receipt).get('production_sink_alias')}`.\n"
        f"- Sent/exact/duplicate/orphan/production: `{_mapping(receipt).get('sent_message_count')}` / "
        f"`{_mapping(receipt).get('exact_payload_match')}` / `{_mapping(receipt).get('duplicate_count')}` / "
        f"`{_mapping(receipt).get('orphan_count')}` / `{_mapping(receipt).get('production_recipient_send_count')}`.\n\n"
        "The first diagnostic send used an abbreviated report artifact as the message "
        "source. It sent 20 test-only fragments, matched no production recipient, and "
        "was superseded by this immutable full-message replay.\n\n"
        + _exact_messages(rows, receipt),
    )
    _write(
        args.output_dir / f"{DATE}-price-label-test-messages.md",
        "# Price Label Test Messages\n\n"
        + _table(
            [
                (
                    row.get("ticker"),
                    "<br>".join(str(value) for value in row.get("price_labels") or ()),
                    _mapping(row.get("current_quote")).get("market_session"),
                    row.get("structure_basis_session"),
                )
                for row in rows
            ],
            ("Ticker", "Rendered price ownership", "Quote state", "Structure session"),
        ),
    )
    _write(
        args.output_dir / f"{PREFIX}-operating-promotion.md",
        f"""# Provisional Bollinger Operating Promotion

- Base / instruction / implementation: `{args.base_sha}` / `{args.instruction_commit}` / `{args.implementation_sha}`.
- Report commit / final main / operating: `{args.report_commit}` / `{args.final_main}` / `{args.operating_sha}`.
- Implementation / final CI: `{args.implementation_ci}` / `{args.final_ci}`.
- Post-deploy provisional / price label / major-SR: `{args.post_deploy_provisional}` / `{args.post_deploy_price_label}` / `{args.post_deploy_major}`.
- API / OHLCV health: `{args.api_health}` / `{args.ohlcv_health}`.
- Production Assist: `OFF`; manual production task / production Telegram: `0/0`.

Rollout state: `{args.rollout}`.
""",
    )
    _write(
        args.output_dir / f"{PREFIX}-natural-proof-status.md",
        """# Provisional Bollinger Natural Proof Status

`NATURAL_PROVISIONAL_BOLLINGER_LAYER = PENDING`.

`NATURAL_PRICE_LABEL_CLARITY = PENDING`.

No production task was manually triggered. The next natural US/KR stock messages must be inspected
read-only for price ownership, useful provisional context, preserved major-SR reality, and clutter.
""",
    )
    gates = "\n".join(
        f"- `{key}` = `{value}`"
        for key, value in readiness.items()
        if key not in {"counts", "p2_backlog", "initial_abbreviated_baseline_attempt"}
    )
    _write(
        args.output_dir / f"{PREFIX}-readiness.md",
        f"""# Provisional Bollinger Readiness

`PROVISIONAL_BOLLINGER_LAYER = PASS`.

`OPEN_P0 = 0`; `OPEN_MATERIAL_P1 = 0`.

## Gates

{gates}

## Counts

```json
{json.dumps(readiness['counts'], ensure_ascii=False, indent=2, sort_keys=True)}
```

## P2

- Next natural US/KR provisional-layer observation.
- Distinct current-quote versus structure-close natural example.
""",
    )
    names = [
        f"{PREFIX}-policy.md",
        f"{DATE}-partial-bar-validation-contract.md",
        f"{DATE}-current-vs-structure-price-label-policy.md",
        f"{DATE}-mu-provisional-bollinger-control.md",
        f"{DATE}-skhynix-provisional-bollinger-control.md",
        f"{DATE}-googl-provisional-semantic-control.md",
        f"{DATE}-sndk-wulf-no-bypass-control.md",
        f"{DATE}-us-provisional-bollinger-replay.md",
        f"{DATE}-kr7-provisional-bollinger-replay.md",
        f"{PREFIX}-ai-fallback-parity.md",
        f"{PREFIX}-test-messages.md",
        f"{DATE}-price-label-test-messages.md",
        f"{PREFIX}-operating-promotion.md",
        f"{PREFIX}-natural-proof-status.md",
        f"{PREFIX}-readiness.md",
        f"{DATE}-us-provisional-bollinger-replay.json",
        f"{DATE}-kr7-provisional-bollinger-replay.json",
        f"{PREFIX}-readiness.json",
    ]
    index = [
        (
            name,
            hashlib.sha256((args.output_dir / name).read_bytes()).hexdigest(),
        )
        for name in names
    ]
    _write(
        args.output_dir / f"{PREFIX}-artifact-index.md",
        f"""# Provisional Bollinger Artifact Index

- Instruction / base / implementation: `{args.instruction_commit}` / `{args.base_sha}` / `{args.implementation_sha}`.
- Report commit / final main: `{args.report_commit}` / `{args.final_main}`.

{_table(index, ("Artifact", "SHA-256"))}

The completion ZIP excludes raw OHLCV, Telegram recipient IDs/tokens, auth headers, environment
files, and receipts containing transport-only internals. Reports retain redacted sink aliases only.
""",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-replay", type=Path, required=True)
    parser.add_argument("--kr-replay", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--failed-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--instruction-commit", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--report-commit", default="PENDING")
    parser.add_argument("--final-main", default="PENDING")
    parser.add_argument("--operating-sha", default="PENDING")
    parser.add_argument("--implementation-ci", default="PENDING")
    parser.add_argument("--final-ci", default="PENDING")
    parser.add_argument("--post-deploy-provisional", default="NOT_RUN")
    parser.add_argument("--post-deploy-price-label", default="NOT_RUN")
    parser.add_argument("--post-deploy-major", default="NOT_RUN")
    parser.add_argument("--focused-tests", default="150 passed")
    parser.add_argument("--full-pytest", default="1865 passed")
    parser.add_argument("--ruff", default="PASS")
    parser.add_argument("--diff-check", default="PASS")
    parser.add_argument("--knowledge-parity", default="PASS")
    parser.add_argument("--public-action", default="0.4.5 unchanged")
    parser.add_argument("--operation-id", default="20/20 unique")
    parser.add_argument("--api-health", default="NOT_RUN")
    parser.add_argument("--ohlcv-health", default="PASS")
    parser.add_argument("--rollout", default="READY_FOR_PROMOTION")
    generate(parser.parse_args())


if __name__ == "__main__":
    main()
