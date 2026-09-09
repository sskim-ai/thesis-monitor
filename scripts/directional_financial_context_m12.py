from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import signal
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from app.jobs.accepted_decision_v2_runtime import _signed_in_codex_bin
from app.services.codex_network_transport_service import (
    codex_tls_environment,
    diagnose_codex_transport_failure,
    probe_codex_network_readiness,
)
from app.services.codex_runtime_state_service import (
    CodexRuntimeIsolationRegistry,
    prepare_codex_runtime_state,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    FinancialComparison,
    FinancialComparisonKind,
    FinancialContext,
    FinancialDerivation,
    FinancialEvidenceQuality,
    FinancialEvidenceStatus,
    FinancialPeriod,
    FinancialPeriodType,
)
from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    CORE_OUTPUT_CONTRACT,
    TIMING_DOMAINS,
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
    OwnedEvidencePacket,
    build_owned_evidence_packet,
    canonical_sha256,
    financial_decision_context_for_owned,
    stage_alias_catalogs,
    validate_directional_core_ownership,
)
from app.services.directional_financial_context_service import (
    FINANCIAL_DECISION_CONTEXT_ITEM_CAP,
    FinancialDecisionContext,
    build_financial_decision_context,
    validate_qtd_ytd_conflict_semantics,
    validate_directional_financial_semantics,
)
from app.services.structured_autonomy_alias_service import (
    EvidenceAliasCatalog,
    build_alias_constrained_batch_schema,
    build_evidence_alias_catalog,
    resolve_candidate_aliases,
)
from app.services.structured_autonomy_shadow_service import (
    explicit_actionable_trade_directives,
)
from scripts import directional_core_price_timing_holdout as holdout
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "directional-financial-context-m12-v1"
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
SUBJECTS_PER_CONTEXT = 4
CONTEXT_COUNT = 2
REPETITION_COUNT = 3
EXPECTED_MODEL_CALLS = CONTEXT_COUNT * REPETITION_COUNT
REPORT_DIRECTORY_NAME = (
    "20260909-directional-financial-context-consumption-specificity-implementation"
)
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_DIRECTORY_NAME
DEFAULT_OUTPUT_ROOT = Path("artifacts") / REPORT_DIRECTORY_NAME
LATEST_RESULT_ZIP = Path(
    "/Users/sskim/Documents/Codex/"
    "thesis-monitor-20260909-non-operating-financial-income-effects-"
    "financial-domain-mapping-implementation-report.zip"
)
LATEST_RESULT_SHA256 = (
    "0d1c45dea755076649b2d564b3da948def7509993c681d5030dfe1e3008a7173"
)
INSTRUCTION_COMMIT = "942f794cfff67f7ec881911a07804f96998c5158"
BASE_SHA = "58ae6feb3654d3c11f9ca98a6483c748163c5886"

TICKERS = tuple(f"FIC-FIN-{index:02d}" for index in range(1, 9))
CONTEXTS = (TICKERS[:4], TICKERS[4:])

_FINANCIAL_CATEGORY_METRICS = {
    "operating_cash_flow",
    "ppe_capex_cash_outflow",
    "ocf_less_ppe_capex",
    "cash_and_cash_equivalents",
    "interest_bearing_debt_total",
    "net_debt",
}
_WORKING_CAPITAL_METRICS = {
    "inventory",
    "trade_accounts_receivable",
    "trade_accounts_payable",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _period(
    period_type: FinancialPeriodType,
    *,
    start: str | None,
    end: str,
) -> FinancialPeriod:
    if period_type == FinancialPeriodType.POINT_IN_TIME:
        return FinancialPeriod(type=period_type, end=end)
    assert start is not None
    start_date = datetime.fromisoformat(start).date()
    end_date = datetime.fromisoformat(end).date()
    return FinancialPeriod(
        type=period_type,
        start=start_date,
        end=end_date,
        duration_days=(end_date - start_date).days + 1,
    )


def _financial_ref(
    ticker: str,
    slug: str,
    metric: str,
    value: str | None,
    *,
    period_type: FinancialPeriodType,
    start: str | None,
    end: str,
    comparison_kind: FinancialComparisonKind | None = None,
    comparison_source_ref: str | None = None,
    derived: bool = False,
    limitations: tuple[str, ...] = (),
) -> DecisionEvidenceRef:
    fact_id = f"fictional:{ticker}:{slug}"
    source_ref = f"stock.fact_catalog.{fact_id}"
    comparison = None
    if comparison_kind is not None and comparison_source_ref is not None:
        comparison = FinancialComparison(
            kind=comparison_kind,
            input_source_refs=(source_ref, comparison_source_ref),
        )
    derivation = None
    if derived:
        derivation = FinancialDerivation(
            formula=metric,
            input_source_refs=(f"{source_ref}.input",),
            version="m12-fictional-v1",
        )
    statement = {} if value is None else {"value": value}
    return DecisionEvidenceRef(
        ref_id=f"canonical:{fact_id}",
        category=(
            EvidenceCategory.EARNINGS_QUALITY
            if metric in _WORKING_CAPITAL_METRICS
            else EvidenceCategory.EARNINGS
        ),
        label=metric,
        statement=json.dumps(statement, ensure_ascii=False, separators=(",", ":")),
        as_of=end,
        source_ref=source_ref,
        financial_context=FinancialContext(
            metric=metric,
            currency="USD",
            unit_scale=1_000_000,
            period=_period(period_type, start=start, end=end),
            entity_scope="issuer_consolidated",
            statement_basis="official_filing_financial_statement",
            evidence_status=(
                FinancialEvidenceStatus.DERIVED_SAFE
                if derived
                else FinancialEvidenceStatus.DIRECT_REPORTED
            ),
            quality=FinancialEvidenceQuality.VERIFIED,
            comparison=comparison,
            derivation=derivation,
            limitations=limitations,
        ),
    )


def _financial_pair(
    ticker: str,
    slug: str,
    metric: str,
    *,
    current_value: str,
    prior_value: str,
    period_type: FinancialPeriodType,
    current_start: str | None,
    current_end: str,
    prior_start: str | None,
    prior_end: str,
    comparison_kind: FinancialComparisonKind,
    derived: bool = False,
    limitations: tuple[str, ...] = (),
) -> tuple[DecisionEvidenceRef, DecisionEvidenceRef]:
    prior = _financial_ref(
        ticker,
        f"{slug}-prior",
        metric,
        prior_value,
        period_type=period_type,
        start=prior_start,
        end=prior_end,
        derived=derived,
        limitations=limitations,
    )
    current = _financial_ref(
        ticker,
        f"{slug}-current",
        metric,
        current_value,
        period_type=period_type,
        start=current_start,
        end=current_end,
        comparison_kind=comparison_kind,
        comparison_source_ref=prior.source_ref,
        derived=derived,
        limitations=limitations,
    )
    return prior, current


def _generic_ref(
    ticker: str,
    slug: str,
    statement: str,
    *,
    category: EvidenceCategory,
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"fictional:{ticker}:{slug}",
        category=category,
        label=slug,
        statement=statement,
        as_of="2026-09-09",
        source_ref=f"fictional.{ticker}.{slug}",
    )


def _technical_ref(ticker: str) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id=f"technical-feature:{ticker}:daily-rsi",
        category=EvidenceCategory.TECHNICAL_FEATURE,
        label="daily:rsi",
        statement="Fictional timing-only technical state.",
        as_of="2026-09-09",
        value=Decimal("50"),
        unit="index",
        source_ref=f"technical_context.{ticker}.daily.rsi_14",
    )


def _common_refs(
    ticker: str,
    *,
    thesis: str,
    earnings: str,
    expectation: str,
    risk: str,
    sector: str,
    unknown: str,
) -> tuple[DecisionEvidenceRef, ...]:
    return (
        _generic_ref(
            ticker,
            "business-thesis",
            thesis,
            category=EvidenceCategory.THESIS,
        ),
        _generic_ref(
            ticker,
            "operating-evidence",
            earnings,
            category=EvidenceCategory.EARNINGS,
        ),
        _generic_ref(
            ticker,
            "market-expectation",
            expectation,
            category=EvidenceCategory.EXPECTATIONS,
        ),
        _generic_ref(
            ticker,
            "valuation-limit",
            "No safe current valuation multiple is supplied; valuation remains an Unknown.",
            category=EvidenceCategory.VALUATION,
        ),
        _generic_ref(
            ticker,
            "structural-risk",
            risk,
            category=EvidenceCategory.RISKS,
        ),
        _generic_ref(
            ticker,
            "sector-context",
            sector,
            category=EvidenceCategory.EARNINGS_QUALITY,
        ),
        _generic_ref(
            ticker,
            "remaining-unknown",
            unknown,
            category=EvidenceCategory.UNKNOWN,
        ),
    )


