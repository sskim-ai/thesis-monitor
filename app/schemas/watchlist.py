from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WatchlistItemCreate(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None = None
    notes: str | None = None
    active: bool = True


class WatchlistItemRead(BaseModel):
    id: int
    ticker: str
    company_name: str
    exchange: str | None = None
    notes: str | None = None
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
