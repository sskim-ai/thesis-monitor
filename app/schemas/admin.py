from pydantic import BaseModel


class ReclassifyEventsResponse(BaseModel):
    ticker: str | None = None
    provider: str | None = None
    dry_run: bool
    scanned_count: int
    changed_count: int
    updated_count: int
