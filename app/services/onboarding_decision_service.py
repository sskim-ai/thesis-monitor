from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import traceback
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
    AcceptedV2FundamentalCoreBatch,
    accepted_v2_fundamental_core_prompt,
    accepted_v2_fundamental_core_output_schema,
    accepted_v2_fundamental_core_ref_catalog_manifest,
    accepted_v2_production_prompt,
    accepted_v2_production_repair_prompt,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
    build_accepted_v2_production_context,
    materialize_accepted_v2_stage2_output,
    validate_accepted_v2_candidate_ownership,
    validate_accepted_v2_fundamental_core,
    validate_accepted_v2_fundamental_core_batch_scope,
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
from app.services.directional_balance_service import (
    DirectionalBalance,
    directional_balance_matches_decision,
)
from app.services.directional_balance_variance_service import (
    requires_directional_balance_adjudication,
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
    if evidence.get('dated_reference_price') is not None:
        from app.services.dated_chart_reference import validate_reference
        reference = validate_reference(evidence['dated_reference_price'],evidence.get('dated_reference_evidence'),
            ticker=item.ticker,market=str(evidence.get('market')),as_of=evidence.get('as_of'))
        # The raw proof remains local/DB-only, never in the model prompt.
        values += ((EvidenceCategory.PRICE_STRUCTURE,'dated_reference_price',dict(
            value=reference['value'],currency=reference['currency'],reference_date=reference['reference_date'],
            adjustment_basis=reference['adjustment_basis'],role=reference['role'],
            allowed_use=reference['allowed_use'],current_price=False,valuation_denominator=False)),)
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
    execution_profile=None,
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
    if execution_profile is not None:
        from app.services.production_model_profile import sol_high
        from app.services.official_codex_shadow_transport_service import command_prefix
        profile = sol_high(execution_profile)
        if timeout != profile.timeout_seconds:
            raise ValueError('onboarding_campaign_timeout_profile_mismatch')
        command = [_signed_in_codex_bin(), *command_prefix(profile),
            '--output-schema', str(schema), '-o', str(output), '-']
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


def _generate_onboarding_accepted_decision(
    session: Session,
    item: WatchlistItem,
    evidence: Mapping[str, object],
    *,
    timeout: int,
    data_dir: str | Path | None = None,
    campaign_execution=None,
) -> dict[str, object]:
    def invoke(stage, **kwargs):
        if campaign_execution is not None:
            return campaign_execution.invoke(stage=stage, **kwargs)
        return _invoke_signed_in_codex(**kwargs)

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
        "core_schema": root / f"{claim_id}.core.schema.json",
        "core_prompt": root / f"{claim_id}.core.prompt.txt",
        "core_output": root / f"{claim_id}.core.output.json",
        "core_log": root / f"{claim_id}.core.cli.log",
        "core_ref_catalog": root / f"{claim_id}.core.ref-catalog.json",
        "schema": root / f"{claim_id}.schema.json",
        "ref_catalog": root / f"{claim_id}.ref-catalog.json",
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
        paths["core_schema"],
        accepted_v2_fundamental_core_output_schema(context),
    )
    _atomic_json(
        paths["core_ref_catalog"],
        accepted_v2_fundamental_core_ref_catalog_manifest(context),
    )
    _atomic_text(paths["core_prompt"], accepted_v2_fundamental_core_prompt(context))
    invoke('CORE',
        prompt=paths["core_prompt"],
        output=paths["core_output"],
        log=paths["core_log"],
        schema=paths["core_schema"],
        timeout=timeout,
        state_namespace=claim_id,
    )
    core_output = AcceptedV2FundamentalCoreBatch.model_validate_json(
        paths["core_output"].read_text(encoding="utf-8")
    )
    if validate_accepted_v2_fundamental_core_batch_scope(
        core_output,
        context,
        subjects=(item.ticker,),
    ):
        raise ValueError("onboarding_fundamental_core_identity_mismatch")
    core = core_output.cores[0]
    ownership = context.evidence_ownership[0]
    core_errors = validate_accepted_v2_fundamental_core(core, ownership)
    if core_errors:
        raise ValueError(
            "onboarding_fundamental_core_invalid:" + ",".join(core_errors)
        )
    if campaign_execution is not None:
        campaign_execution.accept(paths['core_output'])
    _atomic_json(
        paths["schema"],
        accepted_v2_stage2_output_schema(context, fundamental_cores=(core,)),
    )
    _atomic_json(
        paths["ref_catalog"],
        accepted_v2_stage2_ref_catalog_manifest(
            context,
            fundamental_cores=(core,),
        ),
    )
    _atomic_text(
        paths["prompt"],
        accepted_v2_production_prompt(context, fundamental_cores=(core,)),
    )
    invoke('DECISION',
        prompt=paths["prompt"],
        output=paths["output"],
        log=paths["log"],
        schema=paths["schema"],
        timeout=timeout,
        state_namespace=claim_id,
    )
    output = materialize_accepted_v2_stage2_output(
        context,
        json.loads(paths["output"].read_text(encoding="utf-8")),
        fundamental_cores=(core,),
        subjects=(item.ticker,),
    )
    if (
        output.packet_id != packet.packet_id
        or output.claim_id != claim_id
        or output.market != packet.market
        or output.assessment_date != packet.assessment_date
        or tuple(output.fundamental_cores) != (core,)
        or len(output.candidates) != 1
        or output.candidates[0].ticker != item.ticker
    ):
        raise ValueError("onboarding_decision_output_identity_mismatch")
    candidate = output.candidates[0]
    validation = validate_preconfirmation_candidate(packet, candidate)
    ownership_errors = validate_accepted_v2_candidate_ownership(
        candidate, core, ownership
    )
    adjudications = {row.ticker: row for row in output.adjudications}
    if not validation.valid or ownership_errors:
        if campaign_execution is not None:
            raise ValueError('onboarding_campaign_stage2_rejected_no_repair')
        _atomic_text(
            paths["repair_prompt"],
            accepted_v2_production_repair_prompt(
                context,
                fundamental_core=core,
                ticker=item.ticker,
                rejected_candidate=candidate,
                validation_errors=tuple(
                    dict.fromkeys((*validation.errors, *ownership_errors))
                ),
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
        repaired = materialize_accepted_v2_stage2_output(
            context,
            json.loads(paths["repair_output"].read_text(encoding="utf-8")),
            fundamental_cores=(core,),
            subjects=(item.ticker,),
        )
        if (
            tuple(repaired.fundamental_cores) != (core,)
            or len(repaired.candidates) != 1
            or repaired.candidates[0].ticker != item.ticker
        ):
            raise ValueError("onboarding_decision_repair_identity_mismatch")
        candidate = repaired.candidates[0]
        validation = validate_preconfirmation_candidate(packet, candidate)
        ownership_errors = validate_accepted_v2_candidate_ownership(
            candidate, core, ownership
        )
        adjudications = {row.ticker: row for row in repaired.adjudications}
    if not validation.valid or ownership_errors:
        raise ValueError(
            "onboarding_decision_validation_failed:"
            + ",".join(tuple(dict.fromkeys((*validation.errors, *ownership_errors))))
        )
    prior = next((row for row in context.prior_accepted if row.ticker == item.ticker), None)
    material_disagreement = bool(
        prior is not None
        and requires_directional_balance_adjudication(
            prior_decision=prior.accepted_decision,
            prior_balance=prior.accepted_directional_balance,
            prior_evidence_sha256=prior.evidence_sha256,
            candidate_decision=candidate.decision,
            candidate_balance=candidate.directional_balance,
            current_evidence_sha256=packet.evidence_sha256,
        )
    )
    adjudication = adjudications.get(item.ticker)
    plan = resolve_accepted_v2_decision(
        packet,
        candidate,
        v1_decision=prior.accepted_decision if prior else candidate.decision,
        v1_directional_balance=(prior.accepted_directional_balance if prior else None),
        v1_buy_drivers=(prior.accepted_buy_drivers if prior else ()),
        v1_sell_drivers=(prior.accepted_sell_drivers if prior else ()),
        v1_balance_summary=(prior.accepted_balance_summary if prior else None),
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
    if campaign_execution is not None:
        campaign_execution.accept(paths['output'])
        result['execution_profile'] = campaign_execution.profile.model_request()
        result['automatic_repair_calls'] = 0
        result['campaign_ledger_identity_sha256'] = _canonical_sha(campaign_execution.ledger.identity)
    _atomic_json(paths["accepted"], result)
    return result


class _CampaignOnboardingExecution:
    """Bind the original two stages to the existing campaign journal, not a new owner."""
    def __init__(self, *, ledger, profile, item, timeout, data_dir):
        from app.services.selected_run_lifecycle import SelectedRunLedger
        from app.services.production_model_profile import sol_high
        if not isinstance(ledger, SelectedRunLedger):
            raise ValueError('onboarding_existing_campaign_ledger_required')
        self.profile = sol_high(profile)
        if timeout != self.profile.timeout_seconds:
            raise ValueError('onboarding_campaign_timeout_profile_mismatch')
        self.ledger, self.ticker = ledger, item.ticker
        matches = [m for m,c in ledger.identity['children'].items() if item.ticker in c['subjects']]
        config = ledger.identity.get('onboarding', {})
        if len(matches) != 1 or config.get('profile') != self.profile.contract:
            raise ValueError('onboarding_campaign_subject_or_profile_not_frozen')
        self.market = matches[0]
        self.prefix = f'ONBOARDING:{ledger.identity["children"][self.market]["generation"]}:{item.ticker}:'
        state = ledger.state()
        if (state['pending'] or self.market+':'+self.ticker in state['onboarding_failed']
                or any(key.startswith(self.prefix) for key in state['used'])):
            raise ValueError('onboarding_campaign_already_attempted_no_retry')
        self.pending = None
        self.output = None
        self.root = Path(data_dir or get_settings().data_dir) / 'onboarding' / self.ticker

    def invoke(self, *, stage, **kwargs):
        prompt, schema, output = (Path(kwargs[key]) for key in ('prompt', 'schema', 'output'))
        if prompt.stat().st_size > 384*1024 or output.exists():
            raise ValueError('onboarding_campaign_input_or_existing_output_invalid')
        payload_hash = _canonical_sha(dict(prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
            schema_sha256=hashlib.sha256(schema.read_bytes()).hexdigest(),
            profile=self.profile.model_request(), ticker=self.ticker, stage=stage))
        self.pending = self.ledger.before_onboarding_model(market=self.market, ticker=self.ticker,
            stage=stage, payload_sha256=payload_hash)
        self.output = output
        _invoke_signed_in_codex(**kwargs, execution_profile=self.profile)
        if output.stat().st_size > 128*1024:
            raise ValueError('onboarding_campaign_output_exceeds_128KiB')

    def accept(self, output):
        if self.pending is None or Path(output) != self.output:
            raise ValueError('onboarding_campaign_acceptance_without_pending_output')
        self.ledger.onboarding_model_result(self.pending, ok=True,
            output_sha256=hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.pending = None

    def fail(self, error):
        raw = self.output.read_bytes() if self.output is not None and self.output.is_file() else b''
        if self.pending is not None:
            self.ledger.onboarding_model_result(self.pending, ok=False,
                output_sha256=hashlib.sha256(raw).hexdigest(), error_type=type(error).__name__)
            self.pending = None
        else:
            self.ledger.fail_onboarding_subject(market=self.market, ticker=self.ticker,
                                               error_type=type(error).__name__)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / ('c22ag-failure-'+_canonical_sha(self.ledger.identity)[:20]+'.json')
        frames = traceback.extract_tb(error.__traceback__)
        with path.open('x', encoding='utf-8') as stream:
            json.dump(dict(status='FAILED_NO_RETRY', ticker=self.ticker,
                error_type=type(error).__name__, exception_detail_exported=False,
                failure_function=frames[-1].name if frames else None,
                failure_file=frames[-1].filename if frames else None,
                failure_line=frames[-1].lineno if frames else None,
                raw_output_sha256=hashlib.sha256(raw).hexdigest(), raw_output_bytes=len(raw),
                execution_profile=self.profile.model_request(), automatic_repair_calls=0,
                ready=False), stream, indent=2)


def generate_onboarding_accepted_decision(session, item, evidence, *, timeout,
                                          data_dir=None, execution_profile=None,
                                          campaign_ledger=None):
    """Legacy defaults are unchanged; C22AG opts into Sol/High and no repair."""
    execution = None
    if execution_profile is not None or campaign_ledger is not None:
        execution = _CampaignOnboardingExecution(ledger=campaign_ledger, profile=execution_profile,
            item=item, timeout=timeout, data_dir=data_dir)
    try:
        return _generate_onboarding_accepted_decision(session, item, evidence, timeout=timeout,
            data_dir=data_dir, campaign_execution=execution)
    except BaseException as error:
        if execution is not None:
            execution.fail(error)
            if not isinstance(error, Exception):
                raise
            # Do not propagate Pydantic input values/private Thesis into reconciler logs.
            raise ValueError('onboarding_campaign_rejected_no_retry:'+type(error).__name__) from None
        raise


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