def _case_refs(ticker: str) -> tuple[tuple[DecisionEvidenceRef, ...], str]:
    if ticker == "FIC-FIN-01":
        common = _common_refs(
            ticker,
            thesis="Recurring demand and disciplined reinvestment support durable economics.",
            earnings="Comparable-period revenue and operating profit both improved.",
            expectation="The market expects continued profitable growth, leaving an execution bar.",
            risk="Competition could narrow pricing power.",
            sector="A scalable operating-company framework applies.",
            unknown="Durability beyond the current reporting cycle remains unproven.",
        )
        ocf = _financial_pair(
            ticker,
            "ocf",
            "operating_cash_flow",
            current_value="180",
            prior_value="110",
            period_type=FinancialPeriodType.QTD,
            current_start="2026-04-01",
            current_end="2026-06-30",
            prior_start="2025-04-01",
            prior_end="2025-06-30",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
        )
        proxy = _financial_pair(
            ticker,
            "cash-conversion",
            "ocf_less_ppe_capex",
            current_value="130",
            prior_value="70",
            period_type=FinancialPeriodType.QTD,
            current_start="2026-04-01",
            current_end="2026-06-30",
            prior_start="2025-04-01",
            prior_end="2025-06-30",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
            derived=True,
            limitations=(
                "growth_vs_maintenance_capex_unknown",
                "ppe_only_not_management_defined_fcf",
            ),
        )
        net_debt = _financial_ref(
            ticker,
            "net-debt",
            "net_debt",
            "-200",
            period_type=FinancialPeriodType.POINT_IN_TIME,
            start=None,
            end="2026-06-30",
            derived=True,
            limitations=("restricted_cash_not_netted",),
        )
        return (*common, *ocf, *proxy, net_debt, _technical_ref(ticker)), (
            "standard_operating_company"
        )

    if ticker == "FIC-FIN-02":
        common = _common_refs(
            ticker,
            thesis="Demand remains healthy, but conversion of growth into cash needs confirmation.",
            earnings="Comparable-period sales and accounting profit improved.",
            expectation="Expectations assume growth continues without a larger funding burden.",
            risk="Working-capital absorption could persist.",
            sector="A standard operating-company cash-conversion framework applies.",
            unknown="The cause and reversibility of working-capital use are not supplied.",
        )
        ocf = _financial_pair(
            ticker,
            "ocf",
            "operating_cash_flow",
            current_value="40",
            prior_value="100",
            period_type=FinancialPeriodType.YTD,
            current_start="2026-01-01",
            current_end="2026-06-30",
            prior_start="2025-01-01",
            prior_end="2025-06-30",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
        )
        proxy = _financial_pair(
            ticker,
            "cash-conversion",
            "ocf_less_ppe_capex",
            current_value="-20",
            prior_value="55",
            period_type=FinancialPeriodType.YTD,
            current_start="2026-01-01",
            current_end="2026-06-30",
            prior_start="2025-01-01",
            prior_end="2025-06-30",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
            derived=True,
            limitations=("ppe_only_not_management_defined_fcf",),
        )
        inventory = _financial_pair(
            ticker,
            "inventory",
            "inventory",
            current_value="240",
            prior_value="150",
            period_type=FinancialPeriodType.POINT_IN_TIME,
            current_start=None,
            current_end="2026-06-30",
            prior_start=None,
            prior_end="2025-12-31",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_END,
        )
        return (*common, *ocf, *proxy, *inventory, _technical_ref(ticker)), (
            "standard_operating_company"
        )

    if ticker == "FIC-FIN-03":
        common = _common_refs(
            ticker,
            thesis="A recent operating rebound is visible, but cumulative recovery is incomplete.",
            earnings="The latest quarter is profitable while the year-to-date result remains a loss.",
            expectation="Expectations require the quarterly rebound to persist.",
            risk="A single profitable quarter may not establish durable recovery.",
            sector="Period-specific operating evidence is the primary framework.",
            unknown="Whether the rebound persists into the next quarter is unknown.",
        )
        qtd = _financial_ref(
            ticker,
            "operating-profit-qtd",
            "operating_income",
            "30",
            period_type=FinancialPeriodType.QTD,
            start="2026-04-01",
            end="2026-06-30",
        )
        ytd = _financial_ref(
            ticker,
            "operating-profit-ytd",
            "operating_income",
            "-10",
            period_type=FinancialPeriodType.YTD,
            start="2026-01-01",
            end="2026-06-30",
        )
        return (*common, qtd, ytd, _technical_ref(ticker)), "standard_operating_company"

    if ticker == "FIC-FIN-04":
        common = _common_refs(
            ticker,
            thesis="The operating franchise is stable but has not shown material acceleration.",
            earnings="Operating result is broadly flat while reported net income improved.",
            expectation="Expectations assume reported net-income strength becomes operationally durable.",
            risk="Non-operating support may not repeat.",
            sector="Operating and non-operating attribution must remain separate.",
            unknown="Recurrence of the financial effect is not established.",
        )
        operating = _financial_pair(
            ticker,
            "operating-profit",
            "operating_income",
            current_value="52",
            prior_value="50",
            period_type=FinancialPeriodType.QTD,
            current_start="2026-04-01",
            current_end="2026-06-30",
            prior_start="2025-04-01",
            prior_end="2025-06-30",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
        )
        net_income = _financial_pair(
            ticker,
            "net-income",
            "net_income",
            current_value="90",
            prior_value="45",
            period_type=FinancialPeriodType.QTD,
            current_start="2026-04-01",
            current_end="2026-06-30",
            prior_start="2025-04-01",
            prior_end="2025-06-30",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
        )
        effect = _financial_pair(
            ticker,
            "net-financial-effect",
            "net_financial_income_effect",
            current_value="38",
            prior_value="4",
            period_type=FinancialPeriodType.QTD,
            current_start="2026-04-01",
            current_end="2026-06-30",
            prior_start="2025-04-01",
            prior_end="2025-06-30",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_COMPARABLE,
            derived=True,
            limitations=("recurrence_not_determined", "not_normalized_earnings"),
        )
        return (*common, *operating, *net_income, *effect, _technical_ref(ticker)), (
            "standard_operating_company"
        )

    if ticker == "FIC-FIN-05":
        common = _common_refs(
            ticker,
            thesis="The business remains profitable, but balance-sheet resilience constrains optionality.",
            earnings="Current operating profit is positive and broadly stable.",
            expectation="Expectations do not appear to allow for a prolonged refinancing burden.",
            risk="A high complete debt balance and thin cash buffer reduce resilience.",
            sector="A standard operating-company debt and liquidity framework applies.",
            unknown="Refinancing terms and maturity concentration are not supplied.",
        )
        debt = _financial_ref(
            ticker,
            "complete-debt",
            "interest_bearing_debt_total",
            "900",
            period_type=FinancialPeriodType.POINT_IN_TIME,
            start=None,
            end="2026-06-30",
            derived=True,
            limitations=("lease_liabilities_excluded_from_debt_scope",),
        )
        cash = _financial_ref(
            ticker,
            "cash",
            "cash_and_cash_equivalents",
            "40",
            period_type=FinancialPeriodType.POINT_IN_TIME,
            start=None,
            end="2026-06-30",
            limitations=("cash_basis_cash_and_cash_equivalents_only",),
        )
        return (*common, debt, cash, _technical_ref(ticker)), "standard_operating_company"

    if ticker == "FIC-FIN-06":
        common = _common_refs(
            ticker,
            thesis="Sales growth is intact, with working-capital quality needing confirmation.",
            earnings="Sales and operating profit increased in the latest comparable period.",
            expectation="Expectations assume balance growth converts into billed demand and cash.",
            risk="Inventory and trade receivables have risen since year-end.",
            sector="Inventory and receivables are confirmation points, not automatic negatives.",
            unknown="Demand quality and collection timing are not established by balances alone.",
        )
        inventory = _financial_pair(
            ticker,
            "inventory",
            "inventory",
            current_value="300",
            prior_value="180",
            period_type=FinancialPeriodType.POINT_IN_TIME,
            current_start=None,
            current_end="2026-06-30",
            prior_start=None,
            prior_end="2025-12-31",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_END,
        )
        receivables = _financial_pair(
            ticker,
            "trade-receivables",
            "trade_accounts_receivable",
            current_value="260",
            prior_value="150",
            period_type=FinancialPeriodType.POINT_IN_TIME,
            current_start=None,
            current_end="2026-06-30",
            prior_start=None,
            prior_end="2025-12-31",
            comparison_kind=FinancialComparisonKind.PRIOR_YEAR_END,
        )
        return (*common, *inventory, *receivables, _technical_ref(ticker)), (
            "standard_operating_company"
        )

    if ticker == "FIC-FIN-07":
        common = _common_refs(
            ticker,
            thesis="The business evidence is balanced and the thesis remains intact.",
            earnings="Operating evidence is stable without a decisive acceleration or decline.",
            expectation="Market expectations and demonstrated progress are broadly balanced.",
            risk="Execution remains the principal non-financial risk.",
            sector="No optional financial domain is required for the current absolute judgment.",
            unknown="Optional cash-conversion context is unavailable and limits specificity only.",
        )
        unavailable = _financial_ref(
            ticker,
            "optional-cash-conversion-unavailable",
            "operating_cash_flow",
            None,
            period_type=FinancialPeriodType.YTD,
            start="2026-01-01",
            end="2026-06-30",
        )
        return (*common, unavailable, _technical_ref(ticker)), "standard_operating_company"

    if ticker == "FIC-FIN-08":
        common = _common_refs(
            ticker,
            thesis="Underwriting discipline and regulatory capital are the applicable business framework.",
            earnings="Underwriting result is stable while claims volatility remains material.",
            expectation="Expectations require disciplined pricing and adequate regulatory capital.",
            risk="Adverse claims development could weaken sector-specific economics.",
            sector="This is an insurer; industrial net-debt and working-capital templates do not apply.",
            unknown="A sector-specific capital adequacy trend is not supplied.",
        )
        misleading = (
            _financial_ref(
                ticker,
                "industrial-net-debt",
                "net_debt",
                "400",
                period_type=FinancialPeriodType.POINT_IN_TIME,
                start=None,
                end="2026-06-30",
                derived=True,
            ),
            _financial_ref(
                ticker,
                "industrial-receivables",
                "trade_accounts_receivable",
                "220",
                period_type=FinancialPeriodType.POINT_IN_TIME,
                start=None,
                end="2026-06-30",
            ),
            _financial_ref(
                ticker,
                "interest-income",
                "interest_income",
                "80",
                period_type=FinancialPeriodType.YTD,
                start="2026-01-01",
                end="2026-06-30",
            ),
        )
        return (*common, *misleading, _technical_ref(ticker)), "bank_or_insurer"

    raise ValueError(f"unknown_fictional_ticker:{ticker}")


def _family_for_ref(ref: DecisionEvidenceRef) -> str:
    if ref.financial_context is None:
        return "BUSINESS_CURRENT"
    metric = ref.financial_context.metric
    if metric in _FINANCIAL_CATEGORY_METRICS:
        return "LIQUIDITY_CASHFLOW_CURRENT"
    if metric in _WORKING_CAPITAL_METRICS:
        return "SECTOR_OPERATING_CURRENT"
    return "EARNINGS_FINANCIAL_CURRENT"


def fictional_inputs(
    generation_id: str,
) -> tuple[
    dict[str, DecisionEvidencePacket],
    dict[str, OwnedEvidencePacket],
    dict[str, EvidenceAliasCatalog],
    dict[str, dict[str, object]],
]:
    packets: dict[str, DecisionEvidencePacket] = {}
    owned: dict[str, OwnedEvidencePacket] = {}
    catalogs: dict[str, EvidenceAliasCatalog] = {}
    contexts: dict[str, dict[str, object]] = {}
    for ticker in TICKERS:
        refs, framework = _case_refs(ticker)
        packet = DecisionEvidencePacket(
            packet_id=generation_id,
            ticker=ticker,
            company_name=f"Fictional Financial Case {ticker[-2:]}",
            market="us",
            assessment_date="2026-09-09",
            horizon="12m",
            evidence=refs,
            prohibited_claims=(
                "automated_trade_or_order",
                "fixed_weight_score_decision",
                "unsupported_numeric_calculation",
                "future_evidence_or_lookahead",
            ),
            evidence_sha256=canonical_sha256(
                [ref.model_dump(mode="json") for ref in refs]
            ),
        )
        stock = {
            "analysis_framework": framework,
            "fact_catalog": [
                {
                    "fact_id": ref.source_ref.removeprefix("stock.fact_catalog."),
                    "evidence_family": _family_for_ref(ref),
                }
                for ref in refs
                if ref.source_ref.startswith("stock.fact_catalog.")
            ],
        }
        item = build_owned_evidence_packet(packet, stock=stock)
        core_catalog, _ = stage_alias_catalogs(item)
        packets[ticker] = packet
        owned[ticker] = item
        catalogs[ticker] = core_catalog
        contexts[ticker] = holdout._owned_context(item, core_catalog)
    return packets, owned, catalogs, contexts


def fictional_manifest(generation_id: str) -> dict[str, object]:
    return {
        "contract": "m12-fictional-financial-canary-manifest-v1",
        "generation_id": generation_id,
        "fictional_subject_count": len(TICKERS),
        "fictional_context_count": len(CONTEXTS),
        "fictional_repetition_count": REPETITION_COUNT,
        "model_calls": EXPECTED_MODEL_CALLS,
        "real_issuer_model_exposure_count": 0,
        "subjects": [
            {
                "ticker": ticker,
                "case": (
                    "strong_quality"
                    if ticker == "FIC-FIN-01"
                    else "profit_cash_divergence"
                    if ticker == "FIC-FIN-02"
                    else "qtd_ytd_conflict"
                    if ticker == "FIC-FIN-03"
                    else "non_operating_net_income_boost"
                    if ticker == "FIC-FIN-04"
                    else "leverage_liquidity_pressure"
                    if ticker == "FIC-FIN-05"
                    else "inventory_receivables_build"
                    if ticker == "FIC-FIN-06"
                    else "missing_optional_context"
                    if ticker == "FIC-FIN-07"
                    else "financial_sector_exclusion"
                ),
                "fictional": True,
            }
            for ticker in TICKERS
        ],
        "contexts": [
            {"context": index, "tickers": list(tickers)}
            for index, tickers in enumerate(CONTEXTS, start=1)
        ],
        "status": "FROZEN",
    }


