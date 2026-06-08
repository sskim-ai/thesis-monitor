from pydantic import BaseModel, ConfigDict


class CompanyProfile(BaseModel):
    ticker: str
    company_name: str
    exchange: str | None = None
    industry: str | None = None
    sector: str | None = None
    business_units: list[str] = []
    major_revenue_sources: list[str] = []
    major_customers: list[str] = []
    ir_url: str | None = None
    filings_url: str | None = None

    model_config = ConfigDict(from_attributes=True)

