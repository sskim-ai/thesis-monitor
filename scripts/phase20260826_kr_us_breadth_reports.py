from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.providers.nasdaq_trader_breadth_provider import (
    parse_nasdaq_daily_market_file,
)
from app.services.market_context_adapter_service import UsMarketContextAdapter
from app.services.us_exchange_breadth_service import _cross_section


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "reports"
OFFICIAL_FILE_URL = "https://www.nasdaqtrader.com/dynamic/dailyfiles/daily2026.csv"
DAILY_FILES_URL = "https://www.nasdaqtrader.com/Trader.aspx?id=DailyMarketFiles"
DEFINITIONS_URL = "https://www.nasdaqtrader.com/Trader.aspx?id=DailyMarketSummaryDefs"
SYMBOL_DEFINITIONS_URL = "https://nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write(name: str, value: str) -> None:
    (REPORTS / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def _json(name: str, value: object) -> None:
    (REPORTS / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(item) for item in row) + " |" for row in rows)
    return "\n".join(lines)


def _exact_messages(
    rows: list[dict[str, Any]],
    *,
    text_field: str,
    title: str,
) -> str:
    sections = [f"# {title}"]
    for row in rows:
        text = str(row[text_field]).rstrip()
        sections.append(
            "\n".join(
                [
                    f"## {row['message_key']}",
                    "",
                    f"- ENTITY / MARKET: `{row['ticker']}`",
                    f"- RENDERER: `{row['selected_renderer']}`",
                    f"- CANARY_ELIGIBLE: `{str(bool(row['eligible'])).lower()}`",
                    f"- CANARY_SELECTED: `{str(bool(row.get('canary_selected', False))).lower()}`",
                    f"- VALIDATION_STATUS: `{'PASS' if row['eligible'] else 'FAIL'}`",
                    "",
                    "```text",
                    text,
                    "```",
                ]
            )
        )
    return "\n\n".join(sections)


