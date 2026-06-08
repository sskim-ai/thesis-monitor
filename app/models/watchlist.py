from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class WatchlistItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True, unique=True)
    company_name: str
    exchange: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

