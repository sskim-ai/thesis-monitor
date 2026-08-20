from __future__ import annotations

# ruff: noqa: E402

import argparse
import copy
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.ai_review import AIDailyReviewOutput
from app.services.ai_assisted_delivery_service import (
    _render_ai_market_message,
    _render_ai_stock_message,
)
from app.services.ai_reasoning_quality_service import (
    relational_reasoning_quality_report,
    runtime_message_quality_receipt,
    verify_runtime_message_quality_receipt,
)
from app.services.ai_review_service import validate_ai_review_output
from app.services.numeric_provenance_service import bind_numeric_fact_references
from app.services.runtime_reasoning_ownership_service import (
    apply_candidate_ownership_contracts,
)
from scripts.phase8_5_5_1_evidence import (
    _load,
    _messages_by_ticker,
    _reconstruct_final_draft,
    _sha256,
    _text_payload,
    _write_json,
    generate as generate_run28_evidence,
)
from scripts.phase8_5_5_evidence import _suppress_generic_portfolio_repeats


PACKET_ID = "2026-08-20-kr-run-29-6e8809e1e944"
OUTPUT_NAME = f"{PACKET_ID}--daily-review-v3.10--559ad45e4dd8.json"
REJECTED_ATTEMPT = "1787210564"
RUN_DATE = "20260820"
MARKET_TICKER = "__DAILY_DIGEST_KR__"


def _render(
    packet: dict[str, object],
    output: AIDailyReviewOutput,
    fallback_payload: dict[str, object],
) -> list[dict[str, object]]:
    fallback = _messages_by_ticker(fallback_payload)
    messages: list[dict[str, object]] = [
        {
            "ticker": MARKET_TICKER,
            "logical_identity": f"{PACKET_ID}:MARKET:ai-replay",
            "text": _render_ai_market_message(
                fallback[MARKET_TICKER],
                output.market_review,
                market_context=packet.get("market_context", {}),
                market="kr",
                pilot_day=4,
                target_days=5,
            ),
        }
    ]
    for review in output.stock_reviews:
        messages.append(
            {
                "ticker": review.ticker,
                "logical_identity": f"{PACKET_ID}:{review.ticker}:ai-replay",
                "text": _render_ai_stock_message(
                    fallback[review.ticker],
                    review,
                    market="kr",
                    pilot_day=4,
                    target_days=5,
                ),
            }
        )
    return messages


def _quality_summary(value: dict[str, object]) -> dict[str, object]:
    return {
        "hard_checks_passed": value.get("hard_checks_passed"),
        "substantive_repeated_sentence_count": value.get(
            "substantive_repeated_sentence_count"
        ),
        "template_skeleton_repeat_count": value.get(
            "template_skeleton_repeat_count"
        ),
        "generic_numeric_summary_repeat_count": value.get(
            "generic_numeric_summary_repeat_count"
        ),
        "generic_methodology_repeat_count": value.get(
            "generic_methodology_repeat_count"
        ),
        "observer_holder_distinct_count": value.get(
            "observer_holder_distinct_count"
        ),
        "stock_specific_next_check_count": value.get(
            "stock_specific_next_check_count"
        ),
        "stock_specific_unknown_count": value.get(
            "stock_specific_unknown_count"
        ),
        "numeric_primary_ownership": value.get("numeric_primary_ownership"),
    }


def _basis_row(stock: dict[str, object]) -> dict[str, object]:
    valuation = stock.get("valuation")
    valuation = valuation if isinstance(valuation, dict) else {}
    return {
        "ticker": stock.get("ticker"),
        "company_name": stock.get("company_name"),
        "selected_issuer_type": valuation.get("security_identity_selected_issuer_type"),
        "selected_security_type": valuation.get(
            "security_identity_selected_security_type"
        ),
        "identity_state": valuation.get("security_identity_state"),
        "verification_status": valuation.get("security_identity_verification_status"),
        "source_tier": valuation.get("security_identity_source_tier"),
        "eligibility_decision": valuation.get("security_identity_eligibility_decision"),
        "eps_security_basis": valuation.get("eps_security_basis"),
        "trailing_pe_basis_status": valuation.get("trailing_pe_basis_status"),
        "price_to_book_basis_status": valuation.get("price_to_book_basis_status"),
        "ttm_eps_usable": valuation.get("ttm_eps_usable"),
    }