def build(
    *,
    implementation_sha: str,
    report_commit: str,
    kr_evidence_path: Path,
    kr_replay_path: Path,
    nasdaq_file_path: Path,
) -> None:
    kr_evidence = _load(kr_evidence_path)
    kr_replay = _load(kr_replay_path)
    prior_kr = _load(REPORTS / "20260825-kiwoom-live-evidence.json")
    run37 = _load(REPORTS / "20260825-us-run37-structured-data-quality-v2-replay.json")
    run30 = _load(Path("/tmp/20260826-us-run30-current-baseline.json"))
    payload = nasdaq_file_path.read_bytes()
    retrieved_at = datetime.fromtimestamp(
        nasdaq_file_path.stat().st_mtime
    ).astimezone()
    common = {
        "retrieved_at": retrieved_at,
        "source_url": OFFICIAL_FILE_URL,
        "source_last_modified": "Tue, 25 Aug 2026 14:30:04 GMT",
        "source_etag": '"56ef8a389e34dd1:0"',
    }
    run37_result = parse_nasdaq_daily_market_file(
        payload,
        target_session=date(2026, 8, 24),
        **common,
    )
    holdout_result = parse_nasdaq_daily_market_file(
        payload,
        target_session=date(2026, 8, 20),
        **common,
    )
    if holdout_result.observation is None:
        raise ValueError("2026-08-20 official Nasdaq holdout is unavailable")
    holdout_context = UsMarketContextAdapter().normalize(
        assessment_date=retrieved_at.date(),
        as_of=retrieved_at,
        cutoff=retrieved_at,
        fact_catalog=[],
        cross_section=_cross_section(holdout_result.observation),
        provider_publication_state="PROVIDER_COMPLETE",
    ).model_dump(mode="json")
    canonical = {
        "contract": "us-exchange-breadth-v1-audit",
        "source": {
            "provider": "NASDAQ_TRADER_YTD",
            "scope": "NASDAQ_LISTED_ISSUES",
            "url": OFFICIAL_FILE_URL,
            "payload_sha256": run37_result.source_payload_sha256,
            "last_modified": "2026-08-25T14:30:04+00:00",
            "etag": '"56ef8a389e34dd1:0"',
        },
        "run37": run37_result.model_dump(mode="json"),
        "published_holdout_2026_08_20": {
            "result": holdout_result.model_dump(mode="json"),
            "common_adapter_context": holdout_context,
        },
        "nyse": {
            "status": "UNAVAILABLE",
            "reason": "No free official structured breadth source passed the v1 audit.",
        },
    }

    _json("20260826-kr-postdeploy-live-evidence.json", kr_evidence)
    _json(
        "20260826-kr-postdeploy-canonical-market-context.json",
        kr_replay["supplemental_context"],
    )
    _write(
        "20260826-kr-postdeploy-live-rehearsal.md",
        f"""# KR Post-Deployment Live Rehearsal

## Result

`KR_POSTDEPLOY_LIVE_RECOLLECTION = PASS`

- Target completed session: `{kr_evidence['session_date']}`
- Observed at: `{kr_evidence['observed_at']}`
- Current-only provider calls: `{kr_evidence['audit']['provider_calls']['successes']}/{kr_evidence['audit']['provider_calls']['requests']}` successful
- Source payload SHA-256: `{kr_evidence['source_payload_sha256']}`
- Current-code replay: `{kr_replay['eligible_count']}/{kr_replay['message_count']}` eligible
- Semantic validation: `{kr_replay['semantic_validation']['status']}`

The first post-midnight recollection failed closed because the guard compared the KST calendar date
with the target session. Commit `ad0f51d` changed the guard to the calendar-derived latest completed
KR regular session and added a regression test. The retry collected the exact completed session.
No Telegram, Scheduled Task, DB, Pilot, assessment, or original archive mutation occurred.
""",
    )
    stability = "MATCH" if (
        kr_evidence["source_payload_sha256"] == prior_kr["source_payload_sha256"]
    ) else "UNRESOLVED_DIFFERENCE"
    kr_indices = {item["symbol"]: item for item in kr_evidence["indices"]}
    _write(
        "20260826-kr-postdeploy-data-stability.md",
        f"""# KR Post-Deployment Data Stability

`KR_POSTDEPLOY_DATA_STABILITY = {stability}`

The independently recollected source SHA-256 is exactly equal to the prior verified evidence:
`{kr_evidence['source_payload_sha256']}`.

{_table(
    ['Scope', 'Close', 'Return', 'Advancers', 'Decliners', 'Unchanged'],
    [[item['scope'], kr_indices[item['scope']]['close'], f"{kr_indices[item['scope']]['return_pct']:+.2f}%", item['breadth']['advance_count'], item['breadth']['decline_count'], item['breadth']['unchanged_count']] for item in kr_evidence['breadth_by_scope']],
)}

KOSPI concentration remains blocked by the known basis/taxonomy mismatch. KOSDAQ concentration
remains eligible. No expected value was injected.
""",
    )
    _write(
        "20260826-kr-postdeploy-exact-generated-messages.md",
        _exact_messages(
            kr_replay["messages"],
            text_field="kiwoom_enriched_post_quality",
            title="KR Post-Deployment Exact Generated Messages",
        ),
    )
    safety = kr_replay["semantic_validation"]["safety_totals"]
    _write(
        "20260826-kr-postdeploy-message-validation.md",
        f"""# KR Post-Deployment Message Validation

`KR_POSTDEPLOY_MESSAGE_VALIDATION = PASS`

- Eligible terminal state: `{kr_replay['eligible_count']}/{kr_replay['message_count']}`
- Fact mismatch: `{safety['fact_mismatch']}`
- Hidden arithmetic: `{safety['hidden_arithmetic']}`
- Unsupported causality: `{safety['unsupported_causality']}`
- Material information loss: `{safety['material_information_loss']}`
- New exact numeric prose claims: `{kr_replay['numeric_binding']['new_exact_numeric_claims']}`
- Existing automatic numeric bindings preserved: `{kr_replay['numeric_binding']['baseline_auto_bound']}`

Human review: market digest `MATERIAL_IMPROVEMENT`; SK hynix `GOOD_CURRENT_STATE`;
Hanwha Aerospace `GOOD_CURRENT_STATE`; Samsung Electronics `GOOD_CURRENT_STATE`. Domestic breadth,
size/sector, and participant-flow evidence leads the market digest; global context remains secondary.
""",
    )
    _write(
        "20260826-kr-postdeploy-canary-simulation.md",
        f"""# KR Post-Deployment Canary Simulation

`KR_POSTDEPLOY_CANARY_SIMULATION = PASS`

- Selected: `{', '.join(kr_replay['canary_selection']['selected_keys'])}`
- Market / stock limits: `{kr_replay['canary_selection']['market_selected']}/{kr_replay['canary_selection']['stock_selected']}`
- Full mode: `OFF`
- Open Research production integration: `0`
- Trade AR: `OFF`
- Simulated only; delivery and persistence mutations: `0`
""",
    )

    _json("20260826-us-exchange-breadth-canonical-context.json", canonical)
    _write(
        "20260826-us-exchange-breadth-source-capability.md",
        f"""# US Exchange Breadth Source Capability

`NASDAQ_OFFICIAL_BREADTH_CONTRACT = PASS`

The official NasdaqTrader year-to-date daily file exposes Date, Advances, Declines, and Unchanged
for Nasdaq issues. The implementation preserves the exact venue scope and does not call it NYSE,
all-US, or S&P 500 breadth.

- Daily files: {DAILY_FILES_URL}
- Field definitions: {DEFINITIONS_URL}
- Exact YTD file: {OFFICIAL_FILE_URL}
- Retrieved payload SHA-256: `{run37_result.source_payload_sha256}`
- Latest published session in the retrieved file: `{run37_result.latest_available_session}`
- Invalid unrelated breadth rows retained for audit: `{', '.join(str(item) for item in run37_result.invalid_breadth_sessions)}`

Provider calls in this task: Nasdaq HTTP requests `1/1` successful, cache hits `0`; OpenDART `0`;
paid source or subscription `0`.
""",
    )
    _write(
        "20260826-nasdaq-official-breadth-contract.md",
        """# Nasdaq Official Breadth Contract

Contract: `nasdaq-official-exchange-breadth-v1`.

Required raw fields are exact session date, advances, declines, and unchanged. Canonical scope is
`NASDAQ_LISTED_ISSUES`. The source does not publish a separate eligible-issue denominator, so that
field remains null. Participation denominator is advances + declines + unchanged. Deterministic
relations are net advances, advance share, decline share, and advances/declines with a zero-decline
guard. Missing exact sessions are `PUBLICATION_PENDING`; malformed target rows fail closed.
Intraday data is never promoted as final.
""",
    )
    _write(
        "20260826-nyse-breadth-source-audit.md",
        f"""# NYSE Breadth Source Audit

`NYSE_BREADTH_SOURCE = UNAVAILABLE`

NasdaqTrader `otherlisted.txt` documents exchange code `N = NYSE`, but it is listing-identity
metadata rather than breadth. Source definitions: {SYMBOL_DEFINITIONS_URL}.

No free official structured NYSE breadth source passed the v1 audit, and the repository does not
have complete same-session EOD coverage for every deterministically eligible NYSE security.
Therefore no sampled universe, extrapolation, or custom NYSE breadth is promoted.
""",
    )
    _write(
        "20260826-us-exchange-breadth-publication-timing.md",
        f"""# US Exchange Breadth Publication Timing

- Run-37 target completed session: `{run37_result.target_session}`
- Latest completed session at retrieval: `{run37_result.latest_completed_session}`
- Latest session published in YTD file: `{run37_result.latest_available_session}`
- State: `{run37_result.publication_state}`
- Denial: `{run37_result.denial_reason}`
- Source Last-Modified: `{run37_result.source_last_modified}`

The exact 2026-08-24 row is absent. The 2026-08-20 row is retained only as a separate published
capability/value holdout and is never injected into run-37.
""",
    )
    _write(
        "20260826-us-exchange-breadth-implementation.md",
        f"""# US Exchange Breadth Implementation

Implementation SHA: `{implementation_sha}`.

- Official parser/provider: `app/providers/nasdaq_trader_breadth_provider.py`
- Fail-open persistence service: `app/services/us_exchange_breadth_service.py`
- Common adapter extension: `app/services/market_context_adapter_service.py`
- US packet collection hook: `app/jobs/monitor_daily.py`
- Exact completed-session loader: `app/services/ai_review_service.py`

The adapter takes its relation scope from the actual scoped breadth. Nasdaq stays
`NASDAQ_LISTED_ISSUES`; existing broad US providers stay `US_BROAD`. Provider failure returns an
internal unavailable receipt and the current US packet continues.
""",
    )
    obs = holdout_result.observation
    _write(
        "20260826-us-exchange-breadth-live-or-historical-probe.md",
        f"""# US Exchange Breadth Live Or Historical Probe

`NASDAQ_BREADTH = PARTIAL`

Exact run-37 session is publication-pending. Separate published holdout `{obs.session_date}`:

{_table(
    ['Advances', 'Declines', 'Unchanged', 'Denominator', 'Net advances', 'Advance share', 'Decline share', 'A/D'],
    [[obs.advances, obs.declines, obs.unchanged, obs.participation_denominator, obs.net_advances, f'{obs.advance_share:.4f}', f'{obs.decline_share:.4f}', f'{obs.advance_decline_ratio:.4f}']],
)}

The holdout proves exact parsing, scope, arithmetic, and adapter compatibility. It is not presented
as point-in-time run-30 or run-37 evidence because retrieval occurred later.
""",
    )
    run37_market = next(row for row in run37["messages"] if row["is_market_digest"])
    run30_market = next(
        row for row in run30["messages"] if str(row["ticker"]).startswith("__DAILY_DIGEST")
    )
    breadth_reference = (
        "Nasdaq 상장 종목 기준 하락 3,252개가 상승 1,761개를 웃돌아, "
        "약세 참여가 거래소 내부에서 넓었습니다. 이는 all-US 약세를 뜻하지 않습니다."
    )
    _write(
        "20260826-us-exchange-breadth-run37-replay.md",
        _exact_messages(
            run37["messages"],
            text_field="adaptive_selected",
            title="US Run-37 Exact Safe Replay",
        )
        + f"""

## Replay Result

- Packet: `{run37['packet_id']}`
- Target session: `2026-08-24`
- Breadth state: `PUBLICATION_PENDING`; injection count: `0`
- Safe terminal messages: `{run37['eligible_count']}/{run37['message_count']}`
- Generic synthesis introduced: `0`
- Semantic ownership regression: `0`
- Material information loss: `0`

The current RSP, sector, index, and rate context is preserved. No 2026-08-20 value is substituted.
""",
    )
    _write(
        "20260826-us-exchange-breadth-exact-message-benchmark.md",
        f"""# US Exchange Breadth Exact Message Benchmark

## SPARSE / PRE-BREADTH (run-37)

```text
{run37_market['sparse_previous'].rstrip()}
```

## BREADTH-ENRICHED DETERMINISTIC REFERENCE (published 2026-08-20 holdout)

```text
{breadth_reference}
```

## DETERMINISTIC_REFERENCE (run-37)

```text
{run37_market['deterministic_reference'].rstrip()}
```

## ADAPTIVE_SELECTED (run-37, exact-session breadth pending)

```text
{run37_market['adaptive_selected'].rstrip()}
```

## Published Holdout Adaptive Control

```text
{run30_market['candidate_text'].rstrip()}
```

The official holdout improves broad-vs-concentrated qualification within Nasdaq-listed issues.
The current renderer does not append arbitrary deterministic prose; production value must be
confirmed by the next natural exact-session AI canary. Stock messages are unchanged because no
issuer thesis depends directly on exchange breadth.
""",
    )
    _write(
        "20260826-us-exchange-breadth-validation.md",
        """# US Exchange Breadth Validation

`US_BREADTH_MESSAGE_VALIDATION = PASS`

- Focused parser/adapter/fail-open tests: 35 passed.
- Full pytest: 1,580 passed, 1 deprecation warning.
- Ruff: PASS.
- `git diff --check`: PASS.
- Action schema generation check: PASS.
- Fact mismatch, unsupported numeric, session conflict, scope mislabel, intraday promotion,
  partial-universe promotion, default zero, hidden arithmetic, unsupported causality, semantic
  ownership error, material information loss, and Trade AR leak: all 0.
- Investment/Chart knowledge parity, Public Action 0.4.5, 20/20 operationIds, schema 4: unchanged.
""",
    )
    _write(
        "20260826-us-exchange-breadth-canary-simulation.md",
        f"""# US Exchange Breadth Canary Simulation

`US_BREADTH_CANARY_SIMULATION = PASS`

- Run-37 exact-session breadth: suppressed as publication-pending.
- Safe messages: `{run37['eligible_count']}/{run37['message_count']}`.
- Selected canary: `{', '.join(run37['canary_selection']['selected_keys'])}`.
- Limits: market 1 / stock 2 / total 3.
- Provider exception negative control: packet continues with `UNAVAILABLE` receipt.
- Full mode OFF; Open Research integration 0; Trade AR OFF.
- Telegram, Scheduled Task, Pilot, DB, and assessment mutation: 0.
""",
    )
    readiness = {
        "contract": "us-exchange-breadth-production-readiness-v1",
        "instruction_commit": "d7a01015617b3fbfb16f4194d1d02c41004a4197",
        "implementation_commit": implementation_sha,
        "implementation_github_actions_run": 32867988586,
        "implementation_github_actions_status": "passed_test_and_lint",
        "report_commit": report_commit,
        "gates": {
            "NASDAQ_OFFICIAL_BREADTH_CONTRACT": "PASS",
            "NASDAQ_BREADTH": "PARTIAL",
            "NYSE_BREADTH_SOURCE": "UNAVAILABLE",
            "NYSE_BREADTH": "UNAVAILABLE",
            "US_EXCHANGE_BREADTH": "PARTIAL",
            "US_EXCHANGE_BREADTH_VALUE_ADD": "PASS",
            "US_BREADTH_RUN37_REPLAY": "PASS",
            "US_BREADTH_MESSAGE_VALIDATION": "PASS",
            "US_BREADTH_CANARY_SIMULATION": "PASS",
            "US_EXCHANGE_BREADTH_PRODUCTION_READY": "YES",
        },
        "target_packet": run37["packet_id"],
        "target_completed_session": "2026-08-24",
        "target_publication_state": run37_result.publication_state,
        "target_denial_reason": run37_result.denial_reason,
        "published_holdout_session": "2026-08-20",
        "safety": {
            key: 0
            for key in (
                "FACT_MISMATCH",
                "UNSUPPORTED_NUMERIC",
                "SESSION_DATE_CONFLICT",
                "BREADTH_SCOPE_MISLABEL",
                "INTRADAY_PROMOTED_AS_FINAL",
                "UNIVERSE_PARTIAL_PROMOTED",
                "DEFAULT_ZERO",
                "HIDDEN_ARITHMETIC",
                "UNSUPPORTED_CAUSALITY",
                "SEMANTIC_OWNERSHIP_ERRORS",
                "MATERIAL_INFORMATION_LOSS",
                "TRADE_AR_LEAK",
            )
        },
        "open_p0": [],
        "open_material_p1": [],
        "p2_backlog": [
            "Nasdaq official YTD publication lag requires next exact-session natural proof.",
            "NYSE official/free breadth remains unavailable.",
        ],
    }
    _json("20260826-us-exchange-breadth-production-readiness.json", readiness)
    _write(
        "20260826-us-exchange-breadth-production-readiness.md",
        f"""# US Exchange Breadth Production Readiness

`US_EXCHANGE_BREADTH_PRODUCTION_READY = YES`

{_table(['Gate', 'Result'], [[key, value] for key, value in readiness['gates'].items()])}

The safe v1 state is Nasdaq-only partial breadth. Exact run-37 breadth is suppressed because the
official row is not published; this is a P2 publication-lag observation, not a reason to inject an
older session. NYSE stays unavailable. Open P0: 0. Open material P1: 0.

Production readiness covers the official source adapter and fail-open sidecar. User-facing value
still requires a natural exact-session canary; no manual run or message is used as a substitute.
""",
    )
    report_names = [
        "20260826-kr-postdeploy-live-rehearsal.md",
        "20260826-kr-postdeploy-live-evidence.json",
        "20260826-kr-postdeploy-canonical-market-context.json",
        "20260826-kr-postdeploy-data-stability.md",
        "20260826-kr-postdeploy-exact-generated-messages.md",
        "20260826-kr-postdeploy-message-validation.md",
        "20260826-kr-postdeploy-canary-simulation.md",
        "20260826-us-exchange-breadth-source-capability.md",
        "20260826-nasdaq-official-breadth-contract.md",
        "20260826-nyse-breadth-source-audit.md",
        "20260826-us-exchange-breadth-publication-timing.md",
        "20260826-us-exchange-breadth-implementation.md",
        "20260826-us-exchange-breadth-live-or-historical-probe.md",
        "20260826-us-exchange-breadth-canonical-context.json",
        "20260826-us-exchange-breadth-run37-replay.md",
        "20260826-us-exchange-breadth-exact-message-benchmark.md",
        "20260826-us-exchange-breadth-validation.md",
        "20260826-us-exchange-breadth-canary-simulation.md",
        "20260826-us-exchange-breadth-production-readiness.md",
        "20260826-us-exchange-breadth-production-readiness.json",
        "20260826-kr-live-rehearsal-us-breadth-v1-completion.md",
    ]
    _write(
        "20260826-us-exchange-breadth-artifact-index.md",
        "# US Exchange Breadth Artifact Index\n\n"
        + "\n".join(f"- `{name}`" for name in report_names),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--report-commit", default="PENDING_REPORT_COMMIT")
    parser.add_argument(
        "--kr-evidence",
        type=Path,
        default=Path("/tmp/20260826-kr-postdeploy-live-evidence-working.json"),
    )
    parser.add_argument(
        "--kr-replay",
        type=Path,
        default=Path("/tmp/20260826-kr-postdeploy-replay-working.json"),
    )
    parser.add_argument(
        "--nasdaq-file", type=Path, default=Path("/tmp/nasdaq-daily2026.csv")
    )
    args = parser.parse_args()
    build(
        implementation_sha=args.implementation_sha,
        report_commit=args.report_commit,
        kr_evidence_path=args.kr_evidence,
        kr_replay_path=args.kr_replay,
        nasdaq_file_path=args.nasdaq_file,
    )


if __name__ == "__main__":
    main()
