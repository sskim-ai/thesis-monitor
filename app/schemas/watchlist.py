from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WatchlistItemCreate(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None = None
    notes: str | None = None


class WatchlistItemRead(BaseModel):
    id: int
    ticker: str
    company_name: str
    exchange: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