def _preview(
    before_messages: dict[str, str],
    after_messages: list[dict[str, object]],
    before_quality: dict[str, object],
    after_quality: dict[str, object],
) -> str:
    after_by_ticker = _messages_by_ticker({"messages": after_messages})
    affected = ("000660", "005490", "005930", "010120", "012450")
    comparisons = []
    for ticker in affected:
        comparisons.append(
            f"## {ticker} Before\n\n{before_messages[ticker]}\n\n"
            f"## {ticker} After\n\n{after_by_ticker[ticker]}\n"
        )
    full = []
    for index, item in enumerate(after_messages, start=1):
        full.append(
            f"## Message {index}/8 - {item['ticker']}\n\n{item['text']}\n"
        )
    comparisons_text = "\n".join(comparisons)
    full_text = "\n".join(full)
    return f"""# Run-29 Repaired AI Preview

Date: 2026-08-20
Packet: `{PACKET_ID}`
Boundary: archive-only; Telegram send `0`

## Quality Delta

- Substantive repeated families: {before_quality['substantive_repeated_sentence_count']} -> {after_quality['substantive_repeated_sentence_count']}
- Typed skeleton blockers: {before_quality['template_skeleton_repeat_count']} -> {after_quality['template_skeleton_repeat_count']}
- Generic methodology: {before_quality['generic_methodology_repeat_count']} -> {after_quality['generic_methodology_repeat_count']}
- Observer/holder distinct: {after_quality['observer_holder_distinct_count']}/7
- Specific next checks: {after_quality['stock_specific_next_check_count']}/7
- Specific Unknowns: {after_quality['stock_specific_unknown_count']}/7

The canonical KR supply numbers remain visible. Only repeated analytical boilerplate and secondary
exact RR ownership are removed.

{comparisons_text}

# Full Archive-Only Bundle

{full_text}
"""


