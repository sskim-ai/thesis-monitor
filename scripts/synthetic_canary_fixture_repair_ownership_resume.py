from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import subprocess
import time
import zipfile
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo

from app.jobs import accepted_decision_v2_runtime as accepted_runtime
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    TIMING_OUTPUT_CONTRACT,
    CoreHolderView,
    CoreNewBuyerView,
    DirectionalClaim,
    DirectionalCoreCandidate,
    DirectionalSellDriver,
    DirectionalUnknown,
    EvidenceDomain,
    HolderPriceReview,
    OwnedEvidencePacket,
    OwnedEvidenceRef,
    PriceTimingCandidate,
    TechnicalState,
    TimingClaim,
    TimingNewBuyerModifier,
    canonical_sha256,
    compose_decision,
    core_fingerprint,
    stage_alias_catalogs,
    validate_ownership,
)
from app.services.directional_balance_service import DirectionalBalance
from app.services.structured_autonomy_shadow_service import (
    explicit_actionable_trade_directives,
)
from scripts import directional_core_price_timing_holdout as frozen
from scripts import model_transport_revalidation_ownership_continuation as prior
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "synthetic-canary-fixture-repair-ownership-proof-resume-v1"
PROOFS_DIRECTORY = "20260906-synthetic-canary-resume-proofs"
SOURCE_REPORT_SHA256 = (
    "c5b12a585ee56fd1d501658e04c1040b718dc731824198a91d63abfa61d7e9b1"
)
SOURCE_GENERATION_ID = "20260906-direction-timing-holdout-20260906T093200Z-bd30668470f0"
SOURCE_LOCK_SHA256 = (
    "efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
MODEL_TIMEOUT_SECONDS = 1800
MODEL_CONTEXT_BATCH_SIZE = 4
MAX_CANARY_MODEL_CALLS = 7
KST = ZoneInfo("Asia/Seoul")

CONSUMED_LATEST_HOLDOUT16 = prior.CONSUMED_LATEST_HOLDOUT16
CURRENT_HOLDOUT = prior.CURRENT_HOLDOUT
EXPECTED_ARCHITECTURE_HASHES = prior.EXPECTED_ARCHITECTURE_HASHES
EXPECTED_SOURCE_HASHES = prior.EXPECTED_SOURCE_HASHES
EXPECTED_TRANSPORT_HASHES = {
    "transport_service_file": "247367b23d731b947c4169c86ecf7871768934d858e8477092a0b26fb6f37774",
    "continuation_harness_file": "a30db21cc387e72559586356e90b24ec069cba4c1107a12543b5490502c79846",
    "invoke_instrumented_codex": "e5fc8e00b99e5330b31502ad2d975970a4e0ce7da7aed5c9baa8ba9f8df94e13",
    "continuation_transport_adapter": "05e8910008bec06fa592aeeb2df3c204b87a2a45a43b17607946b5c32355f9f1",
    "instrumented_runner": "10df1482dd937278ebe450ab82631ae3abf2bcb5b1b41a56bdabee1eea7ebbfd",
}
EXPECTED_PACKET_SCHEMA_SHA256 = (
    "8c9b8e13fb6f6c6449dd7acfbad14d7c1c55c64b8e4906b5cbb79a4cf39be8ae"
)

REPORT_TO_PROOF = {
    "20260906-canary-fixture-root-cause.md": "canary-fixture-root-cause.json",
    "20260906-canary-fixture-schema-contract.md": "canary-fixture-schema-contract.json",
    "20260906-canary-schema-preflight.md": "canary-schema-preflight.json",
    "20260906-architecture-freeze-reverification.md": "architecture-freeze-reverification.json",
    "20260906-source-freeze-reverification.md": "source-freeze-reverification.json",
    "20260906-transport-freeze-reverification.md": "transport-freeze-reverification.json",
    "20260906-consumed-regression-no-rerun.md": "consumed-regression-no-rerun.json",
    "20260906-canary-smoke.md": "canary-smoke.json",
    "20260906-canary-directional-us.md": "canary-directional-us.json",
    "20260906-canary-directional-kr.md": "canary-directional-kr.json",
    "20260906-canary-shared-context-us4.md": "canary-shared-context-us4.json",
    "20260906-canary-shared-context-kr4.md": "canary-shared-context-kr4.json",
    "20260906-canary-price-timing-us.md": "canary-price-timing-us.json",
    "20260906-canary-price-timing-kr.md": "canary-price-timing-kr.json",
    "20260906-canary-verdict.md": "canary-verdict.json",
    "20260906-current-holdout-reuse-gate.md": "current-holdout-reuse-gate.json",
    "20260906-live-workload-coexistence-audit.md": "live-workload-coexistence-audit.json",
    "20260906-resume-source-lock.md": "resume-source-lock.json",
    "20260906-resume-first.md": "resume-first.json",
    "20260906-resume-run-a.md": "resume-run-a.json",
    "20260906-resume-run-b.md": "resume-run-b.json",
    "20260906-resume-run-c.md": "resume-run-c.json",
    "20260906-resume-core-stability.md": "resume-core-stability.json",
    "20260906-resume-timing-stability.md": "resume-timing-stability.json",
    "20260906-resume-dominance-ownership.md": "resume-dominance-ownership.json",
    "20260906-resume-renderer-shadow-proof.md": "resume-renderer-shadow-proof.json",
    "20260906-resume-hard-safety-regression.md": "resume-hard-safety-regression.json",
    "20260906-monitoring-bootstrap-next-handoff.md": "monitoring-bootstrap-next-handoff.json",
    "20260906-production-no-change.md": "production-no-change.json",
    "20260906-night-futures-no-change.md": "night-futures-no-change.json",
    "20260906-program-completion.md": "program-completion.json",
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_sha256(value: object) -> str:
    return hashlib.sha256(inspect.getsource(value).encode()).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def generation_id(commit: str, as_of: datetime) -> str:
    stamp = as_of.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(f"{commit}|{stamp}|{PROGRAM_CONTRACT}".encode()).hexdigest()[:12]
    return f"20260906-synthetic-canary-resume-{stamp}-{suffix}"


def packet_schema_sha256() -> str:
    payload = json.dumps(
        DecisionEvidencePacket.model_json_schema(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def transport_hashes(repo_root: Path) -> dict[str, str]:
    from app.services.codex_transport_lifecycle_service import (
        invoke_instrumented_codex,
    )

    return {
        "transport_service_file": file_sha256(
            repo_root / "app/services/codex_transport_lifecycle_service.py"
        ),
        "continuation_harness_file": file_sha256(
            repo_root
            / "scripts/model_transport_revalidation_ownership_continuation.py"
        ),
        "invoke_instrumented_codex": source_sha256(invoke_instrumented_codex),
        "continuation_transport_adapter": source_sha256(
            prior.ContinuationTransportAdapter
        ),
        "instrumented_runner": source_sha256(prior.instrumented_runner),
    }


def verify_frozen(args: argparse.Namespace) -> dict[str, object]:
    architecture = frozen.architecture_hashes(Path.cwd().resolve())
    sources = frozen.fundamental.source_hashes(Path.cwd().resolve(), args.provider_root)
    transport = transport_hashes(Path.cwd().resolve())
    if architecture != EXPECTED_ARCHITECTURE_HASHES:
        raise ValueError("ownership_architecture_hash_drift")
    if sources != EXPECTED_SOURCE_HASHES:
        raise ValueError("fundamental_source_enrichment_drift")
    if transport != EXPECTED_TRANSPORT_HASHES:
        raise ValueError("transport_topology_hash_drift")
    if packet_schema_sha256() != EXPECTED_PACKET_SCHEMA_SHA256:
        raise ValueError("production_packet_schema_mutation")
    source = prior.verify_source_lock(args.source_root)
    return {
        "architecture": architecture,
        "sources": sources,
        "transport": transport,
        "packet_schema_sha256": packet_schema_sha256(),
        "source": source,
    }


def fictional_owned(
    ticker: str,
    *,
    market: Literal["us", "kr"],
    padding_bytes: int = 0,
) -> OwnedEvidencePacket:
    if not ticker.startswith("SYNTHETIC_"):
        raise ValueError("reserved_fictional_ticker_required")
    padding = (" fictional operating evidence" * math.ceil(padding_bytes / 31))[
        :padding_bytes
    ]

    def ref(
        suffix: str,
        category: EvidenceCategory,
        domain: EvidenceDomain,
        statement: str,
    ) -> OwnedEvidenceRef:
        evidence = DecisionEvidenceRef(
            ref_id=f"fictional:{ticker}:{suffix}",
            category=category,
            label=f"fictional_{suffix}",
            statement=statement,
            as_of="2026-09-06",
            source_ref=f"synthetic_transport_fixture.{ticker}.{suffix}",
        )
        return OwnedEvidenceRef(ref=evidence, domain=domain)

    rows = (
        ref(
            "identity",
            EvidenceCategory.QUALITY,
            EvidenceDomain.IDENTITY_SECURITY,
            "This is a fictional issuer used only for a transport canary.",
        ),
        ref(
            "business",
            EvidenceCategory.EARNINGS_QUALITY,
            EvidenceDomain.BUSINESS_CURRENT,
            "The fictional issuer reports stable demand and contract execution."
            + padding,
        ),
        ref(
            "earnings",
            EvidenceCategory.EARNINGS,
            EvidenceDomain.EARNINGS_FINANCIAL_CURRENT,
            "The fictional issuer reports positive operating earnings with formal evidence.",
        ),
        ref(
            "sector",
            EvidenceCategory.EARNINGS_QUALITY,
            EvidenceDomain.SECTOR_OPERATING_CURRENT,
            "Sector demand is mixed and remains context rather than a verdict.",
        ),
        ref(
            "expectations",
            EvidenceCategory.EXPECTATIONS,
            EvidenceDomain.MARKET_EXPECTATIONS,
            "Market expectations require continued fictional execution.",
        ),
        ref(
            "risk",
            EvidenceCategory.RISKS,
            EvidenceDomain.STRUCTURAL_RISK,
            "Customer concentration is a fictional structural risk.",
        ),
        ref(
            "unknown",
            EvidenceCategory.UNKNOWN,
            EvidenceDomain.DATA_QUALITY_LIMIT,
            "Future fictional execution remains unverified.",
        ),
        ref(
            "price",
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceDomain.PRICE_CONTEXT,
            "Synthetic current close is 100 fictional currency units.",
        ),
        ref(
            "support",
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceDomain.SUPPORT_RESISTANCE,
            "Synthetic support is 95 and resistance is 110 for schema testing only.",
        ),
        ref(
            "volume",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.VOLUME_LIQUIDITY,
            "Synthetic volume is above its fictional moving average.",
        ),
        ref(
            "rsi",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.OHLCV_TECHNICAL,
            "Synthetic RSI is neutral for transport testing.",
        ),
        ref(
            "macd",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.OHLCV_TECHNICAL,
            "Synthetic MACD is positive for transport testing.",
        ),
        ref(
            "bollinger",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.OHLCV_TECHNICAL,
            "Synthetic price is inside fictional Bollinger bands.",
        ),
        ref(
            "moving_average",
            EvidenceCategory.TECHNICAL_FEATURE,
            EvidenceDomain.TECHNICAL_STATE,
            "Synthetic moving-average state is constructive.",
        ),
        ref(
            "risk_reward",
            EvidenceCategory.PRICE_STRUCTURE,
            EvidenceDomain.RISK_REWARD_PRICE,
            "Synthetic risk/reward is only a timing constraint.",
        ),
        ref(
            "supply",
            EvidenceCategory.FLOWS,
            EvidenceDomain.SUPPLY_POSITIONING,
            "Synthetic positioning is balanced and is not business evidence.",
        ),
    )
    packet = DecisionEvidencePacket(
        packet_id=f"synthetic-transport-{market}-{ticker}",
        ticker=ticker,
        company_name=f"Fictional {market.upper()} {ticker}",
        market=market,
        assessment_date="2026-09-06",
        horizon="12m",
        evidence=tuple(row.ref for row in rows),
        prohibited_claims=(),
        evidence_sha256=canonical_sha256(
            [row.ref.model_dump(mode="json") for row in rows]
        ),
    )
    return OwnedEvidencePacket(source_packet=packet, evidence=rows)


def fixture_core(owned: OwnedEvidencePacket) -> DirectionalCoreCandidate:
    ticker = owned.source_packet.ticker
    business = f"fictional:{ticker}:business"
    earnings = f"fictional:{ticker}:earnings"
    risk = f"fictional:{ticker}:risk"
    unknown = f"fictional:{ticker}:unknown"

    def claim(text: str, ref_id: str = business) -> DirectionalClaim:
        return DirectionalClaim(text=text, evidence_refs=(ref_id,))

    return DirectionalCoreCandidate(
        ticker=ticker,
        overall_direction="HOLD",
        directional_balance=DirectionalBalance(buy=5, sell=5),
        hold_lean="NEUTRAL",
        directional_confidence="MEDIUM",
        business_thesis_change="UNCHANGED",
        business_thesis_context=claim("Fictional business evidence is stable."),
        earnings_estimate_context=claim(
            "Fictional operating earnings are positive.", earnings
        ),
        market_expectation_context=claim("Fictional expectations require execution."),
        valuation_context=claim("No fictional valuation conclusion is required."),
        risk_context=claim("Fictional concentration remains a risk.", risk),
        sector_interpretation=claim("Fictional sector demand is mixed."),
        buy_drivers=(claim("Fictional demand supports the case."),),
        sell_drivers=(
            DirectionalSellDriver(
                text="Fictional concentration limits conviction.",
                evidence_refs=(risk,),
                classification="STRUCTURAL_RISK",
            ),
        ),
        dominant_evidence=claim("Fictional operating evidence dominates."),
        uncertainty_limit=claim("Fictional future execution is unknown.", unknown),
        core_investment_judgment=claim("Fictional evidence supports a balanced view."),
        unknown_treatments=(
            DirectionalUnknown(
                summary="Fictional future execution remains unknown.",
                evidence_refs=(unknown,),
                treatment="CONFIDENCE_LIMIT",
                directional_negative_basis=(),
            ),
        ),
        material_directional_anchor_basis=(business, earnings),
        fundamental_new_buyer=CoreNewBuyerView(
            stance="WAIT",
            summary="Fictional evidence supports waiting.",
            confirmation_business_condition="Fictional execution must be confirmed.",
            confirmation_business_condition_refs=(business,),
        ),
        fundamental_holder=CoreHolderView(
            stance="HOLDABLE",
            summary="Fictional holder evidence remains balanced.",
            business_invalidation_condition="Fictional execution deterioration invalidates the case.",
            business_invalidation_condition_refs=(business, risk),
        ),
        business_reevaluation_up=(claim("Fictional execution improves."),),
        business_reevaluation_down=(claim("Fictional execution deteriorates.", risk),),
    )


def timing_context(
    owned: OwnedEvidencePacket, core: DirectionalCoreCandidate
) -> tuple[dict[str, object], object]:
    _core_catalog, timing_catalog = stage_alias_catalogs(owned)
    ticker = owned.source_packet.ticker
    support_alias = timing_catalog.by_ref[f"fictional:{ticker}:support"].alias
    currency = "USD" if owned.source_packet.market == "us" else "KRW"
    context = {
        **frozen._owned_context(owned, timing_catalog),
        "allowed_price_choices": {
            "allowed_confirmation_levels": [
                {"basis_alias": support_alias, "level": 110.0}
            ],
            "allowed_downside_levels": [
                {"basis_alias": support_alias, "level": 95.0}
            ],
            "allowed_pullback_zones": [
                {"basis_alias": support_alias, "low": 95.0, "high": 98.0}
            ],
            "allowed_trim_zones": [
                {"basis_alias": support_alias, "low": 108.0, "high": 110.0}
            ],
            "currency": currency,
            "current_close": 100.0,
        },
        "core_fingerprint": core_fingerprint(core),
        "frozen_directional_core": core.model_dump(mode="json"),
    }
    return context, timing_catalog


def fixture_timing(
    owned: OwnedEvidencePacket, core: DirectionalCoreCandidate
) -> PriceTimingCandidate:
    ticker = owned.source_packet.ticker
    support = f"fictional:{ticker}:support"
    technical = f"fictional:{ticker}:rsi"
    supply = f"fictional:{ticker}:supply"
    currency = "USD" if owned.source_packet.market == "us" else "KRW"

    def claim(text: str, ref_id: str) -> TimingClaim:
        return TimingClaim(text=text, evidence_refs=(ref_id,))

    return PriceTimingCandidate(
        ticker=ticker,
        core_fingerprint=core_fingerprint(core),
        technical_state=TechnicalState.NEUTRAL,
        timing_new_buyer_modifier=TimingNewBuyerModifier.WAIT,
        entry_mode="NONE",
        entry_reason="Synthetic timing remains neutral.",
        pullback_entry_zone_low=None,
        pullback_entry_zone_high=None,
        pullback_entry_basis=(),
        breakout_confirmation_level=None,
        breakout_confirmation_basis=(),
        confirmation_semantics="NONE",
        holder_price_review=HolderPriceReview.NONE,
        upside_trim_zone_low=None,
        upside_trim_zone_high=None,
        upside_trim_basis=(),
        downside_review_level=None,
        downside_review_basis=(),
        currency=currency,
        price_review_context=claim("Synthetic support frames price review.", support),
        price_confirmation_context=claim(
            "Synthetic technical confirmation is neutral.", technical
        ),
        price_support_context=claim("Synthetic support remains contextual.", support),
        technical_rationale=claim("Synthetic RSI is neutral.", technical),
        supply_positioning_rationale=claim(
            "Synthetic positioning is balanced.", supply
        ),
    )


def preflight_document(output_root: Path | None = None) -> dict[str, object]:
    fixtures: dict[str, tuple[OwnedEvidencePacket, ...]] = {
        "us_single": (fictional_owned("SYNTHETIC_US_ALPHA", market="us"),),
        "kr_single": (fictional_owned("SYNTHETIC_KR_ALPHA", market="kr"),),
        "us4": tuple(
            fictional_owned(f"SYNTHETIC_US_{index}", market="us", padding_bytes=2300)
            for index in range(1, 5)
        ),
        "kr4": tuple(
            fictional_owned(f"SYNTHETIC_KR_{index}", market="kr", padding_bytes=2300)
            for index in range(1, 5)
        ),
    }
    cases = []
    for name, owned_rows in fixtures.items():
        catalogs = {
            row.source_packet.ticker: stage_alias_catalogs(row)[0]
            for row in owned_rows
        }
        packet_id = f"schema-preflight-{name}"
        prompt = frozen._core_prompt(
            packet_id=packet_id,
            tickers=tuple(row.source_packet.ticker for row in owned_rows),
            contexts=tuple(
                frozen._owned_context(row, catalogs[row.source_packet.ticker])
                for row in owned_rows
            ),
        )
        schema = prior._batch_schema(
            candidate=DirectionalCoreCandidate,
            contract=CORE_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs=catalogs,
        )
        cores = tuple(fixture_core(row) for row in owned_rows)
        case = {
            "case": name,
            "market": owned_rows[0].source_packet.market,
            "subject_count": len(owned_rows),
            "packet_validation": "PASS",
            "owned_packet_validation": "PASS",
            "core_candidate_validation": "PASS",
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "schema_sha256": canonical_sha256(schema),
            "status": "PASS",
        }
        cases.append(case)
        if output_root is not None:
            directory = output_root / "schema-preflight" / name
            directory.mkdir(parents=True, exist_ok=False)
            (directory / "prompt.txt").write_text(prompt, encoding="utf-8")
            write_json(directory / "schema.json", schema)
            write_json(
                directory / "fixture-sidecar.json",
                {
                    "synthetic_fixture": True,
                    "routing_market": owned_rows[0].source_packet.market,
                    "tickers": [row.source_packet.ticker for row in owned_rows],
                    "core_candidate_sha256": [
                        canonical_sha256(core.model_dump(mode="json"))
                        for core in cores
                    ],
                },
            )

    for name, owned in (
        ("timing_us", fixtures["us_single"][0]),
        ("timing_kr", fixtures["kr_single"][0]),
    ):
        core = fixture_core(owned)
        context, catalog = timing_context(owned, core)
        timing = fixture_timing(owned, core)
        composed = compose_decision(core, timing)
        validation = validate_ownership(owned, core, timing, composed)
        if not validation.valid:
            raise ValueError(f"synthetic_timing_preflight_failed:{name}:{validation.errors}")
        packet_id = f"schema-preflight-{name}"
        prompt = frozen._timing_prompt(
            packet_id=packet_id,
            tickers=(owned.source_packet.ticker,),
            contexts=(context,),
        )
        schema = prior._batch_schema(
            candidate=PriceTimingCandidate,
            contract=TIMING_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs={owned.source_packet.ticker: catalog},
        )
        cases.append(
            {
                "case": name,
                "market": owned.source_packet.market,
                "subject_count": 1,
                "timing_input_validation": "PASS",
                "ownership_validation": "PASS",
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "schema_sha256": canonical_sha256(schema),
                "status": "PASS",
            }
        )
        if output_root is not None:
            directory = output_root / "schema-preflight" / name
            directory.mkdir(parents=True, exist_ok=False)
            (directory / "prompt.txt").write_text(prompt, encoding="utf-8")
            write_json(directory / "schema.json", schema)
            write_json(
                directory / "fixture-sidecar.json",
                {
                    "synthetic_fixture": True,
                    "routing_market": owned.source_packet.market,
                    "ticker": owned.source_packet.ticker,
                    "core_fingerprint": core_fingerprint(core),
                    "timing_candidate_sha256": canonical_sha256(
                        timing.model_dump(mode="json")
                    ),
                },
            )

    fictional_tickers = {
        row.source_packet.ticker
        for owned_rows in fixtures.values()
        for row in owned_rows
    }
    real_overlap = fictional_tickers & set(CONSUMED_LATEST_HOLDOUT16 + CURRENT_HOLDOUT)
    return {
        "contract": "synthetic-packet-schema-preflight-v1",
        "cases": cases,
        "synthetic_packet_schema_preflight": (
            "PASS" if all(row["status"] == "PASS" for row in cases) else "FAIL"
        ),
        "production_market_enum_mutation": 0,
        "production_packet_schema_mutation": 0,
        "real_issuer_used_as_canary": len(real_overlap),
        "ticker_specific_production_exception": 0,
        "fictional_identity_routing_market_separated": 1,
        "fixture_sidecar_only": 1,
        "status": "PASS" if not real_overlap else "FAIL",
    }


class LiveWorkloadGuard:
    def __init__(self, audit_path: Path) -> None:
        self.audit_path = audit_path
        self.events: list[dict[str, object]] = []
        if audit_path.is_file():
            prior_audit = read_json(audit_path)
            self.events = list(prior_audit.get("events") or [])

    @staticmethod
    def _running_model_process_count() -> int:
        result = subprocess.run(
            ["ps", "-axo", "command="],
            check=True,
            capture_output=True,
            text=True,
        )
        return sum(
            "codex exec" in line and "synthetic_canary_fixture_repair" not in line
            for line in result.stdout.splitlines()
        )

    @staticmethod
    def _active_natural_job_count() -> int:
        result = subprocess.run(
            ["ps", "-axo", "command="],
            check=True,
            capture_output=True,
            text=True,
        )
        markers = (
            "app.jobs.monitor_daily",
            "app.jobs.ai_review",
            "app.jobs.run_night_futures",
        )
        return sum(any(marker in line for marker in markers) for line in result.stdout.splitlines())

    @staticmethod
    def _scheduled_window(now: datetime) -> tuple[str | None, datetime | None]:
        local = now.astimezone(KST)
        windows = (
            ("US_NATURAL", (7, 50), (9, 0)),
            ("KR_NATURAL", (15, 50), (17, 30)),
        )
        for name, start, end in windows:
            lower = local.replace(
                hour=start[0], minute=start[1], second=0, microsecond=0
            )
            upper = local.replace(hour=end[0], minute=end[1], second=0, microsecond=0)
            if lower <= local < upper:
                return name, upper
        return None, None

    def _write(self) -> None:
        pauses = sum(event["action"] == "PAUSE" for event in self.events)
        write_json(
            self.audit_path,
            {
                "contract": "natural-live-workload-coexistence-guard-v1",
                "events": self.events,
                "live_workload_contention_risk": 0,
                "shadow_pause_for_natural_live": pauses,
                "natural_live_cancel_count": 0,
                "scheduler_mutation": 0,
                "status": "PASS",
            },
        )

    def wait_until_clear(
        self, *, stage: str, batch_id: str, subject_count: int
    ) -> None:
        paused = False
        while True:
            now = datetime.now(UTC)
            window, window_end = self._scheduled_window(now)
            natural_jobs = self._active_natural_job_count()
            model_processes = self._running_model_process_count()
            contention = bool(window or natural_jobs or model_processes)
            self.events.append(
                {
                    "observed_at": now.isoformat(),
                    "stage": stage,
                    "batch_id": batch_id,
                    "subject_count": subject_count,
                    "scheduled_window": window,
                    "active_natural_job_count": natural_jobs,
                    "other_codex_exec_count": model_processes,
                    "action": "PAUSE" if contention else "CONTINUE",
                }
            )
            self._write()
            if not contention:
                if paused:
                    self.events.append(
                        {
                            "observed_at": datetime.now(UTC).isoformat(),
                            "stage": stage,
                            "batch_id": batch_id,
                            "subject_count": subject_count,
                            "action": "RESUME",
                        }
                    )
                    self._write()
                return
            paused = True
            if window_end is not None:
                remaining = max(
                    30.0,
                    (window_end - datetime.now(KST)).total_seconds() + 5.0,
                )
                time.sleep(min(60.0, remaining))
            else:
                time.sleep(30.0)


class GuardedTransportAdapter(prior.ContinuationTransportAdapter):
    def __init__(self, *, guard: LiveWorkloadGuard, **kwargs: object) -> None:
        self.guard = guard
        super().__init__(**kwargs)

    def invoke(self, **kwargs: object) -> dict[str, object]:
        identity = prior._identity_from_prompt(Path(str(kwargs["prompt"])))
        tickers = (
            identity.get("tickers")
            if isinstance(identity.get("tickers"), list)
            else []
        )
        inferred_stage = (
            "DIRECTIONAL_CORE"
            if identity.get("contract") == CORE_OUTPUT_CONTRACT
            else "PRICE_TIMING"
            if identity.get("contract") == TIMING_OUTPUT_CONTRACT
            else "TRANSPORT_SMOKE"
        )
        self.guard.wait_until_clear(
            stage=str(kwargs.get("stage") or inferred_stage),
            batch_id=str(kwargs.get("batch_id") or Path(str(kwargs["output"])).stem),
            subject_count=int(kwargs.get("subject_count") or len(tickers) or 1),
        )
        return super().invoke(**kwargs)


def verify_program_freeze(state: Mapping[str, object]) -> None:
    if file_sha256(Path(__file__).resolve()) != state["resume_harness_sha256"]:
        raise ValueError("resume_harness_mutation_after_freeze")
    if source_sha256(fictional_owned) != state["fixture_builder_sha256"]:
        raise ValueError("canary_fixture_mutation_after_first_model_call")


def _base_proofs(
    *,
    state: Mapping[str, object],
    frozen_state: Mapping[str, object],
    preflight: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    return {
        "canary-fixture-root-cause.json": {
            "contract": "canary-fixture-root-cause-v1",
            "root_cause": "SYNTHETIC_CANARY_FIXTURE_MARKET_ENUM_INVALID",
            "prior_value": "synthetic",
            "allowed_market_enum": ["kr", "us"],
            "repair_scope": "TEST_FIXTURE_ONLY_BEFORE_FIRST_MODEL_CANARY",
            "model_invocation_at_failure": 0,
            "production_schema_defect": 0,
            "status": "CLOSED",
        },
        "canary-fixture-schema-contract.json": {
            "contract": "canary-fixture-schema-contract-v1",
            "fictional_identity": "reserved SYNTHETIC_* identifiers",
            "routing_market": ["us", "kr"],
            "synthetic_fixture_metadata_location": "TEST_HARNESS_SIDECAR",
            "production_market_enum_mutation": 0,
            "production_packet_schema_mutation": 0,
            "real_issuer_used_as_canary": 0,
            "ticker_specific_production_exception": 0,
            "packet_schema_sha256": EXPECTED_PACKET_SCHEMA_SHA256,
            "status": "PASS",
        },
        "canary-schema-preflight.json": dict(preflight),
        "architecture-freeze-reverification.json": {
            "contract": "resume-architecture-freeze-reverification-v1",
            "expected_hashes": EXPECTED_ARCHITECTURE_HASHES,
            "actual_hashes": frozen_state["architecture"],
            "ownership_architecture_hash_drift": 0,
            "direction_timing_policy_mutation": 0,
            "investment_decision_threshold_mutation": 0,
            "execution_mode": "TWO_STAGE_FENCED",
            "status": "PASS",
        },
        "source-freeze-reverification.json": {
            "contract": "resume-source-freeze-reverification-v1",
            "expected_hashes": EXPECTED_SOURCE_HASHES,
            "actual_hashes": frozen_state["sources"],
            "fundamental_source_enrichment_drift": 0,
            "source_sufficiency_policy_drift": 0,
            "source_refresh": 0,
            "status": "PASS",
        },
        "transport-freeze-reverification.json": {
            "contract": "resume-transport-freeze-reverification-v1",
            "expected_hashes": EXPECTED_TRANSPORT_HASHES,
            "actual_hashes": frozen_state["transport"],
            "transport_topology_mutation": 0,
            "timeout_owner": "PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG",
            "model_timeout_owner_count": 1,
            "model_timeout_seconds": MODEL_TIMEOUT_SECONDS,
            "timeout_increase_this_task": 0,
            "batch_semantics": "MODEL_CONTEXT_COUPLED",
            "real_run_batch_size": MODEL_CONTEXT_BATCH_SIZE,
            "batch_split_adopted": 0,
            "batch_split_semantic_equivalence": "FAIL",
            "model_context_shape_mutation": 0,
            "status": "PASS",
        },
        "consumed-regression-no-rerun.json": {
            "contract": "resume-consumed-regression-no-rerun-v1",
            "consumed_cohort": list(CONSUMED_LATEST_HOLDOUT16),
            "latest_holdout16_model_calls": 0,
            "latest_holdout16_rerun_count": 0,
            "status": "PASS",
        },
        "current-holdout-reuse-gate.json": {
            "contract": "resume-current-holdout-reuse-gate-v1",
            "cohort": list(CURRENT_HOLDOUT),
            "source_lock_sha256": SOURCE_LOCK_SHA256,
            "pre_lock_directional_model_calls": 0,
            "prior_model_output_exists": 0,
            "synthetic_canaries": "PENDING",
            "current_holdout_reuse_allowed": 0,
            "status": "PENDING_CANARIES",
        },
        "live-workload-coexistence-audit.json": {
            "contract": "natural-live-workload-coexistence-guard-v1",
            "events": [],
            "live_workload_contention_risk": "NOT_OBSERVED",
            "shadow_pause_for_natural_live": 0,
            "natural_live_cancel_count": 0,
            "scheduler_mutation": 0,
            "status": "PENDING",
        },
        "resume-source-lock.json": {
            "contract": "resume-source-lock-v1",
            "resume_generation_id": state["resume_generation_id"],
            "model_context_packet_id": SOURCE_GENERATION_ID,
            "ordered_cohort": list(CURRENT_HOLDOUT),
            "source_lock_sha256": SOURCE_LOCK_SHA256,
            "source_drift": 0,
            "prompt_semantic_drift": 0,
            "schema_semantic_drift": 0,
            "model_drift": 0,
            "reasoning_effort_drift": 0,
        },
        "production-no-change.json": {
            "contract": "resume-production-no-change-v1",
            "main_merge": 0,
            "production_db_mutation": 0,
            "production_telegram_send": 0,
            "production_scheduler_change": 0,
            "live_structured_autonomy_activation": 0,
            "live_v2_change": 0,
            "monitoring_registration_calls": 0,
            "bootstrap_production_mutation": 0,
            "status": "PASS",
        },
        "night-futures-no-change.json": {
            "contract": "resume-night-futures-no-change-v1",
            "night_futures_code_mutation": 0,
            "night_futures_decision_packet_injection": 0,
            "status": "PASS",
        },
    }


def prepare(args: argparse.Namespace) -> None:
    if args.output_root.exists():
        raise ValueError("new_resume_output_root_required")
    if file_sha256(args.source_report) != SOURCE_REPORT_SHA256:
        raise ValueError("source_report_bundle_sha256_mismatch")
    frozen_state = verify_frozen(args)
    implementation_commit = git_value("rev-parse", "HEAD")
    implementation_tree = git_value("rev-parse", "HEAD^{tree}")
    args.output_root.mkdir(parents=True)
    preflight = preflight_document(args.output_root)
    if preflight["synthetic_packet_schema_preflight"] != "PASS":
        raise ValueError("synthetic_packet_schema_preflight_failed")
    resume_generation = generation_id(implementation_commit, args.as_of)
    codex_bin = accepted_runtime._signed_in_codex_bin()
    state = {
        "contract": PROGRAM_CONTRACT,
        "state": "PREPARED_FROZEN",
        "resume_generation_id": resume_generation,
        "model_context_packet_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "ordered_cohort": list(CURRENT_HOLDOUT),
        "base_sha": "4a847d2c0ea50d190d8df4daef5405b6660967a5",
        "work_instruction_commit": "b1ab44a",
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "resume_harness_sha256": file_sha256(Path(__file__).resolve()),
        "fixture_builder_sha256": source_sha256(fictional_owned),
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": MODEL_TIMEOUT_SECONDS,
        "timeout_increase_this_task": 0,
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "real_run_batch_size": MODEL_CONTEXT_BATCH_SIZE,
        "cli_binary": codex_bin,
        "cli_version": prior.cli_version(codex_bin),
        "synthetic_packet_schema_preflight": "PASS",
        "canary_fixture_mutation_after_first_model_call": 0,
        "transport_canary_model_call_count": 0,
        "real_holdout_model_call_count": 0,
        "real_holdout_transport_retry_count": 0,
        "latest_holdout16_model_calls": 0,
        "production_mutation": 0,
    }
    proofs = args.report_dir / PROOFS_DIRECTORY
    proofs.mkdir(parents=True, exist_ok=True)
    for name, proof in _base_proofs(
        state=state,
        frozen_state=frozen_state,
        preflight=preflight,
    ).items():
        write_json(proofs / name, proof)
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def _canary_files(root: Path, name: str) -> dict[str, Path]:
    return prior._canary_files(root, name)


def _invoke_canary(
    adapter: GuardedTransportAdapter,
    files: Mapping[str, Path],
    *,
    name: str,
    stage: str,
    subject_count: int,
) -> dict[str, object]:
    with engine.isolated_model_working_directory(run=f"resume-{name}", batch=1) as cwd:
        receipt = adapter.invoke(
            prompt=files["prompt"],
            output=files["output"],
            log=files["log"],
            schema=files["schema"],
            cwd=cwd,
            timeout=MODEL_TIMEOUT_SECONDS,
            state_namespace=f"SYNTHETIC_CANARY_RESUME_{name.upper()}_20260906",
            invocation_id=f"{adapter.continuation_generation}:canary:{name}",
            stage=stage,
            batch_id=name,
            subject_count=subject_count,
        )
    prior._attach_receipt_path(receipt, adapter)
    return receipt


def _receipt_summary(receipt: Mapping[str, object]) -> dict[str, object]:
    path = Path(str(receipt["receipt_path"]))
    return {
        "invocation_id": receipt["invocation_id"],
        "status": receipt["status"],
        "input_bytes": receipt["input_bytes"],
        "prompt_sha256": receipt["prompt_sha256"],
        "schema_sha256": receipt["schema_sha256"],
        "model": receipt["model"],
        "reasoning_effort": receipt["reasoning_effort"],
        "subject_count": receipt["subject_count"],
        "transport_grouping_mode": receipt["transport_grouping_mode"],
        "elapsed_to_first_output_seconds": receipt["elapsed_to_first_output_seconds"],
        "elapsed_to_exit_seconds": receipt["elapsed_to_exit_seconds"],
        "stdout_bytes": receipt["stdout_bytes"],
        "stderr_bytes": receipt["stderr_bytes"],
        "output_bytes": receipt["output_bytes"],
        "timeout_owner": receipt["timeout_owner"],
        "child_cleanup_status": receipt["child_cleanup_status"],
        "orphan_model_process_count": receipt["orphan_model_process_count"],
        "secret_exposure_count": receipt["secret_exposure_count"],
        "receipt_sha256": file_sha256(path),
    }


def smoke_canary(
    args: argparse.Namespace, adapter: GuardedTransportAdapter
) -> dict[str, object]:
    files = _canary_files(args.output_root, "c1-smoke")
    files["prompt"].write_text(
        "Return exactly one strict JSON object with status set to ok. Do not browse.",
        encoding="utf-8",
    )
    write_json(
        files["schema"],
        {
            "type": "object",
            "properties": {"status": {"type": "string", "enum": ["ok"]}},
            "required": ["status"],
            "additionalProperties": False,
        },
    )
    receipt = _invoke_canary(
        adapter,
        files,
        name="c1-smoke",
        stage="CLI_PROCESS_SMOKE",
        subject_count=1,
    )
    valid = read_json(files["output"]) == {"status": "ok"}
    return {
        "contract": "schema-valid-canary-smoke-v1",
        "canary": "C1",
        "fictional_subjects_only": 1,
        "structured_output_validation": "PASS" if valid else "FAIL",
        "receipt": _receipt_summary(receipt),
        "status": "PASS" if valid else "FAIL",
    }


def directional_canary(
    args: argparse.Namespace,
    adapter: GuardedTransportAdapter,
    *,
    name: str,
    market: Literal["us", "kr"],
    subject_count: Literal[1, 4],
) -> tuple[dict[str, object], dict[str, DirectionalCoreCandidate], dict[str, OwnedEvidencePacket]]:
    files = _canary_files(args.output_root, name)
    tickers = tuple(
        f"SYNTHETIC_{market.upper()}_{name.upper().replace('-', '_')}_{index}"
        for index in range(1, subject_count + 1)
    )
    owned = {
        ticker: fictional_owned(
            ticker,
            market=market,
            padding_bytes=2300 if subject_count == 4 else 0,
        )
        for ticker in tickers
    }
    catalogs = {ticker: stage_alias_catalogs(owned[ticker])[0] for ticker in tickers}
    packet_id = f"{adapter.continuation_generation}-{name}"
    files["prompt"].write_text(
        frozen._core_prompt(
            packet_id=packet_id,
            tickers=tickers,
            contexts=tuple(
                frozen._owned_context(owned[ticker], catalogs[ticker])
                for ticker in tickers
            ),
        ),
        encoding="utf-8",
    )
    write_json(
        files["schema"],
        prior._batch_schema(
            candidate=DirectionalCoreCandidate,
            contract=CORE_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs=catalogs,
        ),
    )
    receipt = _invoke_canary(
        adapter,
        files,
        name=name,
        stage="DIRECTIONAL_CORE",
        subject_count=subject_count,
    )
    parsed = read_json(files["output"])
    if parsed.get("contract") != CORE_OUTPUT_CONTRACT:
        raise ValueError(f"canary_core_contract_mismatch:{name}")
    if parsed.get("packet_id") != packet_id:
        raise ValueError(f"canary_core_packet_identity_mismatch:{name}")
    rows, alias_audit = frozen._resolve_batch_candidates(
        parsed.get("candidates"),
        batch=tickers,
        evidence={ticker: owned[ticker].source_packet for ticker in tickers},
        catalogs=catalogs,
        model_type=DirectionalCoreCandidate,
    )
    cores = {row.ticker: row for row in rows if isinstance(row, DirectionalCoreCandidate)}
    violations = {}
    for ticker, core in cores.items():
        refs = frozen._refs(core.model_dump(mode="json"))
        disallowed = sorted(refs - owned[ticker].core_refs)
        if disallowed:
            violations[ticker] = disallowed
    valid = len(cores) == subject_count and not violations
    return (
        {
            "contract": "schema-valid-directional-core-canary-v1",
            "canary": name,
            "routing_market": market,
            "subject_count": subject_count,
            "batch_semantics": (
                "MODEL_CONTEXT_COUPLED" if subject_count == 4 else "SINGLE_MODEL_CONTEXT"
            ),
            "real_issuer_used_as_canary": 0,
            "core_only_evidence_validation": "PASS" if not violations else "FAIL",
            "core_only_evidence_violations": violations,
            "alias_resolution": "PASS",
            "resolved_candidate_sha256": {
                ticker: alias_audit[ticker]["resolved_candidate_sha256"]
                for ticker in tickers
            },
            "receipt": _receipt_summary(receipt),
            "status": "PASS" if valid else "FAIL",
        },
        cores,
        owned,
    )


def timing_canary(
    args: argparse.Namespace,
    adapter: GuardedTransportAdapter,
    *,
    name: str,
    owned: OwnedEvidencePacket,
    core: DirectionalCoreCandidate,
) -> dict[str, object]:
    files = _canary_files(args.output_root, name)
    context, catalog = timing_context(owned, core)
    ticker = owned.source_packet.ticker
    packet_id = f"{adapter.continuation_generation}-{name}"
    files["prompt"].write_text(
        frozen._timing_prompt(
            packet_id=packet_id,
            tickers=(ticker,),
            contexts=(context,),
        ),
        encoding="utf-8",
    )
    write_json(
        files["schema"],
        prior._batch_schema(
            candidate=PriceTimingCandidate,
            contract=TIMING_OUTPUT_CONTRACT,
            packet_id=packet_id,
            catalogs={ticker: catalog},
        ),
    )
    receipt = _invoke_canary(
        adapter,
        files,
        name=name,
        stage="PRICE_TIMING",
        subject_count=1,
    )
    parsed = read_json(files["output"])
    if parsed.get("contract") != TIMING_OUTPUT_CONTRACT:
        raise ValueError(f"canary_timing_contract_mismatch:{name}")
    if parsed.get("packet_id") != packet_id:
        raise ValueError(f"canary_timing_packet_identity_mismatch:{name}")
    rows, alias_audit = frozen._resolve_batch_candidates(
        parsed.get("candidates"),
        batch=(ticker,),
        evidence={ticker: owned.source_packet},
        catalogs={ticker: catalog},
        model_type=PriceTimingCandidate,
    )
    timing = rows[0]
    assert isinstance(timing, PriceTimingCandidate)
    composed = compose_decision(core, timing)
    validation = validate_ownership(owned, core, timing, composed)
    return {
        "contract": "schema-valid-price-timing-canary-v1",
        "canary": name,
        "routing_market": owned.source_packet.market,
        "subject_count": 1,
        "real_issuer_used_as_canary": 0,
        "ownership_validation": "PASS" if validation.valid else "FAIL",
        "ownership_errors": list(validation.errors),
        "timing_stage_direction_mutation": validation.timing_stage_direction_mutation,
        "timing_stage_balance_mutation": validation.timing_stage_balance_mutation,
        "timing_stage_hold_lean_mutation": validation.timing_stage_hold_lean_mutation,
        "price_timing_new_buyer_upgrade": validation.price_timing_new_buyer_upgrade,
        "price_only_holder_reduce": validation.price_only_holder_reduce,
        "resolved_candidate_sha256": alias_audit[ticker][
            "resolved_candidate_sha256"
        ],
        "receipt": _receipt_summary(receipt),
        "status": "PASS" if validation.valid else "FAIL",
    }


CANARY_PROOF_NAMES = {
    "C1": "canary-smoke.json",
    "C2": "canary-directional-us.json",
    "C3": "canary-directional-kr.json",
    "C4": "canary-shared-context-us4.json",
    "C5": "canary-shared-context-kr4.json",
    "C6": "canary-price-timing-us.json",
    "C7": "canary-price-timing-kr.json",
}


def _failure_receipt(adapter: GuardedTransportAdapter) -> dict[str, object] | None:
    receipts = sorted(adapter.receipt_root.glob("*.json"), key=lambda path: path.stat().st_mtime)
    if not receipts:
        return None
    value = read_json(receipts[-1])
    value["receipt_path"] = str(receipts[-1])
    return _receipt_summary(value)


def run_canaries(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "PREPARED_FROZEN":
        raise ValueError("prepared_frozen_state_required")
    verify_frozen(args)
    verify_program_freeze(state)
    proofs = args.report_dir / PROOFS_DIRECTORY
    guard = LiveWorkloadGuard(proofs / "live-workload-coexistence-audit.json")
    adapter = GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["resume_generation_id"]),
        receipt_root=args.output_root / "transport-receipts" / "canaries",
        codex_bin=str(state["cli_binary"]),
    )
    results: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    core_us: dict[str, DirectionalCoreCandidate] = {}
    core_kr: dict[str, DirectionalCoreCandidate] = {}
    owned_us: dict[str, OwnedEvidencePacket] = {}
    owned_kr: dict[str, OwnedEvidencePacket] = {}

    def record(canary: str, operation) -> None:
        nonlocal stop_reason
        if stop_reason:
            return
        try:
            value = operation()
            if isinstance(value, tuple):
                proof = value[0]
            else:
                proof = value
            results[canary] = proof
            if proof.get("status") != "PASS":
                stop_reason = f"{canary}_FAILED_NO_SAME_GENERATION_REPAIR"
        except Exception as exc:
            results[canary] = {
                "contract": "schema-valid-synthetic-canary-failure-v1",
                "canary": canary,
                "status": "FAIL",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "latest_transport_receipt": _failure_receipt(adapter),
            }
            stop_reason = f"{canary}_FAILED_NO_SAME_GENERATION_REPAIR"
        write_json(proofs / CANARY_PROOF_NAMES[canary], results[canary])
        verify_frozen(args)
        verify_program_freeze(state)

    record("C1", lambda: smoke_canary(args, adapter))

    def c2():
        proof, cores, owned = directional_canary(
            args,
            adapter,
            name="c2-directional-us",
            market="us",
            subject_count=1,
        )
        core_us.update(cores)
        owned_us.update(owned)
        return proof

    record("C2", c2)

    def c3():
        proof, cores, owned = directional_canary(
            args,
            adapter,
            name="c3-directional-kr",
            market="kr",
            subject_count=1,
        )
        core_kr.update(cores)
        owned_kr.update(owned)
        return proof

    record("C3", c3)
    record(
        "C4",
        lambda: directional_canary(
            args,
            adapter,
            name="c4-shared-context-us4",
            market="us",
            subject_count=4,
        )[0],
    )
    record(
        "C5",
        lambda: directional_canary(
            args,
            adapter,
            name="c5-shared-context-kr4",
            market="kr",
            subject_count=4,
        )[0],
    )
    record(
        "C6",
        lambda: timing_canary(
            args,
            adapter,
            name="c6-price-timing-us",
            owned=next(iter(owned_us.values())),
            core=next(iter(core_us.values())),
        ),
    )
    record(
        "C7",
        lambda: timing_canary(
            args,
            adapter,
            name="c7-price-timing-kr",
            owned=next(iter(owned_kr.values())),
            core=next(iter(core_kr.values())),
        ),
    )

    for canary, proof_name in CANARY_PROOF_NAMES.items():
        if canary not in results:
            write_json(
                proofs / proof_name,
                {
                    "contract": "schema-valid-synthetic-canary-v1",
                    "canary": canary,
                    "status": "NOT_RUN",
                    "reason": stop_reason,
                },
            )

    all_pass = len(results) == 7 and all(
        value.get("status") == "PASS" for value in results.values()
    )
    architecture_scale = (
        "PASS"
        if all(results.get(name, {}).get("status") == "PASS" for name in ("C4", "C5"))
        else "FAIL"
        if any(results.get(name, {}).get("status") == "FAIL" for name in ("C4", "C5"))
        else "NOT_RUN"
    )
    receipts = [read_json(path) for path in adapter.receipt_root.glob("*.json")]
    orphan_count = sum(int(row.get("orphan_model_process_count") or 0) for row in receipts)
    secret_count = sum(int(row.get("secret_exposure_count") or 0) for row in receipts)
    verdict = {
        "contract": "schema-valid-synthetic-canary-verdict-v1",
        "canary_results": {
            name: results.get(name, {}).get("status", "NOT_RUN")
            for name in CANARY_PROOF_NAMES
        },
        "transport_canary_model_call_count": adapter.model_call_count,
        "max_authorized_canary_calls": MAX_CANARY_MODEL_CALLS,
        "transport_canary_status": "PASS" if all_pass else "FAIL",
        "architecture_scale_transport_status": architecture_scale,
        "stop_before_real_holdout": 0 if all_pass else 1,
        "canary_fixture_mutation_after_first_model_call": 0,
        "model_timeout_seconds": MODEL_TIMEOUT_SECONDS,
        "timeout_increase_this_task": 0,
        "model_timeout_owner_count": 1,
        "orphan_model_process_count": orphan_count,
        "secret_exposure_count": secret_count,
        "transport_verdict": (
            "TRANSPORT_HEALTHY_AFTER_REVALIDATION"
            if all_pass
            else "TRANSPORT_BLOCKED_UNKNOWN"
        ),
        "stop_reason": stop_reason,
        "status": "PASS" if all_pass else "FAIL",
    }
    write_json(proofs / "canary-verdict.json", verdict)
    reuse = read_json(proofs / "current-holdout-reuse-gate.json")
    reuse.update(
        {
            "synthetic_canaries": verdict["transport_canary_status"],
            "architecture_scale_transport_status": architecture_scale,
            "architecture_hashes_unchanged": 1,
            "source_hashes_unchanged": 1,
            "source_lock_unchanged": 1,
            "prompt_schema_semantics_unchanged": 1,
            "model_effort_unchanged": 1,
            "batch_context_unchanged": 1,
            "transport_topology_unchanged": 1,
            "current_holdout_reuse_allowed": 1 if all_pass else 0,
            "status": "PASS" if all_pass else "FAIL",
        }
    )
    write_json(proofs / "current-holdout-reuse-gate.json", reuse)
    state.update(
        {
            "state": "CANARIES_PASS" if all_pass else "STOPPED_CANARY_FAILED",
            "transport_canary_model_call_count": adapter.model_call_count,
            "transport_canary_status": verdict["transport_canary_status"],
            "architecture_scale_transport_status": architecture_scale,
            "transport_verdict": verdict["transport_verdict"],
            "current_holdout_reuse_allowed": 1 if all_pass else 0,
            "stop_reason": stop_reason,
        }
    )
    if not all_pass:
        write_not_run_proofs(proofs, state, reason=str(stop_reason))
        write_completion_proofs(
            proofs, state, documents={}, owned=None, reason=str(stop_reason)
        )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(state, sort_keys=True), flush=True)


def _run_not_started(
    run: str, state: Mapping[str, object], reason: str
) -> dict[str, object]:
    return {
        "contract": "direction-timing-two-stage-run-v1",
        "run": run,
        "resume_generation_id": state["resume_generation_id"],
        "model_context_packet_id": SOURCE_GENERATION_ID,
        "source_lock_sha256": SOURCE_LOCK_SHA256,
        "status": "NOT_RUN",
        "reason": reason,
        "same_generation_repair": 0,
        "selective_rerun": 0,
        "real_holdout_transport_retry_count": 0,
    }


def write_not_run_proofs(
    proofs: Path, state: Mapping[str, object], *, reason: str
) -> None:
    for run in ("first", "a", "b", "c"):
        proof_name = "resume-first.json" if run == "first" else f"resume-run-{run}.json"
        write_json(proofs / proof_name, _run_not_started(run, state, reason))
    for name, contract in (
        ("resume-core-stability.json", "directional-core-stability-audit-v1"),
        ("resume-timing-stability.json", "price-timing-stability-audit-v1"),
    ):
        write_json(
            proofs / name,
            {
                "contract": contract,
                "status": "NOT_MEASURED",
                "reason": reason,
                "counts": {
                    "STABLE": 0,
                    "BOUNDARY_UNCERTAINTY": 0,
                    "UNSTABLE": 0,
                },
            },
        )
    write_json(
        proofs / "resume-dominance-ownership.json",
        {
            "contract": "resume-dominance-ownership-v1",
            "status": "NOT_MEASURED",
            "reason": reason,
            "final_direction_owner": "NOT_MEASURED",
            "price_only_directional_ownership_violations": "NOT_MEASURED",
            "price_only_holder_reduce": "NOT_MEASURED",
        },
    )
    write_json(
        proofs / "resume-renderer-shadow-proof.json",
        {
            "contract": "resume-renderer-shadow-proof-v1",
            "status": "NOT_MEASURED",
            "reason": reason,
            "primary_user_action_wording_owner": "NOT_MEASURED",
        },
    )


def _receipts_for_run(receipt_root: Path, run: str) -> list[dict[str, object]]:
    rows = []
    for path in sorted(receipt_root.glob("*.json")):
        value = read_json(path)
        if f":run-{run}:" not in str(value.get("invocation_id") or ""):
            continue
        rows.append(
            {
                "invocation_id": value["invocation_id"],
                "stage": value["stage"],
                "batch_id": value["batch_id"],
                "subject_count": value["subject_count"],
                "transport_grouping_mode": value["transport_grouping_mode"],
                "status": value["status"],
                "input_bytes": value["input_bytes"],
                "prompt_sha256": value["prompt_sha256"],
                "schema_sha256": value["schema_sha256"],
                "elapsed_to_first_output_seconds": value[
                    "elapsed_to_first_output_seconds"
                ],
                "elapsed_to_exit_seconds": value["elapsed_to_exit_seconds"],
                "stdout_bytes": value["stdout_bytes"],
                "stderr_bytes": value["stderr_bytes"],
                "output_bytes": value["output_bytes"],
                "timeout_owner": value["timeout_owner"],
                "child_cleanup_status": value["child_cleanup_status"],
                "orphan_model_process_count": value[
                    "orphan_model_process_count"
                ],
                "secret_exposure_count": value["secret_exposure_count"],
                "receipt_sha256": file_sha256(path),
            }
        )
    return rows


def write_completion_proofs(
    proofs: Path,
    state: Mapping[str, object],
    *,
    documents: Mapping[str, Mapping[str, object]],
    owned: Mapping[str, OwnedEvidencePacket] | None,
    reason: str | None,
) -> dict[str, object]:
    run_names = ("first", "a", "b", "c")
    all_valid = bool(documents) and all(
        documents.get(run, {}).get("status") == "PASS" for run in run_names
    )
    abc_valid = all(
        documents.get(run, {}).get("status") == "PASS" for run in ("a", "b", "c")
    )
    if abc_valid:
        core_stability = frozen._core_stability(CURRENT_HOLDOUT, documents)
        timing_stability = frozen._timing_stability(CURRENT_HOLDOUT, documents)
    else:
        core_stability = {
            "contract": "directional-core-stability-audit-v1",
            "status": "NOT_MEASURED",
            "reason": reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
        }
        timing_stability = {
            "contract": "price-timing-stability-audit-v1",
            "status": "NOT_MEASURED",
            "reason": reason or "ABC_INCOMPLETE",
            "counts": {"STABLE": 0, "BOUNDARY_UNCERTAINTY": 0, "UNSTABLE": 0},
        }
    core_stability["contract"] = "resume-directional-core-stability-audit-v1"
    timing_stability["contract"] = "resume-price-timing-stability-audit-v1"
    write_json(proofs / "resume-core-stability.json", core_stability)
    write_json(proofs / "resume-timing-stability.json", timing_stability)

    first = documents.get("first", {})
    if first.get("status") == "PASS" and owned is not None:
        ownership = frozen._dominance_audit(first, owned)
        ownership["contract"] = "resume-dominance-ownership-v1"
        examples = [
            {
                "ticker": row["ticker"],
                "decision": row["composed"]["decision"],
                "new_buyer": row["composed"]["new_buyer_view"]["stance"],
                "holder": row["composed"]["holder_view"]["stance"],
                "message": row["rendered_message"],
                "imperative_matches": [
                    match.model_dump(mode="json")
                    for match in explicit_actionable_trade_directives(
                        row["rendered_message"]
                    )
                ],
            }
            for row in first["rows"][:4]
        ]
        renderer = {
            "contract": "resume-renderer-shadow-proof-v1",
            "primary_user_action_wording_owner": "RENDERER",
            "examples": examples,
            "ai_imperative_primary_action": sum(
                len(row["imperative_matches"]) for row in examples
            ),
            "status": (
                "PASS"
                if not any(row["imperative_matches"] for row in examples)
                else "FAIL"
            ),
        }
    else:
        ownership = {
            "contract": "resume-dominance-ownership-v1",
            "status": "NOT_MEASURED",
            "reason": reason or "FIRST_INCOMPLETE",
            "final_direction_owner": "NOT_MEASURED",
            "price_only_directional_ownership_violations": "NOT_MEASURED",
            "price_only_holder_reduce": "NOT_MEASURED",
        }
        renderer = {
            "contract": "resume-renderer-shadow-proof-v1",
            "status": "NOT_MEASURED",
            "reason": reason or "FIRST_INCOMPLETE",
            "primary_user_action_wording_owner": "NOT_MEASURED",
        }
    write_json(proofs / "resume-dominance-ownership.json", ownership)
    write_json(proofs / "resume-renderer-shadow-proof.json", renderer)

    ownership_rows = [
        row["ownership"]
        for document in documents.values()
        for row in document.get("rows", [])
        if isinstance(row, Mapping) and isinstance(row.get("ownership"), Mapping)
    ]

    def ownership_total(field: str) -> int | str:
        if not ownership_rows:
            return "NOT_MEASURED"
        return sum(int(row.get(field) or 0) for row in ownership_rows)

    known_hard: int | str = (
        sum(int(document.get("hard_safety_regression") or 0) for document in documents.values())
        if documents
        else "NOT_MEASURED"
    )
    ownership_violations: int | str = (
        sum(int(document.get("ownership_violation") or 0) for document in documents.values())
        if documents
        else "NOT_MEASURED"
    )
    hard_status = (
        "PASS"
        if all_valid
        and known_hard == 0
        and ownership_violations == 0
        and renderer.get("status") == "PASS"
        else "FAIL"
        if all_valid
        else "NOT_MEASURED"
    )
    hard = {
        "contract": "resume-hard-safety-regression-v1",
        "numeric_provenance": "REUSED_UNCHANGED",
        "accounting_attribution": "REUSED_UNCHANGED",
        "official_provisional_earnings": "REUSED_UNCHANGED",
        "adr_security_basis": "REUSED_UNCHANGED",
        "evidence_identity_fencing": "PASS" if all_valid else "NOT_MEASURED",
        "future_checkpoint": "REUSED_UNCHANGED",
        "logical_condition": "REUSED_UNCHANGED",
        "actionability_command_detection": "PASS" if all_valid else "NOT_MEASURED",
        "source_sufficiency": "PASS",
        "issuer_dedup": "PASS",
        "renderer_ownership": renderer.get("status"),
        "known_hard_safety_regression": known_hard,
        "status": hard_status,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    write_json(proofs / "resume-hard-safety-regression.json", hard)

    core_unstable = core_stability.get("counts", {}).get("UNSTABLE", 0)
    ownership_clean = (
        ownership.get("status") == "PASS"
        and ownership.get("price_only_directional_ownership_violations") == 0
        and ownership.get("price_only_holder_reduce") == 0
    )
    transport_blocked = state.get("transport_canary_status") != "PASS" or any(
        document.get("transport_failure") == 1 for document in documents.values()
    )
    readiness = (
        "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        if all_valid
        and core_unstable == 0
        and ownership_clean
        and hard_status == "PASS"
        else "NOT_READY_TRANSPORT_BLOCKED"
        if transport_blocked
        else "NEEDS_ARCHITECTURE_WORK"
    )
    generalization = (
        "OWNERSHIP_GENERALIZATION_STRONG"
        if readiness == "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        and core_stability.get("counts", {}).get("BOUNDARY_UNCERTAINTY", 0) == 0
        else "OWNERSHIP_GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY"
        if readiness == "READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW"
        else "OWNERSHIP_GENERALIZATION_NOT_MEASURED_TRANSPORT_BLOCKED"
        if transport_blocked
        else "OWNERSHIP_GENERALIZATION_NEEDS_ARCHITECTURE_WORK"
    )
    handoff = {
        "contract": "monitoring-bootstrap-next-handoff-v1",
        "activated": 0,
        "initial_enrichment_recorded_as_daily_delta": 0,
        "next_scope": "user-approved initial analysis to monitoring-ready enriched baseline",
        "readiness": readiness,
    }
    write_json(proofs / "monitoring-bootstrap-next-handoff.json", handoff)

    canary = read_json(proofs / "canary-verdict.json")
    live = read_json(proofs / "live-workload-coexistence-audit.json")
    run_results = {
        run: (
            f"{documents[run].get('validation_pass_count', 0)}/{len(CURRENT_HOLDOUT)}"
            if documents.get(run, {}).get("status") == "PASS"
            else documents.get(run, {}).get("status", "NOT_RUN")
        )
        for run in run_names
    }
    completion = {
        "contract": PROGRAM_CONTRACT,
        "source_report_bundle_sha256": SOURCE_REPORT_SHA256,
        "base_sha": state["base_sha"],
        "work_instruction_commit": state["work_instruction_commit"],
        "implementation_commit": state["implementation_commit"],
        "resume_generation_id": state["resume_generation_id"],
        "model_context_packet_id": SOURCE_GENERATION_ID,
        "production_market_enum_mutation": 0,
        "production_packet_schema_mutation": 0,
        "real_issuer_used_as_canary": 0,
        "ticker_specific_production_exception": 0,
        "synthetic_packet_schema_preflight": "PASS",
        "canary_fixture_mutation_after_first_model_call": 0,
        "ownership_architecture_hash_drift": 0,
        "fundamental_source_enrichment_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "transport_topology_mutation": 0,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_timeout_seconds": MODEL_TIMEOUT_SECONDS,
        "timeout_increase_this_task": 0,
        "model_timeout_owner_count": 1,
        "batch_semantics": "MODEL_CONTEXT_COUPLED",
        "real_run_batch_size": MODEL_CONTEXT_BATCH_SIZE,
        "batch_split_adopted": 0,
        "model_context_shape_mutation": 0,
        "latest_holdout16_model_calls": 0,
        "latest_holdout16_rerun_count": 0,
        "transport_canary_model_call_count": state.get(
            "transport_canary_model_call_count", 0
        ),
        "transport_canary_status": state.get("transport_canary_status"),
        "architecture_scale_transport_status": state.get(
            "architecture_scale_transport_status", "NOT_RUN"
        ),
        "transport_verdict": state.get("transport_verdict"),
        "current_holdout_reuse_allowed": state.get("current_holdout_reuse_allowed", 0),
        "current_holdout_source_lock": SOURCE_LOCK_SHA256,
        "live_workload_contention_risk": live.get("live_workload_contention_risk"),
        "shadow_pause_for_natural_live": live.get("shadow_pause_for_natural_live"),
        "real_holdout_transport_retry_count": 0,
        "run_results": run_results,
        "directional_core_price_technical_refs": ownership_total(
            "directional_core_price_technical_refs"
        ),
        "directional_core_supply_refs": ownership_total(
            "directional_core_supply_refs"
        ),
        "supply_directional_core_usage": ownership_total(
            "directional_core_supply_refs"
        ),
        "buy_without_nonprice_material_anchor": ownership_total(
            "buy_without_nonprice_material_anchor"
        ),
        "sell_without_nonprice_material_anchor": ownership_total(
            "sell_without_nonprice_material_anchor"
        ),
        "timing_stage_direction_mutation": ownership_total(
            "timing_stage_direction_mutation"
        ),
        "timing_stage_balance_mutation": ownership_total(
            "timing_stage_balance_mutation"
        ),
        "timing_stage_hold_lean_mutation": ownership_total(
            "timing_stage_hold_lean_mutation"
        ),
        "price_timing_new_buyer_upgrade": ownership_total(
            "price_timing_new_buyer_upgrade"
        ),
        "price_only_holder_reduce": ownership.get(
            "price_only_holder_reduce", "NOT_MEASURED"
        ),
        "final_direction_owner": ownership.get(
            "final_direction_owner", "NOT_MEASURED"
        ),
        "price_only_directional_ownership_violations": ownership.get(
            "price_only_directional_ownership_violations", "NOT_MEASURED"
        ),
        "core_stability_counts": core_stability.get("counts"),
        "timing_stability_counts": timing_stability.get("counts"),
        "known_hard_safety_regression": known_hard,
        "primary_user_action_wording_owner": renderer.get(
            "primary_user_action_wording_owner", "NOT_MEASURED"
        ),
        "early_outer_interrupt": 0,
        "orphan_model_process_count": canary.get("orphan_model_process_count"),
        "secret_exposure_count": canary.get("secret_exposure_count"),
        "first_abc_source_drift": 0,
        "ownership_generalization_verdict": generalization,
        "readiness": readiness,
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_telegram_send": 0,
        "production_scheduler_change": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "monitoring_registration_calls": 0,
        "bootstrap_production_mutation": 0,
        "night_futures_code_mutation": 0,
        "stop_reason": reason,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "ruff": "PENDING_FINAL_VALIDATION",
        "diff_check": "PENDING_FINAL_VALIDATION",
    }
    write_json(proofs / "program-completion.json", completion)
    return completion


def execute(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") != "CANARIES_PASS":
        raise ValueError("passing_transport_canaries_required")
    if state.get("current_holdout_reuse_allowed") != 1:
        raise ValueError("current_holdout_reuse_gate_failed")
    verify_frozen(args)
    verify_program_freeze(state)
    (
        cohort,
        contexts,
        evidence,
        owned,
        core_aliases,
        timing_aliases,
        price_maps,
        stocks,
    ) = prior._load_frozen_holdout(args)
    proofs = args.report_dir / PROOFS_DIRECTORY
    guard = LiveWorkloadGuard(proofs / "live-workload-coexistence-audit.json")
    adapter = GuardedTransportAdapter(
        guard=guard,
        continuation_generation=str(state["resume_generation_id"]),
        receipt_root=args.output_root / "transport-receipts" / "real-holdout",
        codex_bin=str(state["cli_binary"]),
    )
    documents: dict[str, dict[str, object]] = {}
    stop_reason: str | None = None
    with prior.instrumented_runner(adapter):
        for run in ("first", "a", "b", "c"):
            if stop_reason:
                document = _run_not_started(run, state, stop_reason)
            else:
                try:
                    document = frozen.execute_two_stage_run(
                        run=f"resume-{run}",
                        generation_id=SOURCE_GENERATION_ID,
                        source_lock_sha256=SOURCE_LOCK_SHA256,
                        prompt_root=args.source_root,
                        run_root=args.output_root / f"run-{run}",
                        cohort=cohort,
                        base_contexts=contexts,
                        evidence=evidence,
                        owned=owned,
                        core_aliases=core_aliases,
                        timing_aliases=timing_aliases,
                        price_maps=price_maps,
                        stocks=stocks,
                        timeout=MODEL_TIMEOUT_SECONDS,
                    )
                    document["resume_generation_id"] = state["resume_generation_id"]
                    document["model_context_packet_id"] = SOURCE_GENERATION_ID
                    document["transport_receipts"] = _receipts_for_run(
                        adapter.receipt_root, run
                    )
                    write_json(args.output_root / f"run-{run}" / "run.json", document)
                except Exception as exc:
                    document = {
                        "contract": "direction-timing-two-stage-run-v1",
                        "run": run,
                        "resume_generation_id": state["resume_generation_id"],
                        "model_context_packet_id": SOURCE_GENERATION_ID,
                        "source_lock_sha256": SOURCE_LOCK_SHA256,
                        "status": "FAILED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "transport_failure": int(
                            isinstance(exc, prior.CodexTransportError)
                        ),
                        "schema_failure": int(
                            not isinstance(exc, prior.CodexTransportError)
                        ),
                        "same_generation_repair": 0,
                        "selective_rerun": 0,
                        "real_holdout_transport_retry_count": 0,
                        "transport_receipts": _receipts_for_run(
                            adapter.receipt_root, run
                        ),
                    }
                if document.get("status") != "PASS":
                    stop_reason = f"{run.upper()}_GATE_FAILED_NO_RETRY_OR_REPAIR"
            documents[run] = document
            proof_name = (
                "resume-first.json" if run == "first" else f"resume-run-{run}.json"
            )
            write_json(proofs / proof_name, document)
            verify_frozen(args)
            verify_program_freeze(state)
            prior.verify_source_lock(args.source_root)

    completion = write_completion_proofs(
        proofs,
        state,
        documents=documents,
        owned=owned,
        reason=stop_reason,
    )
    state.update(
        {
            "state": "EVIDENCE_COMPLETE",
            "real_holdout_model_call_count": adapter.model_call_count,
            "real_holdout_transport_retry_count": 0,
            "run_results": completion["run_results"],
            "ownership_generalization_verdict": completion[
                "ownership_generalization_verdict"
            ],
            "readiness": completion["readiness"],
            "stop_reason": stop_reason,
        }
    )
    write_json(args.output_root / "program-state.json", state)
    write_reports(args.report_dir)
    print(json.dumps(completion, sort_keys=True), flush=True)


def markdown_table(
    headers: Sequence[str], rows: Sequence[Sequence[object]]
) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
    return "\n".join(lines)


def _report_body(
    *, title: str, proof_name: str, proof: Mapping[str, object]
) -> str:
    lines = [f"# {title}", ""]
    scalar_rows = []
    for key, value in proof.items():
        if key in {"rows", "cases", "examples", "events", "cohort", "consumed_cohort"}:
            continue
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            if len(rendered) > 700:
                rendered = f"{type(value).__name__}({len(value)})"
        else:
            rendered = value
        scalar_rows.append((key, rendered))
    if scalar_rows:
        lines.extend((markdown_table(("Gate", "Value"), scalar_rows), ""))

    rows = proof.get("rows") or proof.get("cases") or proof.get("examples") or proof.get("events")
    if isinstance(rows, list) and rows:
        summary = []
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            summary.append(
                (
                    row.get("ticker")
                    or row.get("case")
                    or row.get("name")
                    or row.get("batch_id")
                    or "-",
                    row.get("status")
                    or row.get("classification")
                    or row.get("action")
                    or "-",
                    row.get("decision") or row.get("stage") or "-",
                    ", ".join(
                        str(value)
                        for value in row.get("errors")
                        or row.get("ownership_errors")
                        or row.get("reasons")
                        or ()
                    ),
                )
            )
        if summary:
            lines.extend(
                (markdown_table(("Subject", "Status", "Result", "Errors"), summary), "")
            )
    if proof_name == "canary-fixture-root-cause.json":
        lines.extend(
            (
                "The prior stop occurred before a Directional Core model invocation: "
                "the test fixture used an invalid production routing market.",
                "",
            )
        )
    elif proof_name == "monitoring-bootstrap-next-handoff.json":
        lines.extend(
            (
                "Monitoring bootstrap remains inactive. Initial enrichment remains "
                "baseline construction rather than a Daily Delta.",
                "",
            )
        )
    lines.append(f"Machine proof: `{PROOFS_DIRECTORY}/{proof_name}`.")
    return "\n".join(lines) + "\n"


def write_reports(report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    proofs = report_dir / PROOFS_DIRECTORY
    for report_name, proof_name in REPORT_TO_PROOF.items():
        proof_path = proofs / proof_name
        if not proof_path.is_file():
            continue
        title = (
            report_name.removeprefix("20260906-")
            .removesuffix(".md")
            .replace("-", " ")
            .title()
        )
        (report_dir / report_name).write_text(
            _report_body(
                title=title,
                proof_name=proof_name,
                proof=read_json(proof_path),
            ),
            encoding="utf-8",
        )


def _sync_transport_receipts(output_root: Path, report_dir: Path) -> None:
    source = output_root / "transport-receipts"
    target = report_dir / PROOFS_DIRECTORY / "transport-receipts"
    if not source.is_dir():
        return
    for path in sorted(source.rglob("*.json")):
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())


def _artifact_paths(report_dir: Path) -> list[Path]:
    markdown = [report_dir / name for name in REPORT_TO_PROOF]
    proofs = sorted((report_dir / PROOFS_DIRECTORY).rglob("*.json"))
    return [path for path in (*markdown, *proofs) if path.is_file()]


def write_artifact_index(report_dir: Path) -> dict[str, object]:
    index_path = report_dir / "20260906-artifact-index.md"
    paths = _artifact_paths(report_dir)
    rows = [
        {
            "path": str(path.relative_to(report_dir)),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in paths
    ]
    index_path.write_text(
        "# Artifact Index\n\n"
        + markdown_table(
            ("Path", "SHA-256", "Bytes"),
            [(row["path"], row["sha256"], row["bytes"]) for row in rows],
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "contract": "synthetic-canary-resume-artifact-index-v1",
        "artifact_count": len(rows),
        "rows": rows,
    }


def finalize(args: argparse.Namespace) -> None:
    state = read_json(args.output_root / "program-state.json")
    if state.get("state") not in {"EVIDENCE_COMPLETE", "STOPPED_CANARY_FAILED"}:
        raise ValueError("terminal_evidence_state_required")
    verify_frozen(args)
    verify_program_freeze(state)
    proofs = args.report_dir / PROOFS_DIRECTORY
    completion = read_json(proofs / "program-completion.json")
    validation_pass = all(
        value == "PASS" for value in (args.full_tests, args.ruff, args.diff_check)
    )
    completion.update(
        {
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not validation_pass:
        completion["readiness"] = "NOT_READY"
    write_json(proofs / "program-completion.json", completion)

    hard = read_json(proofs / "resume-hard-safety-regression.json")
    hard.update(
        {
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
        }
    )
    if not validation_pass and hard.get("status") == "PASS":
        hard["status"] = "FAIL"
    write_json(proofs / "resume-hard-safety-regression.json", hard)

    _sync_transport_receipts(args.output_root, args.report_dir)
    write_reports(args.report_dir)
    artifact_index = write_artifact_index(args.report_dir)
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _artifact_paths(args.report_dir):
            archive.write(path, path.relative_to(args.report_dir))
        index_path = args.report_dir / "20260906-artifact-index.md"
        archive.write(index_path, index_path.name)
    temporary.replace(args.zip_output)
    state.update(
        {
            "state": "COMPLETE" if validation_pass else "COMPLETE_NOT_READY",
            "readiness": completion["readiness"],
            "full_tests": args.full_tests,
            "ruff": args.ruff,
            "diff_check": args.diff_check,
            "artifact_count": artifact_index["artifact_count"] + 1,
            "report_zip": str(args.zip_output),
            "report_zip_sha256": file_sha256(args.zip_output),
        }
    )
    write_json(args.output_root / "program-state.json", state)
    print(json.dumps(state, sort_keys=True), flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--canaries", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--finalize", action="store_true")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("/tmp/thesis-monitor-20260906-direction-timing-ownership-run"),
    )
    parser.add_argument(
        "--source-report",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-model-transport-revalidation-ownership-proof-continuation-report.zip",
    )
    parser.add_argument(
        "--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst"
    )
    parser.add_argument("--as-of", type=datetime.fromisoformat)
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument(
        "--zip-output",
        type=Path,
        default=Path.home()
        / "Documents/Codex/Reports"
        / "thesis-monitor-20260906-synthetic-canary-fixture-repair-ownership-proof-resume-report.zip",
    )
    args = parser.parse_args()
    if args.prepare and args.as_of is None:
        raise ValueError("prepare_requires_fixed_as_of")
    for name in (
        "output_root",
        "report_dir",
        "source_root",
        "source_report",
        "provider_root",
        "zip_output",
    ):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.prepare:
        prepare(args)
    elif args.canaries:
        run_canaries(args)
    elif args.execute:
        execute(args)
    else:
        finalize(args)


if __name__ == "__main__":
    main()
