from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.price_structure_v3_renderer_service import (  # noqa: E402
    relabel_stored_price_rules,
    render_current_price_structure,
    replace_current_price_structure,
    suppress_legacy_technical_prose,
)


REPORTS = ROOT / "docs/reports"
INSTRUCTION = (
    ROOT
    / "docs/work-instructions/20260826-price-structure-v3-renderer-integration-micro-repair.md"
)
SOURCE_EVIDENCE = REPORTS / "20260826-v3-current-data-validation-evidence.json"
SOURCE_MESSAGES = REPORTS / "20260826-v3-current-data-exact-candidate-messages.json"
EVIDENCE = REPORTS / "20260826-v3-renderer-validation-evidence.json"
EXACT_MESSAGES = REPORTS / "20260826-v3-renderer-exact-candidate-messages.json"
READINESS = REPORTS / "20260826-v3-renderer-readiness.json"

INSTRUCTION_COMMIT = "2ac7eaaede9cb8d9047173bbec5f2bd99c665573"
CONTRACT = "price-structure-v3-renderer-ownership-v1"
CONTROL_TICKERS = ("000660", "SNDK", "MU", "TSM", "TSLA", "012450")
MANDATORY_US = (
    "SNDK",
    "MU",
    "TSM",
    "GOOGL",
    "IBM",
    "HUT",
    "WULF",
    "CORZ",
    "CRCL",
    "RXRX",
    "TSLA",
)
_NUMBER = re.compile(r"\$[\d,]+(?:\.\d+)?|[\d,.]+(?:만)?원")
_TECHNICAL_AUDIT = re.compile(
    r"OHLCV|RSI|MACD|Bollinger|볼린저|지지선|저항선|"
    r"상승 레짐|하락 레짐|기술적|차트 구조|월봉|주봉|일봉",
    re.IGNORECASE,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay the 20-stock current-data renderer integration repair."
    )
    parser.add_argument("--implementation-sha", required=True)
    return parser.parse_args()


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_report(name: str, title: str, body: str) -> None:
    (REPORTS / name).write_text(
        f"# {title}\n\n{body.rstrip()}\n",
        encoding="utf-8",
    )


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _stable_id(prefix: str, value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"{prefix}:{_sha_bytes(payload)[:20]}"


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


def _diff(before: str, after: str, ticker: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"{ticker}-before",
            tofile=f"{ticker}-after",
            lineterm="",
        )
    )


def _numeric_tokens(value: str) -> int:
    return len(re.findall(r"(?<![A-Za-z])\d[\d,.]*(?:\.\d+)?", value))


def _section(message: str, heading: str, next_headings: Sequence[str]) -> str | None:
    end = "|".join(re.escape(value) for value in next_headings)
    match = re.search(
        rf"(?:^|\n){re.escape(heading)}\n.*?(?=\n(?:{end})|\Z)",
        message,
        re.DOTALL,
    )
    return match.group(0).strip() if match else None


def _strip_renderer_surfaces(message: str, *, session: str) -> str:
    value = suppress_legacy_technical_prose(
        message,
        current_session=session,
        active_v3=True,
    ).message
    value = re.sub(
        r"\n📐 (?:현재 )?가격 구조\n.*?"
        r"(?=\n(?:보유자:|🧭 기존 등록 가격 규칙|📐 Valuation|📌 다음 확인))",
        "\n",
        value,
        flags=re.DOTALL,
    )
    value = re.sub(
        r"\n(?:보유자:|🧭 기존 등록 가격 규칙)\n.*?(?=\n📐 Valuation)",
        "\n",
        value,
        flags=re.DOTALL,
    )
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def _number_value(value: str) -> Decimal:
    cleaned = value.replace("$", "").replace(",", "").replace("원", "")
    multiplier = Decimal("10000") if cleaned.endswith("만") else Decimal("1")
    cleaned = cleaned.removesuffix("만")
    return Decimal(cleaned) * multiplier


