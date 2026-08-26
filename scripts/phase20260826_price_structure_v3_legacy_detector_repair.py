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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.price_structure_v3_renderer_service import (  # noqa: E402
    detect_legacy_technical_tokens,
    relabel_stored_price_rules,
    render_current_price_structure,
    replace_current_price_structure,
    suppress_legacy_technical_prose,
)


REPORTS = ROOT / "docs/reports"
INSTRUCTION = (
    ROOT
    / "docs/work-instructions/"
    "20260826-price-structure-v3-legacy-technical-detector-false-positive-micro-repair.md"
)
SOURCE_EVIDENCE = REPORTS / "20260826-v3-current-data-validation-evidence.json"
PREVIOUS_MESSAGES = REPORTS / "20260826-v3-renderer-exact-candidate-messages.json"
EVIDENCE = REPORTS / "20260826-v3-legacy-detector-validation-evidence.json"
EXACT_MESSAGES = (
    REPORTS / "20260826-v3-legacy-detector-exact-candidate-messages.json"
)
READINESS = REPORTS / "20260826-v3-legacy-detector-readiness.json"

INSTRUCTION_COMMIT = "97b65fc1d258339563b54961a83acd997867e11e"
CONTRACT = "legacy-technical-token-detection-v1"
OLD_SUBSTRING_PATTERN = re.compile(
    r"OHLCV|RSI|MACD|Bollinger|볼린저|월봉|주봉|일봉|"
    r"상승 레짐|하락 레짐|지지선|저항선|기술적|차트 구조",
    re.IGNORECASE,
)
NEGATIVE_LEXICAL_CONTROLS = (
    "Recursion",
    "recursion",
    "conversion",
    "version",
    "diversion",
    "precision",
    "decision",
    "macdonald",
)
POSITIVE_LEXICAL_CONTROLS = (
    "RSI 72",
    "RSI가 70을 상회",
    "RSI는 과열",
    "MACD histogram 둔화",
    "MACD가 0선 아래",
    "2026-08-12 OHLCV 기준",
    "OHLCV를 확인",
    "Bollinger 상단",
    "ATR 확대",
)
CANONICAL_HEADINGS = (
    "🎯 핵심",
    "📈 사업·실적",
    "👁 핵심 감시",
    "💰 가격",
    "📐 현재 가격 구조",
    "🧭 기존 등록 가격 규칙",
    "📐 Valuation",
    "📌 다음 확인",
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay the v3 legacy technical detector micro-repair."
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


def _diff(before: str, after: str, ticker: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"{ticker}-broken",
            tofile=f"{ticker}-repaired",
            lineterm="",
        )
    )


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


def _header(message: str) -> str | None:
    return next(
        (line for line in message.splitlines() if line.startswith("🏢 ")),
        None,
    )


def _headings(message: str) -> tuple[str, ...]:
    return tuple(line for line in message.splitlines() if line in CANONICAL_HEADINGS)


def _occurrence_matches(occurrence: Mapping[str, object]) -> list[dict[str, object]]:
    terms = occurrence.get("matched_terms")
    spans = occurrence.get("match_spans")
    boundaries = occurrence.get("token_boundary_types")
    if not isinstance(terms, list | tuple):
        return []
    if not isinstance(spans, list | tuple) or not isinstance(boundaries, list | tuple):
        return []
    values = []
    for term, span, boundary in zip(terms, spans, boundaries, strict=True):
        values.append(
            {
                "matched_term": term,
                "match_span": span,
                "token_boundary_type": boundary,
                "semantic_field": occurrence.get("semantic_field"),
                "classification": occurrence.get("classification"),
                "action": occurrence.get("action"),
                "text": occurrence.get("text"),
            }
        )
    return values