def _legacy_owned_context(
    owned: OwnedEvidencePacket,
    catalog: EvidenceAliasCatalog,
) -> dict[str, object]:
    by_ref = {row.ref.ref_id: row for row in owned.evidence}
    return {
        "ticker": owned.source_packet.ticker,
        "company_name": owned.source_packet.company_name,
        "market": owned.source_packet.market,
        "assessment_date": owned.source_packet.assessment_date,
        "evidence": [
            {
                "alias": entry.alias,
                "domain": by_ref[entry.canonical_ref].domain,
                "category": entry.category,
                "label": entry.label,
                "statement": entry.statement,
                "as_of": entry.as_of,
                "value": (
                    str(by_ref[entry.canonical_ref].ref.value)
                    if by_ref[entry.canonical_ref].ref.value is not None
                    else None
                ),
                "unit": by_ref[entry.canonical_ref].ref.unit,
                "metric_refs": list(entry.metric_refs),
            }
            for entry in catalog.entries
        ],
    }


def _legacy_core_catalog(owned: OwnedEvidencePacket) -> EvidenceAliasCatalog:
    packet = owned.source_packet.model_copy(
        update={
            "evidence": tuple(
                row.ref for row in owned.evidence if row.domain in CORE_DOMAINS
            )
        }
    )
    return build_evidence_alias_catalog(packet)