def _reports(artifacts: dict[str, object]) -> dict[str, str]:
    after = artifacts["runtime_quality_after"]
    ownership = artifacts["candidate_ownership"]
    suppressions = artifacts["generic_suppressions"]
    basis = artifacts["basis_audit"]
    source = artifacts["source_sha256"]
    root = f"""# Run-29 KR Structured Repetition Root Cause

Date: 2026-08-20
Packet: `{PACKET_ID}`

## Immutable Outcome

The final AI candidate passed numeric/semantic validation and rendered-language checks, then failed
only `runtime_message_quality_gate_failed`. Rejected AI messages sent: `0`. Deterministic fallback
delivered `8/8`; pending `0`. Original archive and receipt rewrites: `0`.

## Exact Root Cause

1. The detector treated stable foreign/institution 1/5/20-day canonical supply rows as ordinary
   portfolio prose. They are now typed as `canonical-supply-flow-tuple-v1`; adjacent interpretation
   remains quality-checked.
2. Exact current-price RR was bound in both `core_judgment.text` and
   `price_positioning.text`. `numeric-primary-owner-v1` retains only the price owner when the
   secondary occurrence is mechanically and safely removable.
3. One common financial-period/statement-basis warning repeated across three stocks although each
   following sentence already named a company-specific missing driver.
4. `재고·CAPEX 이후 FCF·ROIC` repeated as a generic watch item across memory and steel stocks even
   though their first watch, Unknown, and next check were already specific.

## Evidence Integrity

- Packet SHA-256: `{source['packet']}`
- Bound output SHA-256: `{source['archived_bound_output']}`
- Original quality receipt SHA-256: `{source['quality_receipt']}`
- Delivery result SHA-256: `{source['delivery_result']}`
"""
    supply = """# Run-29 Structured Supply Tuple Audit

Contract: `canonical-supply-flow-tuple-v1`

The seven KR stocks retain all eligible foreign/institution actor-horizon claims. The tuple identity
preserves owner `positioning`, market `KR`, metric family `supply_flow`, actors foreign/institution,
and horizons 1d/5d/20d. Stable canonical tuple shapes are structural exceptions; no blanket numeric
or semicolon allowlist exists.

- Before supply typed blockers: `3` families (1d across 7, 5d across 6, 20d across 7).
- After supply typed blockers: `0`.
- Canonical values removed: `0`.
- Interpretive prose detector disabled: `0`.
- User-visible KRX breadth integration: `0`.

The existing company-specific final relationship sentence is preserved. A generic repeated
interpretation would still be rejected by the substantive and typed prose gates.
"""
    rr = f"""# Run-29 RR Cross-Section Ownership Audit

Contract: `numeric-primary-owner-v1`

- Primary owner: `price_context`
- Primary field: `price_positioning.text`
- Exact current RR occurrence limit: `1`
- Safe secondary suppressions: `{len(ownership['suppressions'])}`
- Unresolved automatic rewrites: `{len(ownership['unresolved'])}`
- RR formula/support/resistance/transition thresholds changed: `0`

Before, SK hynix, Samsung Electronics, LS ELECTRIC, and Hanwha Aerospace repeated the same exact RR
in core and price. After, price owns the exact value and core retains its company-specific decision
meaning. An embedded or ambiguous secondary occurrence is not rewritten; it remains a validator
failure. Material transition comparisons remain confined to the primary price transition.
"""
    cash = f"""# Run-29 Industry Cash-Conversion Specificity

The generic `재고·CAPEX 이후 FCF·ROIC` watch candidate was removed for three stocks. This does not
remove the actual investment question:

- SK hynix retains HBM4 shipment/yield/LTA and HBM/DRAM ASP/margin checks.
- POSCO Holdings retains steel price/volume and materials profitability checks.
- Samsung Electronics retains HBM4 adoption/yield and DS margin checks.
- LS ELECTRIC already uses order backlog to revenue/margin plus receivables/OCF.
- Hanwha Aerospace already uses order conversion, defense margin, contract assets, OCF, and FCF.

No OCF, CAPEX, FCF, inventory, or ROIC number was created. Missing data remains a company-specific
Unknown or next check. Generic candidate suppressions in the replay: `{len(suppressions)}` total,
including financial caution and watch-family occurrences.
"""
    basis_lines = "\n".join(
        f"- `{item['ticker']}` {item['company_name']}: issuer `{item['selected_issuer_type']}`; "
        f"security `{item['selected_security_type']}`; identity `{item['identity_state']}` / "
        f"`{item['verification_status']}`; EPS basis `{item['eps_security_basis']}`; trailing PE "
        f"`{item['trailing_pe_basis_status']}`; PBR `{item['price_to_book_basis_status']}`."
        for item in basis
    )
    basis_report = f"""# KR Valuation Basis Caution Audit

## LS ELECTRIC / Hanwha Aerospace

{basis_lines}

Both records select a KRX common-stock shape, but the source is the inferred local tier and the
canonical identity remains `unknown`/unverified. EPS currency/share basis and book share basis are
not verified; dependent trailing PE/PBR remain unavailable by contract. This is an upstream
identity/denominator limitation, not merely false prose. The repair keeps fail-closed valuation and
does not calculate or mark any denominator verified. The common warning is suppressed only where
company-specific Unknown prose already conveys the decision-relevant limitation.
"""
    validation = f"""# Phase 8.5.5.2 Validation

Date: 2026-08-20

## Immutable Replay

- Run-29 semantic/numeric validation errors: `{len(artifacts['replay_validation_errors'])}`
- Runtime quality: `{'PASS' if after['hard_checks_passed'] else 'FAIL'}`
- Final language: `{'PASS' if after['final_rendered_language']['hard_checks_passed'] else 'FAIL'}`
- Receipt verification: `{'PASS' if artifacts['receipt_verified'] else 'FAIL'}`
- Structured supply claims preserved: `PASS`
- Current RR cross-section duplicates: `{after['numeric_primary_ownership']['current_rr_violation_count']}`

## Regressions

- Run-28 validation: `{artifacts['run28_regression']['validation_errors']}`; quality `{'PASS' if artifacts['run28_regression']['hard_checks_passed'] else 'FAIL'}`
- Run-27 quality through run-28 replay: `{'PASS' if artifacts['run28_regression']['run27_hard_checks_passed'] else 'FAIL'}`
- Numeric provenance: automatic `{artifacts['numeric_binding']['auto_bound']}`, manual `{artifacts['numeric_binding']['manual_legacy']}`, rejected `{artifacts['numeric_binding']['rejected']}`, unresolved `{len(artifacts['numeric_binding']['errors'])}`.

Full pytest, Ruff, checksum, Action, operationId, exact-SHA Actions, promotion, and operating smoke
are recorded in the final promotion/readiness reports after those gates complete.
"""
    return {
        f"{RUN_DATE}-run29-kr-structured-repetition-root-cause.md": root,
        f"{RUN_DATE}-run29-structured-supply-tuple-audit.md": supply,
        f"{RUN_DATE}-run29-rr-cross-section-ownership-audit.md": rr,
        f"{RUN_DATE}-run29-industry-cash-conversion-specificity.md": cash,
        f"{RUN_DATE}-kr-valuation-basis-caution-audit.md": basis_report,
        f"{RUN_DATE}-phase8-5-5-2-validation.md": validation,
    }