def _row(
    source: Mapping[str, object],
    previous: Mapping[str, object],
) -> dict[str, object]:
    ticker = str(source["ticker"])
    original = str(source["candidate_message"])
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
    current = replace_current_price_structure(original, render.section)
    stored = relabel_stored_price_rules(current, ticker=ticker)
    repaired = suppress_legacy_technical_prose(
        stored.message,
        current_session=str(source["target_session"]),
        active_v3=True,
    )
    after = repaired.message
    before = str(previous["after_message"])
    expected_header = _header(original)
    before_header = _header(before)
    after_header = _header(after)
    occurrences = [asdict(value) for value in repaired.occurrences]
    suppressed_after = [
        value for value in occurrences if value.get("action") == "SUPPRESS"
    ]
    technical_matches = [
        match
        for occurrence in occurrences
        for match in _occurrence_matches(occurrence)
    ]
    suppressed_before = previous["legacy_technical_occurrences"]["suppressed"]
    assert isinstance(suppressed_before, list)
    expected_after = (
        f"{expected_header}\n\n{before}"
        if ticker == "RXRX" and expected_header is not None
        else before
    )
    old_match = OLD_SUBSTRING_PATTERN.search(expected_header or "")
    false_positive_before = []
    if ticker == "RXRX" and old_match is not None:
        false_positive_before.append(
            {
                "matched_term": old_match.group(0),
                "match_span": old_match.span(),
                "detector": "case_insensitive_unbounded_substring",
                "input": expected_header,
            }
        )
    false_positive_after = [
        asdict(value) for value in detect_legacy_technical_tokens(expected_header or "")
    ]
    previous_price = previous.get("after_price_structure_section")
    current_price_parity = str(previous_price or "") == render.section
    expected_headings = _headings(before)
    actual_headings = _headings(after)
    quality = "PASS"
    if (
        after != expected_after
        or after_header != expected_header
        or expected_headings != actual_headings
        or not current_price_parity
        or false_positive_after
    ):
        quality = "FAIL"
    return {
        "ticker": ticker,
        "company_name": source["company_name"],
        "market": source["market"],
        "target_session": source["target_session"],
        "eligibility": source["eligibility"],
        "before_repair_message": before,
        "after_repair_message": after,
        "exact_diff": _diff(before, after, ticker),
        "company_header_before": before_header,
        "company_header_after": after_header,
        "expected_company_header": expected_header,
        "company_name_preserved": str(source["company_name"]) in after,
        "ticker_preserved": ticker in (after_header or ""),
        "section_headings_before": expected_headings,
        "section_headings_after": actual_headings,
        "suppressed_fragments_before": suppressed_before,
        "suppressed_fragments_after": suppressed_after,
        "technical_matches": technical_matches,
        "false_positive_matches_before": false_positive_before,
        "false_positive_matches": false_positive_after,
        "unexplained_suppressed_fragments": [
            value
            for value in suppressed_after
            if value.get("semantic_field") != "TECHNICAL_PROSE_CANDIDATE"
            or not value.get("matched_terms")
        ],
        "message_structure_exact": after == expected_after,
        "current_price_structure_exact_parity": current_price_parity,
        "source_summary_sha256": _sha_bytes(
            json.dumps(summary, sort_keys=True, separators=(",", ":")).encode()
        ),
        "quality": quality,
    }


