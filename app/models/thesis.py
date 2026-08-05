from datetime import date, datetime, timezone

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


class InvestmentThesis(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ticker", "version"),)

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    version: int = Field(index=True)
    core_thesis: str = Field(sa_column=Column(Text))
    time_horizon: str | None = None
    strengthen_signals: str = Field(default="[]", sa_column=Column(Text))
    weaken_signals: str = Field(default="[]", sa_column=Column(Text))
    invalidation_signals: str = Field(default="[]", sa_column=Column(Text))
    status: str = Field(default="active", index=True)
    source: str = "custom_gpt"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThesisAssessment(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ticker", "assessment_date"),)

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    thesis_version: int
    assessment_date: date = Field(index=True)
    status: str = Field(index=True)
    score: int = 0
    confidence: float = 0.0
    summary: str = Field(sa_column=Column(Text))
    new_buyer_view: str = Field(sa_column=Column(Text))
    holder_view: str = Field(sa_column=Column(Text))
    price_view: str = Field(sa_column=Column(Text))
    risk_level: str
    evidence: str = Field(default="[]", sa_column=Column(Text))
    price_context: str = Field(default="{}", sa_column=Column(Text))
    thesis_snapshot: str = Field(default="{}", sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MonitorRun(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("run_date", "run_type"),)

    id: int | None = Field(default=None, primary_key=True)
    run_date: date = Field(index=True)
    run_type: str = Field(default="daily")
    status: str = Field(default="running", index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    ticker_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    details: str = Field(default="{}", sa_column=Column(Text))


class NotificationDelivery(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("ticker", "assessment_date", "channel"),)

    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    assessment_date: date = Field(index=True)
    channel: str = Field(default="kakao_self")
    status: str = Field(default="pending", index=True)
    payload: str = Field(sa_column=Column(Text))
    attempt_count: int = 0
    last_error: str | None = Field(default=None, sa_column=Column(Text))
    sent_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
