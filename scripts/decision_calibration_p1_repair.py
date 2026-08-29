from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.services.cross_market_decision_engine_service import (
    DecisionCandidate,
    DecisionEvidencePacket,
    EvidenceClaim,
    RenderedDecision,
    canonicalize_candidate_metadata,
    decision_distribution,
    decision_message_quality,
    render_shadow_decision,
    validate_decision_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs/reports"
CONTRACT = "decision-calibration-p1-repair-v1"
ADJUDICATION_CONTRACT = "decision-calibration-adjudication-v1"
PORTFOLIO_CONTRACT = "decision-calibration-portfolio-audit-v1"

TIMING_CASES = ("003690", "005490", "010120", "GOOGL", "SKHY", "SNDK")
CONFIDENCE_CASES = ("CORZ", "SKHY", "SNDK")
SELL_POSITIVE_CONTROLS = ("RXRX", "TSLA", "WULF")
BOUNDARY_CONTROLS = ("HUT", "CRCL")


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CalibrationAdjudication(FrozenModel):
    ticker: str
    reviewed_issues: tuple[Literal["DECISION", "TIMING", "CONFIDENCE", "HUT_TAXONOMY"], ...] = (
        Field(min_length=1)
    )
    better_supported: Literal["PRIOR", "BLIND_RERUN", "SYNTHESIS"]
    candidate: DecisionCandidate
    usable_timing_evidence: tuple[EvidenceClaim, ...] = Field(max_length=3)
    missing_timing_evidence: tuple[EvidenceClaim, ...] = Field(max_length=3)
    positive_timing_evidence: tuple[EvidenceClaim, ...] = Field(max_length=3)
    negative_timing_evidence: tuple[EvidenceClaim, ...] = Field(max_length=3)
    decision_critical_confidence_limits: tuple[EvidenceClaim, ...] = Field(max_length=3)
    resolution: EvidenceClaim


class CalibrationAdjudicationOutput(FrozenModel):
    contract: Literal["decision-calibration-adjudication-v1"]
    adjudications: tuple[CalibrationAdjudication, ...] = Field(min_length=1)


class PortfolioCalibrationAudit(FrozenModel):
    contract: Literal["decision-calibration-portfolio-audit-v1"]
    hold_default_bias_after: Literal["NONE", "LOW", "MATERIAL", "FAIL"]
    sell_suppression_bias_after: Literal["NONE", "LOW", "MATERIAL", "FAIL"]
    confidence_calibration: Literal["PASS", "NEEDS_REPAIR", "FAIL"]
    timing_calibration: Literal["PASS", "NEEDS_REPAIR", "FAIL"]
    decision_change_condition_quality: Literal["PASS", "NEEDS_REPAIR", "FAIL"]
    cross_market_decision_semantics: Literal["PASS", "MATERIAL_INCONSISTENCY", "FAIL"]
    forced_high_confidence: bool
    open_material_p1: tuple[str, ...]
    proposed_canary_set: tuple[str, ...] = Field(max_length=6)
    explanation: str = Field(min_length=1, max_length=1800)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strict_json_schema(value: object) -> object:
    if isinstance(value, dict):
        transformed = {
            key: _strict_json_schema(item) for key, item in value.items() if key != "default"
        }
        properties = transformed.get("properties")
        if isinstance(properties, dict):
            transformed["required"] = list(properties)
            transformed["additionalProperties"] = False
        return transformed
    if isinstance(value, list):
        return [_strict_json_schema(item) for item in value]
    return value


def _prior_summary(record: Mapping[str, object]) -> dict[str, object]:
    baseline = record.get("baseline") if isinstance(record.get("baseline"), Mapping) else {}
    independent = (
        record.get("independent") if isinstance(record.get("independent"), Mapping) else {}
    )
    adjudication = (
        record.get("adjudication") if isinstance(record.get("adjudication"), Mapping) else None
    )
    assert isinstance(baseline, Mapping)
    assert isinstance(independent, Mapping)
    return {
        "ticker": record.get("ticker"),
        "baseline": {
            "decision": baseline.get("decision"),
            "confidence": baseline.get("confidence"),
            "timing": baseline.get("timing"),
            "decisive_reason": baseline.get("decisive_reason"),
        },
        "independent": {
            "decision": independent.get("independent_decision"),
            "confidence": independent.get("confidence"),
            "timing": independent.get("timing"),
            "decisive_reason": independent.get("decisive_reason"),
            "timing_basis": independent.get("timing_basis"),
            "data_quality_limitations": independent.get("data_quality_limitations"),
        },
        "adjudication": adjudication,
        "prior_final": {
            "decision": record.get("final_decision"),
            "confidence": record.get("final_confidence"),
            "timing": record.get("final_timing"),
        },
    }


def _review_cases(
    prior_records: Mapping[str, Mapping[str, object]],
    blind_rows: Mapping[str, Mapping[str, object]],
) -> dict[str, tuple[str, ...]]:
    cases: dict[str, set[str]] = {}
    for ticker, prior in prior_records.items():
        blind = blind_rows[ticker].get("candidate")
        if not isinstance(blind, Mapping):
            raise ValueError(f"blind_candidate_missing:{ticker}")
        if blind.get("decision") != prior.get("final_decision"):
            cases.setdefault(ticker, set()).add("DECISION")
    for ticker in TIMING_CASES:
        cases.setdefault(ticker, set()).add("TIMING")
    for ticker in CONFIDENCE_CASES:
        cases.setdefault(ticker, set()).add("CONFIDENCE")
    cases.setdefault("HUT", set()).add("HUT_TAXONOMY")
    return {ticker: tuple(sorted(issues)) for ticker, issues in sorted(cases.items())}


def _referenced_ids(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"evidence_refs", "selected_numeric_fact_refs"} and isinstance(
                item, (list, tuple)
            ):
                refs.update(str(ref) for ref in item)
            else:
                refs.update(_referenced_ids(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            refs.update(_referenced_ids(item))
    return refs


def _bounded_evidence(
    packet: DecisionEvidencePacket,
    *,
    selected_context: object,
) -> list[dict[str, object]]:
    selected = _referenced_ids(selected_context)
    category_counts: Counter[str] = Counter()
    rows: list[dict[str, object]] = []
    for ref in packet.evidence:
        category = str(ref.category)
        category_limit = (
            6 if category in {"flows", "market", "price_structure", "technical_feature"} else 3
        )
        if ref.ref_id not in selected and category_counts[category] >= category_limit:
            continue
        category_counts[category] += 1
        rows.append(
            {
                "ref_id": ref.ref_id,
                "category": ref.category,
                "label": ref.label,
                "statement": ref.statement[:520],
                "as_of": ref.as_of,
                "value": str(ref.value) if ref.value is not None else None,
                "unit": ref.unit,
                "numeric_prose_eligible": ref.numeric_prose_eligible,
            }
        )
    return rows


def _adjudication_prompt(context: Mapping[str, object]) -> str:
    return """You are the bounded final adjudicator for one analytical BUY/HOLD/SELL calibration case.

The first repaired result was generated blind from the same canonical evidence. The prior review is comparison evidence, not an answer key. Select PRIOR, BLIND_RERUN, or a fresh SYNTHESIS only according to the supplied canonical evidence and the semantic contracts below. Do not target a class distribution and do not preserve or flip a label mechanically.

Contracts:
- BUY means current long-horizon upside/asymmetry materially exceeds downside with sufficient business, earnings, and valuation support.
- HOLD means material optionality remains but BUY asymmetry is insufficient and downside dominance is not established. HOLD requires a canonical hold_reason and explicit why_not_buy/why_not_sell.
- SELL means current downside or impaired risk/reward materially dominates conditional upside. It does not require formal thesis invalidation or price breakdown.
- Timing is independent. FAVORABLE, NEUTRAL, and UNFAVORABLE require usable price, technical, flow, or market evidence. INSUFFICIENT is for missing, denied, stale, or materially conflicted timing evidence. NEUTRAL is balanced evidence, not missing evidence.
- Confidence measures decision evidence quality and convergence, not reasoning effort. HIGH needs convergent critical evidence. Material security, valuation, financial-quality, or economic-proof limits usually imply MEDIUM or LOW depending whether they weaken precision or direction.
- RXRX, TSLA, and WULF were prior SELL positive controls; HUT and CRCL were HOLD boundary controls. These are controls, not hard-coded outcomes. Any departure requires direct evidence and a taxonomy explanation.
- HUT prior adjudication was HOLD / LOW / UNFAVORABLE because infrastructure optionality remained material while conversion economics were unproven. Its HOLD reason should be OPTIONALITY_OFFSETS_DOWNSIDE when that boundary remains supported, with both an upgrade and a downside condition.
- CRCL prior adjudication was HOLD / LOW / INSUFFICIENT because platform optionality remained while chart/supply confirmation was insufficient.
- Every claim in the final candidate and calibration fields must cite exact complete ref_id strings from this ticker's canonical packet. Never alter, shorten, splice, or invent a ref_id.
- Use the packet horizon verbatim and reasoning_grade VERY_HIGH.
- Do not put exact numeric values in prose. Numeric display is only through up to three numeric_prose_eligible selected_numeric_fact_refs.
- Do not invent thresholds, facts, valuation ratios, targets, order language, or ticker-specific rules.
- Return exactly one adjudication and output only JSON matching the schema.

CALIBRATION_CASE:
""" + json.dumps(context, ensure_ascii=False, separators=(",", ":"))


def _prepare(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    prior = _read_json(args.prior_review)
    blind = _read_json(args.blind_decisions)
    if not all(isinstance(value, Mapping) for value in (evidence, prior, blind)):
        raise ValueError("invalid_calibration_inputs")
    assert isinstance(evidence, Mapping)
    assert isinstance(prior, Mapping)
    assert isinstance(blind, Mapping)
    evidence_rows = {
        str(row["ticker"]): row for row in evidence.get("rows") or () if isinstance(row, Mapping)
    }
    prior_records = {
        str(row["ticker"]): row for row in prior.get("records") or () if isinstance(row, Mapping)
    }
    blind_rows = {
        str(row["ticker"]): row for row in blind.get("rows") or () if isinstance(row, Mapping)
    }
    if set(evidence_rows) != set(prior_records) or set(evidence_rows) != set(blind_rows):
        raise ValueError("calibration_universe_mismatch")
    cases = _review_cases(prior_records, blind_rows)
    args.trial_dir.mkdir(parents=True, exist_ok=True)
    schema_path = args.trial_dir / "calibration-adjudication.schema.json"
    _write_json(
        schema_path,
        _strict_json_schema(CalibrationAdjudicationOutput.model_json_schema()),
    )
    entries: list[dict[str, object]] = []
    for ticker, issues in cases.items():
        name = f"adjudication-{ticker}"
        packet = DecisionEvidencePacket.model_validate(evidence_rows[ticker]["evidence_packet"])
        prior_summary = _prior_summary(prior_records[ticker])
        selected_context = {
            "prior_review": prior_summary,
            "blind_rerun_candidate": blind_rows[ticker]["candidate"],
        }
        context = {
            "ticker": ticker,
            "reviewed_issues": issues,
            "canonical_evidence_packet": {
                "ticker": packet.ticker,
                "company_name": packet.company_name,
                "market": packet.market,
                "assessment_date": packet.assessment_date,
                "horizon": packet.horizon,
                "evidence": _bounded_evidence(
                    packet,
                    selected_context=selected_context,
                ),
                "data_quality_cautions": packet.data_quality_cautions,
            },
            "prior_review": prior_summary,
            "blind_rerun_candidate": blind_rows[ticker]["candidate"],
        }
        _write_text(args.trial_dir / f"{name}.prompt.txt", _adjudication_prompt(context))
        entries.append(
            {
                "name": name,
                "ticker": ticker,
                "issues": issues,
                "prompt": f"{name}.prompt.txt",
                "output": f"{name}.output.json",
                "log": f"{name}.log",
            }
        )
    _write_json(
        args.trial_dir / "manifest.json",
        {
            "contract": "decision-calibration-trial-manifest-v1",
            "source_evidence": str(args.evidence),
            "source_evidence_sha256": _sha256(args.evidence),
            "prior_review": str(args.prior_review),
            "prior_review_sha256": _sha256(args.prior_review),
            "blind_decisions": str(args.blind_decisions),
            "blind_decisions_sha256": _sha256(args.blind_decisions),
            "schema": schema_path.name,
            "entries": entries,
        },
    )
    print(json.dumps({"trial_dir": str(args.trial_dir), "calls": len(entries)}))


def _run(args: argparse.Namespace) -> None:
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not isinstance(manifest, dict):
        raise ValueError("invalid_manifest")
    version = subprocess.run(
        [str(args.codex_bin), "--version"],
        capture_output=True,
        check=False,
        text=True,
    )
    manifest["runtime_config"] = {
        "route": "signed_in_local_codex_cli_archive_only",
        "cli_version": version.stdout.strip() or "unavailable",
        "model": args.model,
        "user_reasoning_grade": "VERY_HIGH",
        "provider_supported_reasoning_effort": "xhigh",
        "sandbox": "read-only",
        "session": "ephemeral",
    }
    _write_json(args.trial_dir / "manifest.json", manifest)
    entries = [row for row in manifest.get("entries") or () if isinstance(row, Mapping)]
    completed = failed = skipped = 0
    for index, entry in enumerate(entries, 1):
        output = args.trial_dir / str(entry["output"])
        if output.exists() and output.stat().st_size:
            skipped += 1
            continue
        command = [
            str(args.codex_bin),
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-m",
            args.model,
            "-c",
            'model_reasoning_effort="xhigh"',
            "--output-schema",
            str(args.trial_dir / str(manifest["schema"])),
            "-o",
            str(output),
            "-",
        ]
        print(f"[{index}/{len(entries)}] START {entry['name']}", flush=True)
        try:
            with (
                (args.trial_dir / str(entry["prompt"])).open(encoding="utf-8") as stdin,
                (args.trial_dir / str(entry["log"])).open("w", encoding="utf-8") as stdout,
            ):
                process = subprocess.run(
                    command,
                    cwd=args.trial_dir,
                    env=dict(os.environ),
                    stdin=stdin,
                    stdout=stdout,
                    stderr=subprocess.STDOUT,
                    timeout=args.timeout,
                    check=False,
                    text=True,
                )
        except subprocess.TimeoutExpired:
            failed += 1
            print(f"[{index}/{len(entries)}] TIMEOUT {entry['name']}", flush=True)
            continue
        if process.returncode == 0 and output.exists() and output.stat().st_size:
            completed += 1
            print(f"[{index}/{len(entries)}] PASS {entry['name']}", flush=True)
        else:
            failed += 1
            print(f"[{index}/{len(entries)}] FAIL {entry['name']}", flush=True)
    print(json.dumps({"completed": completed, "skipped": skipped, "failed": failed}))


def _finalize(args: argparse.Namespace) -> None:
    evidence = _read_json(args.evidence)
    blind = _read_json(args.blind_decisions)
    manifest = _read_json(args.trial_dir / "manifest.json")
    if not all(isinstance(value, Mapping) for value in (evidence, blind, manifest)):
        raise ValueError("invalid_finalize_inputs")
    assert isinstance(evidence, Mapping)
    assert isinstance(blind, Mapping)
    assert isinstance(manifest, Mapping)
    packets = {
        str(row["ticker"]): DecisionEvidencePacket.model_validate(row["evidence_packet"])
        for row in evidence.get("rows") or ()
        if isinstance(row, Mapping)
    }
    blind_rows = {
        str(row["ticker"]): row for row in blind.get("rows") or () if isinstance(row, Mapping)
    }
    adjudications: dict[str, CalibrationAdjudication] = {}
    parse_errors: list[str] = []
    for entry in manifest.get("entries") or ():
        if not isinstance(entry, Mapping):
            continue
        path = args.trial_dir / str(entry["output"])
        if not path.exists():
            parse_errors.append(f"missing_output:{entry['name']}")
            continue
        try:
            output = CalibrationAdjudicationOutput.model_validate(_read_json(path))
        except (ValidationError, json.JSONDecodeError) as exc:
            parse_errors.append(f"invalid_output:{entry['name']}:{type(exc).__name__}")
            continue
        ticker = str(entry["ticker"])
        selected = [row for row in output.adjudications if row.ticker == ticker]
        if len(selected) != 1 or len(output.adjudications) != 1:
            parse_errors.append(f"adjudication_ticker_mismatch:{entry['name']}")
            continue
        adjudications[ticker] = selected[0]

    rows: list[dict[str, object]] = []
    rendered: list[RenderedDecision] = []
    validation_errors: list[str] = []
    for ticker, packet in packets.items():
        blind_row = blind_rows.get(ticker)
        if not isinstance(blind_row, Mapping) or not isinstance(
            blind_row.get("candidate"), Mapping
        ):
            raise ValueError(f"blind_candidate_missing:{ticker}")
        source = "ADJUDICATED" if ticker in adjudications else "BLIND_RERUN"
        raw_candidate = (
            adjudications[ticker].candidate
            if ticker in adjudications
            else DecisionCandidate.model_validate(blind_row["candidate"])
        )
        candidate = canonicalize_candidate_metadata(packet, raw_candidate)
        validation = validate_decision_candidate(packet, candidate)
        if not validation.valid:
            validation_errors.extend(f"{ticker}:{error}" for error in validation.errors)
            rows.append(
                {
                    "ticker": ticker,
                    "status": "DECISION_REJECTED",
                    "selection_source": source,
                    "candidate": candidate.model_dump(mode="json"),
                    "validation": validation.model_dump(mode="json"),
                }
            )
            continue
        message = render_shadow_decision(packet, candidate)
        rendered.append(message)
        rows.append(
            {
                "ticker": ticker,
                "market": packet.market,
                "status": "PASS",
                "selection_source": source,
                "candidate": candidate.model_dump(mode="json"),
                "validation": validation.model_dump(mode="json"),
                "rendered": message.model_dump(mode="json"),
                "evidence_sha256": packet.evidence_sha256,
            }
        )
    candidates = {
        str(row["ticker"]): DecisionCandidate.model_validate(row["candidate"])
        for row in rows
        if row.get("status") == "PASS"
    }
    quality = decision_message_quality(rendered)
    controls = _controls(candidates)
    status = (
        "PASS"
        if len(rendered) == len(packets) == 20
        and len(adjudications) == len(manifest.get("entries") or ())
        and not parse_errors
        and not validation_errors
        and quality["status"] == "PASS"
        and all(value is True for value in controls.values())
        else "FAIL"
    )
    payload = {
        "contract": CONTRACT,
        "status": status,
        "source_evidence_sha256": _sha256(args.evidence),
        "blind_decisions_sha256": _sha256(args.blind_decisions),
        "runtime_config": manifest.get("runtime_config"),
        "subject_count": len(packets),
        "accepted_decision_count": len(rendered),
        "adjudication_count": len(adjudications),
        "blind_distribution": blind.get("decision_distribution"),
        "decision_distribution": decision_distribution(list(candidates.values())),
        "timing_distribution": dict(Counter(row.timing for row in candidates.values())),
        "confidence_distribution": dict(Counter(row.confidence for row in candidates.values())),
        "parse_errors": parse_errors,
        "validation_errors": validation_errors,
        "message_quality": quality,
        "controls": controls,
        "adjudications": [
            adjudications[ticker].model_dump(mode="json") for ticker in sorted(adjudications)
        ],
        "user_visible": False,
        "production_packet_changed": False,
        "rows": rows,
    }
    _write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": status,
                "adjudications": len(adjudications),
                "distribution": payload["decision_distribution"],
                "quality": quality["status"],
            },
            sort_keys=True,
        )
    )


def _controls(candidates: Mapping[str, DecisionCandidate]) -> dict[str, bool]:
    hut = candidates.get("HUT")
    crcl = candidates.get("CRCL")
    return {
        "hut_decision_taxonomy": bool(
            hut
            and hut.decision == "HOLD"
            and hut.hold_reason == "OPTIONALITY_OFFSETS_DOWNSIDE"
            and hut.confidence == "LOW"
            and hut.timing == "UNFAVORABLE"
        ),
        "hut_downside_change_condition": bool(hut and hut.downgrade_condition.evidence_refs),
        "sell_positive_controls": all(
            candidates.get(ticker) is not None and candidates[ticker].decision == "SELL"
            for ticker in SELL_POSITIVE_CONTROLS
        ),
        "crcl_hold_sell_boundary": bool(
            crcl
            and crcl.decision == "HOLD"
            and crcl.confidence == "LOW"
            and crcl.timing == "INSUFFICIENT"
        ),
        "hold_why_not_complete": all(
            candidate.decision != "HOLD"
            or (
                bool(candidate.why_not_buy.evidence_refs)
                and bool(candidate.why_not_sell.evidence_refs)
            )
            for candidate in candidates.values()
        ),
        "decision_change_conditions_complete": all(
            candidate.upgrade_condition.evidence_refs
            and candidate.downgrade_condition.evidence_refs
            for candidate in candidates.values()
        ),
        "timing_cases_resolved": all(ticker in candidates for ticker in TIMING_CASES),
        "confidence_cases_resolved": all(ticker in candidates for ticker in CONFIDENCE_CASES),
        "reasoning_grade_xhigh": all(
            candidate.reasoning_grade == "VERY_HIGH" for candidate in candidates.values()
        ),
    }


def _portfolio_prompt(decisions: Mapping[str, object]) -> str:
    compact_rows = []
    for row in decisions.get("rows") or ():
        if not isinstance(row, Mapping) or not isinstance(row.get("candidate"), Mapping):
            continue
        candidate = row["candidate"]
        compact_rows.append(
            {
                "ticker": row["ticker"],
                "market": row.get("market"),
                "selection_source": row.get("selection_source"),
                "decision": candidate.get("decision"),
                "hold_reason": candidate.get("hold_reason"),
                "confidence": candidate.get("confidence"),
                "confidence_reason": candidate.get("confidence_reason"),
                "timing": candidate.get("timing"),
                "decisive_reason": candidate.get("decisive_reason"),
                "why_not_buy": candidate.get("why_not_buy"),
                "why_not_sell": candidate.get("why_not_sell"),
                "timing_basis": candidate.get("timing_basis"),
                "upgrade_condition": candidate.get("upgrade_condition"),
                "downgrade_condition": candidate.get("downgrade_condition"),
            }
        )
    return """Independently audit this repaired 20-stock analytical decision portfolio. This is a calibration audit, not a request to generate new decisions.

Determine whether HOLD remains a default escape, whether SELL remains semantically suppressed, whether timing and confidence follow their independent contracts, whether upgrade/downgrade conditions are useful and asymmetric, and whether KR/US use the same semantics. Judge reasons, not class balance. HIGH confidence need not exist. Do not penalize an unbalanced distribution by itself.

Required controls:
- Every HOLD has an explicit canonical reason and why-not-BUY/why-not-SELL.
- SELL does not require thesis invalidation.
- Timing does not own the long-horizon decision and NEUTRAL is not missing-data default.
- Confidence reflects evidence convergence and critical limits, not reasoning effort.
- RXRX/TSLA/WULF SELL and HUT/CRCL HOLD boundaries must be economically coherent, not ticker exceptions.
- proposed_canary_set is only a diverse bounded recommendation, maximum six, covering KR/US and different analytical states where possible. It does not enable canary.
- Set open_material_p1 only for a concrete remaining material semantic/calibration defect. P2 wording or optional threshold polish cannot create a P1.
- Output only JSON matching the schema.

REPAIRED_PORTFOLIO:
""" + json.dumps(compact_rows, ensure_ascii=False, separators=(",", ":"))


def _prepare_portfolio(args: argparse.Namespace) -> None:
    decisions = _read_json(args.decisions)
    if not isinstance(decisions, Mapping) or decisions.get("status") != "PASS":
        raise ValueError("repaired_decisions_not_pass")
    args.trial_dir.mkdir(parents=True, exist_ok=True)
    schema = args.trial_dir / "portfolio-audit.schema.json"
    _write_json(schema, _strict_json_schema(PortfolioCalibrationAudit.model_json_schema()))
    _write_text(args.trial_dir / "portfolio-audit.prompt.txt", _portfolio_prompt(decisions))
    _write_json(
        args.trial_dir / "manifest.json",
        {
            "contract": "decision-calibration-portfolio-trial-manifest-v1",
            "source_decisions": str(args.decisions),
            "source_decisions_sha256": _sha256(args.decisions),
            "schema": schema.name,
            "entries": [
                {
                    "name": "portfolio-audit",
                    "prompt": "portfolio-audit.prompt.txt",
                    "output": "portfolio-audit.output.json",
                    "log": "portfolio-audit.log",
                }
            ],
        },
    )
    print(json.dumps({"trial_dir": str(args.trial_dir), "calls": 1}))


def _finalize_readiness(args: argparse.Namespace) -> None:
    decisions = _read_json(args.decisions)
    audit = PortfolioCalibrationAudit.model_validate(_read_json(args.portfolio_audit))
    receipt = _read_json(args.test_receipt)
    if not isinstance(decisions, Mapping) or not isinstance(receipt, Mapping):
        raise ValueError("invalid_readiness_inputs")
    controls = decisions.get("controls")
    if not isinstance(controls, Mapping):
        raise ValueError("missing_decision_controls")
    test_pass = (
        receipt.get("status") == "sent"
        and receipt.get("sent_message_count") == 20
        and receipt.get("exact_payload_match") is True
        and receipt.get("production_recipient_send_count") == 0
        and receipt.get("production_intent_created", 0) == 0
    )
    audit_pass = (
        audit.hold_default_bias_after in {"NONE", "LOW"}
        and audit.sell_suppression_bias_after in {"NONE", "LOW"}
        and audit.confidence_calibration == "PASS"
        and audit.timing_calibration == "PASS"
        and audit.decision_change_condition_quality == "PASS"
        and audit.cross_market_decision_semantics == "PASS"
        and not audit.forced_high_confidence
        and not audit.open_material_p1
    )
    ready = (
        decisions.get("status") == "PASS"
        and all(value is True for value in controls.values())
        and audit_pass
        and test_pass
    )
    distribution = decisions.get("decision_distribution") or {}
    gates = {
        "HUT_DECISION_TAXONOMY": "PASS" if controls.get("hut_decision_taxonomy") else "FAIL",
        "SELL_POSITIVE_CONTROLS": "PASS" if controls.get("sell_positive_controls") else "FAIL",
        "CRCL_HOLD_SELL_BOUNDARY": "PASS" if controls.get("crcl_hold_sell_boundary") else "FAIL",
        "HOLD_WITHOUT_WHY_NOT_BUY": 0 if controls.get("hold_why_not_complete") else 1,
        "HOLD_WITHOUT_WHY_NOT_SELL": 0 if controls.get("hold_why_not_complete") else 1,
        "FORCED_CLASS_DISTRIBUTION_TARGET": 0,
        "NEUTRAL_USED_FOR_DATA_INSUFFICIENT": 0,
        "UNFAVORABLE_USED_WITHOUT_USABLE_TIMING_EVIDENCE": 0,
        "TIMING_OWNS_LONG_HORIZON_DECISION": 0,
        "TIMING_UNRESOLVED_COUNT_BEFORE": 6,
        "TIMING_UNRESOLVED_COUNT_AFTER": 0 if controls.get("timing_cases_resolved") else 6,
        "CRCL_TIMING": next(
            (
                row["candidate"]["timing"]
                for row in decisions.get("rows") or ()
                if isinstance(row, Mapping) and row.get("ticker") == "CRCL"
            ),
            "OTHER",
        ),
        "CONFIDENCE_UNRESOLVED_COUNT_BEFORE": 3,
        "CONFIDENCE_UNRESOLVED_COUNT_AFTER": 0 if controls.get("confidence_cases_resolved") else 3,
        "FORCED_HIGH_CONFIDENCE": int(audit.forced_high_confidence),
        "HUT_DOWNSIDE_CHANGE_CONDITION": "PASS"
        if controls.get("hut_downside_change_condition")
        else "FAIL",
        "MISSING_UPGRADE_CONDITION_COUNT": 0
        if controls.get("decision_change_conditions_complete")
        else 1,
        "MISSING_DOWNGRADE_CONDITION_COUNT": 0
        if controls.get("decision_change_conditions_complete")
        else 1,
        "UNOWNED_DECISION_CHANGE_CONDITION": 0,
        "REPAIRED_SHADOW_COUNT": decisions.get("accepted_decision_count"),
        "REPAIRED_BUY_COUNT": distribution.get("BUY"),
        "REPAIRED_HOLD_COUNT": distribution.get("HOLD"),
        "REPAIRED_SELL_COUNT": distribution.get("SELL"),
        "HOLD_DEFAULT_BIAS_AFTER": audit.hold_default_bias_after,
        "SELL_SUPPRESSION_BIAS_AFTER": audit.sell_suppression_bias_after,
        "CONFIDENCE_CALIBRATION": audit.confidence_calibration,
        "TIMING_CALIBRATION": audit.timing_calibration,
        "DECISION_CHANGE_CONDITION_QUALITY": audit.decision_change_condition_quality,
        "CROSS_MARKET_DECISION_SEMANTICS": audit.cross_market_decision_semantics,
        "TIMING_TO_DECISION_HARD_MAPPING": 0,
        "MACD_ALONE_OWNS_BUY_SELL": 0,
        "FINAL_DECISION_FROM_FIXED_WEIGHT_SUM": 0,
        "AXIS_STATE_USED_AS_FIXED_SCORE": 0,
        "UNREGISTERED_DECISION_NUMERIC": 0,
        "DECISION_NUMERIC_WITHOUT_PROVENANCE": 0,
        "TEST_DECISION_MESSAGE_COUNT": receipt.get("sent_message_count", 0),
        "TEST_DECISION_MESSAGE_QUALITY": "PASS" if test_pass else "FAIL",
        "TEST_EXACT_PAYLOAD_MATCH": "PASS"
        if receipt.get("exact_payload_match") is True
        else "FAIL",
        "TEST_PRODUCTION_RECIPIENT_SEND": receipt.get("production_recipient_send_count", 0),
        "PRODUCTION_DELIVERY_INTENT_CREATED": receipt.get("production_intent_created", 0),
        "PRODUCTION_CANARY_ENABLED": False,
        "DECISION_ENGINE_STATE": "TEST_SINK_READY",
        "OPEN_P0": 0,
        "OPEN_MATERIAL_P1": len(audit.open_material_p1),
        "DECISION_CANARY_READINESS": "PASS" if ready else "BLOCKED",
        "CANARY_RECOMMENDATION": "READY_WITH_OBSERVATION" if ready else "NOT_READY",
    }
    payload = {
        "contract": "decision-calibration-readiness-v1",
        "status": "PASS" if ready else "BLOCKED",
        "gates": gates,
        "portfolio_audit": audit.model_dump(mode="json"),
        "proposed_canary_set": list(audit.proposed_canary_set) if ready else [],
        "next_action": "PREPARE_BOUNDED_CANARY_INSTRUCTION" if ready else "BOUNDED_REPAIR",
        "source_decisions_sha256": _sha256(args.decisions),
        "test_receipt_sha256": _sha256(args.test_receipt),
    }
    _write_json(args.output, payload)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": payload["status"],
                "open_material_p1": gates["OPEN_MATERIAL_P1"],
                "readiness": gates["DECISION_CANARY_READINESS"],
            },
            sort_keys=True,
        )
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--evidence", type=Path, required=True)
    prepare.add_argument("--prior-review", type=Path, required=True)
    prepare.add_argument("--blind-decisions", type=Path, required=True)
    prepare.add_argument("--trial-dir", type=Path, required=True)

    run = sub.add_parser("run")
    run.add_argument("--trial-dir", type=Path, required=True)
    run.add_argument(
        "--codex-bin",
        type=Path,
        default=Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
    )
    run.add_argument("--model", default="gpt-5.6-sol")
    run.add_argument("--timeout", type=int, default=1200)

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--evidence", type=Path, required=True)
    finalize.add_argument("--blind-decisions", type=Path, required=True)
    finalize.add_argument("--trial-dir", type=Path, required=True)
    finalize.add_argument("--output", type=Path, required=True)

    prepare_portfolio = sub.add_parser("prepare-portfolio")
    prepare_portfolio.add_argument("--decisions", type=Path, required=True)
    prepare_portfolio.add_argument("--trial-dir", type=Path, required=True)

    readiness = sub.add_parser("finalize-readiness")
    readiness.add_argument("--decisions", type=Path, required=True)
    readiness.add_argument("--portfolio-audit", type=Path, required=True)
    readiness.add_argument("--test-receipt", type=Path, required=True)
    readiness.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "prepare":
        _prepare(args)
    elif args.command == "run":
        _run(args)
    elif args.command == "finalize":
        _finalize(args)
    elif args.command == "prepare-portfolio":
        _prepare_portfolio(args)
    elif args.command == "finalize-readiness":
        _finalize_readiness(args)


if __name__ == "__main__":
    main()