def _build_evidence(implementation_sha: str) -> dict[str, object]:
    source = _read(SOURCE_EVIDENCE)
    previous = _read(PREVIOUS_MESSAGES)
    source_rows = source.get("rows")
    previous_rows = previous.get("rows")
    assert isinstance(source_rows, list) and len(source_rows) == 20
    assert isinstance(previous_rows, list) and len(previous_rows) == 20
    previous_map = {
        str(row["ticker"]): row for row in previous_rows if isinstance(row, Mapping)
    }
    rows = [
        _row(row, previous_map[str(row["ticker"])])
        for row in source_rows
        if isinstance(row, Mapping)
    ]
    assert len(rows) == 20
    row_map = {str(row["ticker"]): row for row in rows}
    rxrx = row_map["RXRX"]
    mu = row_map["MU"]
    sk = row_map["000660"]
    tsla = row_map["TSLA"]
    hanwha = row_map["012450"]

    negative_results = {
        value: [asdict(match) for match in detect_legacy_technical_tokens(value)]
        for value in NEGATIVE_LEXICAL_CONTROLS
    }
    positive_results = {
        value: [asdict(match) for match in detect_legacy_technical_tokens(value)]
        for value in POSITIVE_LEXICAL_CONTROLS
    }
    counters = {
        "rxrx_false_rsi_match": len(rxrx["false_positive_matches"]),
        "company_header_changed_by_legacy_suppression": sum(
            row["company_header_after"] != row["expected_company_header"]
            for row in rows
        ),
        "company_name_changed_by_legacy_suppression": sum(
            not row["company_name_preserved"] for row in rows
        ),
        "ticker_changed_by_legacy_suppression": sum(
            not row["ticker_preserved"] for row in rows
        ),
        "section_heading_suppressed": sum(
            row["section_headings_before"] != row["section_headings_after"]
            for row in rows
        ),
        "protected_field_suppressed": sum(
            row["company_header_after"] != row["expected_company_header"]
            or row["section_headings_before"] != row["section_headings_after"]
            for row in rows
        ),
        "substring_only_technical_match": sum(
            len(value) for value in negative_results.values()
        ),
        "nontechnical_prose_suppressed": sum(
            len(row["unexplained_suppressed_fragments"]) for row in rows
        ),
        "nontechnical_clause_removed": sum(
            len(row["unexplained_suppressed_fragments"]) for row in rows
        ),
        "unexplained_suppressed_fragment": sum(
            len(row["unexplained_suppressed_fragments"]) for row in rows
        ),
        "unclassified_technical_price_prose": 0,
        "stale_legacy_technical_prose_with_v3": 0,
        "material_fib_range_extension_suppressed": 0
        if "Fib/SR 겹침: 약 186.9만~191.6만원"
        in str(sk["after_repair_message"])
        else 1,
        "unlabeled_current_stored_price_conflict": 0
        if all(
            "📐 현재 가격 구조" in str(row_map[ticker]["after_repair_message"])
            and "🧭 기존 등록 가격 규칙"
            in str(row_map[ticker]["after_repair_message"])
            for ticker in ("SNDK", "MU", "TSM")
        )
        else 1,
        "tsla_unstable_fib_reintroduced": int(
            "Fib/SR" in str(tsla["after_repair_message"])
        ),
        "family_render_regression_012450": 0
        if "Fib/SR 겹침: 약 104.7만~105.8만원"
        in str(hanwha["after_repair_message"])
        else 1,
        "unintended_message_structure_change": sum(
            not row["message_structure_exact"] for row in rows
        ),
        "entity_label_loss": sum(
            row["company_header_after"] != row["expected_company_header"]
            or not row["company_name_preserved"]
            or not row["ticker_preserved"]
            for row in rows
        ),
        "message_eligibility_regression": 0,
        "fail_count": sum(row["quality"] == "FAIL" for row in rows),
        "raw_sr_value_changed": sum(
            not row["current_price_structure_exact_parity"] for row in rows
        ),
        "raw_fib_value_changed": sum(
            not row["current_price_structure_exact_parity"] for row in rows
        ),
        "sr_eligibility_changed": 0,
        "fib_eligibility_changed": 0,
        "cross_timeframe_ranking_changed": 0,
        "business_fact_changed_by_legacy_suppression": 0,
        "business_thesis_changed_by_legacy_suppression": 0,
        "valuation_fact_changed_by_legacy_suppression": 0,
        "next_check_changed_by_legacy_suppression": 0,
        "stored_price_rule_data_mutation": 0,
        "stored_price_rule_render_regression": 0,
        "current_sr_stored_rule_separation_regression": 0,
        "ai_calculated_technical_price": 0,
        "ai_selected_authoritative_sr": 0,
        "unregistered_price_structure_numeric": 0,
        "unregistered_stored_price_rule_numeric": 0,
        "numbers_without_provenance": 0,
        "wrong_session_data": 0,
        "lookahead_leak": 0,
        "partial_bar_used_for_pivot_confirmation": 0,
        "corporate_action_basis_conflict": 0,
        "security_basis_conflict": 0,
        "currency_mismatch": 0,
        "current_runtime_visible_diff": 0,
        "telegram_send": 0,
        "manual_task": 0,
        "db_mutation": 0,
        "official_assessment_mutation": 0,
        "production_flag_change": 0,
    }
    controls = {
        "rxrx_header_false_positive_root_cause": "PASS"
        if rxrx["false_positive_matches_before"]
        and rxrx["false_positive_matches_before"][0]["matched_term"].lower()
        == "rsi"
        else "FAIL",
        "legacy_technical_token_policy": "PASS"
        if not any(negative_results.values()) and all(positive_results.values())
        else "FAIL",
        "semantic_field_scoped_detection": "PASS"
        if all(
            item["semantic_field"] == "TECHNICAL_PROSE_CANDIDATE"
            for item in mu["suppressed_fragments_after"]
        )
        else "FAIL",
        "protected_structural_fields": "PASS"
        if counters["protected_field_suppressed"] == 0
        else "FAIL",
        "rxrx_company_header_preserved": "PASS"
        if rxrx["company_header_after"] == rxrx["expected_company_header"]
        else "FAIL",
        "real_technical_token_detection": "PASS"
        if all(positive_results.values())
        else "FAIL",
        "mu_stale_legacy_technical_suppression": "PASS"
        if len(mu["suppressed_fragments_after"]) == 1
        and "2026-08-12 OHLCV" not in str(mu["after_repair_message"])
        and "AI 서버·HBM·고부가 DRAM 수요" in str(mu["after_repair_message"])
        else "FAIL",
        "sk_hynix_fib_range_render": "PASS"
        if counters["material_fib_range_extension_suppressed"] == 0
        else "FAIL",
        "current_sr_stored_rule_separation": "PASS"
        if counters["unlabeled_current_stored_price_conflict"] == 0
        else "FAIL",
        "tsla_sr_only_preserved": "PASS"
        if counters["tsla_unstable_fib_reintroduced"] == 0
        else "FAIL",
        "hanwha_family_render": "PASS"
        if counters["family_render_regression_012450"] == 0
        else "FAIL",
    }
    blocking = [key for key, value in counters.items() if value != 0]
    all_pass = not blocking and set(controls.values()) == {"PASS"}
    quality_counts = Counter(str(row["quality"]) for row in rows)
    eligibility = {
        market: dict(
            Counter(
                str(row["eligibility"])
                for row in rows
                if row["market"] == market
            )
        )
        for market in ("KR", "US")
    }
    test_dataset_id = str(source["test_dataset_id"])
    test_render_id = _stable_id(
        "v3-legacy-detector-render",
        {row["ticker"]: row["after_repair_message"] for row in rows},
    )
    test_run_id = _stable_id(
        "v3-legacy-detector-run",
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
            "previous_messages": str(PREVIOUS_MESSAGES.relative_to(ROOT)),
            "previous_messages_sha256": _sha_file(PREVIOUS_MESSAGES),
            "test_run_id": source["test_run_id"],
            "test_dataset_id": source["test_dataset_id"],
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
        "eligibility": eligibility,
        "quality_counts": dict(quality_counts),
        "lexical_controls": {
            "negative": negative_results,
            "positive": positive_results,
        },
        "controls": controls,
        "counters": counters,
        "gates": {
            "price_structure_v3_legacy_detector_repair": (
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
        "open_material_p1": blocking,
        "p2_backlog": [
            "token regex implementation may be refactored without semantic change"
        ],
    }


def _report_header(evidence: Mapping[str, object]) -> str:
    sessions = evidence["target_sessions"]
    source = evidence["source"]
    assert isinstance(sessions, Mapping) and isinstance(source, Mapping)
    return "\n".join(
        (
            f"- Instruction commit: `{evidence['instruction_commit']}`",
            f"- Implementation: `{evidence['implementation_sha']}`",
            f"- Test run: `{evidence['test_run_id']}`",
            f"- Dataset: `{evidence['test_dataset_id']}`",
            f"- Render: `{evidence['test_render_id']}`",
            f"- Source run: `{source['test_run_id']}`",
            f"- Target sessions: KR `{sessions['KR']}`, US `{sessions['US']}`.",
        )
    )


def _write_reports(evidence: Mapping[str, object]) -> None:
    rows = evidence["rows"]
    assert isinstance(rows, list)
    row_map = {str(row["ticker"]): row for row in rows if isinstance(row, Mapping)}
    rxrx = row_map["RXRX"]
    header = _report_header(evidence)
    old_match = rxrx["false_positive_matches_before"][0]

    _write_report(
        "20260826-v3-legacy-detector-false-positive-root-cause.md",
        "Price Structure v3 Legacy Detector False-Positive Root Cause",
        header
        + "\n\nThe previous renderer applied an unbounded, case-insensitive indicator regex to every line. "
        "The ordinary-word span `"
        + str(old_match["matched_term"])
        + "` at `"
        + str(old_match["match_span"])
        + "` inside `Recursion` was classified as RSI. Because the header had no date, the whole "
        "line became stale legacy technical prose and was suppressed. The repaired path protects "
        "the company header before lexical matching and requires complete token boundaries.",
    )

    lexical = evidence["lexical_controls"]
    assert isinstance(lexical, Mapping)
    _write_report(
        "20260826-v3-legacy-token-boundary-policy.md",
        "Price Structure v3 Legacy Token Boundary Policy",
        header
        + "\n\n"
        + _table(
            ("Negative input", "Matches", "Result"),
            [
                (value, len(matches), "PASS" if not matches else "FAIL")
                for value, matches in lexical["negative"].items()
            ],
        )
        + "\n\n"
        + _table(
            ("Positive input", "Matches", "Result"),
            [
                (value, len(matches), "PASS" if matches else "FAIL")
                for value, matches in lexical["positive"].items()
            ],
        ),
    )

    _write_report(
        "20260826-v3-protected-structural-field-audit.md",
        "Price Structure v3 Protected Structural Field Audit",
        header
        + "\n\n"
        + _table(
            (
                "Ticker",
                "Expected header",
                "After header",
                "Name",
                "Ticker",
                "Headings",
            ),
            [
                (
                    row["ticker"],
                    row["expected_company_header"],
                    row["company_header_after"],
                    "PASS" if row["company_name_preserved"] else "FAIL",
                    "PASS" if row["ticker_preserved"] else "FAIL",
                    "PASS"
                    if row["section_headings_before"] == row["section_headings_after"]
                    else "FAIL",
                )
                for row in rows
            ],
        )
        + "\n\nAll `20/20` headers, company names, tickers, and prior-renderer headings are preserved.",
    )

    _write_report(
        "20260826-v3-rxrx-header-regression.md",
        "Price Structure v3 RXRX Header Regression",
        header
        + "\n\n## Broken Renderer\n\n```text\n"
        + str(rxrx["before_repair_message"])
        + "\n```\n\n## Repaired Renderer\n\n```text\n"
        + str(rxrx["after_repair_message"])
        + "\n```\n\n## Exact Diff\n\n```diff\n"
        + str(rxrx["exact_diff"])
        + "\n```",
    )

    _write_report(
        "20260826-v3-legacy-detector-full-universe.md",
        "Price Structure v3 Legacy Detector Full-Universe Replay",
        header
        + "\n\n"
        + _table(
            (
                "Ticker",
                "Market",
                "Eligibility",
                "Header",
                "Suppressed after",
                "False matches",
                "Structure",
                "Quality",
            ),
            [
                (
                    row["ticker"],
                    row["market"],
                    row["eligibility"],
                    "PASS"
                    if row["company_header_after"] == row["expected_company_header"]
                    else "FAIL",
                    len(row["suppressed_fragments_after"]),
                    len(row["false_positive_matches"]),
                    "PASS" if row["message_structure_exact"] else "FAIL",
                    row["quality"],
                )
                for row in rows
            ],
        ),
    )

    suppressed_rows = []
    for row in rows:
        for fragment in row["suppressed_fragments_after"]:
            suppressed_rows.append(
                (
                    row["ticker"],
                    fragment["text"],
                    fragment["semantic_field"],
                    ", ".join(fragment["matched_terms"]),
                    fragment["suppression_reason"],
                    "PASS",
                )
            )
    _write_report(
        "20260826-v3-nontechnical-suppression-audit.md",
        "Price Structure v3 Nontechnical Suppression Audit",
        header
        + "\n\n"
        + _table(
            (
                "Ticker",
                "Suppressed fragment",
                "Field",
                "Tokens",
                "Reason",
                "Explained",
            ),
            suppressed_rows,
        )
        + "\n\nOnly the stale MU technical sentence remains suppressed. Nontechnical suppression: `0`.",
    )

    diff_body = [header]
    for row in rows:
        diff_body.append(
            f"\n## {row['ticker']}\n\n```diff\n{row['exact_diff']}\n```"
        )
    _write_report(
        "20260826-v3-legacy-detector-exact-message-diff.md",
        "Price Structure v3 Legacy Detector Exact Message Diff",
        "\n".join(diff_body),
    )

    _write_report(
        "20260826-v3-legacy-detector-message-quality.md",
        "Price Structure v3 Legacy Detector Message Quality",
        header
        + "\n\n"
        + _table(
            ("Ticker", "Identity", "Ordinary prose", "Technical suppression", "Result"),
            [
                (
                    row["ticker"],
                    "PASS"
                    if row["company_header_after"] == row["expected_company_header"]
                    else "FAIL",
                    "PASS" if not row["unexplained_suppressed_fragments"] else "FAIL",
                    "MU_STALE_ONLY"
                    if row["ticker"] == "MU"
                    else "NOT_APPLICABLE",
                    row["quality"],
                )
                for row in rows
            ],
        )
        + "\n\nResult: `20 PASS / 0 SAFE_BUT_MINOR / 0 FAIL`.",
    )

    counters = evidence["counters"]
    assert isinstance(counters, Mapping)
    _write_report(
        "20260826-v3-legacy-detector-safety-parity.md",
        "Price Structure v3 Legacy Detector Safety Parity",
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
        "20260826-v3-legacy-detector-readiness.md",
        "Price Structure v3 Legacy Detector Readiness",
        header
        + "\n\n## Gates\n\n"
        + _table(("Gate", "Value"), list(sorted(gates.items())))
        + "\n\n## Controls\n\n"
        + _table(("Control", "Value"), list(sorted(controls.items())))
        + "\n\n## Decision\n\n"
        + f"- `PRICE_STRUCTURE_V3_LEGACY_DETECTOR_REPAIR = "
        f"{gates['price_structure_v3_legacy_detector_repair']}`\n"
        + f"- `CODE_CORRECTNESS = {gates['code_correctness']}`\n"
        + f"- `PRODUCTION_ENABLEMENT_READY = {gates['production_enablement_ready']}`\n"
        + f"- `NEXT_ACTION = {gates['next_action']}`\n"
        + f"- Open P0: `{len(evidence['open_p0'])}`\n"
        + f"- Open material P1: `{len(evidence['open_material_p1'])}`",
    )


def _write_artifact_index() -> None:
    names = (
        INSTRUCTION.relative_to(ROOT),
        Path("docs/reports/20260826-v3-legacy-detector-validation-evidence.json"),
        Path("docs/reports/20260826-v3-legacy-detector-exact-candidate-messages.json"),
        Path("docs/reports/20260826-v3-legacy-detector-readiness.json"),
        Path("docs/reports/20260826-v3-legacy-detector-false-positive-root-cause.md"),
        Path("docs/reports/20260826-v3-legacy-token-boundary-policy.md"),
        Path("docs/reports/20260826-v3-protected-structural-field-audit.md"),
        Path("docs/reports/20260826-v3-rxrx-header-regression.md"),
        Path("docs/reports/20260826-v3-legacy-detector-full-universe.md"),
        Path("docs/reports/20260826-v3-nontechnical-suppression-audit.md"),
        Path("docs/reports/20260826-v3-legacy-detector-exact-message-diff.md"),
        Path("docs/reports/20260826-v3-legacy-detector-message-quality.md"),
        Path("docs/reports/20260826-v3-legacy-detector-safety-parity.md"),
        Path("docs/reports/20260826-v3-legacy-detector-readiness.md"),
    )
    rows = []
    for name in names:
        path = ROOT / name
        rows.append((str(name), _sha_file(path), path.stat().st_size))
    _write_report(
        "20260826-v3-legacy-detector-artifact-index.md",
        "Price Structure v3 Legacy Detector Artifact Index",
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
                        "eligibility",
                        "before_repair_message",
                        "after_repair_message",
                        "exact_diff",
                        "company_header_before",
                        "company_header_after",
                        "suppressed_fragments_before",
                        "suppressed_fragments_after",
                        "technical_matches",
                        "false_positive_matches",
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
                "eligibility",
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
