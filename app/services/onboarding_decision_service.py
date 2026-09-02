from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from app.config import get_settings
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.accepted_decision_v2_runtime_service import (
    REASONING_EFFORT,
    REASONING_MODEL,
    AcceptedV2ProductionBatchOutput,
    accepted_v2_production_prompt,
    accepted_v2_production_repair_prompt,
    build_accepted_v2_production_context,
)
from app.services.accepted_decision_v2_service import (
    AcceptedDecisionStatus,
    resolve_accepted_v2_decision,
    validate_accepted_v2_decision,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.codex_runtime_state_service import prepare_codex_runtime_state
from app.services.decision_canary_service import strict_json_schema
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_matches_decision,
)
from app.services.preconfirmation_decision_v2_service import (
    validate_preconfirmation_candidate,
)


ONBOARDING_DECISION_CONTRACT = "onboarding-accepted-decision-v1"


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _canonical_sha(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _stable_ref(ticker: str, category: EvidenceCategory, label: str, value: object) -> str:
    digest = _canonical_sha([ticker, category, label, value])[:20]
    return f"onboarding:{ticker}:{category}:{digest}"


def _compact(value: object, limit: int = 900) -> str:
    text = (
        value.strip()
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    )
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _evidence_ref(
    *,
    ticker: str,
    category: EvidenceCategory,
    label: str,
    value: object,
    as_of: str,
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=_stable_ref(ticker, category, label, value),
        category=category,
        label=label,
        statement=_compact(value),
        as_of=as_of,
        source_ref=f"onboarding_initial_evidence.{label}",
    )


def build_onboarding_decision_evidence_packet(
    session: Session,
    item: WatchlistItem,
    evidence: Mapping[str, object],
) -> DecisionEvidencePacket:
    thesis = session.exec(
        select(InvestmentThesis)
        .where(
            InvestmentThesis.ticker == item.ticker,
            InvestmentThesis.status == "active",
        )
        .order_by(InvestmentThesis.version.desc())
    ).first()
    if thesis is None:
        raise ValueError("investment_logic_missing")
    as_of = str(evidence.get("as_of") or "")[:10]
    if not as_of:
        raise ValueError("initial_evidence_as_of_missing")
    values = (
        (EvidenceCategory.THESIS, "current_thesis", evidence.get("current_thesis")),
        (
            EvidenceCategory.EARNINGS,
            "latest_safe_earnings_checkpoint",
            evidence.get("latest_safe_earnings_checkpoint"),
        ),
        (
            EvidenceCategory.EXPECTATIONS,
            "market_expectations",
            evidence.get("market_expectations"),
        ),
        (EvidenceCategory.CATALYSTS, "relevant_events", evidence.get("relevant_events")),
        (EvidenceCategory.VALUATION, "valuation_context", evidence.get("valuation_context")),
        (EvidenceCategory.PRICE_STRUCTURE, "price_structure", evidence.get("price_structure")),
        (
            EvidenceCategory.MARKET,
            "material_market_context",
            evidence.get("material_market_context"),
        ),
        (EvidenceCategory.UNKNOWN, "material_unknowns", evidence.get("material_unknowns")),
    )
    refs = tuple(
        _evidence_ref(
            ticker=item.ticker,
            category=category,
            label=label,
            value=value,
            as_of=as_of,
        )
        for category, label, value in values
        if value not in (None, "", [], {})
    )
    if len(refs) < 3:
        raise ValueError("onboarding_decision_evidence_insufficient")
    payload = [row.model_dump(mode="json") for row in refs]
    source_fingerprint = str(evidence.get("fingerprint") or "")
    packet_id = f"onboarding-{item.ticker}-{source_fingerprint.rsplit(':', 1)[-1][:16]}"
    cautions: list[str] = []
    earnings = evidence.get("latest_safe_earnings_checkpoint")
    if isinstance(earnings, Mapping) and earnings.get("status") != "AVAILABLE":
        cautions.append("safe_financial_checkpoint_unavailable")
    return DecisionEvidencePacket(
        packet_id=packet_id,
        ticker=item.ticker,
        company_name=item.company_name,
        market="kr" if item.ticker.isdigit() else "us",
        assessment_date=as_of,
        horizon=thesis.time_horizon or "6-24개월",
        evidence=refs,
        prohibited_claims=(
            "automated_trade_or_order",
            "fixed_weight_score_decision",
            "unsupported_numeric_calculation",
            "valuation_from_technical_indicator",
            "future_evidence_or_lookahead",
        ),
        data_quality_cautions=tuple(cautions),
        evidence_sha256=_canonical_sha(payload),
    )


def _signed_in_codex_bin() -> str:
    candidates = (
        os.environ.get("CODEX_CLI_BIN"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
        shutil.which("codex"),
        "/Users/sskim/Applications/Codex.app/Contents/Resources/codex",
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise ValueError("signed_in_codex_cli_missing")


def _invoke_signed_in_codex(
    *,
    prompt: Path,
    output: Path,
    log: Path,
    schema: Path,
    timeout: int,
    state_namespace: str,
) -> None:
    prompt = prompt.resolve()
    output = output.resolve()
    log = log.resolve()
    schema = schema.resolve()
    runtime_state = prepare_codex_runtime_state(
        Path(get_settings().data_dir).resolve() / "codex_runtime_state" / "onboarding",
        namespace=state_namespace,
    )
    command = [
        _signed_in_codex_bin(),
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "-m",
        REASONING_MODEL,
        "-c",
        f'model_reasoning_effort="{REASONING_EFFORT}"',
        "--output-schema",
        str(schema),
        "-o",
        str(output),
        "-",
    ]
    with prompt.open(encoding="utf-8") as stdin, log.open("w", encoding="utf-8") as stdout:
        process = subprocess.run(
            command,
            cwd=prompt.parent,
            env=runtime_state.environment(),
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            text=True,
        )
    if process.returncode != 0 or not output.exists() or not output.stat().st_size:
        raise ValueError("signed_in_codex_cli_onboarding_decision_failed")


def generate_onboarding_accepted_decision(
    session: Session,
    item: WatchlistItem,
    evidence: Mapping[str, object],
    *,
    timeout: int,
    data_dir: str | Path | None = None,
) -> dict[str, object]:
    packet = build_onboarding_decision_evidence_packet(session, item, evidence)
    claim_id = f"onboarding-{packet.evidence_sha256[:20]}"
    packet_shell = {
        "packet_id": packet.packet_id,
        "market": packet.market,
        "assessment_date": packet.assessment_date,
        "stocks": [{"ticker": item.ticker}],
    }
    context = build_accepted_v2_production_context(
        packet=packet_shell,
        claim_id=claim_id,
        evidence_packets=(packet,),
    )
    root = Path(data_dir or get_settings().data_dir) / "onboarding" / item.ticker
    paths = {
        "context": root / f"{claim_id}.context.json",
        "schema": root / f"{claim_id}.schema.json",
        "prompt": root / f"{claim_id}.prompt.txt",
        "output": root / f"{claim_id}.output.json",
        "log": root / f"{claim_id}.cli.log",
        "repair_prompt": root / f"{claim_id}.repair.prompt.txt",
        "repair_output": root / f"{claim_id}.repair.output.json",
        "repair_log": root / f"{claim_id}.repair.cli.log",
        "accepted": root / f"{claim_id}.accepted.json",
    }
    _atomic_json(paths["context"], context.model_dump(mode="json"))
    _atomic_json(
        paths["schema"],
        strict_json_schema(AcceptedV2ProductionBatchOutput.model_json_schema()),
    )
    _atomic_text(paths["prompt"], accepted_v2_production_prompt(context))
    _invoke_signed_in_codex(
        prompt=paths["prompt"],
        output=paths["output"],
        log=paths["log"],
        schema=paths["schema"],
        timeout=timeout,
        state_namespace=claim_id,
    )
    output = AcceptedV2ProductionBatchOutput.model_validate_json(
        paths["output"].read_text(encoding="utf-8")
    )
    if (
        output.packet_id != packet.packet_id
        or output.claim_id != claim_id
        or output.market != packet.market
        or output.assessment_date != packet.assessment_date
        or len(output.candidates) != 1
        or output.candidates[0].ticker != item.ticker
    ):
        raise ValueError("onboarding_decision_output_identity_mismatch")
    candidate = output.candidates[0]
    validation = validate_preconfirmation_candidate(packet, candidate)
    adjudications = {row.ticker: row for row in output.adjudications}
    if not validation.valid:
        _atomic_text(
            paths["repair_prompt"],
            accepted_v2_production_repair_prompt(
                context,
                ticker=item.ticker,
                rejected_candidate=candidate,
                validation_errors=tuple(dict.fromkeys(validation.errors)),
            ),
        )
        _invoke_signed_in_codex(
            prompt=paths["repair_prompt"],
            output=paths["repair_output"],
            log=paths["repair_log"],
            schema=paths["schema"],
            timeout=timeout,
            state_namespace=claim_id,
        )
        repaired = AcceptedV2ProductionBatchOutput.model_validate_json(
            paths["repair_output"].read_text(encoding="utf-8")
        )
        if len(repaired.candidates) != 1 or repaired.candidates[0].ticker != item.ticker:
            raise ValueError("onboarding_decision_repair_identity_mismatch")
        candidate = repaired.candidates[0]
        validation = validate_preconfirmation_candidate(packet, candidate)
        adjudications = {row.ticker: row for row in repaired.adjudications}
    if not validation.valid:
        raise ValueError("onboarding_decision_validation_failed:" + ",".join(validation.errors))
    prior = next((row for row in context.prior_accepted if row.ticker == item.ticker), None)
    material_disagreement = bool(
        prior is not None and candidate.decision != prior.accepted_decision
    )
    adjudication = adjudications.get(item.ticker)
    plan = resolve_accepted_v2_decision(
        packet,
        candidate,
        v1_decision=prior.accepted_decision if prior else candidate.decision,
        material_disagreement=material_disagreement,
        adjudication=adjudication,
    )
    accepted_validation = validate_accepted_v2_decision(packet, plan)
    if plan.status != AcceptedDecisionStatus.READY or not accepted_validation.valid:
        raise ValueError(
            "onboarding_accepted_decision_not_ready:" + ",".join(accepted_validation.errors)
        )
    result = {
        "contract": ONBOARDING_DECISION_CONTRACT,
        "status": "READY",
        "ticker": item.ticker,
        "source_initial_evidence_fingerprint": evidence.get("fingerprint"),
        "decision_evidence_sha256": packet.evidence_sha256,
        "accepted_decision": plan.accepted_decision,
        "accepted_decision_id": plan.accepted_decision_id,
        "accepted_evidence_fingerprint": plan.accepted_evidence_fingerprint,
        "accepted_source": plan.accepted_source,
        "accepted_as_of": plan.accepted_as_of,
        "accepted_directional_balance": (
            plan.accepted_directional_balance.model_dump(mode="json")
            if plan.accepted_directional_balance is not None
            else None
        ),
        "accepted_buy_drivers": [
            claim.model_dump(mode="json") for claim in plan.accepted_buy_drivers
        ],
        "accepted_sell_drivers": [
            claim.model_dump(mode="json") for claim in plan.accepted_sell_drivers
        ],
        "candidate_validation": validation.model_dump(mode="json"),
        "accepted_validation": accepted_validation.model_dump(mode="json"),
        "accepted_plan": plan.model_dump(mode="json"),
        "raw_candidate_grants_ready": False,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    _atomic_json(paths["accepted"], result)
    return result


def validate_onboarding_decision_readiness(
    payload: Mapping[str, object],
    *,
    ticker: str,
    initial_evidence_fingerprint: str,
) -> tuple[bool, str | None]:
    if payload.get("contract") != ONBOARDING_DECISION_CONTRACT:
        return False, "accepted_decision_contract_missing"
    if payload.get("status") != "READY" or payload.get("ticker") != ticker:
        return False, "accepted_decision_not_ready"
    if payload.get("source_initial_evidence_fingerprint") != initial_evidence_fingerprint:
        return False, "accepted_decision_evidence_mismatch"
    if payload.get("accepted_decision") not in {"BUY", "HOLD", "SELL"}:
        return False, "accepted_decision_value_missing"
    if not payload.get("accepted_decision_id") or not payload.get("accepted_evidence_fingerprint"):
        return False, "accepted_decision_lineage_missing"
    if payload.get("raw_candidate_grants_ready") is not False:
        return False, "raw_candidate_grants_ready"
    balance = payload.get("accepted_directional_balance")
    if balance is not None:
        if not isinstance(balance, Mapping):
            return False, "accepted_directional_balance_invalid"
        try:
            parsed_balance = DirectionalBalance.model_validate(balance)
        except (TypeError, ValueError):
            return False, "accepted_directional_balance_invalid"
        if not directional_balance_matches_decision(parsed_balance, payload["accepted_decision"]):
            return False, "accepted_decision_balance_mismatch"
    return True, None