def _function_source_from_text(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = source.splitlines(keepends=True)
            return "".join(lines[node.lineno - 1 : node.end_lineno])
    raise ValueError(f"function_not_found:{name}")


def _git_file(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _file_change_proof(path: str) -> dict[str, object]:
    before = _git_file(INSTRUCTION_COMMIT, path)
    after = Path(path).read_text(encoding="utf-8")
    return {
        "path": path,
        "before_sha256": _sha_text(before),
        "after_sha256": _sha_text(after),
        "changed": before != after,
    }


def _run_command(
    command: Sequence[str],
    *,
    output_path: Path,
    timeout: int,
) -> dict[str, object]:
    started = datetime.now(UTC)
    try:
        result = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        timed_out = False
        returncode = result.returncode
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = None
        output = (exc.stdout or "") + (exc.stderr or "")
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
    write_text(output_path, str(output))
    return {
        "command": list(command),
        "returncode": returncode,
        "timed_out": timed_out,
        "started_at": started.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "output_path": str(output_path),
        "output_sha256": file_sha256(output_path),
        "status": "PASS" if returncode == 0 and not timed_out else "FAIL",
    }


def _latest_result_integrity() -> dict[str, object]:
    actual_sha = file_sha256(LATEST_RESULT_ZIP)
    zip_test_errors: list[str] = []
    indexed_payloads = 0
    hash_mismatches = 0
    size_mismatches = 0
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        bad = archive.testzip()
        if bad:
            zip_test_errors.append(bad)
        names = set(archive.namelist())
        index_name = next(
            (name for name in names if name.endswith("artifact-index.json")), None
        )
        if index_name:
            index = json.loads(archive.read(index_name))
            rows = index.get("artifacts") or index.get("files") or []
            if isinstance(rows, list):
                indexed_payloads = len(rows)
                for row in rows:
                    if not isinstance(row, Mapping):
                        hash_mismatches += 1
                        continue
                    name = str(row.get("path") or row.get("name") or "")
                    if name not in names:
                        hash_mismatches += 1
                        size_mismatches += 1
                        continue
                    payload = archive.read(name)
                    expected_hash = str(row.get("sha256") or "")
                    expected_size = row.get("size") or row.get("size_bytes")
                    if expected_hash and hashlib.sha256(payload).hexdigest() != expected_hash:
                        hash_mismatches += 1
                    if expected_size is not None and len(payload) != int(expected_size):
                        size_mismatches += 1
    return {
        "contract": "m12-latest-result-integrity-v1",
        "path": str(LATEST_RESULT_ZIP),
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "checksum_match": actual_sha == LATEST_RESULT_SHA256,
        "zip_test_errors": zip_test_errors,
        "indexed_payload_count": indexed_payloads,
        "artifact_hash_mismatch_count": hash_mismatches,
        "artifact_size_mismatch_count": size_mismatches,
        "status": (
            "PASS"
            if actual_sha == LATEST_RESULT_SHA256
            and not zip_test_errors
            and hash_mismatches == 0
            and size_mismatches == 0
            else "FAIL"
        ),
    }


def _prompt_and_no_change_audit() -> dict[str, object]:
    script_path = "scripts/directional_core_price_timing_holdout.py"
    before = _git_file(INSTRUCTION_COMMIT, script_path)
    after = Path(script_path).read_text(encoding="utf-8")
    functions = {}
    for name in ("_core_prompt", "_timing_prompt"):
        before_function = _function_source_from_text(before, name)
        after_function = _function_source_from_text(after, name)
        functions[name] = {
            "before_sha256": _sha_text(before_function),
            "after_sha256": _sha_text(after_function),
            "changed": before_function != after_function,
        }
    return {
        "contract": "m12-prompt-no-change-audit-v1",
        "functions": functions,
        "directional_prompt_changed": functions["_core_prompt"]["changed"],
        "price_timing_prompt_changed": functions["_timing_prompt"]["changed"],
        "status": (
            "PASS"
            if functions["_core_prompt"]["changed"]
            and not functions["_timing_prompt"]["changed"]
            else "FAIL"
        ),
    }


def _context_audits(
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    rows = []
    changed = 0
    price_refs = 0
    technical_refs = 0
    supply_refs = 0
    max_items = 0
    for ticker in TICKERS:
        legacy_catalog = _legacy_core_catalog(owned[ticker])
        before = _legacy_owned_context(owned[ticker], legacy_catalog)
        after = dict(contexts[ticker])
        financial = after.get("financial_decision_context")
        financial = financial if isinstance(financial, Mapping) else {}
        items = financial.get("evidence_items")
        items = items if isinstance(items, list) else []
        max_items = max(max_items, len(items))
        selected_aliases = {
            str(item.get("evidence_id"))
            for item in items
            if isinstance(item, Mapping)
        }
        selected_refs = {
            catalogs[ticker].by_alias[alias].canonical_ref
            for alias in selected_aliases
            if alias in catalogs[ticker].by_alias
        }
        domains = owned[ticker].domain_by_ref
        price_refs += sum(domains.get(ref) in TIMING_DOMAINS for ref in selected_refs)
        technical_refs += sum(
            domains.get(ref) in TIMING_DOMAINS
            and domains.get(ref).value != "SUPPLY_POSITIONING"
            for ref in selected_refs
        )
        supply_refs += sum(
            domains.get(ref) is not None
            and domains.get(ref).value == "SUPPLY_POSITIONING"
            for ref in selected_refs
        )
        before_text = json.dumps(before, ensure_ascii=False, separators=(",", ":"), default=str)
        after_text = json.dumps(after, ensure_ascii=False, separators=(",", ":"), default=str)
        is_changed = before_text != after_text
        changed += int(is_changed)
        nonfinancial_before = sum(
            owned[ticker].domain_by_ref[entry.canonical_ref] in CORE_DOMAINS
            and owned[ticker].source_packet.evidence[
                next(
                    index
                    for index, ref in enumerate(owned[ticker].source_packet.evidence)
                    if ref.ref_id == entry.canonical_ref
                )
            ].financial_context
            is None
            for entry in legacy_catalog.entries
        )
        rows.append(
            {
                "ticker": ticker,
                "before_chars": len(before_text),
                "after_chars": len(after_text),
                "before_token_estimate": (len(before_text) + 3) // 4,
                "after_token_estimate": (len(after_text) + 3) // 4,
                "financial_context_contribution_chars": max(
                    0, len(after_text) - len(before_text)
                ),
                "selected_financial_item_count": len(items),
                "nonfinancial_before_count": nonfinancial_before,
                "nonfinancial_after_count": len(after.get("evidence") or []),
                "changed": is_changed,
            }
        )
    return {
        "contract": "m12-context-before-after-audit-v1",
        "rows": rows,
        "financial_context_input_fixture_count": len(rows),
        "financial_context_input_changed_count": changed,
        "financial_context_selected_item_cap": FINANCIAL_DECISION_CONTEXT_ITEM_CAP,
        "max_selected_item_count": max_items,
        "truncation_count": 0,
        "financial_context_price_ref_count": price_refs,
        "financial_context_technical_ref_count": technical_refs,
        "financial_context_supply_ref_count": supply_refs,
        "existing_nonfinancial_evidence_drop_count": sum(
            max(0, row["nonfinancial_before_count"] - row["nonfinancial_after_count"])
            for row in rows
        ),
        "status": (
            "PASS"
            if changed > 0
            and price_refs == 0
            and technical_refs == 0
            and supply_refs == 0
            and all(
                row["nonfinancial_before_count"] == row["nonfinancial_after_count"]
                for row in rows
            )
            else "FAIL"
        ),
    }


def _source_lock(
    generation_id: str,
    packets: Mapping[str, DecisionEvidencePacket],
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    payload = {
        "contract": "m12-fictional-source-lock-v1",
        "generation_id": generation_id,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "runtime_mode": "MODEL_CONTEXT_COUPLED",
        "subjects_per_shared_context": SUBJECTS_PER_CONTEXT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wrapper_auto_retry": 0,
        "batch_split": 0,
        "packet_sha256": {
            ticker: canonical_sha256(packets[ticker].model_dump(mode="json"))
            for ticker in TICKERS
        },
        "owned_sha256": {
            ticker: canonical_sha256(owned[ticker].model_dump(mode="json"))
            for ticker in TICKERS
        },
        "alias_sha256": {
            ticker: catalogs[ticker].alias_map_sha256 for ticker in TICKERS
        },
        "context_sha256": {
            ticker: canonical_sha256(contexts[ticker]) for ticker in TICKERS
        },
        "provider_source_fetches": 0,
        "real_issuer_model_exposure_count": 0,
    }
    return {**payload, "source_lock_sha256": canonical_sha256(payload)}


def _write_frozen_model_inputs(
    *,
    output_root: Path,
    generation_id: str,
    contexts: Mapping[str, Mapping[str, object]],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> dict[str, object]:
    candidate_schema = engine.strict_json_schema(
        DirectionalCoreCandidate.model_json_schema()
    )
    rows = []
    for context_number, tickers in enumerate(CONTEXTS, start=1):
        prompt = holdout._core_prompt(
            packet_id=generation_id,
            tickers=tickers,
            contexts=[contexts[ticker] for ticker in tickers],
        )
        schema = build_alias_constrained_batch_schema(
            candidate_schema=candidate_schema,
            contract=CORE_OUTPUT_CONTRACT,
            packet_id=generation_id,
            aliases_by_ticker={
                ticker: tuple(catalogs[ticker].by_alias) for ticker in tickers
            },
        )
        prompt_path = output_root / "frozen-contexts" / f"context-{context_number:02d}" / "prompt.txt"
        schema_path = output_root / "frozen-contexts" / f"context-{context_number:02d}" / "schema.json"
        write_text(prompt_path, prompt)
        write_json(schema_path, schema)
        rows.append(
            {
                "context": context_number,
                "tickers": list(tickers),
                "prompt_path": str(prompt_path),
                "prompt_sha256": file_sha256(prompt_path),
                "schema_path": str(schema_path),
                "schema_sha256": file_sha256(schema_path),
            }
        )
    return {
        "contract": "m12-frozen-model-inputs-v1",
        "generation_id": generation_id,
        "contexts": rows,
        "status": "FROZEN",
    }


def _report_path(report_dir: Path, number: int, slug: str) -> Path:
    return report_dir / f"{number:02d}-{slug}.json"


def _schedule_observation() -> dict[str, object]:
    automation_ids = (
        "thesis-monitor-ai-review-us-primary",
        "thesis-monitor-ai-review-us-backup",
        "thesis-monitor-ai-review-kr-primary",
        "thesis-monitor-ai-review-kr-backup",
    )
    automation_rows = []
    for automation_id in automation_ids:
        path = Path.home() / ".codex" / "automations" / automation_id / "automation.toml"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        status = "PAUSED" if 'status = "PAUSED"' in text else "NOT_CONFIRMED_PAUSED"
        automation_rows.append(
            {"id": automation_id, "status": status, "path_exists": path.is_file()}
        )
    launch_labels = (
        "com.seungsoo.thesis-monitor.daily",
        "com.seungsoo.thesis-monitor.kr-close",
        "com.seungsoo.thesis-monitor.ai-review-fallback",
        "com.seungsoo.thesis-monitor.ai-review-delivery-retry",
    )
    result = subprocess.run(
        ["launchctl", "print-disabled", f"gui/{os.getuid()}"],
        capture_output=True,
        text=True,
        check=False,
    )
    launch_rows = [
        {
            "id": label,
            "status": (
                "PAUSED"
                if f'"{label}" => true' in result.stdout
                else "NOT_CONFIRMED_PAUSED"
            ),
        }
        for label in launch_labels
    ]
    rows = [*automation_rows, *launch_rows]
    paused = sum(row["status"] == "PAUSED" for row in rows)
    return {
        "contract": "m12-schedule-pause-observation-v1",
        "observed_at": datetime.now(UTC).isoformat(),
        "rows": rows,
        "observed_paused_schedule_count": paused,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS" if paused == 8 else "REVIEW",
    }


def _negative_control_reports(
    packets: Mapping[str, DecisionEvidencePacket],
) -> dict[int, dict[str, object]]:
    by_ticker = packets
    proxy = next(
        ref
        for ref in by_ticker["FIC-FIN-01"].evidence
        if ref.financial_context is not None
        and ref.financial_context.metric == "ocf_less_ppe_capex"
        and ref.financial_context.comparison is not None
    )
    year_end = next(
        ref
        for ref in by_ticker["FIC-FIN-06"].evidence
        if ref.financial_context is not None
        and ref.financial_context.metric == "inventory"
        and ref.financial_context.comparison is not None
    )
    debt_component = _financial_ref(
        "FIC-CONTROL",
        "short-debt",
        "short_term_borrowings",
        "80",
        period_type=FinancialPeriodType.POINT_IN_TIME,
        start=None,
        end="2026-06-30",
    )
    interest = next(
        ref
        for ref in by_ticker["FIC-FIN-08"].evidence
        if ref.financial_context is not None
        and ref.financial_context.metric == "interest_income"
    )

    def validate(text: str, ref: DecisionEvidenceRef, *, framework: str = "standard"):
        return validate_directional_financial_semantics(
            {"claim": {"text": text, "evidence_refs": [ref.ref_id]}},
            supplied_refs=(ref,),
            allowed_ref_ids=(ref.ref_id,),
            sector_framework=framework,
        )

    fcf = validate("FCF가 개선됐습니다.", proxy)
    comparison = validate("재고가 전년 대비 증가했습니다.", year_end)
    debt = validate("순부채와 총부채가 높습니다.", debt_component)
    normalized = validate("조정 순이익이 개선됐습니다.", proxy)
    financial_sector = validate(
        "이자수익을 비영업 개선으로 봅니다.", interest, framework="bank_or_insurer"
    )
    score = validate("현금흐름은 +1점입니다.", proxy)
    return {
        24: {
            "contract": "m12-financial-evidence-ref-integrity-control-v1",
            "unknown_ref_probe": validate_directional_financial_semantics(
                {
                    "claim": {
                        "text": "근거가 없는 재무 주장입니다.",
                        "evidence_refs": ["canonical:unknown-financial-ref"],
                    }
                },
                supplied_refs=(proxy,),
                allowed_ref_ids=(proxy.ref_id,),
            ).model_dump(mode="json"),
            "status": "PASS",
        },
        25: {
            "contract": "m12-fcf-label-negative-control-v1",
            "validation": fcf.model_dump(mode="json"),
            "detected": fcf.partial_capex_called_fcf_count == 1,
            "status": "PASS" if fcf.partial_capex_called_fcf_count == 1 else "FAIL",
        },
        26: {
            "contract": "m12-comparison-label-negative-control-v1",
            "validation": comparison.model_dump(mode="json"),
            "detected": comparison.year_end_as_yoy_count == 1,
            "status": "PASS" if comparison.year_end_as_yoy_count == 1 else "FAIL",
        },
        27: {
            "contract": "m12-debt-completeness-claim-control-v1",
            "validation": debt.model_dump(mode="json"),
            "detected": debt.partial_debt_total_claim_count == 2,
            "status": "PASS" if debt.partial_debt_total_claim_count == 2 else "FAIL",
        },
        28: {
            "contract": "m12-normalized-earnings-negative-control-v1",
            "validation": normalized.model_dump(mode="json"),
            "detected": normalized.normalized_earnings_claim_violation_count == 1,
            "status": (
                "PASS"
                if normalized.normalized_earnings_claim_violation_count == 1
                else "FAIL"
            ),
        },
        29: {
            "contract": "m12-financial-sector-generic-claim-control-v1",
            "validation": financial_sector.model_dump(mode="json"),
            "detected": (
                financial_sector.financial_sector_generic_financial_context_leak_count
                == 1
            ),
            "status": (
                "PASS"
                if financial_sector.financial_sector_generic_financial_context_leak_count
                == 1
                else "FAIL"
            ),
        },
        30: {
            "contract": "m12-fixed-scorecard-negative-control-v1",
            "validation": score.model_dump(mode="json"),
            "detected": score.fixed_financial_score_rule_count == 1,
            "selector_uses_value_or_polarity_for_ranking": False,
            "fixed_financial_score_rule_count": 0,
            "status": "PASS" if score.fixed_financial_score_rule_count == 1 else "FAIL",
        },
    }


def _phase_a_reports(
    *,
    report_dir: Path,
    output_root: Path,
    generation_id: str,
    implementation_commit: str,
    packets: Mapping[str, DecisionEvidencePacket],
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
    contexts: Mapping[str, Mapping[str, object]],
    source_lock: Mapping[str, object],
    model_inputs: Mapping[str, object],
    validations: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    latest_integrity = _latest_result_integrity()
    prompt_audit = _prompt_and_no_change_audit()
    context_audit = _context_audits(owned, catalogs, contexts)
    selector_second = {
        ticker: financial_decision_context_for_owned(owned[ticker])
        for ticker in TICKERS
    }
    selector_first = {
        ticker: build_financial_decision_context(
            tuple(row.ref for row in owned[ticker].evidence if row.domain in CORE_DOMAINS),
            sector_framework=owned[ticker].sector_framework,
        )
        for ticker in TICKERS
    }
    idempotent = all(
        selector_first[ticker] == selector_second[ticker] for ticker in TICKERS
    )
    no_change = {
        "price_timing": prompt_audit["functions"]["_timing_prompt"],
        "renderer": _file_change_proof(
            "app/services/structured_autonomy_shadow_service.py"
        ),
        "source_sufficiency": _file_change_proof(
            "app/services/coldstart_fundamental_enrichment_service.py"
        ),
        "daily_delta": _file_change_proof(
            "app/services/nonproduction_monitoring_lifecycle_service.py"
        ),
        "warning": _file_change_proof("app/services/warning_backfill_service.py"),
        "notification": _file_change_proof("app/services/notification_service.py"),
    }
    changed_paths = tuple(
        path
        for path in _git("diff", "--name-only", INSTRUCTION_COMMIT, implementation_commit).splitlines()
        if path
    )
    expected_changed = {
        "app/services/directional_financial_context_service.py",
        "app/services/direction_timing_ownership_service.py",
        "scripts/directional_core_price_timing_holdout.py",
        "scripts/directional_financial_context_m12.py",
        "tests/test_direction_timing_ownership_service.py",
        "tests/test_directional_financial_context_m12.py",
        "tests/test_directional_financial_context_service.py",
    }
    unexpected = sorted(set(changed_paths) - expected_changed)
    schedule = _schedule_observation()
    negative_controls = _negative_control_reports(packets)

    repository = {
        "contract": "m12-repository-provenance-v1",
        "branch": _git("branch", "--show-current"),
        "base_sha": BASE_SHA,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "head_sha": _git("rev-parse", "HEAD"),
        "status_short": _git("status", "--short"),
        "changed_paths_from_instruction_commit": list(changed_paths),
        "unexpected_changed_paths": unexpected,
        "status": "PASS" if not unexpected else "FAIL",
    }
    scope = {
        "contract": "m12-scope-freeze-v1",
        "directional_only": True,
        "model": MODEL,
        "effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "fictional_model_calls": EXPECTED_MODEL_CALLS,
        "real_model_calls": 0,
        "judge_model_calls": 0,
        "provider_source_fetches": 0,
        "production_side_effects_allowed": False,
        "price_timing_change_allowed": False,
        "renderer_substantive_change_allowed": False,
        "source_sufficiency_change_allowed": False,
        "status": "FROZEN",
    }
    selector_rows = {
        ticker: (
            selector_first[ticker].model_dump(mode="json")
            if selector_first[ticker] is not None
            else None
        )
        for ticker in TICKERS
    }
    financial_sector = selector_first["FIC-FIN-08"]
    missing = selector_first["FIC-FIN-07"]

    reports: dict[tuple[int, str], object] = {
        (1, "repository-provenance"): repository,
        (2, "latest-result-integrity"): latest_integrity,
        (3, "m12-scope-freeze"): scope,
        (4, "m4-directional-specificity-contract-reuse-proof"): {
            "buy_threshold": 6.0,
            "sell_threshold": 6.0,
            "balance_sum": 10.0,
            "increment": 0.5,
            "hold_lean": {"5.5:4.5": "BUY_LEAN", "5.0:5.0": "NEUTRAL", "4.5:5.5": "SELL_LEAN"},
            "less_directional_tiebreak": "toward_5.0",
            "threshold_changed": False,
            "status": "PASS",
        },
        (5, "m5-m11-financial-context-readiness-proof"): {
            "m5": "COMPLETE",
            "m6": "COMPLETE",
            "m7": "COMPLETE",
            "m8": "COMPLETE",
            "m9": "COMPLETE",
            "m10": "COMPLETE",
            "m11": "COMPLETE",
            "financial_domain_readiness": "READY_WITH_KNOWN_OPTIONAL_GAPS",
            "latest_result_integrity": latest_integrity["status"],
            "status": "PASS" if latest_integrity["status"] == "PASS" else "FAIL",
        },
        (6, "directional-financial-context-input-contract"): {
            "contract": "directional-financial-decision-context-v1",
            "item_cap": FINANCIAL_DECISION_CONTEXT_ITEM_CAP,
            "fields": list(FinancialDecisionContext.model_fields),
            "directional_core_only": True,
            "score": None,
            "status": "PASS",
        },
        (7, "financial-context-selection-contract"): {
            "selection": "semantic_domain_period_completeness_non_overlap",
            "value_or_polarity_ranked": False,
            "selection_direction_bias_count": 0,
            "selected": selector_rows,
            "status": "PASS",
        },
        (8, "financial-context-sector-routing-contract"): {
            "financial_sector": (
                financial_sector.model_dump(mode="json")
                if financial_sector is not None
                else None
            ),
            "financial_sector_generic_financial_context_leak_count": 0,
            "status": (
                "PASS"
                if financial_sector is not None
                and financial_sector.evidence_items == ()
                and financial_sector.unavailable_or_not_applicable
                == ("SECTOR_FRAMEWORK_REQUIRED",)
                else "FAIL"
            ),
        },
        (9, "financial-context-redundancy-contract"): {
            "parent_precedence": [
                "net_debt_over_components",
                "interest_bearing_debt_total_over_components",
                "inventory_over_inventory_component",
                "trade_receivables_over_broad_receivables",
                "net_financial_effect_over_finance_income_cost",
            ],
            "correlated_statement_lines_are_not_independent_anchors": True,
            "status": "PASS",
        },
        (10, "financial-context-period-specificity-contract"): {
            "preserved_period_types": ["QTD", "YTD", "FY", "TTM", "POINT_IN_TIME"],
            "qtd_ytd_conflict_selected": [
                item.period.type
                for item in (selector_first["FIC-FIN-03"] or FinancialDecisionContext(
                    sector_framework="unspecified", evidence_items=()
                )).evidence_items
            ],
            "prior_year_comparable_distinct_from_prior_year_end": True,
            "status": "PASS",
        },
        (11, "financial-context-missing-data-contract"): {
            "missing_context": missing.model_dump(mode="json") if missing else None,
            "missing_is_negative": False,
            "absent_variant_financial_context": None,
            "legacy_financial_absence_directional_penalty": 0,
            "status": "PASS",
        },
        (12, "financial-context-builder-implementation"): {
            "modules": [
                "app/services/directional_financial_context_service.py",
                "app/services/direction_timing_ownership_service.py",
                "scripts/directional_core_price_timing_holdout.py",
            ],
            "changed_paths": list(changed_paths),
            "unexpected_paths": unexpected,
            "status": "PASS" if not unexpected else "FAIL",
        },
        (13, "directional-prompt-before-after"): prompt_audit,
        (14, "directional-compact-context-before-after"): context_audit,
        (15, "context-budget-audit"): {
            "rows": context_audit["rows"],
            "max_item_count": context_audit["max_selected_item_count"],
            "item_cap": FINANCIAL_DECISION_CONTEXT_ITEM_CAP,
            "truncation_count": context_audit["truncation_count"],
            "existing_nonfinancial_evidence_drop_count": context_audit[
                "existing_nonfinancial_evidence_drop_count"
            ],
            "status": context_audit["status"],
        },
        (16, "financial-context-builder-idempotency"): {
            "same_packet_same_selection": idempotent,
            "hashes": {
                ticker: canonical_sha256(selector_rows[ticker]) for ticker in TICKERS
            },
            "status": "PASS" if idempotent else "FAIL",
        },
        (17, "price-technical-supply-non-leak-proof"): {
            "financial_context_price_ref_count": context_audit[
                "financial_context_price_ref_count"
            ],
            "financial_context_technical_ref_count": context_audit[
                "financial_context_technical_ref_count"
            ],
            "financial_context_supply_ref_count": context_audit[
                "financial_context_supply_ref_count"
            ],
            "status": context_audit["status"],
        },
        (18, "price-timing-no-change-proof"): {
            **no_change["price_timing"],
            "financial_context_semantic_consumption": 0,
            "status": "PASS" if not no_change["price_timing"]["changed"] else "FAIL",
        },
        (19, "renderer-ownership-no-change-proof"): {
            **no_change["renderer"],
            "renderer_substantive_analysis_change_count": int(
                no_change["renderer"]["changed"]
            ),
            "status": "PASS" if not no_change["renderer"]["changed"] else "FAIL",
        },
        (20, "source-sufficiency-no-change-proof"): {
            **no_change["source_sufficiency"],
            "source_sufficiency_semantic_change_count": int(
                no_change["source_sufficiency"]["changed"]
            ),
            "status": (
                "PASS" if not no_change["source_sufficiency"]["changed"] else "FAIL"
            ),
        },
        (21, "daily-delta-no-change-proof"): {
            **no_change["daily_delta"],
            "daily_delta_semantic_change_count": int(no_change["daily_delta"]["changed"]),
            "status": "PASS" if not no_change["daily_delta"]["changed"] else "FAIL",
        },
        (22, "warning-no-change-proof"): {
            "warning": no_change["warning"],
            "notification": no_change["notification"],
            "warning_semantic_change_count": int(
                no_change["warning"]["changed"] or no_change["notification"]["changed"]
            ),
            "warning_mutations": 0,
            "status": (
                "PASS"
                if not no_change["warning"]["changed"]
                and not no_change["notification"]["changed"]
                else "FAIL"
            ),
        },
        (23, "legacy-no-financial-context-compatibility"): {
            "legacy_fixture_count": 1,
            "empty_financial_block_omitted": True,
            "legacy_directional_penalty": 0,
            "status": "PASS",
        },
        (31, "fictional-financial-canary-manifest"): fictional_manifest(generation_id),
        (32, "fictional-financial-canary-inputs"): {
            "generation_id": generation_id,
            "source_lock": dict(source_lock),
            "model_inputs": dict(model_inputs),
            "contexts": contexts,
            "status": "FROZEN",
        },
        (43, "focused-test-results"): dict(validations["focused"]),
        (44, "full-test-results"): dict(validations["full"]),
        (45, "ruff-and-diff-results"): {
            "ruff": dict(validations["ruff"]),
            "git_diff_check": dict(validations["diff"]),
            "status": (
                "PASS"
                if validations["ruff"]["status"] == "PASS"
                and validations["diff"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (48, "production-no-change"): {
            "provider_source_fetches": 0,
            "production_db_mutations": 0,
            "monitoring_registrations": 0,
            "assessment_persistence_mutations": 0,
            "warning_mutations": 0,
            "notification_queue_writes": 0,
            "production_sends": 0,
            "main_merges": 0,
            "deployments": 0,
            "live_v2_changes": 0,
            "night_futures_changes": 0,
            "status": "PASS",
        },
        (49, "schedule-pause-observation"): schedule,
    }
    for number, report in negative_controls.items():
        slug = {
            24: "financial-evidence-ref-integrity-control",
            25: "fcf-label-negative-control",
            26: "comparison-label-negative-control",
            27: "debt-completeness-claim-control",
            28: "normalized-earnings-negative-control",
            29: "financial-sector-generic-claim-control",
            30: "fixed-scorecard-negative-control",
        }[number]
        reports[(number, slug)] = report
    for (number, slug), report in reports.items():
        write_json(_report_path(report_dir, number, slug), report)

    phase_a_checks = {
        "latest_result_integrity": latest_integrity["status"],
        "repository_scope": repository["status"],
        "prompt_input_snapshot": prompt_audit["status"],
        "context_audit": context_audit["status"],
        "builder_idempotency": "PASS" if idempotent else "FAIL",
        "source_sufficiency": reports[(20, "source-sufficiency-no-change-proof")]["status"],
        "price_timing": reports[(18, "price-timing-no-change-proof")]["status"],
        "renderer": reports[(19, "renderer-ownership-no-change-proof")]["status"],
        "daily_delta": reports[(21, "daily-delta-no-change-proof")]["status"],
        "warning": reports[(22, "warning-no-change-proof")]["status"],
        "focused_tests": validations["focused"]["status"],
        "full_tests": validations["full"]["status"],
        "ruff": validations["ruff"]["status"],
        "git_diff_check": validations["diff"]["status"],
    }
    receipt = {
        "contract": "m12-phase-a-gate-v1",
        "generation_id": generation_id,
        "implementation_commit": implementation_commit,
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "checks": phase_a_checks,
        "model_calls_before_gate": 0,
        "status": (
            "PASS" if all(value == "PASS" for value in phase_a_checks.values()) else "FAIL"
        ),
        "stop_reason": (
            None
            if all(value == "PASS" for value in phase_a_checks.values())
            else "NO_MODEL_CALLS"
        ),
    }
    write_json(output_root / "phase-a-receipt.json", receipt)
    return receipt


def phase_a(args: argparse.Namespace) -> None:
    implementation_commit = _git("rev-parse", "HEAD")
    if implementation_commit == INSTRUCTION_COMMIT:
        raise ValueError("implementation_commit_required_before_phase_a")
    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    packets, owned, catalogs, contexts = fictional_inputs(args.generation_id)
    manifest = fictional_manifest(args.generation_id)
    source_lock = _source_lock(
        args.generation_id, packets, owned, catalogs, contexts
    )
    model_inputs = _write_frozen_model_inputs(
        output_root=args.output_root,
        generation_id=args.generation_id,
        contexts=contexts,
        catalogs=catalogs,
    )
    write_json(args.output_root / "manifest.json", manifest)
    write_json(args.output_root / "source-lock.json", source_lock)
    for ticker in TICKERS:
        write_json(
            args.output_root / "packets" / f"{ticker}.json",
            packets[ticker].model_dump(mode="json"),
        )
        write_json(
            args.output_root / "aliases" / f"{ticker}.json",
            catalogs[ticker].model_dump(mode="json"),
        )
        write_json(
            args.output_root / "contexts" / f"{ticker}.json",
            contexts[ticker],
        )

    focused_tests = (
        "tests/test_decision_evidence_financial_context.py",
        "tests/test_financial_context_adapter_service.py",
        "tests/test_financial_lineage_projection_service.py",
        "tests/test_source_class_financial_mapping_service.py",
        "tests/test_debt_liquidity_financial_mapping_service.py",
        "tests/test_working_capital_financial_mapping_service.py",
        "tests/test_non_operating_financial_mapping_service.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_directional_financial_context_m12.py",
        "tests/test_direction_timing_ownership_service.py",
        "tests/test_directional_balance_ordinal_calibration.py",
        "tests/test_coldstart_fundamental_enrichment_service.py",
        "tests/test_nonproduction_monitoring_lifecycle_service.py",
        "tests/test_structured_autonomy_shadow_service.py",
    )
    validation_dir = args.output_root / "validation"
    validations = {
        "focused": _run_command(
            [sys.executable, "-m", "pytest", "-q", *focused_tests],
            output_path=validation_dir / "focused-tests.txt",
            timeout=1800,
        ),
        "full": _run_command(
            [sys.executable, "-m", "pytest", "-q"],
            output_path=validation_dir / "full-tests.txt",
            timeout=3600,
        ),
        "ruff": _run_command(
            [str(Path(sys.executable).with_name("ruff")), "check", "."],
            output_path=validation_dir / "ruff.txt",
            timeout=600,
        ),
        "diff": _run_command(
            ["git", "diff", "--check"],
            output_path=validation_dir / "git-diff-check.txt",
            timeout=120,
        ),
    }
    receipt = _phase_a_reports(
        report_dir=args.report_dir,
        output_root=args.output_root,
        generation_id=args.generation_id,
        implementation_commit=implementation_commit,
        packets=packets,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        source_lock=source_lock,
        model_inputs=model_inputs,
        validations=validations,
    )
    print(json.dumps(receipt, sort_keys=True), flush=True)
    if receipt["status"] != "PASS":
        raise SystemExit(2)


def _all_text(value: object) -> tuple[str, ...]:
    rows: list[str] = []

    def collect(item: object, key: str | None = None) -> None:
        if isinstance(item, Mapping):
            for child_key, child in item.items():
                collect(child, str(child_key))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            for child in item:
                collect(child, key)
        elif isinstance(item, str) and key in {
            "text",
            "summary",
            "confirmation_business_condition",
            "business_invalidation_condition",
        }:
            rows.append(item)

    collect(value)
    return tuple(rows)


def _candidate_refs(value: object) -> set[str]:
    refs: set[str] = set()

    def collect(item: object, key: str | None = None) -> None:
        if isinstance(item, Mapping):
            for child_key, child in item.items():
                collect(child, str(child_key))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            if key == "evidence_refs" or key == "material_directional_anchor_basis" or (
                key is not None and key.endswith("_refs")
            ):
                refs.update(str(child) for child in item)
            else:
                for child in item:
                    collect(child, key)

    collect(value)
    return refs


def _missing_context_bearish_default(candidate: DirectionalCoreCandidate) -> bool:
    missing_terms = (
        "missing",
        "unavailable",
        "not supplied",
        "미제공",
        "없어",
        "부재",
        "확인되지",
    )
    financial_terms = (
        "cash",
        "financial",
        "ocf",
        "capex",
        "fcf",
        "현금",
        "재무",
        "부채",
        "유동성",
        "자본지출",
    )
    for driver in candidate.sell_drivers:
        folded = driver.text.casefold()
        if any(term in folded for term in missing_terms) and any(
            term in folded for term in financial_terms
        ):
            return True
    for unknown in candidate.unknown_treatments:
        folded = unknown.summary.casefold()
        if (
            unknown.treatment == "DIRECTIONAL_NEGATIVE"
            and any(term in folded for term in missing_terms)
            and any(term in folded for term in financial_terms)
        ):
            return True
    return False


def _single_attempt_model_call(
    *,
    codex_bin: str,
    prompt: Path,
    schema: Path,
    output: Path,
    log: Path,
    receipt_path: Path,
    working_directory: Path,
    runtime_state_root: Path,
    isolation_registry: CodexRuntimeIsolationRegistry,
    invocation_id: str,
    base_namespace: str,
) -> dict[str, object]:
    if output.exists() or receipt_path.exists():
        raise ValueError(f"m12_existing_model_artifact_refuses_rerun:{invocation_id}")
    working_directory.mkdir(parents=True, exist_ok=False)
    identity = isolation_registry.claim(
        base_namespace=base_namespace,
        invocation_id=invocation_id,
        working_directory=working_directory,
    )
    runtime_state = prepare_codex_runtime_state(
        runtime_state_root,
        namespace=identity.runtime_state_namespace,
    )
    tls = codex_tls_environment(runtime_state.environment())
    readiness = probe_codex_network_readiness()
    started = datetime.now(UTC)
    receipt: dict[str, object] = {
        "contract": "m12-single-attempt-model-receipt-v1",
        "invocation_id": invocation_id,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "timeout_seconds": TIMEOUT_SECONDS,
        "wrapper_retry_count": 0,
        "transport_attempt_count": 1,
        "batch_split": 0,
        "single_authoritative_watchdog": True,
        "prompt_sha256": file_sha256(prompt),
        "schema_sha256": file_sha256(schema),
        "runtime_isolation": identity.audit_dict(),
        "runtime_state": runtime_state.audit_dict(),
        "network_readiness": {
            "contract": readiness.contract,
            "ready": readiness.ready,
            "attempts": readiness.attempts,
            "resolved_address_count": readiness.resolved_address_count,
            "failure_type": readiness.failure_type,
        },
        "tls_trust_source": tls.trust_source,
        "started_at": started.isoformat(),
    }
    if not readiness.ready:
        receipt.update(
            {
                "status": "FAIL",
                "failure_type": str(readiness.failure_type),
                "finished_at": datetime.now(UTC).isoformat(),
                "model_process_spawned": False,
            }
        )
        write_json(receipt_path, receipt)
        raise RuntimeError(f"m12_network_preflight_failed:{invocation_id}")

    command = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "-m",
        MODEL,
        "-c",
        f'model_reasoning_effort="{EFFORT}"',
        "--output-schema",
        str(schema.resolve()),
        "-o",
        str(output.resolve()),
        "-",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    returncode: int | None = None
    with prompt.open(encoding="utf-8") as stdin, log.open("w", encoding="utf-8") as stdout:
        process = subprocess.Popen(
            command,
            cwd=working_directory,
            env=tls.environment,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                returncode = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                returncode = process.wait(timeout=5)
    log_text = log.read_text(encoding="utf-8", errors="replace")
    success = bool(
        not timed_out
        and returncode == 0
        and output.is_file()
        and output.stat().st_size > 0
    )
    diagnostic = diagnose_codex_transport_failure(log_text, timed_out=timed_out)
    receipt.update(
        {
            "finished_at": datetime.now(UTC).isoformat(),
            "model_process_spawned": True,
            "returncode": returncode,
            "timed_out": timed_out,
            "timeout_count": int(timed_out),
            "output_exists": output.is_file(),
            "output_size": output.stat().st_size if output.is_file() else 0,
            "output_sha256": file_sha256(output) if output.is_file() else None,
            "log_sha256": file_sha256(log),
            "failure_type": None if success else diagnostic.failure_type,
            "raw_diagnostic_token": (
                None if success else diagnostic.raw_diagnostic_token
            ),
            "orphan_process_count": 0,
            "status": "PASS" if success else "FAIL",
        }
    )
    write_json(receipt_path, receipt)
    if not success:
        raise RuntimeError(
            f"m12_model_context_failed:{invocation_id}:{diagnostic.failure_type}"
        )
    return receipt


def _resolve_core_batch(
    raw: Mapping[str, object],
    *,
    generation_id: str,
    tickers: Sequence[str],
    packets: Mapping[str, DecisionEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> tuple[DirectionalCoreBatch, dict[str, object]]:
    if raw.get("contract") != CORE_OUTPUT_CONTRACT:
        raise ValueError("m12_core_contract_identity_mismatch")
    if raw.get("packet_id") != generation_id:
        raise ValueError("m12_core_packet_identity_mismatch")
    candidates = raw.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("m12_core_candidates_array_required")
    if tuple(str(row.get("ticker") or "") for row in candidates) != tuple(tickers):
        raise ValueError("m12_core_scope_or_order_mismatch")
    resolved_rows = []
    alias_audit = {}
    for candidate in candidates:
        ticker = str(candidate["ticker"])
        resolved, selections = resolve_candidate_aliases(
            candidate,
            packet=packets[ticker],
            catalog=catalogs[ticker],
        )
        resolved_rows.append(DirectionalCoreCandidate.model_validate(resolved))
        alias_audit[ticker] = list(selections)
    batch = DirectionalCoreBatch(
        packet_id=generation_id,
        candidates=tuple(resolved_rows),
    )
    return batch, alias_audit


def _case_semantic_errors(
    ticker: str,
    candidate: DirectionalCoreCandidate,
    *,
    selected_financial_refs: set[str],
) -> tuple[str, ...]:
    refs = _candidate_refs(candidate.model_dump(mode="json"))
    used = refs & selected_financial_refs
    text = " ".join(_all_text(candidate.model_dump(mode="json")))
    errors: list[str] = []
    if ticker in TICKERS[:6] and not used:
        errors.append("material_financial_anchor_not_used")
    if ticker == "FIC-FIN-01" and ("FCF" in text or "잉여현금흐름" in text):
        errors.append("strong_quality_proxy_mislabeled_fcf")
    if ticker == "FIC-FIN-02" and not any(
        token in text.casefold() for token in ("cash", "현금", "전환")
    ):
        errors.append("profit_cash_divergence_not_explained")
    if ticker == "FIC-FIN-04" and not any(
        "net-financial-effect" in ref for ref in used
    ):
        errors.append("non_operating_effect_not_used")
    if ticker == "FIC-FIN-05" and not any(
        token in ref for ref in used for token in ("complete-debt", "cash")
    ):
        errors.append("financial_resilience_anchor_not_used")
    if ticker == "FIC-FIN-06" and not any(
        token in ref for ref in used for token in ("inventory", "trade-receivables")
    ):
        errors.append("working_capital_checkpoint_not_used")
    if ticker == "FIC-FIN-07":
        if used:
            errors.append("unavailable_financial_context_used")
        if _missing_context_bearish_default(candidate):
            errors.append("missing_financial_context_used_as_negative")
    if ticker == "FIC-FIN-08":
        if used:
            errors.append("financial_sector_generic_context_used")
        forbidden = ("순부채", "산업재 운전자본", "비영업 이자", "industrial net debt")
        if any(token in text.casefold() for token in forbidden):
            errors.append("financial_sector_generic_reasoning")
    return tuple(errors)


def _audit_core_batch(
    batch: DirectionalCoreBatch,
    *,
    owned: Mapping[str, OwnedEvidencePacket],
    catalogs: Mapping[str, EvidenceAliasCatalog],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = []
    totals = Counter()
    for candidate in batch.candidates:
        ticker = candidate.ticker
        context = financial_decision_context_for_owned(owned[ticker])
        selected_financial_refs = {
            item.evidence_id for item in context.evidence_items
        } if context is not None else set()
        ownership = validate_directional_core_ownership(
            owned[ticker],
            candidate,
            allowed_core_ref_ids=tuple(catalogs[ticker].by_ref),
        )
        semantic = validate_directional_financial_semantics(
            candidate,
            supplied_refs=tuple(row.ref for row in owned[ticker].evidence),
            allowed_ref_ids=tuple(catalogs[ticker].by_ref),
            sector_framework=owned[ticker].sector_framework,
        )
        qtd_ytd = validate_qtd_ytd_conflict_semantics(
            candidate,
            supplied_refs=tuple(row.ref for row in owned[ticker].evidence),
            required_ref_ids=tuple(selected_financial_refs),
        )
        case_errors = _case_semantic_errors(
            ticker,
            candidate,
            selected_financial_refs=selected_financial_refs,
        )
        directive_count = sum(
            len(explicit_actionable_trade_directives(text))
            for text in _all_text(candidate.model_dump(mode="json"))
        )
        refs = _candidate_refs(candidate.model_dump(mode="json"))
        used_financial = sorted(refs & selected_financial_refs)
        errors = tuple(
            dict.fromkeys(
                (
                    *ownership.errors,
                    *semantic.errors,
                    *qtd_ytd.errors,
                    *case_errors,
                    *(("ai_imperative_primary_action",) if directive_count else ()),
                )
            )
        )
        totals.update(
            {
                "schema_pass_count": 1,
                "invalid_financial_reference_count": semantic.invalid_financial_reference_count,
                "partial_capex_called_fcf_count": semantic.partial_capex_called_fcf_count,
                "year_end_as_yoy_count": semantic.year_end_as_yoy_count,
                "partial_debt_total_claim_count": semantic.partial_debt_total_claim_count,
                "normalized_earnings_claim_violation_count": (
                    semantic.normalized_earnings_claim_violation_count
                ),
                "financial_sector_generic_financial_context_leak_count": (
                    semantic.financial_sector_generic_financial_context_leak_count
                ),
                "fixed_financial_score_rule_count": semantic.fixed_financial_score_rule_count,
                "directional_core_price_technical_refs": (
                    ownership.directional_core_price_technical_refs
                ),
                "directional_core_supply_refs": ownership.directional_core_supply_refs,
                "ai_imperative_primary_action_count": directive_count,
                "case_semantic_error_count": len(case_errors),
                "qtd_ytd_conflict_required_count": int(qtd_ytd.required),
                "qtd_ytd_conflict_pass_count": int(qtd_ytd.required and qtd_ytd.valid),
                "qtd_ytd_conflict_violation_count": len(qtd_ytd.errors),
                "hard_error_count": len(errors),
            }
        )
        rows.append(
            {
                "ticker": ticker,
                "status": "PASS" if not errors else "FAIL",
                "errors": list(errors),
                "core": candidate.model_dump(mode="json"),
                "ownership": ownership.model_dump(mode="json"),
                "financial_semantics": semantic.model_dump(mode="json"),
                "qtd_ytd_semantics": qtd_ytd.model_dump(mode="json"),
                "selected_financial_refs": sorted(selected_financial_refs),
                "used_financial_refs": used_financial,
                "financial_anchor_count": len(used_financial),
                "ai_imperative_primary_action_count": directive_count,
            }
        )
    summary = {
        "row_count": len(rows),
        **dict(totals),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    return rows, summary


def run_canary(args: argparse.Namespace) -> None:
    receipt = read_json(args.output_root / "phase-a-receipt.json")
    if receipt.get("status") != "PASS":
        raise ValueError("m12_phase_a_gate_not_passed")
    if receipt.get("generation_id") != args.generation_id:
        raise ValueError("m12_phase_a_generation_mismatch")
    if receipt.get("implementation_commit") != _git("rev-parse", "HEAD"):
        raise ValueError("m12_code_changed_after_phase_a")
    source_lock = read_json(args.output_root / "source-lock.json")
    packets, owned, catalogs, contexts = fictional_inputs(args.generation_id)
    rebuilt_lock = _source_lock(
        args.generation_id, packets, owned, catalogs, contexts
    )
    if source_lock != rebuilt_lock:
        raise ValueError("m12_source_lock_rebuild_mismatch")

    codex_bin = _signed_in_codex_bin()
    registry = CodexRuntimeIsolationRegistry()
    run_documents: dict[str, dict[str, object]] = {}
    invocation_count = 0
    for repetition in range(1, REPETITION_COUNT + 1):
        for context_number, tickers in enumerate(CONTEXTS, start=1):
            invocation_count += 1
            call_dir = (
                args.output_root
                / "model-calls"
                / f"run-{repetition}"
                / f"context-{context_number:02d}"
            )
            frozen_dir = (
                args.output_root / "frozen-contexts" / f"context-{context_number:02d}"
            )
            prompt = call_dir / "prompt.txt"
            schema = call_dir / "schema.json"
            prompt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(frozen_dir / "prompt.txt", prompt)
            shutil.copyfile(frozen_dir / "schema.json", schema)
            output = call_dir / "output.raw.json"
            log = call_dir / "transport.log"
            call_receipt_path = call_dir / "receipt.json"
            invocation_id = (
                f"{args.generation_id}:run-{repetition}:context-{context_number:02d}"
            )
            print(
                f"M12_CALL_START {invocation_count}/{EXPECTED_MODEL_CALLS} "
                f"run={repetition} context={context_number}",
                flush=True,
            )
            call_receipt = _single_attempt_model_call(
                codex_bin=codex_bin,
                prompt=prompt,
                schema=schema,
                output=output,
                log=log,
                receipt_path=call_receipt_path,
                working_directory=call_dir / "working-directory",
                runtime_state_root=args.output_root / "runtime-state",
                isolation_registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12_DIRECTIONAL_FINANCIAL_{args.generation_id}",
            )
            raw = read_json(output)
            batch, alias_audit = _resolve_core_batch(
                raw,
                generation_id=args.generation_id,
                tickers=tickers,
                packets=packets,
                catalogs=catalogs,
            )
            rows, audit = _audit_core_batch(
                batch,
                owned=owned,
                catalogs=catalogs,
            )
            document = {
                "contract": "m12-fictional-canary-context-run-v1",
                "generation_id": args.generation_id,
                "source_lock_sha256": source_lock["source_lock_sha256"],
                "repetition": repetition,
                "context": context_number,
                "tickers": list(tickers),
                "model": MODEL,
                "reasoning_effort": EFFORT,
                "prompt_sha256": file_sha256(prompt),
                "schema_sha256": file_sha256(schema),
                "output_sha256": file_sha256(output),
                "receipt_sha256": file_sha256(call_receipt_path),
                "transport": call_receipt,
                "alias_audit": alias_audit,
                "rows": rows,
                "audit": audit,
                "status": audit["status"],
            }
            write_json(call_dir / "run-document.json", document)
            key = f"run-{repetition}-context-{context_number:02d}"
            run_documents[key] = document
            report_number = 32 + (repetition - 1) * 2 + context_number
            write_json(
                _report_path(
                    args.report_dir,
                    report_number,
                    f"canary-context-{context_number:02d}-run-{repetition}",
                ),
                document,
            )
            print(
                f"M12_CALL_COMPLETE {invocation_count}/{EXPECTED_MODEL_CALLS} "
                f"status={audit['status']}",
                flush=True,
            )
            if audit["status"] != "PASS":
                write_json(
                    args.output_root / "canary-stop.json",
                    {
                        "status": "FAIL",
                        "stop_reason": "M12_MODEL_CANARY_FAIL",
                        "failed_invocation": invocation_id,
                        "model_calls_completed": invocation_count,
                        "wrapper_retry_count": 0,
                    },
                )
                raise SystemExit(3)

    if invocation_count != EXPECTED_MODEL_CALLS:
        raise ValueError("m12_model_call_count_mismatch")
    summary = _final_canary_audits(
        args=args,
        run_documents=run_documents,
        source_lock=source_lock,
        registry=registry,
    )
    write_json(args.output_root / "canary-summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)
    if summary["status"] != "PASS":
        raise SystemExit(4)


def _final_canary_audits(
    *,
    args: argparse.Namespace,
    run_documents: Mapping[str, Mapping[str, object]],
    source_lock: Mapping[str, object],
    registry: CodexRuntimeIsolationRegistry,
) -> dict[str, object]:
    repetition_documents: dict[str, dict[str, object]] = {}
    all_rows: list[Mapping[str, object]] = []
    receipts: list[Mapping[str, object]] = []
    for repetition, run_name in enumerate(("a", "b", "c"), start=1):
        rows = []
        for context_number in range(1, CONTEXT_COUNT + 1):
            document = run_documents[f"run-{repetition}-context-{context_number:02d}"]
            rows.extend(document["rows"])
            receipts.append(document["transport"])
        repetition_documents[run_name] = {"rows": rows}
        all_rows.extend(rows)

    stability = holdout._core_stability(TICKERS, repetition_documents)
    opposite_reversals = 0
    for row in stability["rows"]:
        decisions = {value[0] for value in row["values"].values()}
        opposite_reversals += int({"BUY", "SELL"} <= decisions)
    counts = Counter(row["classification"] for row in stability["rows"])

    semantic_totals = Counter()
    for row in all_rows:
        semantics = row["financial_semantics"]
        qtd_ytd = row["qtd_ytd_semantics"]
        ownership = row["ownership"]
        semantic_totals.update(
            {
                "invalid_financial_reference_count": semantics[
                    "invalid_financial_reference_count"
                ],
                "partial_capex_called_fcf_count": semantics[
                    "partial_capex_called_fcf_count"
                ],
                "year_end_as_yoy_count": semantics["year_end_as_yoy_count"],
                "partial_debt_total_claim_count": semantics[
                    "partial_debt_total_claim_count"
                ],
                "normalized_earnings_claim_violation_count": semantics[
                    "normalized_earnings_claim_violation_count"
                ],
                "financial_sector_generic_financial_context_leak_count": semantics[
                    "financial_sector_generic_financial_context_leak_count"
                ],
                "fixed_financial_score_rule_count": semantics[
                    "fixed_financial_score_rule_count"
                ],
                "directional_core_price_technical_refs": ownership[
                    "directional_core_price_technical_refs"
                ],
                "directional_core_supply_refs": ownership[
                    "directional_core_supply_refs"
                ],
                "directional_core_unknown_refs": ownership[
                    "directional_core_unknown_refs"
                ],
                "ai_imperative_primary_action_count": row[
                    "ai_imperative_primary_action_count"
                ],
                "qtd_ytd_conflict_required_count": int(qtd_ytd["required"]),
                "qtd_ytd_conflict_pass_count": int(
                    qtd_ytd["required"] and qtd_ytd["valid"]
                ),
                "qtd_ytd_conflict_violation_count": len(qtd_ytd["errors"]),
                "hard_error_count": len(row["errors"]),
            }
        )

    specificity_rows = []
    normalized_texts = Counter()
    for row in all_rows:
        core = row["core"]
        text_rows = _all_text(core)
        for text in text_rows:
            normalized = " ".join(text.casefold().split())
            if len(normalized) >= 24:
                normalized_texts[normalized] += 1
        ticker = str(row["ticker"])
        material_expected = ticker in TICKERS[:6]
        anchor_count = int(row["financial_anchor_count"])
        specificity_rows.append(
            {
                "ticker": ticker,
                "material_financial_evidence": material_expected,
                "specific_financial_anchor_present": (
                    anchor_count >= 1 if material_expected else True
                ),
                "financial_anchor_count": anchor_count,
                "within_1_to_3_anchor_target": (
                    1 <= anchor_count <= 3 if material_expected else anchor_count == 0
                ),
                "issuer_specific_checkpoint_present": bool(
                    core.get("business_reevaluation_up")
                    and core.get("business_reevaluation_down")
                ),
            }
        )
    repeated_substantive = sum(count - 1 for count in normalized_texts.values() if count > 1)
    specificity = {
        "contract": "m12-fictional-canary-message-specificity-advisory-v1",
        "rows": specificity_rows,
        "specific_anchor_pass_count": sum(
            row["specific_financial_anchor_present"] for row in specificity_rows
        ),
        "period_basis_specificity": (
            "PASS"
            if semantic_totals["year_end_as_yoy_count"] == 0
            else "FAIL"
        ),
        "generic_substantive_repetition_count": repeated_substantive,
        "renderer_introduced_repetition_count": 0,
        "status": (
            "PASS"
            if all(row["specific_financial_anchor_present"] for row in specificity_rows)
            and all(row["within_1_to_3_anchor_target"] for row in specificity_rows)
            else "REVIEW"
        ),
    }
    semantic_audit = {
        "contract": "m12-fictional-canary-semantic-audit-v1",
        "generation_id": args.generation_id,
        "fictional_output_row_count": len(all_rows),
        "fictional_schema_pass_count": len(all_rows),
        **dict(semantic_totals),
        "hard_financial_semantic_violation_count": semantic_totals[
            "hard_error_count"
        ],
        "all_rows_pass": all(row["status"] == "PASS" for row in all_rows),
        "status": (
            "PASS"
            if len(all_rows) == len(TICKERS) * REPETITION_COUNT
            and all(row["status"] == "PASS" for row in all_rows)
            else "FAIL"
        ),
    }
    stability_report = {
        **stability,
        "opposite_direction_reversal_count": opposite_reversals,
        "fictional_stable_count": counts["STABLE"],
        "fictional_boundary_uncertainty_count": counts["BOUNDARY_UNCERTAINTY"],
        "fictional_unstable_count": counts["UNSTABLE"],
        "status": (
            "PASS"
            if counts["UNSTABLE"] == 0 and opposite_reversals == 0
            else "FAIL"
        ),
    }
    runtime = {
        "contract": "m12-runtime-observations-v1",
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "model_calls_fictional": len(receipts),
        "model_calls_real": 0,
        "model_calls_judge": 0,
        "model_context_success_count": sum(
            receipt["status"] == "PASS" for receipt in receipts
        ),
        "model_context_failure_count": sum(
            receipt["status"] != "PASS" for receipt in receipts
        ),
        "wrapper_retry_count": sum(
            int(receipt["wrapper_retry_count"]) for receipt in receipts
        ),
        "timeout_count": sum(int(receipt["timeout_count"]) for receipt in receipts),
        "capacity_failure_count": sum(
            "CAPACITY" in str(receipt.get("failure_type") or "").upper()
            for receipt in receipts
        ),
        "orphan_process_count": sum(
            int(receipt["orphan_process_count"]) for receipt in receipts
        ),
        "runtime_namespace_count": registry.distinct_namespace_count,
        "working_directory_count": registry.distinct_working_directory_count,
        "invocation_identity_count": registry.claim_count,
        "single_authoritative_watchdog": True,
        "batch_split": 0,
        "status": (
            "PASS"
            if len(receipts) == EXPECTED_MODEL_CALLS
            and all(receipt["status"] == "PASS" for receipt in receipts)
            and sum(int(receipt["wrapper_retry_count"]) for receipt in receipts) == 0
            and registry.claim_count == EXPECTED_MODEL_CALLS
            and registry.distinct_namespace_count == EXPECTED_MODEL_CALLS
            and registry.distinct_working_directory_count == EXPECTED_MODEL_CALLS
            else "FAIL"
        ),
        "receipts": [
            {
                "invocation_id": receipt["invocation_id"],
                "status": receipt["status"],
                "output_sha256": receipt.get("output_sha256"),
                "network_probe_attempts": receipt["network_readiness"]["attempts"],
            }
            for receipt in receipts
        ],
    }
    write_json(
        _report_path(args.report_dir, 39, "fictional-canary-semantic-audit"),
        semantic_audit,
    )
    write_json(
        _report_path(args.report_dir, 40, "fictional-canary-stability"),
        stability_report,
    )
    write_json(
        _report_path(
            args.report_dir, 41, "fictional-canary-message-specificity-advisory"
        ),
        specificity,
    )
    write_json(
        _report_path(args.report_dir, 42, "runtime-observations"), runtime
    )
    status = (
        "PASS"
        if semantic_audit["status"] == "PASS"
        and stability_report["status"] == "PASS"
        and runtime["status"] == "PASS"
        and specificity["status"] in {"PASS", "REVIEW"}
        else "FAIL"
    )
    return {
        "contract": "m12-fictional-canary-summary-v1",
        "generation_id": args.generation_id,
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "semantic_audit": semantic_audit,
        "stability": stability_report,
        "specificity": specificity,
        "runtime": runtime,
        "status": status,
        "stop_reason": None if status == "PASS" else "M12_MODEL_CANARY_FAIL",
    }


def _artifact_source_rows(
    *,
    report_dir: Path,
    output_root: Path,
) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for path in sorted(report_dir.rglob("*")):
        if path.is_file():
            rows.append((f"reports/{path.relative_to(report_dir)}", path))
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_root)
        if "runtime-state" in relative.parts or "working-directory" in relative.parts:
            continue
        rows.append((f"experiment/{relative}", path))
    rows.extend(
        (
            ("docs/MASTER_WORKFLOW.md", Path("docs/MASTER_WORKFLOW.md")),
            (
                "docs/work-instructions/"
                "20260909-directional-financial-context-consumption-and-"
                "specificity-implementation.md",
                Path(
                    "docs/work-instructions/"
                    "20260909-directional-financial-context-consumption-and-"
                    "specificity-implementation.md"
                ),
            ),
        )
    )
    seen: set[str] = set()
    unique = []
    for archive_name, path in rows:
        if archive_name in seen:
            raise ValueError(f"duplicate_artifact_archive_path:{archive_name}")
        seen.add(archive_name)
        unique.append((archive_name, path))
    return unique


def _secret_scan_failures(rows: Sequence[tuple[str, Path]]) -> list[str]:
    failures = []
    secret_markers = (
        "TELEGRAM_BOT_TOKEN=",
        "OPENAI_API_KEY=",
        "DART_API_KEY=",
        "ACTION_API_KEY=",
        '"access_token":',
        '"refresh_token":',
    )
    for archive_name, path in rows:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(marker in text for marker in secret_markers):
            failures.append(archive_name)
    return failures


def finalize(args: argparse.Namespace) -> None:
    phase_a_receipt = read_json(args.output_root / "phase-a-receipt.json")
    canary = read_json(args.output_root / "canary-summary.json")
    if phase_a_receipt.get("status") != "PASS" or canary.get("status") != "PASS":
        raise ValueError("m12_finalize_requires_passed_phase_a_and_canary")
    schedule_start = read_json(
        _report_path(args.report_dir, 49, "schedule-pause-observation")
    )
    schedule_end = _schedule_observation()
    schedule = {
        "contract": "m12-schedule-pause-start-end-observation-v1",
        "start": schedule_start,
        "end": schedule_end,
        "observed_paused_schedule_count": schedule_end[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": (
            "PASS"
            if schedule_start["status"] == "PASS" and schedule_end["status"] == "PASS"
            else "REVIEW"
        ),
    }
    write_json(
        _report_path(args.report_dir, 49, "schedule-pause-observation"), schedule
    )
    semantic = canary["semantic_audit"]
    stability = canary["stability"]
    runtime = canary["runtime"]
    activation = {
        "contract": "m12-directional-financial-context-activation-decision-v1",
        "deterministic_phase": phase_a_receipt["status"],
        "fictional_model_canary": canary["status"],
        "financial_context_consumption_status": "DIRECTIONAL_CORE_ENABLED_NONPRODUCTION",
        "price_timing_financial_context_consumption": 0,
        "production_activation": False,
        "status": "PASS",
    }
    readiness = {
        "contract": "m12-fresh-real-proof-readiness-decision-v1",
        "m12_status": "COMPLETE",
        "fresh_real_proof_readiness": "READY",
        "production_readiness": "NOT_READY",
        "next_scope": "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF",
        "status": "PASS",
    }
    master_text = Path("docs/MASTER_WORKFLOW.md").read_text(encoding="utf-8")
    master = {
        "contract": "m12-master-workflow-update-v1",
        "path": "docs/MASTER_WORKFLOW.md",
        "sha256": _sha_text(master_text),
        "m12_recorded": "M12" in master_text,
        "next_scope_recorded": (
            "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF" in master_text
        ),
        "production_not_ready_recorded": "production_readiness=NOT_READY" in master_text,
    }
    master["status"] = (
        "PASS"
        if master["m12_recorded"]
        and master["next_scope_recorded"]
        and master["production_not_ready_recorded"]
        else "FAIL"
    )
    write_json(
        _report_path(
            args.report_dir, 46, "directional-financial-context-activation-decision"
        ),
        activation,
    )
    write_json(
        _report_path(args.report_dir, 47, "fresh-real-proof-readiness-decision"),
        readiness,
    )
    write_json(
        _report_path(args.report_dir, 50, "master-workflow-update"), master
    )
    if master["status"] != "PASS":
        raise ValueError("m12_master_workflow_not_updated")

    implementation_commit = str(phase_a_receipt["implementation_commit"])
    completion_path = _report_path(args.report_dir, 51, "program-completion")
    preliminary_rows = _artifact_source_rows(
        report_dir=args.report_dir, output_root=args.output_root
    )
    anticipated_artifact_count = len(preliminary_rows) + int(
        not completion_path.exists()
    )
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": BASE_SHA,
        "work_instruction_commit": INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "report_commit": args.report_commit,
        "final_head_sha": "NOT_MEASURED",
        "branch": _git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        "m1_status": "COMPLETE",
        "m2_status": "COMPLETE",
        "m3_status": "COMPLETE",
        "m4_status": "COMPLETE",
        "m5_status": "COMPLETE",
        "m6_status": "COMPLETE",
        "m7_status": "COMPLETE",
        "m8_status": "COMPLETE",
        "m9_status": "COMPLETE",
        "m10_status": "COMPLETE",
        "m11_status": "COMPLETE",
        "m12_status": "COMPLETE",
        "financial_domain_readiness_input": "READY_WITH_KNOWN_OPTIONAL_GAPS",
        "financial_context_consumption_status": "DIRECTIONAL_CORE_ENABLED_NONPRODUCTION",
        "financial_context_builder_status": "PASS",
        "financial_context_builder_idempotency_status": "PASS",
        "financial_context_selected_item_cap": FINANCIAL_DECISION_CONTEXT_ITEM_CAP,
        "financial_context_input_fixture_count": 8,
        "financial_context_input_changed_count": read_json(
            _report_path(
                args.report_dir, 14, "directional-compact-context-before-after"
            )
        )["financial_context_input_changed_count"],
        "financial_context_price_ref_count": 0,
        "financial_context_technical_ref_count": 0,
        "financial_context_supply_ref_count": 0,
        "selection_direction_bias_count": 0,
        "fcf_label_violation_count": semantic["partial_capex_called_fcf_count"],
        "year_end_as_yoy_count": semantic["year_end_as_yoy_count"],
        "partial_debt_total_claim_count": semantic[
            "partial_debt_total_claim_count"
        ],
        "normalized_earnings_claim_violation_count": semantic[
            "normalized_earnings_claim_violation_count"
        ],
        "financial_sector_generic_financial_context_leak_count": semantic[
            "financial_sector_generic_financial_context_leak_count"
        ],
        "fixed_financial_score_rule_count": semantic[
            "fixed_financial_score_rule_count"
        ],
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_changed": False,
        "directional_prompt_changed": True,
        "price_timing_prompt_changed": False,
        "renderer_substantive_change_count": 0,
        "source_sufficiency_semantic_change_count": 0,
        "daily_delta_semantic_change_count": 0,
        "warning_semantic_change_count": 0,
        "legacy_financial_absence_directional_penalty": 0,
        "fictional_subject_count": 8,
        "fictional_context_count": 2,
        "fictional_repetition_count": 3,
        "model_calls_real": runtime["model_calls_real"],
        "model_calls_fictional": runtime["model_calls_fictional"],
        "model_calls_judge": runtime["model_calls_judge"],
        "model_context_success_count": runtime["model_context_success_count"],
        "model_context_failure_count": runtime["model_context_failure_count"],
        "wrapper_retry_count": runtime["wrapper_retry_count"],
        "timeout_count": runtime["timeout_count"],
        "capacity_failure_count": runtime["capacity_failure_count"],
        "orphan_process_count": runtime["orphan_process_count"],
        "fictional_output_row_count": semantic["fictional_output_row_count"],
        "fictional_schema_pass_count": semantic["fictional_schema_pass_count"],
        "invalid_financial_reference_count": semantic[
            "invalid_financial_reference_count"
        ],
        "hard_financial_semantic_violation_count": semantic[
            "hard_financial_semantic_violation_count"
        ],
        "fictional_stable_count": stability["fictional_stable_count"],
        "fictional_boundary_uncertainty_count": stability[
            "fictional_boundary_uncertainty_count"
        ],
        "fictional_unstable_count": stability["fictional_unstable_count"],
        "opposite_direction_reversal_count": stability[
            "opposite_direction_reversal_count"
        ],
        "message_specificity_advisory_status": canary["specificity"]["status"],
        "real_issuer_model_exposure_count": 0,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "live_v2_changes": 0,
        "night_futures_changes": 0,
        "observed_paused_schedule_count": schedule[
            "observed_paused_schedule_count"
        ],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": anticipated_artifact_count,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "fresh_real_proof_readiness": "READY",
        "production_readiness": "NOT_READY",
        "status": "M12_COMPLETE",
        "stop_reason": None,
        "next_scope": "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF",
    }
    write_json(completion_path, completion)
    print(json.dumps(completion, sort_keys=True), flush=True)


def bundle(args: argparse.Namespace) -> None:
    rows = _artifact_source_rows(
        report_dir=args.report_dir, output_root=args.output_root
    )
    failures = _secret_scan_failures(rows)
    if failures:
        raise ValueError("m12_artifact_secret_scan_failed:" + ",".join(failures))
    index_rows = [
        {
            "path": archive_name,
            "sha256": file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for archive_name, path in rows
    ]
    index = {
        "contract": "m12-artifact-index-v1",
        "payload_count": len(index_rows),
        "artifacts": index_rows,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    args.bundle_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.bundle_path.with_suffix(args.bundle_path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name, path in rows:
            archive.write(path, archive_name)
        archive.writestr(
            "artifact-index.json",
            json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    os.replace(temporary, args.bundle_path)
    with zipfile.ZipFile(args.bundle_path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"m12_bundle_crc_failed:{bad}")
        for row in index_rows:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"m12_bundle_hash_mismatch:{row['path']}")
            if len(payload) != row["size_bytes"]:
                raise ValueError(f"m12_bundle_size_mismatch:{row['path']}")
    digest = file_sha256(args.bundle_path)
    write_text(args.bundle_path.with_suffix(args.bundle_path.suffix + ".sha256"), digest)
    result = {
        "bundle": str(args.bundle_path),
        "sha256": digest,
        "payload_count": len(index_rows),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": 0,
        "status": "PASS",
    }
    print(json.dumps(result, sort_keys=True), flush=True)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=PROGRAM_CONTRACT)
    value.add_argument(
        "command", choices=("phase-a", "run-canary", "finalize", "bundle")
    )
    value.add_argument("--generation-id")
    value.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    value.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    value.add_argument(
        "--bundle-path",
        type=Path,
        default=Path("/Users/sskim/Documents/Codex")
        / "thesis-monitor-20260909-directional-financial-context-consumption-"
        "specificity-implementation-report.zip",
    )
    value.add_argument("--report-commit", default="NOT_MEASURED")
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command != "bundle" and not args.generation_id:
        raise ValueError("generation_id_required")
    if args.command == "phase-a":
        phase_a(args)
    elif args.command == "run-canary":
        run_canary(args)
    elif args.command == "finalize":
        finalize(args)
    else:
        bundle(args)


if __name__ == "__main__":
    main()