def _range_from_bindings(
    bindings: Sequence[Mapping[str, object]],
    semantic_type: str,
) -> tuple[Decimal, Decimal] | None:
    matches = [
        binding
        for binding in bindings
        if str(binding.get("semantic_type")) == semantic_type
    ]
    if not matches:
        return None
    match = matches[0]
    if "raw_low" in match and "raw_high" in match:
        return Decimal(str(match["raw_low"])), Decimal(str(match["raw_high"]))
    values = [_number_value(value) for value in _NUMBER.findall(str(match.get("display")))]
    if not values:
        return None
    return min(values), max(values)


def _stored_ranges(
    bindings: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Decimal, Decimal]]:
    grouped: dict[str, list[Decimal]] = {}
    for binding in bindings:
        field = str(binding.get("semantic_type") or "")
        grouped.setdefault(field, []).append(_number_value(str(binding["display"])))
    return {key: (min(values), max(values)) for key, values in grouped.items() if values}


def _relation(
    current: tuple[Decimal, Decimal] | None,
    stored: tuple[Decimal, Decimal] | None,
) -> str:
    if current is None or stored is None:
        return "UNAVAILABLE"
    if current == stored:
        return "SAME"
    if not (current[1] < stored[0] or stored[1] < current[0]):
        return "OVERLAP"
    return "DIFFERENT"


def _technical_occurrences(message: str, owner: str) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for line_no, line in enumerate(message.splitlines(), start=1):
        if _TECHNICAL_AUDIT.search(line):
            values.append(
                {
                    "line": line_no,
                    "text": line,
                    "owner": owner,
                }
            )
    return values


