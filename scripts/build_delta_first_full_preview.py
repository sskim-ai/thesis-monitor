from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from sqlmodel import Session, create_engine

from app.schemas.ai_review import AIDailyReviewOutput, AIStockReview
from app.services.ai_assisted_delivery_service import _render_ai_stock_message
from app.services.ai_reasoning_quality_service import runtime_message_quality_receipt
from app.services.ai_review_service import _validate_bound_ai_review_output
from app.services.delta_first_rendering_service import (
    build_delta_first_render_plan,
    build_delta_first_stock_draft,
    prepare_delta_first_packet,
)
from app.services.numeric_provenance_service import bind_numeric_fact_references


REPRESENTATIVE_TICKERS = ("005930", "005490", "086280", "003690", "000660")
RETROSPECTIVE_PACKET_ID = "2026-08-16-kr-phase8-4-delta-first-retrospective"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an archive-only Phase 8.4 integrated full-message Preview"
    )
    parser.add_argument("--source-packet", required=True, type=Path)
    parser.add_argument("--source-output", required=True, type=Path)
    parser.add_argument("--source-messages", required=True, type=Path)
    parser.add_argument("--deterministic-messages", required=True, type=Path)
    parser.add_argument("--recovery-audit", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--prefix", default="20260817-phase8-4")
    parser.add_argument("--before-rendered-audit", type=Path)
    parser.add_argument(
        "--retrospective-packet-id",
        default=RETROSPECTIVE_PACKET_ID,
    )
    parser.add_argument(
        "--preview-title",
        default="Phase 8.4 Delta-First Integrated Full Message Preview",
    )
    parser.add_argument("--before-label", default="BEFORE")
    parser.add_argument("--after-label", default="AFTER")
    parser.add_argument("--preview-suffix", default="delta-first-full-preview")
    parser.add_argument("--audit-suffix", default="adaptive-selection-audit")
    parser.add_argument("--logical-prefix", default="phase8-4")
    return parser


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write(path, payload)


def _write_text(path: Path, value: str) -> None:
    _atomic_write(path, value.rstrip() + "\n")


def _atomic_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _message_map(value: dict[str, object], *, deterministic: bool = False) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in value.get("messages", []):
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker") or "")
        payload = item.get("payload") if deterministic else item
        text = payload.get("text") if isinstance(payload, dict) else None
        if ticker and isinstance(text, str):
            output[ticker] = text
    return output


def _rendered_message_map(value: dict[str, object]) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in value.get("rendered_messages", []):
        if not isinstance(item, dict):
            continue
        ticker = str(item.get("ticker") or "")
        message = item.get("text")
        if ticker and isinstance(message, str):
            output[ticker] = message
    return output


def _counts(text: str) -> dict[str, int]:
    return {
        "characters": len(text),
        "lines": len(text.splitlines()),
        "sections": sum(
            line.startswith(("🎯", "📈", "💰", "📊", "📐", "⚠️", "👁", "📌"))
            for line in text.splitlines()
        ),
    }


def _markdown_preview(
    source_packet: dict[str, object],
    before: dict[str, str],
    after: dict[str, str],
    audits: dict[str, object],
    names: dict[str, str],
    *,
    title: str,
    before_label: str,
    after_label: str,
) -> str:
    sections = [
        f"# {title}",
        "",
        (
            "Archive-only Preview from source packet "
            f"`{source_packet.get('packet_id')}`. The AFTER blocks are exact renderer output; "
            "they were not edited by hand. Telegram sends: `0`."
        ),
    ]
    for ticker in REPRESENTATIVE_TICKERS:
        before_text = before[ticker]
        after_text = after[ticker]
        audit = audits[ticker]
        before_counts = _counts(before_text)
        after_counts = _counts(after_text)
        sections.extend(
            [
                "",
                "---",
                "",
                f"## {names[ticker]} ({ticker})",
                "",
                f"### {before_label}",
                "",
                before_text,
                "",
                f"### {after_label}",
                "",
                after_text,
                "",
                "### DELTA",
                "",
                (
                    f"- Full schema-4 stock review: yes; materiality: "
                    f"`{audit['plan']['material_delta']}`."
                ),
                (
                    f"- Sections selected: {', '.join(audit['selected_sections'])}; "
                    f"suppressed: {', '.join(audit['suppressed_sections'])}."
                ),
                (
                    f"- Length: {before_counts['characters']} → {after_counts['characters']} "
                    f"characters; {before_counts['lines']} → {after_counts['lines']} lines; "
                    f"{before_counts['sections']} → {after_counts['sections']} sections."
                ),
                (
                    f"- Used Facts: financial {audit['used_fact_counts']['financial']}, "
                    f"price {audit['used_fact_counts']['price']}, "
                    f"supply {audit['used_fact_counts']['supply']}, "
                    f"valuation {audit['used_fact_counts']['valuation']}."
                ),
                "",
                "### HUMAN SCORE",
                "",
                "Recorded in the separate human-quality validation report.",
            ]
        )
    return "\n".join(sections)


def main() -> None:
    args = _parser().parse_args()
    source_packet = _load(args.source_packet)
    source_output = _load(args.source_output)
    source_messages = _load(args.source_messages)
    deterministic_messages = _load(args.deterministic_messages)
    recovery_audit = _load(args.recovery_audit)
    recoveries = recovery_audit.get("results")
    if not isinstance(recoveries, dict):
        raise ValueError("recovery audit results missing")

    packet = prepare_delta_first_packet(
        source_packet,
        recoveries,
        REPRESENTATIVE_TICKERS,
        packet_id=args.retrospective_packet_id,
    )
    packet_stocks = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    original_reviews = {
        str(item.get("ticker") or ""): item
        for item in source_output.get("stock_reviews", [])
        if isinstance(item, dict)
    }
    drafts: list[dict[str, object]] = []
    selection_audit: dict[str, object] = {}
    for ticker in REPRESENTATIVE_TICKERS:
        draft, audit = build_delta_first_stock_draft(
            packet_stocks[ticker],
            original_reviews[ticker],
            recoveries[ticker],
        )
        drafts.append(draft)
        selection_audit[ticker] = audit

    binding = bind_numeric_fact_references(packet, {"stock_reviews": drafts})
    if binding.errors:
        raise ValueError("numeric binding failed: " + "; ".join(binding.errors))
    typed_errors = binding.report.get("typed_valuation_interpretations", {}).get(
        "errors", []
    )
    if typed_errors:
        raise ValueError(
            "typed valuation binding failed: "
            + "; ".join(str(item) for item in typed_errors)
        )
    output_value = dict(source_output)
    output_value["packet_id"] = args.retrospective_packet_id
    output_value["stock_reviews"] = binding.output["stock_reviews"]
    output = AIDailyReviewOutput.model_validate(output_value)

    database_uri = f"sqlite:///file:{args.database.resolve()}?mode=ro&immutable=1&uri=true"
    engine = create_engine(database_uri)
    with Session(engine) as session:
        validated, validation_errors = _validate_bound_ai_review_output(
            session,
            packet,
            output.model_dump(mode="json"),
        )
    if validated is None or validation_errors:
        raise ValueError("full validation failed: " + "; ".join(validation_errors))

    before_messages = (
        _rendered_message_map(_load(args.before_rendered_audit))
        if args.before_rendered_audit is not None
        else _message_map(source_messages)
    )
    deterministic = _message_map(deterministic_messages, deterministic=True)
    names = {
        ticker: str(packet_stocks[ticker].get("company_name") or ticker)
        for ticker in REPRESENTATIVE_TICKERS
    }
    after_messages: dict[str, str] = {}
    rendered: list[dict[str, object]] = []
    market_ticker = "__DAILY_DIGEST_KR__"
    rendered.append(
        {
            "ticker": market_ticker,
            "text": before_messages[market_ticker],
            "logical_identity": (
                f"{args.logical_prefix}:{args.retrospective_packet_id}:market"
            ),
        }
    )
    for review in output.stock_reviews:
        stock = packet_stocks[review.ticker]
        financial_available = bool(selection_audit[review.ticker]["financial_available"])
        plan = build_delta_first_render_plan(
            stock,
            financial_available=financial_available,
        )
        text = _render_ai_stock_message(
            deterministic[review.ticker],
            AIStockReview.model_validate(review),
            market="kr",
            pilot_day=3,
            target_days=5,
            render_plan=plan,
        )
        after_messages[review.ticker] = text
        rendered.append(
            {
                "ticker": review.ticker,
                "text": text,
                "logical_identity": (
                    f"{args.logical_prefix}:{args.retrospective_packet_id}:"
                    f"stock:{review.ticker}"
                ),
            }
        )

    receipt = runtime_message_quality_receipt(
        packet,
        output,
        rendered,
        binding_errors=binding.errors,
        validation_errors=validation_errors,
    )
    if receipt.get("status") != "passed":
        quality = receipt.get("check_results", {})
        raise ValueError(
            "runtime quality gate failed: "
            + json.dumps(
                {
                    "errors": receipt.get("errors", []),
                    "substantive_repeats": quality.get(
                        "substantive_repeated_sentence_count"
                    ),
                    "template_repeats": quality.get("template_skeleton_repeats"),
                    "supply_repeats": quality.get("supply_routing"),
                    "completeness": quality.get("message_set_completeness"),
                    "headings": quality.get("rendered_heading_quality"),
                    "final_language": quality.get("final_rendered_language"),
                    "supply_coverage": quality.get("kr_supply_numeric_coverage"),
                },
                ensure_ascii=False,
            )
        )

    prefix = args.prefix
    output_dir = args.output_dir
    context = {
        "source_packet": source_packet.get("packet_id"),
        "retrospective_packet": args.retrospective_packet_id,
        "source_packet_sha256": _sha256(args.source_packet),
        "source_output_sha256": _sha256(args.source_output),
        "source_messages_sha256": _sha256(args.source_messages),
        "recovery_audit_sha256": _sha256(args.recovery_audit),
        "source_database_sha256": _sha256(args.database),
        "provider_calls": 0,
        "telegram_sends": 0,
        "database_mutations": 0,
        "pilot_mutations": 0,
        "human_quality_status": "pending_work_human_review",
    }
    _write_json(
        output_dir / f"{prefix}-full-schema-output.json",
        {"artifact_context": context, "output": output.model_dump(mode="json")},
    )
    _write_json(
        output_dir / f"{prefix}-numeric-binding.json",
        {"artifact_context": context, "result": binding.report},
    )
    _write_json(
        output_dir / f"{prefix}-validator.json",
        {
            "artifact_context": context,
            "result": {"status": "passed", "errors": validation_errors},
        },
    )
    _write_json(
        output_dir / f"{prefix}-runtime-quality-receipt.json",
        {"artifact_context": context, "receipt": receipt},
    )
    _write_json(
        output_dir / f"{prefix}-{args.audit_suffix}.json",
        {
            "artifact_context": context,
            "contract": "delta-first-rendering-v1",
            "stocks": selection_audit,
            "rendered_messages": rendered,
        },
    )
    _write_text(
        output_dir / f"{prefix}-{args.preview_suffix}.md",
        _markdown_preview(
            source_packet,
            before_messages,
            after_messages,
            selection_audit,
            names,
            title=args.preview_title,
            before_label=args.before_label,
            after_label=args.after_label,
        ),
    )


if __name__ == "__main__":
    main()
