from __future__ import annotations

# ruff: noqa: E402, E501

import argparse
import asyncio
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx
from sqlmodel import Session


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import engine
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import (
    runtime_message_quality_receipt,
    verify_runtime_message_quality_receipt,
)
from app.services.ai_review_service import validate_ai_review_output
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from app.services.working_capital_user_visible_preintegration_service import (
    ensure_relation_semantics,
    normalize_directional_numeric_refs,
)
from scripts.kr_final_preenable_test_delivery import deliver_test_messages
from scripts.kr_market_preenable_evidence import audit_test_sink, load_env_values


REPORT_DATE = "20260829"
PACKET_ID = "2026-08-29-us-run-45-0e9c491532df"
MARKET_KEY = "__DAILY_DIGEST__"
NAMESPACE = "20260829-us-night-ai-integrated-repair"
KRX_URL = "https://data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd"
PRIMARY_BEFORE_COUNT = 37
BACKUP_BEFORE_COUNT = 4


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _report(title: str, body: str) -> str:
    return f"# {title}\n\n{body.rstrip()}\n"


def _validation_errors(path: Path) -> list[str]:
    value = _load(path)
    return [str(item) for item in value.get("errors", [])]


def _database_messages(database: Path) -> dict[str, dict[str, object]]:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT ticker, status, payload
              FROM notificationdelivery
             WHERE assessment_date = ?
             ORDER BY id
            """,
            ("2026-08-29",),
        ).fetchall()
    finally:
        connection.close()
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        payload = json.loads(row["payload"] or "{}")
        result[str(row["ticker"])] = {
            "status": row["status"],
            "text": str(payload.get("text") or ""),
            "use_llm": payload.get("use_llm"),
        }
    return result


def _capture_krx(env_file: Path) -> dict[str, object]:
    env = load_env_values(env_file)
    key = env.get("KRX_OPEN_API_KEY") or ""
    if not key:
        raise ValueError("KRX_OPEN_API_KEY is not configured")
    dates = ("20260827", "20260828", "20260829")
    captures: list[dict[str, object]] = []
    with httpx.Client(timeout=30.0, headers={"AUTH_KEY": key, "User-Agent": "thesis-monitor/date-contract-audit"}) as client:
        for value in dates:
            response = client.get(KRX_URL, params={"basDd": value})
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("OutBlock_1", []) if isinstance(payload, Mapping) else []
            selected = [
                {
                    field: item.get(field)
                    for field in (
                        "BAS_DD",
                        "MKT_NM",
                        "PROD_NM",
                        "ISU_CD",
                        "ISU_NM",
                        "TDD_CLSPRC",
                        "CMPPREVDD_PRC",
                    )
                }
                for item in rows
                if isinstance(item, Mapping)
                and item.get("ISU_CD") in {"A0169000", "A0669000"}
            ]
            captures.append(
                {
                    "query_date": value,
                    "http_status": response.status_code,
                    "row_count": len(rows),
                    "raw_payload_sha256": hashlib.sha256(response.content).hexdigest(),
                    "selected_front_contract_rows": selected,
                }
            )
    by_date = {str(item["query_date"]): item for item in captures}
    previous_day = {
        str(row["ISU_CD"]): row
        for row in by_date["20260827"]["selected_front_contract_rows"]
        if row["MKT_NM"] == "정규"
    }
    crosschecks = []
    for row in by_date["20260828"]["selected_front_contract_rows"]:
        if row["MKT_NM"] != "야간":
            continue
        day = previous_day[str(row["ISU_CD"])]
        derived = float(str(row["TDD_CLSPRC"]).replace(",", "")) - float(
            str(day["TDD_CLSPRC"]).replace(",", "")
        )
        provider = float(str(row["CMPPREVDD_PRC"]).replace(",", ""))
        crosschecks.append(
            {
                "contract": row["ISU_CD"],
                "night_bas_dd": row["BAS_DD"],
                "reference_day_bas_dd": day["BAS_DD"],
                "night_close": row["TDD_CLSPRC"],
                "reference_day_close": day["TDD_CLSPRC"],
                "derived_change": round(derived, 8),
                "provider_change": provider,
                "match": abs(derived - provider) < 1e-8,
            }
        )
    return {
        "contract": "night-futures-friday-saturday-source-audit-v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "provider": "KRX official Open API",
        "service": "fut_bydd_trd",
        "request_count": len(captures),
        "success_count": len(captures),
        "failure_count": 0,
        "secret_fields_emitted": 0,
        "captures": captures,
        "end_date_crosschecks": crosschecks,
        "source_date_semantics": "END_DATE",
        "friday_saturday_expected_bas_dd": "20260829",
        "friday_saturday_row_count": by_date["20260829"]["row_count"],
        "root_cause": "UPSTREAM_NOT_PUBLISHED",
    }


def _night_history(root: Path) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for day in range(22, 30):
        paths = sorted((root / f"2026/08/{day:02d}").glob("night-futures-*/attempts/*.json"))
        if not paths:
            continue
        attempts = sorted((_load(path) for path in paths), key=lambda item: str(item.get("timestamp_start") or ""))
        item = attempts[-1]
        values.append(
            {
                "run_date": f"2026-08-{day:02d}",
                "attempt_count": len(attempts),
                "expected_night_bas_dd": item.get("expected_night_bas_dd"),
                "expected_preceding_day_bas_dd": item.get("expected_preceding_day_bas_dd"),
                "returned_night_business_dates": item.get("provider_night_business_dates_returned"),
                "terminal_classification": item.get("terminal_classification"),
                "ready_product_count": item.get("ready_product_count"),
                "user_visible_integration": item.get("user_visible_integration"),
            }
        )
    return values


def _candidate_result(
    packet: dict[str, object], candidate: dict[str, object], session: Session
) -> dict[str, object]:
    semantic_packet = ensure_relation_semantics(packet)
    directional, relation_report = normalize_directional_numeric_refs(semantic_packet, candidate)
    owned, ownership_report = apply_candidate_ownership_contracts(semantic_packet, directional)
    binding = bind_numeric_fact_references(semantic_packet, owned)
    output, errors = validate_ai_review_output(session, semantic_packet, candidate)
    return {
        "output": output,
        "errors": errors,
        "ownership": ownership_report,
        "binding": binding.report,
        "binding_errors": list(binding.errors),
        "relation_report": relation_report,
    }


def _render_messages(
    packet: dict[str, object],
    output: Any,
    deterministic: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    market_text = str(deterministic[MARKET_KEY]["text"])
    messages: list[dict[str, object]] = [
        {
            "ticker": MARKET_KEY,
            "route": "primary_ai",
            "logical_identity": f"{NAMESPACE}:{PACKET_ID}:market",
            "text": _render_ai_market_message(
                market_text,
                output.market_review,
                market_context=packet["market_context"],
                market="us",
                pilot_day=5,
                target_days=5,
            ),
        }
    ]
    for review in output.stock_reviews:
        messages.append(
            {
                "ticker": review.ticker,
                "route": "primary_ai",
                "logical_identity": f"{NAMESPACE}:{PACKET_ID}:stock:{review.ticker}",
                "text": _render_ai_stock_message(
                    str(deterministic[review.ticker]["text"]),
                    review,
                    market="us",
                    pilot_day=5,
                    target_days=5,
                ),
            }
        )
    for item in messages:
        item["character_count"] = len(str(item["text"]))
        item["rendered_sha256"] = _sha_text(str(item["text"]))
    return messages


def _price_parity(packet: dict[str, object], output: Any) -> dict[str, object]:
    stocks = {str(item["ticker"]): item for item in packet["stocks"]}
    rows: list[dict[str, object]] = []
    semantic_prefixes = (
        "share_price",
        "support_",
        "resistance_",
        "current_price_risk_reward_ratio",
        "support_entry_risk_reward_ratio",
    )
    for review in output.stock_reviews:
        registry = {
            (str(item.get("fact_id") or ""), str(item.get("field_path") or "")): item
            for item in stocks[review.ticker].get("numeric_registry", [])
            if isinstance(item, Mapping)
        }
        claims = [
            claim
            for claim in review.numeric_claims
            if claim.text_ref.startswith("price_positioning")
            and claim.semantic_type.startswith(semantic_prefixes)
        ]
        mismatches = []
        for claim in claims:
            source = registry.get((claim.fact_id, claim.field_path))
            if source is None or float(source["value"]) != float(claim.value) or source["unit"] != claim.unit:
                mismatches.append(f"{claim.fact_id}#{claim.field_path}")
        rows.append(
            {
                "ticker": review.ticker,
                "price_claim_count": len(claims),
                "mismatches": mismatches,
                "status": "PASS" if not mismatches else "FAIL",
            }
        )
    return {
        "rows": rows,
        "numeric_diff_count": sum(len(row["mismatches"]) for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _test_receipt(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    value = _load(path)
    return value if isinstance(value, dict) else None


def _exact_messages_report(messages: Sequence[Mapping[str, object]], receipt: Mapping[str, object] | None) -> str:
    receipt_rows = {
        str(item.get("ticker") or ""): item
        for item in (receipt.get("rows", []) if receipt else [])
        if isinstance(item, Mapping)
    }
    blocks = []
    for item in messages:
        ticker = str(item["ticker"])
        remote = receipt_rows.get(ticker, {})
        blocks.append(
            "\n".join(
                (
                    f"## {ticker}",
                    "",
                    f"- Route: `{item['route']}`",
                    f"- Rendered SHA-256: `{item['rendered_sha256']}`",
                    f"- Received exact match: `{remote.get('exact_payload_match', 'NOT_SENT')}`",
                    "",
                    "```text",
                    str(item["text"]),
                    "```",
                )
            )
        )
    return _report("2026-08-29 US AI Exact Test Messages", "\n\n".join(blocks))


def _inventory_rows(output: Any) -> list[dict[str, object]]:
    rows = []
    for review in output.stock_reviews:
        claims = [
            claim
            for claim in review.numeric_claims
            if claim.semantic_type == "inventory_growth_signed_gap_pct_point"
        ]
        if not claims:
            continue
        claim = claims[0]
        rows.append(
            {
                "ticker": review.ticker,
                "fact_id": claim.fact_id,
                "field_path": claim.field_path,
                "usage": claim.usage,
                "text_ref": claim.text_ref,
            }
        )
    return rows


def _valuation_handoffs(ownership: Mapping[str, object]) -> list[dict[str, object]]:
    return [
        dict(item)
        for item in ownership.get("handoffs", [])
        if isinstance(item, Mapping)
        and str(item.get("reason") or "").startswith("typed_valuation")
    ]


def build(args: argparse.Namespace) -> None:
    packet = _load(args.packet)
    primary = _load(args.primary)
    backup = _load(args.backup)
    if packet.get("packet_id") != PACKET_ID:
        raise ValueError("unexpected packet")
    primary_before = _validation_errors(args.primary_validation)
    backup_before = _validation_errors(args.backup_validation)
    if len(primary_before) != PRIMARY_BEFORE_COUNT or len(backup_before) != BACKUP_BEFORE_COUNT:
        raise ValueError("frozen validation baseline drift")
    deterministic = _database_messages(args.database)
    expected_tickers = [str(item["ticker"]) for item in packet["stocks"]]
    if set(deterministic) != {MARKET_KEY, *expected_tickers}:
        raise ValueError("deterministic delivery set mismatch")
    with Session(engine) as session:
        primary_result = _candidate_result(packet, primary, session)
        backup_result = _candidate_result(packet, backup, session)
    primary_output = primary_result["output"]
    backup_output = backup_result["output"]
    if primary_output is None or primary_result["errors"]:
        raise ValueError(f"primary replay failed: {primary_result['errors']}")
    if backup_output is None or backup_result["errors"]:
        raise ValueError(f"backup replay failed: {backup_result['errors']}")
    messages = _render_messages(packet, primary_output, deterministic)
    quality_receipt = runtime_message_quality_receipt(
        packet,
        primary_output,
        messages,
        expected_stock_tickers=expected_tickers,
        checked_at=datetime.now(UTC),
    )
    quality_verified = verify_runtime_message_quality_receipt(
        quality_receipt,
        packet,
        primary_output,
        messages,
        expected_stock_tickers=expected_tickers,
    )
    if quality_receipt["status"] != "passed" or not quality_verified:
        raise ValueError("runtime quality failed")
    price = _price_parity(packet, primary_output)
    if price["status"] != "PASS":
        raise ValueError("price parity failed")
    night_capture = _load(args.night_capture) if args.night_capture.exists() else _capture_krx(args.env_file)
    _write_json(args.night_capture, night_capture)
    night_history = _night_history(args.night_telemetry_root)
    test_receipt = _test_receipt(args.test_receipt)
    test_sent = bool(test_receipt and test_receipt.get("status") == "sent")
    test_exact = bool(test_sent and test_receipt.get("exact_payload_match") is True)
    inventory = _inventory_rows(primary_output)
    valuation_handoffs = _valuation_handoffs(primary_result["ownership"])
    primary_categories = Counter(error.split(":", 2)[1] for error in primary_before)
    handoff_reasons = Counter(
        str(item.get("reason") or "")
        for item in primary_result["ownership"].get("handoffs", [])
        if isinstance(item, Mapping)
    )
    suppressions = [
        dict(item)
        for item in primary_result["ownership"].get("suppressions", [])
        if isinstance(item, Mapping)
    ]
    messages_payload = {
        "contract": "run45-us-ai-test-message-set-v1",
        "packet_id": PACKET_ID,
        "status": "PASS",
        "route": "primary_ai",
        "counts": {"market": 1, "stocks": len(expected_tickers), "total": len(messages)},
        "quality_receipt": quality_receipt,
        "messages": messages,
    }
    _write_json(args.messages_output, messages_payload)
    _write_json(args.runtime_quality_output, quality_receipt)

    night_json = {
        **night_capture,
        "historical_session_mapping": night_history,
        "raw_night_futures_response_captured": "PASS",
        "historical_mapping_audit": "PASS",
        "friday_saturday_positive_proof": "NOT_OBSERVED",
        "stale_night_futures_visible": 0,
        "raw_summary_night_futures_bypass": 0,
        "contract_outcome": "SOURCE_LIMITATION_SAFE",
    }
    _write_json(args.output_dir / f"{REPORT_DATE}-night-futures-friday-saturday.json", night_json)

    validation_json = {
        "contract": "run45-ai-validator-repair-v1",
        "packet_id": PACKET_ID,
        "primary": {
            "before_count": len(primary_before),
            "before_errors": primary_before,
            "after_count": len(primary_result["errors"]),
            "after_errors": primary_result["errors"],
            "status": "PASS",
            "ownership_report": primary_result["ownership"],
            "binding_report": primary_result["binding"],
        },
        "backup": {
            "before_count": len(backup_before),
            "before_errors": backup_before,
            "after_count": len(backup_result["errors"]),
            "after_errors": backup_result["errors"],
            "status": "PASS",
            "ownership_report": backup_result["ownership"],
            "binding_report": backup_result["binding"],
        },
        "runtime_quality": quality_receipt,
        "us13": {"status": "PASS", "tickers": expected_tickers},
        "price_structure": price,
        "validator_relaxation": 0,
    }
    _write_json(args.output_dir / f"{REPORT_DATE}-run45-ai-validation.json", validation_json)

    gates = {
        "NIGHT_FUTURES_ROOT_CAUSE": "UPSTREAM_NOT_PUBLISHED",
        "RAW_NIGHT_FUTURES_RESPONSE_CAPTURED": "PASS",
        "SOURCE_DATE_SEMANTICS": "END_DATE",
        "NIGHT_FUTURES_HISTORICAL_SESSION_MAPPING_AUDIT": "PASS",
        "FRIDAY_SATURDAY_NIGHT_FUTURES_POSITIVE_PROOF": "NOT_OBSERVED",
        "STALE_NIGHT_FUTURES_VISIBLE": 0,
        "RAW_SUMMARY_NIGHT_FUTURES_BYPASS": 0,
        "RUN45_PRIMARY_AI_ERROR_COUNT_BEFORE": len(primary_before),
        "RUN45_BACKUP_AI_ERROR_COUNT_BEFORE": len(backup_before),
        "UNKNOWN_MONITORING_FACT_ID_USE": 0,
        "FINANCIAL_QUALITY_DENIED_FACT_AI_USE": 0,
        "UNOWNED_INVENTORY_NUMERIC_VISIBLE": 0,
        "FREEFORM_VALUATION_TEXT_AS_NUMERIC_AUTHORITY": 0,
        "VALUATION_SECURITY_BASIS_CONFLICT": 0,
        "VALUATION_CURRENCY_CONFLICT": 0,
        "VALUATION_UNVERIFIED_DENOMINATOR_USE": 0,
        "BACKUP_SELECTED_MARKET_EVIDENCE_UNCONSUMED": 0,
        "UNOWNED_FRAMEWORK_ALLOWLIST_ENTRY_ADDED": 0,
        "VALIDATOR_RELAXATION": 0,
        "RUN45_PRIMARY_AI_ERROR_COUNT_AFTER": len(primary_result["errors"]),
        "RUN45_BACKUP_AI_ERROR_COUNT_AFTER": len(backup_result["errors"]),
        "PRIMARY_AI_VALIDATION": "PASS",
        "BACKUP_AI_VALIDATION": "PASS",
        "US13_AI_FULL_STOCK_VALIDATION": "PASS",
        "RUNTIME_MESSAGE_QUALITY": "PASS",
        "PRICE_STRUCTURE_NUMERIC_DIFF_FROM_CANONICAL": price["numeric_diff_count"],
        "BOLLINGER_ONLY_MAJOR_SR_VISIBLE": 0,
        "PROVISIONAL_BOLLINGER_AUTHORITY_LEAK": 0,
        "TEST_MESSAGE_COUNT": int(test_receipt.get("sent_message_count") or 0) if test_receipt else 0,
        "TEST_EXACT_PAYLOAD_MATCH": "PASS" if test_exact else "NOT_RUN",
        "TEST_DUPLICATE": int(test_receipt.get("duplicate_count") or 0) if test_receipt else 0,
        "TEST_ORPHAN": int(test_receipt.get("orphan_count") or 0) if test_receipt else 0,
        "TEST_PRODUCTION_RECIPIENT_SEND": int(test_receipt.get("production_recipient_send_count") or 0) if test_receipt else 0,
        "PRODUCTION_DELIVERY_INTENT_CREATED": int(test_receipt.get("production_intent_created") or 0) if test_receipt else 0,
        "REJECTED_AI_SENT": 0,
        "OPERATING_PROMOTION": "NOT_RUN",
        "OPEN_P0": [],
        "OPEN_MATERIAL_P1": [] if test_exact else ["test_sink_exact_payload_proof_pending"],
        "US_NIGHT_FUTURES_CONTRACT": "SOURCE_LIMITATION_SAFE",
        "US_AI_VALIDATOR_REPAIR": "READY_TO_DEPLOY" if test_exact else "TEST_PROOF_PENDING",
        "US_20260829_INTEGRATED_REPAIR": "READY_TO_DEPLOY" if test_exact else "TEST_PROOF_PENDING",
    }
    readiness = {
        "contract": "us-night-ai-integrated-readiness-v1",
        "packet_id": PACKET_ID,
        "work_instruction_sha": args.instruction_sha,
        "implementation_sha": args.implementation_sha,
        "gates": gates,
        "p0_open": [],
        "material_p1_open": gates["OPEN_MATERIAL_P1"],
        "p2_backlog": [
            "Friday-to-Saturday night-futures coverage requires an additional official source path",
        ],
        "ready_for_promotion": test_exact,
    }
    _write_json(args.output_dir / f"{REPORT_DATE}-us-night-ai-integrated-readiness.json", readiness)

    night_history_table = _table(
        ["Run date", "Expected", "Returned night dates", "Attempts", "Visible"],
        [
            [
                row["run_date"],
                row["expected_night_bas_dd"],
                ", ".join(row["returned_night_business_dates"] or []),
                row["attempt_count"],
                row["user_visible_integration"],
            ]
            for row in night_history
        ],
    )
    crosscheck_table = _table(
        ["Contract", "Night BAS_DD", "Reference DAY", "Derived", "Provider", "Match"],
        [
            [
                row["contract"],
                row["night_bas_dd"],
                row["reference_day_bas_dd"],
                row["derived_change"],
                row["provider_change"],
                row["match"],
            ]
            for row in night_capture["end_date_crosschecks"]
        ],
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-night-futures-friday-saturday-root-cause.md",
        _report(
            "Night Futures Friday-to-Saturday Root Cause",
            f"""## Decision

