from datetime import date, timedelta
import json

from sqlmodel import Session, select

from app.models.event import CanonicalIssue, Event
from app.models.financial import (
    CapitalReturnHistory,
    DividendHistory,
    FinancialSnapshot,
    HistoricalValuationObservation,
)
from app.models.security import (
    ConsensusEstimate,
    ProviderResponseCache,
    SecurityMaster,
    ShareCountObservation,
)
from app.models.watchlist import WatchlistItem
from app.schemas.thesis import DataCoverage, ValuationSnapshot
from app.services.event_identity import (
    event_has_valid_document_identity,
    event_is_eligible_for_current_analysis,
)
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.financial_validation import financial_snapshot_is_usable
from app.config import get_settings


def _issuer_type(item: WatchlistItem | None, events: list[Event]) -> str:
    if item and item.issuer_type:
        return item.issuer_type
    if item and (item.exchange or "").upper() == "KRX":
        return "krx"
    if any("filed 20-f" in event.title.lower() or "filed 6-k" in event.title.lower() for event in events):
        return "foreign_private_issuer"
    return "domestic_us"


def _coverage(value: bool, partial: bool = False) -> str:
    return "partial" if partial else "full" if value else "unavailable"


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


class DataCoverageService:
    def build(
        self,
        session: Session,
        ticker: str,
        snapshot: ValuationSnapshot | None = None,
    ) -> DataCoverage:
        item = session.exec(select(WatchlistItem).where(WatchlistItem.ticker == ticker)).first()
        all_rows = list(session.exec(select(FinancialSnapshot).where(FinancialSnapshot.ticker == ticker)).all())
        rows = [row for row in all_rows if financial_snapshot_is_usable(row)]
        all_events = list(session.exec(select(Event).where(Event.ticker == ticker)).all())
        quarantined_events = [
            event
            for event in all_events
            if not event_has_valid_document_identity(event)
        ]
        rejected_events = [
            event for event in all_events if event.identity_status.startswith("rejected")
        ]
        events = [
            event
            for event in all_events
            if event_is_eligible_for_current_analysis(event)
        ]
        dividends = list(session.exec(select(DividendHistory).where(DividendHistory.ticker == ticker)).all())
        issues = list(session.exec(select(CanonicalIssue).where(CanonicalIssue.ticker == ticker)).all())
        security = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == ticker)
        ).first()
        estimates = list(
            session.exec(
                select(ConsensusEstimate).where(ConsensusEstimate.ticker == ticker)
            ).all()
        )
        share_observations = list(
            session.exec(
                select(ShareCountObservation).where(
                    ShareCountObservation.ticker == ticker
                )
            ).all()
        )
        capital_returns = list(
            session.exec(
                select(CapitalReturnHistory).where(
                    CapitalReturnHistory.ticker == ticker,
                    CapitalReturnHistory.return_type == "buyback",
                )
            ).all()
        )
        foreign_cache = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == "sec_edgar",
                ProviderResponseCache.ticker == ticker,
                ProviderResponseCache.data_type == "foreign_6k_exhibits",
            )
        ).first()
        history = list(
            session.exec(
                select(HistoricalValuationObservation).where(
                    HistoricalValuationObservation.ticker == ticker
                )
            ).all()
        )
        issuer_type = _issuer_type(item, events)
        freshness = FinancialFreshnessService().assess(session, ticker)
        reasons: list[str] = []
        if not rows:
            reasons.append("provider_not_supported")
        if freshness.refresh_required:
            reasons.append(freshness.reason_code or "stale_data")
        elif freshness.status == "refresh_due":
            reasons.append("reporting_cadence_exceeded")
        history_years = (
            (max(row.observation_date for row in history) - min(row.observation_date for row in history)).days / 365.25
            if len(history) > 1 else 0.0
        )
        if item and item.created_at.date() < date.today().replace(year=max(1, date.today().year - 5)) and history_years < 3:
            reasons.append("insufficient_history")
        if issuer_type in {"adr", "foreign_private_issuer"}:
            if (item is None or item.adr_ratio is None) and (
                security is None or security.adr_ratio is None
            ):
                reasons.append("missing_adr_ratio")
        valuation_status = "unavailable"
        valuation_confidence = 0.0
        if snapshot is not None:
            valuation_status = snapshot.quality
            valuation_confidence = max(
                snapshot.trailing_valuation_confidence,
                snapshot.forward_valuation_confidence,
            )
        price_status = "fresh" if snapshot and snapshot.current_price is not None else "unavailable"
        financial_status = "full" if len(rows) >= 8 else "partial" if rows else "unavailable"
        full_rows = [row for row in rows if row.snapshot_type == "full_statement"]
        preliminary_rows = [
            row for row in rows if row.snapshot_type == "preliminary_earnings"
        ]
        all_full_rows = [row for row in all_rows if row.snapshot_type == "full_statement"]
        all_preliminary_rows = [
            row for row in all_rows if row.snapshot_type == "preliminary_earnings"
        ]
        event_cutoff = date.today() - timedelta(days=get_settings().monitor_lookback_days)
        current_events = [event for event in events if event.date >= event_cutoff]
        current_eligible_validation_failed = any(
            event.event_type != "non_thesis_noise"
            and (
                event.financial_statement_basis_warning
                or event.margin_quality_review
            )
            for event in current_events
        )
        current_official_identity_failure = any(
            event.date >= event_cutoff
            and event.provider in {"opendart", "sec_edgar", "company_ir"}
            and event.event_type != "non_thesis_noise"
            for event in quarantined_events
        )
        event_quality = (
            "validation_failed"
            if current_eligible_validation_failed or current_official_identity_failure
            else "fresh"
        )
        identity_audit_status = (
            "quarantined_history_present"
            if quarantined_events
            else "rejected_candidates_present"
            if rejected_events
            else "clean"
        )
        foreign_status = (
            financial_status if issuer_type in {"adr", "foreign_private_issuer"} else "not_applicable"
        )
        per_share_coverage = (
            "unavailable"
            if issuer_type in {"adr", "foreign_private_issuer"}
            and (item is None or item.adr_ratio is None)
            and (security is None or security.adr_ratio is None)
            else "full"
        )
        try:
            foreign_payload = json.loads(foreign_cache.payload) if foreign_cache else {}
        except json.JSONDecodeError:
            foreign_payload = {}
        foreign_parsing_result = str(
            foreign_payload.get("parsing_result") or "unavailable"
        )
        foreign_filings = foreign_payload.get("filings", [])
        foreign_latest_filing_result = (
            str(
                foreign_payload.get("latest_filing_parse_result")
                or foreign_filings[0].get("parsing_result")
                or "unavailable"
            )
            if isinstance(foreign_filings, list)
            and foreign_filings
            and isinstance(foreign_filings[0], dict)
            else "unavailable"
        )
        any_foreign_statement_parsed = bool(
            foreign_payload.get("any_statement_parsed")
            or foreign_payload.get("parsed_statement")
        )
        latest_foreign_financial_period = foreign_payload.get(
            "latest_financial_statement_period"
        )
        latest_foreign_financial_filing_date = foreign_payload.get(
            "latest_financial_statement_filing_date"
        )
        if issuer_type in {"adr", "foreign_private_issuer"}:
            if foreign_parsing_result == "validation_failed":
                reasons.append("foreign_financial_parsing_failed")
            if foreign_latest_filing_result == "not_financial_exhibit":
                reasons.append("foreign_latest_filing_not_financial")
        filing_discovery = (
            str(foreign_payload.get("filing_discovery_coverage") or foreign_cache.status)
            if foreign_cache and issuer_type in {"adr", "foreign_private_issuer"}
            else foreign_status
        )
        statement_parsing = (
            str(foreign_payload.get("statement_parsing_coverage") or "partial")
            if foreign_cache and foreign_cache.status in {"success", "partial"}
            else financial_status
            if issuer_type in {"adr", "foreign_private_issuer"}
            else "not_applicable"
        )
        historical_quality = "unavailable"
        if snapshot is not None:
            stats = snapshot.historical_pe_statistics or snapshot.historical_pb_statistics
            if stats is not None:
                historical_quality = stats.history_quality
        consensus_quality = "unavailable"
        if snapshot and snapshot.consensus_disagreement:
            consensus_quality = "conflicting"
        elif (
            snapshot
            and snapshot.forward_pe_status == "value"
            and snapshot.forward_pe_source == "consensus_forward"
        ):
            consensus_quality = snapshot.consensus_status or "partial"
            if consensus_quality == "unavailable":
                consensus_quality = "partial"
        elif estimates:
            statuses = {row.coverage_status for row in estimates}
            consensus_quality = (
                "full" if "full" in statuses else "partial" if statuses else "unavailable"
            )
        forward_quality = (
            "fresh"
            if snapshot and snapshot.forward_valuation_confidence >= 0.7
            else "partial"
            if snapshot and snapshot.forward_valuation_confidence > 0
            else "unavailable"
        )
        full_quality = (
            "validation_failed"
            if all_full_rows and not full_rows
            else freshness.full_financial_freshness
            if full_rows
            else "unavailable"
        )
        preliminary_quality = (
            "validation_failed"
            if all_preliminary_rows and (
                not preliminary_rows
                or any(row.financial_statement_basis_warning for row in all_preliminary_rows)
            )
            else freshness.preliminary_financial_freshness
            if preliminary_rows
            else "not_applicable"
        )
        if preliminary_quality == "validation_failed":
            reasons.append("preliminary_validation_failed")
            if any(
                row.period_mapping_validation_failed for row in all_preliminary_rows
            ):
                reasons.append("preliminary_period_mapping_failed")
        preliminary_soft_outliers = {
            outlier
            for row in preliminary_rows
            for outlier in _json_list(row.financial_soft_outliers)
        }
        if preliminary_soft_outliers.intersection(
            {
                "operating_income_exceeds_revenue",
                "net_income_exceeds_revenue",
                "unusually_high_or_low_operating_margin",
                "unusually_high_or_low_net_margin",
            }
        ):
            reasons.append("preliminary_profitability_outlier")
        financial_quality = (
            "refresh_pending"
            if freshness.refresh_required
            else "refresh_due"
            if freshness.status == "refresh_due"
            else "validation_failed"
            if freshness.status == "preliminary_only"
            and preliminary_quality == "validation_failed"
            else "partial"
            if freshness.status == "preliminary_only"
            else financial_status
        )
        component_issues = [
            ("재무 구성", financial_quality),
            ("Consensus", consensus_quality),
            ("Forward Valuation", forward_quality),
        ]
        concerning = [
            f"{label} {quality}"
            for label, quality in component_issues
            if quality
            in {
                "partial",
                "stale",
                "unavailable",
                "conflicting",
                "refresh_pending",
                "refresh_due",
                "validation_failed",
            }
        ]
        overall_quality = "partial" if concerning else "current"
        reason_messages: list[str] = []
        if preliminary_quality == "validation_failed":
            preliminary_warning_text = " ".join(
                row.quality_warnings or "" for row in all_preliminary_rows
            )
            if any(row.period_mapping_validation_failed for row in all_preliminary_rows):
                reason_messages.append(
                    "격리된 잠정실적의 재무기간 종료일이 공시일보다 뒤로 매핑되어 "
                    "현재 재무 context와 Valuation 분모에 사용하지 않았습니다."
                )
            elif (
                "Absolute net income exceeds revenue" in preliminary_warning_text
                or "Operating margin is outside" in preliminary_warning_text
            ):
                reason_messages.append(
                    "잠정실적 원문을 semantic table 기준으로 읽었지만 순이익이 매출을 "
                    "초과하거나 영업이익률이 sanity 범위를 벗어나 숫자 검증에 실패했습니다. "
                    "해당 값은 Valuation 분모에 사용하지 않았습니다."
                )
            else:
                reason_messages.append(
                    "최신 잠정실적의 숫자 검증에 실패해 매출·이익과 Valuation 분모에 "
                    "사용하지 않았습니다."
                )
        if freshness.status == "refresh_due":
            reason_messages.append(
                "정식 재무 보고 주기가 경과해 최신 filing 반영 여부를 확인 중입니다."
            )
        if freshness.full_financial_freshness == "stale":
            reason_messages.append(
                "정식 재무제표가 존재하지만 현재 reporting cadence 기준으로 오래됐습니다."
            )
        if consensus_quality in {"unavailable", "conflicting"}:
            reason_messages.append(f"Consensus 상태는 {consensus_quality}입니다.")
        if foreign_latest_filing_result == "not_financial_exhibit":
            reason_messages.append(
                "최근 foreign filing은 확인됐지만 재무 실적표가 아닌 문서로 판정했습니다."
            )
        if foreign_parsing_result == "validation_failed":
            reason_messages.append(
                "확인된 foreign filing 중 재무표 후보의 자동 구조화·검증이 완료되지 않았습니다."
            )
        overall_reason = (
            " ".join(reason_messages)
            if reason_messages
            else ", ".join(concerning)
            if concerning
            else "핵심 입력 데이터가 현재 기준으로 연결되어 있습니다."
        )
        adjusted_valuation_confidence = valuation_confidence
        if freshness.full_financial_freshness == "stale":
            adjusted_valuation_confidence *= 0.7
        if issuer_type in {"adr", "foreign_private_issuer"} and (
            foreign_latest_filing_result
            in {
                "validation_failed",
                "document_fetch_failed",
                "exhibit_not_found",
                "financial_table_not_found",
                "unsupported_format",
                "unavailable",
            }
            or freshness.status == "foreign_filing_partial"
        ):
            adjusted_valuation_confidence *= 0.7
        return DataCoverage(
            issuer_type=issuer_type,
            financial_coverage_status=financial_status,
            financials=financial_status,
            earnings="fresh" if any(event.event_type in {"guidance_change", "earnings_beat", "earnings_miss"} for event in events) else "partial",
            price=price_status,
            valuation=valuation_status,
            dividend=_coverage(bool(dividends), any(row.quality != "fresh" for row in dividends)),
            capital_actions=_coverage(bool(issues)),
            foreign_filing=foreign_status,
            financial_freshness=freshness.status,
            business_thesis_confidence=0.85 if events or freshness.status == "current" else 0.6,
            valuation_confidence=adjusted_valuation_confidence,
            price_confidence=0.9 if price_status == "fresh" else 0.3,
            macro_impact_confidence=0.75,
            reason_codes=list(dict.fromkeys(reasons)),
            identity_mapping=(security.identity_quality if security else "unavailable"),
            event_relevance=event_quality,
            financial_full=_coverage(bool(full_rows), len(full_rows) < 8),
            financial_preliminary=_coverage(
                bool(preliminary_rows), preliminary_quality == "validation_failed"
            ),
            consensus=consensus_quality,
            shares=_coverage(bool(share_observations) or any(row.common_shares_outstanding for row in rows)),
            buyback=_coverage(bool(capital_returns)),
            historical_valuation=historical_quality,
            forward_valuation=forward_quality,
            filing_discovery_coverage=filing_discovery,
            document_fetch_coverage=(
                str(foreign_payload.get("document_fetch_coverage") or filing_discovery)
                if issuer_type in {"adr", "foreign_private_issuer"}
                else "not_applicable"
            ),
            exhibit_discovery_coverage=(
                str(foreign_payload.get("exhibit_discovery_coverage") or filing_discovery)
                if issuer_type in {"adr", "foreign_private_issuer"}
                else "not_applicable"
            ),
            statement_parsing_coverage=statement_parsing,
            per_share_mapping_coverage=(per_share_coverage if issuer_type in {"adr", "foreign_private_issuer"} else "not_applicable"),
            valuation_coverage=valuation_status,
            price_quality=price_status,
            financial_quality=financial_quality,
            full_financial_availability=freshness.full_financial_availability,
            full_financial_freshness=freshness.full_financial_freshness,
            preliminary_financial_freshness=freshness.preliminary_financial_freshness,
            full_financial_quality=full_quality,
            preliminary_financial_quality=preliminary_quality,
            event_quality=event_quality,
            current_event_quality=event_quality,
            quarantined_event_count=len(quarantined_events),
            rejected_candidate_count=len(rejected_events),
            identity_audit_status=identity_audit_status,
            consensus_quality=consensus_quality,
            historical_valuation_quality=historical_quality,
            forward_valuation_quality=forward_quality,
            share_count_quality=_coverage(
                bool(share_observations)
                or any(row.common_shares_outstanding for row in rows)
            ),
            dividend_quality=_coverage(
                bool(dividends), any(row.quality != "fresh" for row in dividends)
            ),
            foreign_filing_quality=(
                statement_parsing
                if issuer_type in {"adr", "foreign_private_issuer"}
                else "not_applicable"
            ),
            foreign_parsing_result=(
                foreign_parsing_result
                if issuer_type in {"adr", "foreign_private_issuer"}
                else "not_applicable"
            ),
            foreign_latest_filing_result=(
                foreign_latest_filing_result
                if issuer_type in {"adr", "foreign_private_issuer"}
                else "not_applicable"
            ),
            any_foreign_statement_parsed=(
                any_foreign_statement_parsed
                if issuer_type in {"adr", "foreign_private_issuer"}
                else False
            ),
            latest_foreign_filing_parse_result=(
                foreign_latest_filing_result
                if issuer_type in {"adr", "foreign_private_issuer"}
                else "not_applicable"
            ),
            latest_foreign_financial_period=(
                str(latest_foreign_financial_period)
                if latest_foreign_financial_period
                and issuer_type in {"adr", "foreign_private_issuer"}
                else None
            ),
            latest_foreign_financial_filing_date=(
                str(latest_foreign_financial_filing_date)
                if latest_foreign_financial_filing_date
                and issuer_type in {"adr", "foreign_private_issuer"}
                else None
            ),
            overall_data_quality=overall_quality,
            overall_quality_reason=overall_reason,
        )
