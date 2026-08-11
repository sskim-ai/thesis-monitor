from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.security import ProviderCallTelemetry


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
        row.latency_ms = max(0.0, (finished_at - started_at).total_seconds() * 1000)
        if status in {"success", "cached", "partial"}:
            row.success_count += 1
            row.last_success_at = finished_at
            row.error_type = error_type if status == "partial" else None
            row.error_code = error_code if status == "partial" else None
            row.error_reason = error_reason if status == "partial" else None
        else:
            row.failure_count += 1
            row.last_failure_at = finished_at
            row.error_type = error_type
            row.error_code = error_code
            row.error_reason = error_reason
        session.add(row)
        session.flush()
        return row
