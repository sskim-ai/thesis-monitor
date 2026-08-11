from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.security import ProviderCallTelemetry


def _comparable_time(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def summarize_provider_run(
    rows: list[ProviderCallTelemetry],
    run_started_at: datetime,
) -> dict[str, int | str]:
    started = _comparable_time(run_started_at)
    current = [
        row
        for row in rows
        if row.attempted_at and _comparable_time(row.attempted_at) >= started
    ]
    success_statuses = {"success", "cache_hit", "cached", "partial"}
    skip_statuses = {
        "skipped_not_configured",
        "skipped_not_applicable",
        "skipped_budget_exhausted",
        "unsupported_symbol",
    }
    failures = [row for row in current if row.status not in success_statuses | skip_statuses]
    skips = [row for row in current if row.status in skip_statuses]
    successes = [row for row in current if row.status in success_statuses]
    current_status = (
        failures[-1].status
        if failures
        else successes[-1].status
        if successes
        else skips[-1].status
        if skips
        else "not_attempted"
    )
    return {
        "current_run_attempts": len(current),
        "current_run_successes": len(successes),
        "current_run_failures": len(failures),
        "current_run_skips": len(skips),
        "current_run_status": current_status,
        "lifetime_successes": sum(row.success_count for row in rows),
        "lifetime_failures": sum(row.failure_count for row in rows),
        "lifetime_skips": sum(row.skip_count for row in rows),
    }


class ProviderTelemetryService:
    def record(
        self,
        session: Session,
        *,
        provider: str,
        endpoint: str,
        ticker: str,
        started_at: datetime,
        status: str,
        error_type: str | None = None,
        error_code: str | None = None,
        error_reason: str | None = None,
        issuer_type: str = "unknown",
        skip_reason: str | None = None,
    ) -> ProviderCallTelemetry:
        finished_at = datetime.now(timezone.utc)
        row = session.exec(
            select(ProviderCallTelemetry).where(
                ProviderCallTelemetry.provider == provider,
                ProviderCallTelemetry.endpoint == endpoint,
                ProviderCallTelemetry.ticker == ticker.upper(),
            )
        ).first()
        if row is None:
            row = ProviderCallTelemetry(
                provider=provider,
                endpoint=endpoint,
                ticker=ticker.upper(),
            )
        row.attempted_at = started_at
        row.finished_at = finished_at
        row.status = status
        row.issuer_type = issuer_type
        row.latency_ms = max(0.0, (finished_at - started_at).total_seconds() * 1000)
        if status in {"success", "cache_hit", "cached", "partial"}:
            row.success_count += 1
            row.last_success_at = finished_at
            row.error_type = error_type if status == "partial" else None
            row.error_code = error_code if status == "partial" else None
            row.error_reason = error_reason if status == "partial" else None
            row.skip_reason = None
        elif status in {
            "skipped_not_configured",
            "skipped_not_applicable",
            "skipped_budget_exhausted",
            "unsupported_symbol",
        }:
            row.skip_count += 1
            row.skip_reason = skip_reason or error_reason or status
            row.error_type = None
            row.error_code = None
            row.error_reason = None
        else:
            row.failure_count += 1
            row.last_failure_at = finished_at
            row.error_type = error_type
            row.error_code = error_code
            row.error_reason = error_reason
            row.skip_reason = None
        session.add(row)
        session.flush()
        return row
