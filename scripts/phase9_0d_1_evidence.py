from __future__ import annotations

# ruff: noqa: E402

import argparse
import json
import sys
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cash_flow_baseline_consistency_service import (
    CONTRACT_VERSION,
    CanonicalCashFlowEvidence,
    consistency_error,
    decision_to_dict,
    load_canonical_cash_flow_evidence,
    provenance_from_warning_state,
    repair_baseline_cash_flow_text,
    rendered_message_cash_flow_sections,
)


PACKET_ID = "2026-08-21-us-run-30-5a3b7c1c4390"
CANARY_ID = "cf-canary-f5ce3f836df99c546cf6f696"
CUTOFF = date(2026, 8, 21)
INSTRUCTION_COMMIT = "20367c056e6d1da7db3edee37818210c070e1e7d"
INSTRUCTION_PATH = (
    "docs/work-instructions/"
    "20260821-phase-9-0d-1-baseline-cash-flow-consistency-repair.md"
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _canary_attempt(archive: Path) -> Path:
    attempts = sorted(
        (archive / "cash-flow-shadow-canary" / CANARY_ID / "attempts").glob(
            "attempt-*"
        )
    )
    if len(attempts) != 1:
        raise ValueError(f"Expected one immutable canary attempt, found {len(attempts)}")
    return attempts[0]


def _context_map(
    repository: Path,
    natural_sidecar: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    phase9c = _read_json(
        repository / "docs/reports/20260820-phase9-0c-shadow-context.json"
    )
    output = {
        str(row["ticker"]): dict(row["context"])
        for row in phase9c.get("ticker_audit") or ()
        if isinstance(row, dict)
        and row.get("ticker")
        and isinstance(row.get("context"), dict)
    }
    for ticker, context in (natural_sidecar.get("subjects") or {}).items():
        if isinstance(context, dict):
            output[str(ticker)] = dict(context)
    return output


def _evidence_by_ticker(
    repository: Path,
    active_tickers: Sequence[str],
    contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, CanonicalCashFlowEvidence]:
    report = repository / "docs/reports/20260820-phase9-0b-canonical-facts.json"
    output: dict[str, CanonicalCashFlowEvidence] = {}
    for ticker in active_tickers:
        context = contexts.get(ticker, {})
        primary = context.get("primary_period")
        primary_end = None
        if isinstance(primary, dict) and primary.get("period_end"):
            primary_end = date.fromisoformat(str(primary["period_end"]))
        freshness = str(context.get("freshness_state") or "BLOCKED")
        preliminary = (
            primary_end + timedelta(days=1)
            if freshness == "FORMAL_LAGGING_PROVISIONAL" and primary_end
            else None
        )
        evidence = load_canonical_cash_flow_evidence(
            ticker,
            cutoff=CUTOFF,
            latest_formal_period=primary_end,
            latest_preliminary_period=preliminary,
            report_path=report,
        )
        output[ticker] = replace(evidence, freshness_state=freshness)
    return output


def _latest_warning_states(operating: Path, ticker: str) -> dict[str, dict[str, object]]:
    path = operating / "data/history" / f"{ticker}.jsonl"
    if not path.exists():
        return {}
    latest: dict[str, object] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        if str(row.get("assessment_date") or "") <= CUTOFF.isoformat():
            latest = row
    if not latest:
        return {}
    return {
        str(item["warning"]): item
        for item in latest.get("warning_states") or ()
        if isinstance(item, dict) and item.get("warning")
    }


def _append_claims(
    rows: list[dict[str, object]],
    *,
    ticker: str,
    text: str,
    text_ref: str,
    section: str,
    origin_type: str,
    evidence: CanonicalCashFlowEvidence,
    origin_version: str | None = None,
    provenance_refs: Sequence[str] = (),
    provenance_valid: bool = False,
) -> str:
    repair = repair_baseline_cash_flow_text(
        ticker,
        text,
        evidence,
        text_ref=text_ref,
        section=section,
        origin_type=origin_type,
        origin_version=origin_version,
        provenance_refs=provenance_refs,
        provenance_valid=provenance_valid,
    )
    for decision in repair.decisions:
        row = decision_to_dict(decision)
        claim = row["claim"]
        rows.append(
            {
                "ticker": ticker,
                "section": section,
                "text_ref": text_ref,
                "origin": origin_type,
                "origin_version": origin_version,
                "claim_id": claim["claim_id"],
                "exact_short_claim_span": claim["claim_span"],
                "metric_semantic": claim["metric_semantic"],
                "sign_or_state": claim["state_or_sign"],
                "period_type": claim["period_type"],
                "scope": claim["scope"],
                "currentness": claim["claim_currentness"],
                "provenance_available": claim["provenance_valid"],
                "provenance_refs": claim["provenance_refs"],
                "canonical_fact_available": bool(
                    decision.canonical_comparison_fact_id
                ),
                "canonical_comparison_fact_id": (
                    decision.canonical_comparison_fact_id
                ),
                "canonical_freshness": evidence.freshness_state,
                "consistency_result": decision.consistency_result.value,
                "render_action": decision.render_action.value,
                "suppression_reason": decision.suppression_reason,
                "required_qualifier": decision.required_qualifier,
                "validator_error": consistency_error(decision),
                "severity_if_problematic": (
                    "P0"
                    if decision.render_action.value == "SUPPRESS"
                    and decision.claim.claim_currentness.value
                    in {"explicit_current", "implied_current"}
                    else None
                ),
            }
        )
    return repair.text


def _scan_saved_theses(
    operating: Path,
    evidence: Mapping[str, CanonicalCashFlowEvidence],
    rows: list[dict[str, object]],
) -> None:
    list_fields = {
        "strengthen_signals": "strengthen_signals",
        "weaken_signals": "weaken_signals",
        "invalidation_signals": "invalidation_signals",
        "validation_metrics": "validation_metrics",
        "multiple_expansion_signals": "strengthen_signals",
        "multiple_compression_signals": "weaken_signals",
    }
    for ticker in sorted(evidence):
        path = operating / "data/theses" / f"{ticker}.json"
        if not path.exists():
            continue
        thesis = _read_json(path)
        version = f"thesis:{ticker}:v{thesis.get('version')}"
        core = thesis.get("core_thesis")
        if isinstance(core, str):
            _append_claims(
                rows,
                ticker=ticker,
                text=core,
                text_ref=f"data/theses/{ticker}.json:core_thesis",
                section="core_thesis",
                origin_type="saved_thesis",
                origin_version=version,
                evidence=evidence[ticker],
            )
        for field, section in list_fields.items():
            for index, text in enumerate(thesis.get(field) or ()):
                if isinstance(text, str):
                    _append_claims(
                        rows,
                        ticker=ticker,
                        text=text,
                        text_ref=f"data/theses/{ticker}.json:{field}[{index}]",
                        section=section,
                        origin_type="saved_thesis",
                        origin_version=version,
                        evidence=evidence[ticker],
                    )


def _scan_run30(
    packet: Mapping[str, object],
    fallback: Mapping[str, object],
    operating: Path,
    evidence: Mapping[str, CanonicalCashFlowEvidence],
    rows: list[dict[str, object]],
) -> tuple[str, str]:
    for stock in packet.get("stocks") or ():
        if not isinstance(stock, dict) or not stock.get("ticker"):
            continue
        ticker = str(stock["ticker"])
        if ticker not in evidence:
            continue
        thesis = stock.get("thesis")
        core = thesis.get("core_thesis") if isinstance(thesis, dict) else None
        if isinstance(core, str):
            _append_claims(
                rows,
                ticker=ticker,
                text=core,
                text_ref="run30.packet:thesis.core_thesis",
                section="core_thesis",
                origin_type="immutable_packet",
                origin_version=PACKET_ID,
                evidence=evidence[ticker],
            )
        states = _latest_warning_states(operating, ticker)
        for index, text in enumerate(stock.get("data_cautions") or ()):
            if not isinstance(text, str):
                continue
            refs, valid = provenance_from_warning_state(states.get(text))
            _append_claims(
                rows,
                ticker=ticker,
                text=text,
                text_ref=f"run30.packet:data_cautions[{index}]",
                section="data_cautions",
                origin_type="immutable_packet",
                origin_version=PACKET_ID,
                evidence=evidence[ticker],
                provenance_refs=refs,
                provenance_valid=valid,
            )
    before = ""
    after = ""
    for message in fallback.get("messages") or ():
        if not isinstance(message, dict) or not message.get("ticker"):
            continue
        ticker = str(message["ticker"])
        text = str(message.get("text") or "")
        if ticker not in evidence:
            continue
        for heading, section, value in rendered_message_cash_flow_sections(text):
            _append_claims(
                rows,
                ticker=ticker,
                text=value,
                text_ref=f"run30.fallback:{heading}",
                section=section,
                origin_type="immutable_production_fallback",
                origin_version=PACKET_ID,
                evidence=evidence[ticker],
            )
        if ticker == "TSLA":
            before = text
            after = _repair_rendered_message(ticker, text, evidence[ticker])
    return before, after


def _repair_rendered_message(
    ticker: str,
    text: str,
    evidence: CanonicalCashFlowEvidence,
) -> str:
    repaired_message = text
    list_sections = {
        "new_warnings",
        "open_warnings",
        "data_cautions",
        "persistent_risks",
        "next_checks",
        "unknowns",
    }
    for heading, section, value in rendered_message_cash_flow_sections(text):
        if section in list_sections:
            repaired_lines: list[str] = []
            for index, line in enumerate(value.splitlines()):
                bullet = "• " if line.strip().startswith("•") else ""
                item = line.strip().removeprefix("•").strip()
                repaired = repair_baseline_cash_flow_text(
                    ticker,
                    item,
                    evidence,
                    text_ref=f"run30.fallback:{heading}[{index}]",
                    section=section,
                    origin_type="immutable_production_fallback",
                    origin_version=PACKET_ID,
                ).text
                if repaired:
                    repaired_lines.append(f"{bullet}{repaired}")
            repaired_value = "\n".join(repaired_lines)
        else:
            repaired_value = repair_baseline_cash_flow_text(
                ticker,
                value,
                evidence,
                text_ref=f"run30.fallback:{heading}",
                section=section,
                origin_type="immutable_production_fallback",
                origin_version=PACKET_ID,
            ).text
        repaired_message = repaired_message.replace(value, repaired_value, 1)
    return repaired_message


def _counts(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    results = {
        state: sum(row.get("consistency_result") == state for row in rows)
        for state in (
            "CONSISTENT",
            "QUALIFIER_REQUIRED",
            "STALE_CONFLICT",
            "UNSUPPORTED_CLAIM",
            "NOT_COMPARABLE",
            "NO_CANONICAL_CHECK_AVAILABLE",
        )
    }
    actions = {
        action: sum(row.get("render_action") == action for row in rows)
        for action in ("KEEP", "QUALIFY", "SUPPRESS")
    }
    return {
        "total": len(rows),
        "by_consistency_result": results,
        "by_render_action": actions,
        "problematic_current_claims": sum(
            bool(row.get("severity_if_problematic")) for row in rows
        ),
    }


def _post_repair_audit(
    fallback: Mapping[str, object],
    evidence: Mapping[str, CanonicalCashFlowEvidence],
) -> dict[str, object]:
    claim_count = 0
    errors: list[dict[str, str]] = []
    for message in fallback.get("messages") or ():
        if not isinstance(message, dict) or not message.get("ticker"):
            continue
        ticker = str(message["ticker"])
        if ticker not in evidence:
            continue
        repaired_message = _repair_rendered_message(
            ticker,
            str(message.get("text") or ""),
            evidence[ticker],
        )
        for heading, section, value in rendered_message_cash_flow_sections(
            repaired_message
        ):
            repair = repair_baseline_cash_flow_text(
                ticker,
                value,
                evidence[ticker],
                text_ref=f"run30.repaired:{heading}",
                section=section,
                origin_type="archive_only_repaired_preview",
                origin_version=PACKET_ID,
            )
            claim_count += len(repair.decisions)
            for decision in repair.decisions:
                error = consistency_error(decision)
                if error:
                    errors.append(
                        {
                            "ticker": ticker,
                            "section": section,
                            "claim_span": decision.claim.claim_span,
                            "error": error,
                        }
                    )
    return {
        "status": "PASS" if not errors else "FAIL",
        "claim_count": claim_count,
        "error_count": len(errors),
        "errors": errors,
    }


def build_evidence(repository: Path, operating: Path) -> dict[str, object]:
    archive = (
        operating
        / "data/ai_review/pilot/history/2026/08"
        / PACKET_ID
    )
    attempt = _canary_attempt(archive)
    packet = _read_json(archive / "packet.json")
    fallback = _read_json(archive / "fallback-messages.json")
    sidecar = _read_json(attempt / "cash-flow-sidecar.json")
    receipt = _read_json(attempt / "canary-receipt.json")
    canonical = _read_json(
        repository / "docs/reports/20260820-phase9-0b-canonical-facts.json"
    )
    active_tickers = sorted(
        str(item["ticker"])
        for item in canonical.get("active_universe") or ()
        if isinstance(item, dict) and item.get("ticker")
    )
    contexts = _context_map(repository, sidecar)
    evidence = _evidence_by_ticker(repository, active_tickers, contexts)
    rows: list[dict[str, object]] = []
    _scan_saved_theses(operating, evidence, rows)
    before, after = _scan_run30(packet, fallback, operating, evidence, rows)
    tsla_fcf = [
        {
            key: row.get(key)
            for key in (
                "fact_id",
                "value",
                "period_start",
                "period_end",
                "period_type",
                "fiscal_year",
                "fiscal_quarter",
                "filing_date",
                "input_fact_ids",
            )
        }
        for row in canonical.get("canonical_facts") or ()
        if isinstance(row, dict)
        and row.get("ticker") == "TSLA"
        and row.get("metric") == "free_cash_flow_ppe"
        and row.get("period_end") == "2026-06-30"
    ]
    return {
        "audit": "phase9-0d-1-baseline-cash-flow-claim-inventory-v1",
        "as_of": CUTOFF.isoformat(),
        "contract": CONTRACT_VERSION,
        "work_instruction": {
            "path": INSTRUCTION_PATH,
            "version": "1.0",
            "commit": INSTRUCTION_COMMIT,
        },
        "source": {
            "packet_id": PACKET_ID,
            "canary_id": CANARY_ID,
            "canary_status": receipt.get("status"),
            "operating_archive_rewrite_count": 0,
        },
        "universe": {
            "active_subjects": len(active_tickers),
            "tickers": active_tickers,
        },
        "counts": _counts(rows),
        "claims": rows,
        "cross_artifact_post_repair": _post_repair_audit(fallback, evidence),
        "tsla": {
            "root_source": "data/theses/TSLA.json:core_thesis",
            "source_version": "thesis:TSLA:v5",
            "source_created_at": "2026-08-10 14:20:17.365948",
            "source_type": "custom_gpt saved thesis prose",
            "financial_fact_provenance": False,
            "warning_backfill_provenance": "backfilled_saved_thesis",
            "canonical_fcf_same_period_end": tsla_fcf,
            "original_fallback": before,
            "repaired_fallback": after,
            "canonical_number_added_to_repaired_fallback": False,
        },
        "acceptance": {
            "post_repair_unqualified_tsla_fcf_negative": after.count("FCF 적자"),
            "post_repair_unqualified_tsla_turn_positive": after.count(
                "FCF 흑자 전환"
            ),
            "canonical_number_injected": int("$352" in after),
            "stored_thesis_mutations": 0,
            "database_mutations": 0,
            "telegram_deliveries": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument(
        "--operating",
        type=Path,
        default=Path("/Users/sskim/Codex/thesis-monitor"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = build_evidence(args.repository.resolve(), args.operating.resolve())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