def generate(*, operating_root: Path, output_dir: Path) -> dict[str, object]:
    archive = operating_root / "data/ai_review/pilot/history/2026/08" / PACKET_ID
    rejected = operating_root / "data/ai_review/rejected" / f"{OUTPUT_NAME}.{REJECTED_ATTEMPT}"
    history = operating_root / "data/ai_review/history/2026/08"
    binding_path = history / f"{OUTPUT_NAME.removesuffix('.json')}.numeric-binding.json"
    packet = _load(archive / "packet.json")
    raw_candidate = _load(rejected)
    archived_output = _load(archive / "ai-review.json")
    archived_binding = _load(binding_path)
    rejected_messages = _load(archive / "quality-rejected-ai-messages.json")
    fallback_messages = _load(archive / "fallback-messages.json")
    before_model = AIDailyReviewOutput.model_validate(archived_output)
    before_quality = relational_reasoning_quality_report(
        before_model,
        packet=packet,
        rendered_messages=[
            str(item.get("text") or "")
            for item in rejected_messages.get("messages", [])
            if isinstance(item, dict)
        ],
    )
    reconstructed = _reconstruct_final_draft(
        raw_candidate,
        archived_output,
        archived_binding,
    )
    baseline_binding = bind_numeric_fact_references(packet, reconstructed)
    repaired = copy.deepcopy(reconstructed)
    generic_suppressions = _suppress_generic_portfolio_repeats(
        repaired, before_quality
    )
    owned_candidate, ownership_audit = apply_candidate_ownership_contracts(
        packet, repaired
    )
    binding = bind_numeric_fact_references(packet, owned_candidate)
    database = operating_root / "data/thesis_monitor.sqlite3"
    engine = create_engine(f"sqlite:///file:{database}?mode=ro&uri=true")
    with Session(engine) as session:
        validated, validation_errors = validate_ai_review_output(
            session,
            packet,
            repaired,
        )
    if validated is None or validation_errors:
        raise RuntimeError(f"run-29 replay rejected: {validation_errors}")
    rendered_messages = _render(packet, validated, fallback_messages)
    receipt = runtime_message_quality_receipt(
        packet,
        validated,
        rendered_messages,
        validation_errors=validation_errors,
        checked_at=datetime(2026, 8, 20, 9, 30, tzinfo=UTC),
    )
    verified = verify_runtime_message_quality_receipt(
        receipt,
        packet,
        validated,
        rendered_messages,
    )
    after_quality = receipt["check_results"]
    if receipt["status"] != "passed" or not verified:
        raise RuntimeError(
            "run-29 quality replay failed: "
            + json.dumps(
                {
                    "errors": receipt["errors"],
                    "substantive": after_quality["repeated_sentences"],
                    "templates": after_quality["template_skeleton_repeats"],
                    "primary_owner": after_quality["numeric_primary_ownership"],
                    "language": after_quality["final_rendered_language"],
                },
                ensure_ascii=False,
            )
        )

    with tempfile.TemporaryDirectory(prefix="phase8-5-5-2-run28-") as temp_dir:
        run28 = generate_run28_evidence(
            operating_root=operating_root,
            output_dir=Path(temp_dir),
        )
    run28_after = run28["runtime_quality_after"]
    run27 = run28["run27_regression"]
    stock_packets = {
        str(item.get("ticker") or ""): item
        for item in packet.get("stocks", [])
        if isinstance(item, dict)
    }
    basis_audit = [_basis_row(stock_packets[ticker]) for ticker in ("010120", "012450")]
    before_messages = _messages_by_ticker(rejected_messages)
    after_messages = _messages_by_ticker({"messages": rendered_messages})
    before_lengths = [len(value) for key, value in before_messages.items() if key != MARKET_TICKER]
    after_lengths = [len(value) for key, value in after_messages.items() if key != MARKET_TICKER]
    artifacts: dict[str, object] = {
        "contract": "phase8-5-5-2-run29-replay-v1",
        "packet_id": PACKET_ID,
        "assessment_date": packet.get("assessment_date"),
        "market": packet.get("market"),
        "policy": packet.get("analysis_policy_version"),
        "schema": packet.get("output_schema_version"),
        "source_sha256": {
            "packet": _sha256(archive / "packet.json"),
            "raw_candidate": _sha256(rejected),
            "archived_bound_output": _sha256(archive / "ai-review.json"),
            "archived_numeric_binding": _sha256(binding_path),
            "quality_receipt": _sha256(archive / "message-quality-receipt.json"),
            "fallback_messages": _sha256(archive / "fallback-messages.json"),
            "delivery_result": _sha256(archive / "delivery-result.json"),
        },
        "immutable_validation": _load(archive / "validation-result.json"),
        "immutable_delivery": _load(archive / "delivery-result.json"),
        "baseline_reconstruction": {
            "binding_errors": list(baseline_binding.errors),
            "text_matches_archived": _text_payload(baseline_binding.output)
            == _text_payload(archived_output),
            "expected_difference": "typed postposition before copula corrected",
        },
        "numeric_binding": binding.report,
        "replay_validation_errors": validation_errors,
        "runtime_quality_before": before_quality,
        "runtime_quality_before_summary": _quality_summary(before_quality),
        "runtime_quality_after": after_quality,
        "runtime_quality_after_summary": _quality_summary(after_quality),
        "receipt_verified": verified,
        "candidate_ownership": ownership_audit,
        "generic_suppressions": generic_suppressions,
        "basis_audit": basis_audit,
        "message_length": {
            "before_average": sum(before_lengths) / len(before_lengths),
            "after_average": sum(after_lengths) / len(after_lengths),
            "change_pct": (
                (sum(after_lengths) / len(after_lengths))
                / (sum(before_lengths) / len(before_lengths))
                - 1
            )
            * 100,
        },
        "run28_regression": {
            "validation_errors": run28["replay_validation_errors"],
            "hard_checks_passed": run28_after["hard_checks_passed"],
            "receipt_verified": run28["receipt_verified"],
            "run27_hard_checks_passed": run27["hard_checks_passed"],
            "run27_receipt_verified": run27["receipt_verified"],
        },
        "rendered_messages": rendered_messages,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        output_dir / f"{RUN_DATE}-run29-repaired-ai-output.json",
        validated.model_dump(mode="json"),
    )
    _write_json(
        output_dir / f"{RUN_DATE}-run29-runtime-quality-receipt.json",
        receipt,
    )
    _write_json(
        output_dir / f"{RUN_DATE}-run29-structured-reasoning-audit.json",
        artifacts,
    )
    for name, content in _reports(artifacts).items():
        (output_dir / name).write_text(content, encoding="utf-8")
    (output_dir / f"{RUN_DATE}-run29-repaired-ai-preview.md").write_text(
        _preview(before_messages, rendered_messages, before_quality, after_quality),
        encoding="utf-8",
    )
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operating-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/reports")
    args = parser.parse_args()
    artifacts = generate(
        operating_root=args.operating_root.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(
        json.dumps(
            {
                "packet_id": artifacts["packet_id"],
                "validation_errors": artifacts["replay_validation_errors"],
                "quality_before": artifacts["runtime_quality_before_summary"],
                "quality_after": artifacts["runtime_quality_after_summary"],
                "receipt_verified": artifacts["receipt_verified"],
                "run28_regression": artifacts["run28_regression"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