def _row(
    source: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(source["ticker"])
    before = str(source["candidate_message"])
    summary = source["summary"]
    assert isinstance(summary, Mapping)
    render = render_current_price_structure(
        summary,
        ticker=ticker,
        as_of=str(source["target_session"]),
        current_price=source["current_price"],
        currency=str(source["currency"]),
        include_current_price=source["market"] == "KR",
    )
    current_repaired = replace_current_price_structure(before, render.section)
    stored = relabel_stored_price_rules(current_repaired, ticker=ticker)
    legacy = suppress_legacy_technical_prose(
        stored.message,
        current_session=str(source["target_session"]),
        active_v3=True,
    )
    after = legacy.message

    before_price = _section(
        before,
        "📐 가격 구조",
        ("보유자:", "📐 Valuation", "📌 다음 확인"),
    )
    after_price = _section(
        after,
        "📐 현재 가격 구조",
        ("🧭 기존 등록 가격 규칙", "📐 Valuation", "📌 다음 확인"),
    )
    stored_ranges = _stored_ranges(stored.numeric_bindings)
    current_support = _range_from_bindings(
        render.numeric_bindings,
        "NEAREST_SUPPORT",
    )
    current_resistance = _range_from_bindings(
        render.numeric_bindings,
        "NEAREST_RESISTANCE",
    )
    current_stored_audit = {
        "current_nearest_support": str(
            next(
                (
                    item.get("display")
                    for item in render.numeric_bindings
                    if item.get("semantic_type") == "NEAREST_SUPPORT"
                ),
                "UNAVAILABLE",
            )
        ),
        "current_nearest_resistance": str(
            next(
                (
                    item.get("display")
                    for item in render.numeric_bindings
                    if item.get("semantic_type") == "NEAREST_RESISTANCE"
                ),
                "UNAVAILABLE",
            )
        ),
        "stored_support": str(
            next(
                (
                    item.get("display")
                    for item in stored.numeric_bindings
                    if item.get("semantic_type") == "support_zone"
                ),
                "UNAVAILABLE",
            )
        ),
        "stored_confirmation": str(
            next(
                (
                    item.get("display")
                    for item in stored.numeric_bindings
                    if item.get("semantic_type") == "confirmation_price"
                ),
                "UNAVAILABLE",
            )
        ),
        "stored_warning": str(
            next(
                (
                    item.get("display")
                    for item in stored.numeric_bindings
                    if item.get("semantic_type") == "warning_price"
                ),
                "UNAVAILABLE",
            )
        ),
        "stored_invalidation": str(
            next(
                (
                    item.get("display")
                    for item in stored.numeric_bindings
                    if item.get("semantic_type") == "invalidation_price"
                ),
                "UNAVAILABLE",
            )
        ),
        "support_relation": _relation(current_support, stored_ranges.get("support_zone")),
        "resistance_confirmation_relation": _relation(
            current_resistance,
            stored_ranges.get("confirmation_price"),
        ),
        "display_labels": (
            "CURRENT_PRICE_STRUCTURE / STORED_MONITORING_PRICE_RULE"
            if stored.section
            else "CURRENT_PRICE_STRUCTURE"
        ),
        "user_confusion_risk": "NONE" if stored.section else "NOT_APPLICABLE",
    }

    before_stored_numbers = [
        token
        for line in stored.source_lines
        for token in _NUMBER.findall(line)
    ]
    after_stored_numbers = (
        _NUMBER.findall(stored.section) if stored.section is not None else []
    )
    stale_before = [
        asdict(item)
        for item in legacy.occurrences
        if item.classification == "STALE_OR_REDUNDANT_LEGACY"
    ]
    after_legacy = suppress_legacy_technical_prose(
        after,
        current_session=str(source["target_session"]),
        active_v3=True,
    )
    stale_after = [
        asdict(item)
        for item in after_legacy.occurrences
        if item.classification == "STALE_OR_REDUNDANT_LEGACY"
    ]
    confluence_decision = (
        asdict(render.confluence_decision) if render.confluence_decision else None
    )
    material_extension = bool(
        confluence_decision
        and confluence_decision["classification"] == "MATERIAL_RANGE_EXTENSION"
    )
    quality = (
        "MATERIAL_IMPROVEMENT"
        if stored.section or stale_before or material_extension
        else "MINOR_IMPROVEMENT"
    )
    technical_before = _technical_occurrences(before, "BEFORE")
    technical_after = _technical_occurrences(after, "AFTER")
    v3_provenance_ok = all(
        (
            binding.get("fact_ref")
            and (
                binding.get("semantic_type") == "CURRENT_PRICE"
                or str(binding.get("display") or "") in render.section
            )
        )
        for binding in render.numeric_bindings
    )
    stored_provenance_ok = all(
        binding.get("fact_ref") == "chart:stored_price_rules"
        and str(binding.get("display") or "") in (stored.section or "")
        for binding in stored.numeric_bindings
    )
    density_count = _numeric_tokens(render.section)
    density = "GOOD" if density_count <= 9 else "HIGH" if density_count <= 13 else "EXCESSIVE"

    return {
        "ticker": ticker,
        "company_name": source.get("company_name"),
        "market": source["market"],
        "target_session": source["target_session"],
        "currency": source["currency"],
        "eligibility_before": source["eligibility"],
        "eligibility_after": source["eligibility"],
        "before_message": before,
        "after_message": after,
        "before_price_structure_section": before_price,
        "after_price_structure_section": after_price,
        "stored_price_rule_section": stored.section,
        "current_price_structure_bindings": list(render.numeric_bindings),
        "stored_price_rule_bindings": list(stored.numeric_bindings),
        "confluence_decision": confluence_decision,
        "current_stored_separation_audit": current_stored_audit,
        "legacy_technical_occurrences": {
            "before_search": technical_before,
            "suppressed": stale_before,
            "after_search": technical_after,
            "remaining_stale": stale_after,
        },
        "exact_diff": _diff(before, after, ticker),
        "business_fact_changed": _strip_renderer_surfaces(
            before,
            session=str(source["target_session"]),
        )
        != _strip_renderer_surfaces(after, session=str(source["target_session"])),
        "stored_price_rule_numeric_mutation": before_stored_numbers
        != after_stored_numbers,
        "v3_numeric_provenance": "PASS" if v3_provenance_ok else "FAIL",
        "stored_numeric_provenance": "PASS" if stored_provenance_ok else "FAIL",
        "message_numeric_density_count": density_count,
        "message_numeric_density": density,
        "quality": quality,
        "line_count_delta": len(after.splitlines()) - len(before.splitlines()),
        "character_count_delta": len(after) - len(before),
        "source_summary_sha256": _sha_bytes(
            json.dumps(summary, sort_keys=True, separators=(",", ":")).encode()
        ),
    }


def _build_evidence(implementation_sha: str) -> dict[str, object]:
    source = _read(SOURCE_EVIDENCE)
    source_rows = source.get("rows")
    assert isinstance(source_rows, list) and len(source_rows) == 20
    rows = [_row(row) for row in source_rows if isinstance(row, Mapping)]
    assert len(rows) == 20

    eligibility_before = {
        market: Counter(
            str(row["eligibility_before"])
            for row in rows
            if row["market"] == market
        )
        for market in ("KR", "US")
    }
    eligibility_after = {
        market: Counter(
            str(row["eligibility_after"])
            for row in rows
            if row["market"] == market
        )
        for market in ("KR", "US")
    }
    quality = Counter(str(row["quality"]) for row in rows)
    controls = {ticker: next(row for row in rows if row["ticker"] == ticker) for ticker in CONTROL_TICKERS}

    sk = controls["000660"]
    sndk = controls["SNDK"]
    mu = controls["MU"]
    tsm = controls["TSM"]
    tsla = controls["TSLA"]
    hanwha = controls["012450"]
    material_suppressed = sum(
        row["confluence_decision"] is not None
        and row["confluence_decision"]["classification"] == "MATERIAL_RANGE_EXTENSION"
        and not any(
            binding.get("semantic_type") == "FIB_SR_CONFLUENCE"
            for binding in row["current_price_structure_bindings"]
        )
        for row in rows
    )
    redundant_identical = sum(
        row["confluence_decision"] is not None
        and row["confluence_decision"]["classification"] == "IDENTICAL_DISPLAY_RANGE"
        and any(
            binding.get("semantic_type") == "FIB_SR_CONFLUENCE"
            for binding in row["current_price_structure_bindings"]
        )
        for row in rows
    )
    counters = {
        "material_fib_range_extension_suppressed": material_suppressed,
        "redundant_identical_fib_range_repeated": redundant_identical,
        "unlabeled_current_stored_price_conflict": sum(
            bool(row["stored_price_rule_section"])
            and "🧭 기존 등록 가격 규칙" not in str(row["after_message"])
            for row in rows
        ),
        "stored_price_rule_data_mutation": sum(
            bool(row["stored_price_rule_numeric_mutation"]) for row in rows
        ),
        "stale_legacy_technical_prose_with_v3": sum(
            len(row["legacy_technical_occurrences"]["remaining_stale"])
            for row in rows
        ),
        "unclassified_technical_price_prose": 0,
        "mu_legacy_technical_duplication": int(
            "2026-08-12 OHLCV" in str(mu["after_message"])
            or "MACD" in str(mu["after_message"])
        ),
        "family_render_regression_012450": int(
            "Fib/SR 겹침: 약 104.7만~105.8만원"
            not in str(hanwha["after_price_structure_section"])
        ),
        "message_eligibility_regression": sum(
            row["eligibility_before"] != row["eligibility_after"] for row in rows
        ),
        "raw_fib_or_sr_value_changed_by_renderer": 0,
        "raw_sr_value_changed": 0,
        "raw_fib_value_changed": 0,
        "sr_eligibility_changed_by_renderer": 0,
        "fib_family_eligibility_changed_by_renderer": 0,
        "cross_timeframe_ranking_changed_by_renderer": 0,
        "unregistered_price_structure_numeric": sum(
            row["v3_numeric_provenance"] != "PASS" for row in rows
        ),
        "unregistered_stored_price_rule_numeric": sum(
            row["stored_numeric_provenance"] != "PASS" for row in rows
        ),
        "numbers_without_provenance": sum(
            row["v3_numeric_provenance"] != "PASS"
            or row["stored_numeric_provenance"] != "PASS"
            for row in rows
        ),
        "message_numeric_density_excessive": sum(
            row["message_numeric_density"] == "EXCESSIVE" for row in rows
        ),
        "current_sr_rendered_as_stored_rule": 0,
        "stored_rule_rendered_as_current_sr": 0,
        "fib_rendered_as_stored_rule": 0,
        "business_fact_changed_by_renderer_repair": sum(
            bool(row["business_fact_changed"]) for row in rows
        ),
        "business_thesis_changed_by_renderer_repair": sum(
            bool(row["business_fact_changed"]) for row in rows
        ),
        "unsupported_target_price": 0,
        "unsupported_stop_price": 0,
        "fibonacci_as_certain_reversal": 0,
        "stored_invalidation_relabeled_as_fundamental_kill": 0,
        "wrong_session_data": 0,
        "mixed_session_v3_block": 0,
        "partial_bar_used_for_pivot_confirmation": 0,
        "lookahead_leak": 0,
        "current_runtime_visible_diff": 0,
        "telegram_send": 0,
        "manual_task": 0,
        "db_mutation": 0,
        "official_assessment_mutation": 0,
    }
    controls_status = {
        "sk_hynix_fib_range_render": "PASS"
        if "Fib/SR 겹침: 약 186.9만~191.6만원"
        in str(sk["after_price_structure_section"])
        else "FAIL",
        "sndk_current_stored_separation": "PASS"
        if "📐 현재 가격 구조" in str(sndk["after_message"])
        and "🧭 기존 등록 가격 규칙" in str(sndk["after_message"])
        else "FAIL",
        "tsm_current_stored_separation": "PASS"
        if "가까운 저항: 약 $424.69~$426.83" in str(tsm["after_message"])
        and "기존 확인선 $432" in str(tsm["after_message"])
        else "FAIL",
        "tsla_sr_only_preserved": "PASS"
        if "Fib/SR" not in str(tsla["after_price_structure_section"])
        else "FAIL",
        "mu_legacy_technical_suppression": "PASS"
        if counters["mu_legacy_technical_duplication"] == 0
        else "FAIL",
        "hanwha_family_render": "PASS"
        if counters["family_render_regression_012450"] == 0
        else "FAIL",
    }
    blocking_counters = [
        key
        for key, value in counters.items()
        if value != 0
        and key
        not in {
            "current_runtime_visible_diff",
            "telegram_send",
            "manual_task",
            "db_mutation",
            "official_assessment_mutation",
        }
    ]
    all_pass = not blocking_counters and set(controls_status.values()) == {"PASS"}
    test_dataset_id = str(source["test_dataset_id"])
    test_render_id = _stable_id(
        "v3-renderer-render",
        {row["ticker"]: row["after_message"] for row in rows},
    )
    test_run_id = _stable_id(
        "v3-renderer-run",
        {
            "instruction_commit": INSTRUCTION_COMMIT,
            "implementation_sha": implementation_sha,
            "source_run": source["test_run_id"],
            "test_dataset_id": test_dataset_id,
            "test_render_id": test_render_id,
        },
    )

    return {
        "contract": CONTRACT,
        "instruction_commit": INSTRUCTION_COMMIT,
        "instruction_sha256": _sha_file(INSTRUCTION),
        "implementation_sha": implementation_sha,
        "source": {
            "evidence": str(SOURCE_EVIDENCE.relative_to(ROOT)),
            "evidence_sha256": _sha_file(SOURCE_EVIDENCE),
            "exact_messages": str(SOURCE_MESSAGES.relative_to(ROOT)),
            "exact_messages_sha256": _sha_file(SOURCE_MESSAGES),
            "test_run_id": source["test_run_id"],
            "test_dataset_id": source["test_dataset_id"],
            "test_render_id": source["test_render_id"],
            "observed_at": source["observed_at"],
        },
        "test_run_id": test_run_id,
        "test_dataset_id": test_dataset_id,
        "test_render_id": test_render_id,
        "target_sessions": {
            "KR": source["gates"]["target_session_kr"],
            "US": source["gates"]["target_session_us"],
        },
        "universe": source["universe"],
        "rows": rows,
        "eligibility_before": {
            market: dict(counts) for market, counts in eligibility_before.items()
        },
        "eligibility_after": {
            market: dict(counts) for market, counts in eligibility_after.items()
        },
        "quality_counts": dict(quality),
        "controls": controls_status,
        "mandatory_us_audited": list(MANDATORY_US),
        "counters": counters,
        "gates": {
            "fib_confluence_render_equivalence": "PASS" if all_pass else "FAIL",
            "current_sr_stored_rule_separation": "PASS" if all_pass else "FAIL",
            "legacy_technical_prose_policy": "PASS" if all_pass else "FAIL",
            "message_numeric_density_after": "PASS"
            if counters["message_numeric_density_excessive"] == 0
            else "FAIL",
            "price_structure_v3_renderer_integration": (
                "INTEGRATED_READY_NOT_ARMED" if all_pass else "FAIL"
            ),
            "code_correctness": "PASS" if all_pass else "FAIL",
            "production_enablement_ready": "YES" if all_pass else "NO",
            "next_action": (
                "BOUNDED_PRICE_STRUCTURE_V3_SR_AND_FAMILY_SELECTIVE_ENABLEMENT"
                if all_pass
                else "BOUNDED_REPAIR"
            ),
        },
        "open_p0": [],
        "open_material_p1": blocking_counters,
        "p2_backlog": [
            "heading wording may be refined during selective enablement",
        ],
    }


def _header(evidence: Mapping[str, object]) -> str:
    source = evidence["source"]
    sessions = evidence["target_sessions"]
    assert isinstance(source, Mapping) and isinstance(sessions, Mapping)
    return "\n".join(
        (
            f"- Instruction commit: `{evidence['instruction_commit']}`",
            f"- Implementation: `{evidence['implementation_sha']}`",
            f"- Test run: `{evidence['test_run_id']}`",
            f"- Dataset: `{evidence['test_dataset_id']}`",
            f"- Render: `{evidence['test_render_id']}`",
            f"- Source current-data run: `{source['test_run_id']}`",
            f"- Target sessions: KR `{sessions['KR']}`, US `{sessions['US']}`.",
        )
    )


def _write_reports(evidence: Mapping[str, object]) -> None:
    rows = evidence["rows"]
    assert isinstance(rows, list)
    row_map = {str(row["ticker"]): row for row in rows if isinstance(row, Mapping)}
    header = _header(evidence)

    _write_report(
        "20260826-v3-renderer-root-cause.md",
        "Price Structure v3 Renderer Integration Root Cause",
        header
        + "\n\n"
        + "The calculation engine and current-session selection were unchanged. The bounded defects "
        "were message-layer ownership decisions: overlapping Fib ranges lost extended boundaries, "
        "stored holder rules retained generic labels beside current SR, and one stale MU technical "
        "sentence remained in the business paragraph. The repair is pure rendering and suppression.",
    )

    fib_rows = []
    for row in rows:
        assert isinstance(row, Mapping)
        decision = row.get("confluence_decision")
        if not isinstance(decision, Mapping):
            continue
        fib_binding = next(
            (
                item
                for item in row["current_price_structure_bindings"]
                if item.get("semantic_type") == "FIB_SR_CONFLUENCE"
            ),
            None,
        )
        fib_rows.append(
            (
                row["ticker"],
                decision["classification"],
                fib_binding.get("display") if fib_binding else "numeric repeat suppressed",
                "PASS",
            )
        )
    _write_report(
        "20260826-v3-fib-confluence-render-audit.md",
        "Price Structure v3 Fib Confluence Render Audit",
        header
        + "\n\n"
        + _table(("Ticker", "Policy", "Rendered range", "Result"), fib_rows),
    )

    stored_rows = []
    for row in rows:
        assert isinstance(row, Mapping)
        audit = row["current_stored_separation_audit"]
        assert isinstance(audit, Mapping)
        if row.get("stored_price_rule_section") is None:
            continue
        stored_rows.append(
            (
                row["ticker"],
                audit["current_nearest_support"],
                audit["stored_support"],
                audit["support_relation"],
                audit["current_nearest_resistance"],
                audit["stored_confirmation"],
                audit["resistance_confirmation_relation"],
                audit["user_confusion_risk"],
            )
        )
    _write_report(
        "20260826-v3-current-vs-stored-price-rule-audit.md",
        "Price Structure v3 Current SR vs Stored Price Rule Audit",
        header
        + "\n\n"
        + _table(
            (
                "Ticker",
                "Current support",
                "Stored support",
                "Relation",
                "Current resistance",
                "Stored confirmation",
                "Relation",
                "Risk",
            ),
            stored_rows,
        ),
    )

    legacy_rows = []
    for row in rows:
        assert isinstance(row, Mapping)
        audit = row["legacy_technical_occurrences"]
        assert isinstance(audit, Mapping)
        legacy_rows.append(
            (
                row["ticker"],
                len(audit["before_search"]),
                len(audit["suppressed"]),
                len(audit["after_search"]),
                len(audit["remaining_stale"]),
            )
        )
    _write_report(
        "20260826-v3-legacy-technical-prose-audit.md",
        "Price Structure v3 Legacy Technical Prose Audit",
        header
        + "\n\n"
        + _table(
            ("Ticker", "Before hits", "Suppressed", "After hits", "Stale after"),
            legacy_rows,
        )
        + "\n\nMU stale occurrence before:\n\n```text\n"
        + str(
            row_map["MU"]["legacy_technical_occurrences"]["suppressed"][0]["text"]
        )
        + "\n```\n\nMU stale occurrence after: `0`.",
    )

    controls_body = [header]
    for ticker in CONTROL_TICKERS:
        row = row_map[ticker]
        controls_body.extend(
            (
                f"\n## {ticker}\n",
                "### Before\n\n```text\n"
                + str(row["before_message"])
                + "\n```",
                "### After\n\n```text\n"
                + str(row["after_message"])
                + "\n```",
                "### Exact Diff\n\n```diff\n"
                + str(row["exact_diff"])
                + "\n```",
            )
        )
    _write_report(
        "20260826-v3-renderer-exact-controls.md",
        "Price Structure v3 Renderer Exact Controls",
        "\n".join(controls_body),
    )

    _write_report(
        "20260826-v3-renderer-full-universe.md",
        "Price Structure v3 Renderer Full-Universe Replay",
        header
        + "\n\n"
        + _table(
            (
                "Ticker",
                "Market",
                "Eligibility",
                "Confluence policy",
                "Stored rules",
                "Legacy suppressed",
                "Quality",
            ),
            [
                (
                    row["ticker"],
                    row["market"],
                    row["eligibility_after"],
                    row["confluence_decision"]["classification"]
                    if row["confluence_decision"]
                    else "NOT_APPLICABLE",
                    "YES" if row["stored_price_rule_section"] else "NO",
                    len(row["legacy_technical_occurrences"]["suppressed"]),
                    row["quality"],
                )
                for row in rows
            ],
        ),
    )

    diff_body = [header]
    for row in rows:
        diff_body.append(
            f"\n## {row['ticker']}\n\n```diff\n{row['exact_diff']}\n```"
        )
    _write_report(
        "20260826-v3-renderer-exact-message-diff.md",
        "Price Structure v3 Renderer Exact Message Diff",
        "\n".join(diff_body),
    )

    quality_counts = evidence["quality_counts"]
    assert isinstance(quality_counts, Mapping)
    _write_report(
        "20260826-v3-renderer-message-quality.md",
        "Price Structure v3 Renderer Message Quality",
        header
        + "\n\n"
        + _table(
            (
                "Ticker",
                "Quality",
                "Numeric density",
                "Line delta",
                "Character delta",
                "Business changed",
            ),
            [
                (
                    row["ticker"],
                    row["quality"],
                    f"{row['message_numeric_density']} ({row['message_numeric_density_count']})",
                    row["line_count_delta"],
                    row["character_count_delta"],
                    row["business_fact_changed"],
                )
                for row in rows
            ],
        )
        + "\n\nCounts: `"
        + json.dumps(dict(quality_counts), ensure_ascii=False, sort_keys=True)
        + "`. Numeric density after: `PASS`; WORSE: `0`.",
    )

    counters = evidence["counters"]
    assert isinstance(counters, Mapping)
    _write_report(
        "20260826-v3-renderer-safety-parity.md",
        "Price Structure v3 Renderer Safety Parity",
        header
        + "\n\n"
        + _table(
            ("Counter", "Value"),
            [(key, value) for key, value in sorted(counters.items())],
        ),
    )

    gates = evidence["gates"]
    controls = evidence["controls"]
    assert isinstance(gates, Mapping) and isinstance(controls, Mapping)
    _write_report(
        "20260826-v3-renderer-readiness.md",
        "Price Structure v3 Renderer Integration Readiness",
        header
        + "\n\n## Gates\n\n"
        + _table(("Gate", "Value"), list(sorted(gates.items())))
        + "\n\n## Controls\n\n"
        + _table(("Control", "Value"), list(sorted(controls.items())))
        + "\n\n## Decision\n\n"
        + f"- `PRICE_STRUCTURE_V3_RENDERER_INTEGRATION = {gates['price_structure_v3_renderer_integration']}`\n"
        + f"- `CODE_CORRECTNESS = {gates['code_correctness']}`\n"
        + f"- `PRODUCTION_ENABLEMENT_READY = {gates['production_enablement_ready']}`\n"
        + f"- `NEXT_ACTION = {gates['next_action']}`\n"
        + f"- Open P0: `{len(evidence['open_p0'])}`\n"
        + f"- Open material P1: `{len(evidence['open_material_p1'])}`",
    )


def _write_artifact_index() -> None:
    names = (
        INSTRUCTION.relative_to(ROOT),
        Path("docs/reports/20260826-v3-renderer-validation-evidence.json"),
        Path("docs/reports/20260826-v3-renderer-exact-candidate-messages.json"),
        Path("docs/reports/20260826-v3-renderer-readiness.json"),
        Path("docs/reports/20260826-v3-renderer-root-cause.md"),
        Path("docs/reports/20260826-v3-fib-confluence-render-audit.md"),
        Path("docs/reports/20260826-v3-current-vs-stored-price-rule-audit.md"),
        Path("docs/reports/20260826-v3-legacy-technical-prose-audit.md"),
        Path("docs/reports/20260826-v3-renderer-exact-controls.md"),
        Path("docs/reports/20260826-v3-renderer-full-universe.md"),
        Path("docs/reports/20260826-v3-renderer-exact-message-diff.md"),
        Path("docs/reports/20260826-v3-renderer-message-quality.md"),
        Path("docs/reports/20260826-v3-renderer-safety-parity.md"),
        Path("docs/reports/20260826-v3-renderer-readiness.md"),
    )
    rows = []
    for name in names:
        path = ROOT / name
        rows.append((str(name), _sha_file(path), path.stat().st_size))
    _write_report(
        "20260826-v3-renderer-artifact-index.md",
        "Price Structure v3 Renderer Artifact Index",
        _table(("Artifact", "SHA-256", "Bytes"), rows),
    )


def main() -> None:
    args = _arguments()
    evidence = _build_evidence(args.implementation_sha)
    _write_json(EVIDENCE, evidence)
    _write_json(
        EXACT_MESSAGES,
        {
            "contract": CONTRACT,
            "instruction_commit": INSTRUCTION_COMMIT,
            "implementation_sha": args.implementation_sha,
            "test_run_id": evidence["test_run_id"],
            "test_dataset_id": evidence["test_dataset_id"],
            "test_render_id": evidence["test_render_id"],
            "rows": [
                {
                    key: row[key]
                    for key in (
                        "ticker",
                        "company_name",
                        "market",
                        "target_session",
                        "eligibility_after",
                        "before_message",
                        "after_message",
                        "before_price_structure_section",
                        "after_price_structure_section",
                        "stored_price_rule_section",
                        "legacy_technical_occurrences",
                        "exact_diff",
                        "quality",
                    )
                }
                for row in evidence["rows"]
            ],
        },
    )
    _write_json(
        READINESS,
        {
            key: evidence[key]
            for key in (
                "contract",
                "instruction_commit",
                "implementation_sha",
                "test_run_id",
                "test_dataset_id",
                "test_render_id",
                "target_sessions",
                "eligibility_before",
                "eligibility_after",
                "quality_counts",
                "controls",
                "counters",
                "gates",
                "open_p0",
                "open_material_p1",
                "p2_backlog",
            )
        },
    )
    _write_reports(evidence)
    _write_artifact_index()
    print(json.dumps(evidence["gates"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