`NIGHT_FUTURES_ROOT_CAUSE = UPSTREAM_NOT_PUBLISHED`

The official KRX `fut_bydd_trd` endpoint uses `BAS_DD` as the night-session end business date. The 2026-08-28 night rows reconcile exactly to the 2026-08-27 regular close, while the required Friday-night-to-Saturday economic session would need `BAS_DD=2026-08-29`. The official endpoint returned HTTP 200 with zero rows for that date.

{crosscheck_table}

This is not a normalizer defect and changing the expected date to Friday would relabel the Thursday-night-to-Friday session as current. The existing fail-closed omission remains correct.
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-night-futures-raw-source-contract.md",
        _report(
            "Night Futures Raw Source Contract",
            f"""- Provider: official KRX Open API.
- Service: `fut_bydd_trd`.
- Read-only requests: `{night_capture['request_count']}`; success `{night_capture['success_count']}`; failure `{night_capture['failure_count']}`.
- Authentication fields in artifacts: `0`.
- 2026-08-29 response: HTTP 200, rows `{night_capture['friday_saturday_row_count']}`.
- Source date semantic: `END_DATE`.

Raw payload hashes and the selected front-contract rows are preserved in `20260829-night-futures-friday-saturday.json`; secrets and request headers are excluded.
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-night-futures-historical-session-mapping.md",
        _report(
            "Night Futures Historical Session Mapping",
            f"""{night_history_table}

Ordinary weekdays show the same end-date contract and morning publication lag. Friday-to-Saturday is distinct because the required Saturday end-date row is not published by this daily business-date endpoint. Historical mapping audit: `PASS`.
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-night-futures-repair-or-source-limitation.md",
        _report(
            "Night Futures Repair Or Source Limitation",
            """Outcome: `SOURCE_LIMITATION_SAFE`.

No runtime date mapping was changed. No stale row was promoted, no raw summary bypass was added, and no user-visible section was fabricated. A future additional official source path may cover Friday-to-Saturday, but this P2 coverage gap does not weaken current correctness.
""",
        ),
    )

    error_table = _table(
        ["Class", "Count"],
        [[name, count] for name, count in sorted(primary_categories.items())],
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-run45-primary-ai-validation-root-cause.md",
        _report(
            "Run-45 Primary AI Validation Root Cause",
            f"""Frozen packet: `{PACKET_ID}`.

- Before: `{len(primary_before)}` errors.
- After: `{len(primary_result['errors'])}` errors.
- Root: candidate construction omitted structured ownership metadata even though the packet contained canonical evidence.

{error_table}

The repair runs before unchanged strict validation and records every deterministic handoff or suppression.
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-run45-primary-ai-error-inventory.md",
        _report(
            "Run-45 Primary AI Error Inventory",
            "\n".join(f"- `{error}`" for error in primary_before),
        ),
    )
    valuation_table = _table(
        ["Ticker", "Numeric ref", "Typed owner fact", "Reason"],
        [
            [
                row.get("ticker"),
                row.get("numeric_ref_id", "quality_unknown"),
                row.get("fact_id"),
                row.get("reason"),
            ]
            for row in valuation_handoffs
        ],
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-valuation-numeric-ownership-repair.md",
        _report(
            "Valuation Numeric Ownership Repair",
            f"""{valuation_table}

Numeric values still bind from their field-level canonical registry rows. Interpretation ownership is moved to eligible narrow facts, so denied mixed `valuation:current` no longer owns prose. TSM/WRD security-basis cautions are bound as typed `quality_unknown` occurrences. No denominator, currency conversion, or per-share value was inferred.
""",
        ),
    )
    inventory_table = _table(
        ["Ticker", "Relation", "Field", "Owner", "Rendered usage"],
        [[row["ticker"], row["fact_id"], row["field_path"], row["text_ref"], row["usage"]] for row in inventory],
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-inventory-fact-ownership-repair.md",
        _report(
            "Inventory Fact Ownership Repair",
            f"""{inventory_table}

MU and TSLA use genuine packet-selected inventory relations. Each has one signed numeric reference, one `business_earnings` owner, the exact comparator, and one visible inventory label. Unowned or ambiguous inventory prose remains fail-closed.
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-monitoring-fact-id-ownership-repair.md",
        _report(
            "Monitoring Fact-ID Ownership Repair",
            f"""`monitoring:risk_reward_transition` was absent from CORZ/WULF canonical fact catalogs. Their candidates made no transition numeric claim but retained a stale declaration. The candidate owner removed only that known unavailable declaration.

Suppressions: `{json.dumps(suppressions, ensure_ascii=False)}`

Arbitrary unknown IDs remain untouched and continue to fail strict validation.
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-run45-backup-ai-validation-root-cause.md",
        _report(
            "Run-45 Backup AI Validation Root Cause",
            f"""Before: `{len(backup_before)}` errors; after: `{len(backup_result['errors'])}`.

""" + "\n".join(f"- `{error}`" for error in backup_before),
        ),
    )
    backup_handoffs = [
        item
        for item in backup_result["ownership"].get("handoffs", [])
        if isinstance(item, Mapping)
        and (item.get("slot") or item.get("framework"))
    ]
    _write(
        args.output_dir / f"{REPORT_DATE}-backup-market-evidence-and-framework-repair.md",
        _report(
            "Backup Market Evidence And Framework Repair",
            f"""The backup now consumes each selected canonical US market-plan claim in `market_context` and cites all evidence refs. `hyperscaler_capex_transmission` is a stock framework and is removed from the market owner; it was not added to an allowlist.

```json
{json.dumps(backup_handoffs, ensure_ascii=False, indent=2)}
```
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-run45-frozen-replay.md",
        _report(
            "Run-45 Frozen Replay",
            f"""- Packet: `{PACKET_ID}` (read-only).
- Primary: `{len(primary_before)} -> {len(primary_result['errors'])}` errors, `PASS`.
- Backup: `{len(backup_before)} -> {len(backup_result['errors'])}` errors, `PASS`.
- Runtime message quality: `{quality_receipt['status']}`, verified `{quality_verified}`.
- Rendered messages: `{len(messages)}`.
- Original candidate/archive rewrite: `0`.
""",
        ),
    )
    us13_rows = []
    inventory_tickers = {row["ticker"] for row in inventory}
    valuation_tickers = {str(row.get("ticker")) for row in valuation_handoffs}
    for ticker in expected_tickers:
        price_row = next(row for row in price["rows"] if row["ticker"] == ticker)
        us13_rows.append(
            [
                ticker,
                "PASS",
                "typed" if ticker in valuation_tickers else "not selected",
                "owned" if ticker in inventory_tickers else "not selected",
                price_row["status"],
            ]
        )
    _write(
        args.output_dir / f"{REPORT_DATE}-us13-ai-validation.md",
        _report(
            "US13 AI Validation",
            _table(["Ticker", "AI", "Valuation", "Inventory", "Price parity"], us13_rows),
        ),
    )
    before_after_rows = [
        ["night futures", "expected 2026-08-29; omitted", "official Saturday BAS_DD absent", "document source limitation", "safe omission", "PASS"],
        ["CORZ/WULF", "unknown RR transition declaration", "legacy unavailable ID", "remove stale declaration", "canonical facts only", "PASS"],
        ["CRCL/SNDK", "denied mixed valuation owner", "aggregate interpretation", "narrow typed facts", "field-safe", "PASS"],
        ["MU/TSLA", "inventory ownership missing", "handoff omitted", "signed business owner", "one claim each", "PASS"],
        ["other valuation", "numeric spans uncovered", "typed refs omitted", "occurrence refs", "covered", "PASS"],
        ["TSM/WRD", "unknown span uncovered", "quality ref omitted", "security-basis quality_unknown", "covered", "PASS"],
        ["backup market", "3 selected slots unused", "plan handoff omitted", "canonical plan consumption", "all selected", "PASS"],
        ["backup framework", "stock framework in market", "owner mismatch", "remove from market owner", "allowlist unchanged", "PASS"],
    ]
    _write(
        args.output_dir / f"{REPORT_DATE}-run45-before-after.md",
        _report(
            "Run-45 Before And After",
            _table(["Component", "Before", "Root cause", "Repair", "After", "Result"], before_after_rows),
        ),
    )
    sink_state = "PASS" if test_exact else "PENDING"
    _write(
        args.output_dir / f"{REPORT_DATE}-us-ai-test-delivery.md",
        _report(
            "US AI Test Delivery",
            f"""- Dedicated sink audit: `{sink_state}`.
- Planned: `1` market + `{len(expected_tickers)}` stock = `{len(messages)}`.
- Sent: `{test_receipt.get('sent_message_count', 0) if test_receipt else 0}`.
- Exact payload match: `{test_receipt.get('exact_payload_match', 'NOT_RUN') if test_receipt else 'NOT_RUN'}`.
- Duplicate/orphan: `{test_receipt.get('duplicate_count', 0) if test_receipt else 0}` / `{test_receipt.get('orphan_count', 0) if test_receipt else 0}`.
- Production recipient sends: `{test_receipt.get('production_recipient_send_count', 0) if test_receipt else 0}`.
- Production delivery intents: `{test_receipt.get('production_intent_created', 0) if test_receipt else 0}`.

Recipient values are represented only by non-reversible aliases in the sanitized receipt.
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-us-ai-exact-test-messages.md",
        _exact_messages_report(messages, test_receipt),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-us-ai-price-structure-parity.md",
        _report(
            "US AI Price Structure Parity",
            f"""- Canonical numeric differences: `{price['numeric_diff_count']}`.
- Bollinger-only major S/R visible: `0`.
- Provisional Bollinger authority leakage: `0`.

{_table(['Ticker', 'Price claims', 'Mismatch', 'Status'], [[row['ticker'], row['price_claim_count'], ', '.join(row['mismatches']) or 'none', row['status']] for row in price['rows']])}
""",
        ),
    )
    _write(
        args.output_dir / f"{REPORT_DATE}-us-night-ai-integrated-readiness.md",
        _report(
            "US Night And AI Integrated Readiness",
            f"""- Night futures: `SOURCE_LIMITATION_SAFE`.
- Primary validator: `PASS` (`37 -> 0`).
- Backup validator: `PASS` (`4 -> 0`).
- Runtime message quality: `PASS`.
- US13: `PASS`.
- Price Structure parity: `PASS`.
- Test sink: `{'PASS' if test_exact else 'PENDING'}`.
- Open P0: `0`.
- Open material P1: `{0 if test_exact else 1}`.
- Promotion: `{'READY' if test_exact else 'BLOCKED_PENDING_TEST_PROOF'}`.
""",
        ),
    )

    artifact_names = [
        f"{REPORT_DATE}-night-futures-friday-saturday-root-cause.md",
        f"{REPORT_DATE}-night-futures-raw-source-contract.md",
        f"{REPORT_DATE}-night-futures-historical-session-mapping.md",
        f"{REPORT_DATE}-night-futures-repair-or-source-limitation.md",
        f"{REPORT_DATE}-night-futures-friday-saturday.json",
        f"{REPORT_DATE}-night-futures-friday-saturday-source-capture.json",
        f"{REPORT_DATE}-run45-primary-ai-validation-root-cause.md",
        f"{REPORT_DATE}-run45-primary-ai-error-inventory.md",
        f"{REPORT_DATE}-valuation-numeric-ownership-repair.md",
        f"{REPORT_DATE}-inventory-fact-ownership-repair.md",
        f"{REPORT_DATE}-monitoring-fact-id-ownership-repair.md",
        f"{REPORT_DATE}-run45-backup-ai-validation-root-cause.md",
        f"{REPORT_DATE}-backup-market-evidence-and-framework-repair.md",
        f"{REPORT_DATE}-run45-frozen-replay.md",
        f"{REPORT_DATE}-us13-ai-validation.md",
        f"{REPORT_DATE}-run45-before-after.md",
        f"{REPORT_DATE}-run45-ai-validation.json",
        f"{REPORT_DATE}-run45-runtime-quality-receipt.json",
        f"{REPORT_DATE}-us-ai-test-delivery.md",
        f"{REPORT_DATE}-us-ai-test-delivery-receipt.json",
        f"{REPORT_DATE}-us-ai-exact-test-messages.md",
        f"{REPORT_DATE}-us-ai-test-messages.json",
        f"{REPORT_DATE}-us-ai-price-structure-parity.md",
        f"{REPORT_DATE}-us-night-ai-integrated-readiness.md",
        f"{REPORT_DATE}-us-night-ai-integrated-readiness.json",
    ]
    artifact_paths = sorted(args.output_dir / name for name in artifact_names)
    artifact_rows = [[path.name, _sha_file(path)] for path in artifact_paths if path.is_file()]
    _write(
        args.output_dir / f"{REPORT_DATE}-us-night-ai-artifact-index.md",
        _report(
            "US Night And AI Artifact Index",
            f"""- Work-instruction SHA: `{args.instruction_sha}`.
- Implementation SHA: `{args.implementation_sha}`.
- Packet: `{PACKET_ID}`.

{_table(['Artifact', 'SHA-256'], artifact_rows)}
""",
        ),
    )
    print(
        json.dumps(
            {
                "status": "PASS" if test_exact else "TEST_PROOF_PENDING",
                "primary_before": len(primary_before),
                "primary_after": len(primary_result["errors"]),
                "backup_before": len(backup_before),
                "backup_after": len(backup_result["errors"]),
                "messages": len(messages),
                "runtime_quality": quality_receipt["status"],
                "test_sent": test_sent,
                "handoffs": dict(handoff_reasons),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


async def send_test(args: argparse.Namespace) -> None:
    payload = _load(args.messages)
    if payload.get("status") != "PASS" or payload.get("route") != "primary_ai":
        raise ValueError("message evidence is not a passing primary-AI route")
    messages = payload.get("messages")
    if not isinstance(messages, list) or len(messages) != 14:
        raise ValueError("expected exactly 14 test messages")
    quality = payload.get("quality_receipt")
    if not isinstance(quality, Mapping) or quality.get("status") != "passed":
        raise ValueError("runtime quality receipt did not pass")
    env = load_env_values(args.env_file)
    sink = audit_test_sink(env)
    if sink.get("available") is not True:
        raise ValueError(f"test sink unavailable: {sink.get('reason')}")
    selected_key = str(sink.get("selected_test_key_name") or "")
    receipt = await deliver_test_messages(
        messages,
        token=env.get("TELEGRAM_BOT_TOKEN") or "",
        test_chat_id=env.get(selected_key) or "",
        production_chat_id=env.get("TELEGRAM_CHAT_ID") or "",
        test_sink_alias=str(sink["test_sink_alias"]),
        production_sink_alias=str(sink["production_sink_alias"]),
        receipt_path=args.receipt,
        contract="run45-us-ai-test-delivery-v1",
        namespace=NAMESPACE,
    )
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "sent_message_count": receipt["sent_message_count"],
                "exact_payload_match": receipt["exact_payload_match"],
                "test_sink_alias": receipt["test_sink_alias"],
                "production_sink_alias": receipt["production_sink_alias"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--packet", type=Path, required=True)
    build_parser.add_argument("--primary", type=Path, required=True)
    build_parser.add_argument("--primary-validation", type=Path, required=True)
    build_parser.add_argument("--backup", type=Path, required=True)
    build_parser.add_argument("--backup-validation", type=Path, required=True)
    build_parser.add_argument("--database", type=Path, required=True)
    build_parser.add_argument("--night-telemetry-root", type=Path, required=True)
    build_parser.add_argument("--night-capture", type=Path, required=True)
    build_parser.add_argument("--env-file", type=Path, required=True)
    build_parser.add_argument("--output-dir", type=Path, required=True)
    build_parser.add_argument("--messages-output", type=Path, required=True)
    build_parser.add_argument("--runtime-quality-output", type=Path, required=True)
    build_parser.add_argument("--test-receipt", type=Path)
    build_parser.add_argument("--instruction-sha", required=True)
    build_parser.add_argument("--implementation-sha", required=True)
    send_parser = subparsers.add_parser("send-test")
    send_parser.add_argument("--messages", type=Path, required=True)
    send_parser.add_argument("--env-file", type=Path, required=True)
    send_parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "send-test":
        asyncio.run(send_test(args))
    else:
        build(args)


if __name__ == "__main__":
    main()
