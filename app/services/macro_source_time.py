"""Source periods are distinct from query/retrieval/publication timestamps."""

from datetime import date, datetime, timezone
import hashlib
import re

CONTRACT = "macro-source-period-currentness-v1"


def source_period(value, *, daily_required=False):
    token = str(value or "").strip()
    daily = re.fullmatch(r"(\d{4})[-.]?(\d{2})[-.]?(\d{2})", token)
    if daily:
        return date(*(int(v) for v in daily.groups())), "daily"
    monthly = re.fullmatch(r"(\d{4})[-.]?(\d{2})", token)
    if monthly and not daily_required:
        return date(int(monthly[1]), int(monthly[2]), 1), "monthly"
    quarterly = re.fullmatch(r"(\d{4})Q([1-4])", token)
    if quarterly and not daily_required:
        return date(int(quarterly[1]), 3 * (int(quarterly[2]) - 1) + 1, 1), "quarterly"
    if re.fullmatch(r"\d{4}", token) and not daily_required:
        return date(int(token), 1, 1), "annual"
    raise ValueError("source_observation_period_unavailable")


def publication_context(*, provider, series, period, query_as_of, retrieved_at,
                        response_bytes, cadence, latest_verified, published_at=None,
                        daily_required=False):
    if query_as_of.utcoffset() is None or retrieved_at.utcoffset() is None:
        raise ValueError("aware_macro_query_and_retrieval_required")
    observed, precision = source_period(period, daily_required=daily_required)
    if observed > query_as_of.date():
        raise ValueError("future_macro_observation")
    if published_at is not None:
        publication = datetime.fromisoformat(published_at)
        if publication.utcoffset() is None or publication > query_as_of:
            raise ValueError("future_or_naive_macro_publication")
    current = observed == query_as_of.date() and precision == "daily"
    return dict(contract=CONTRACT, provider=provider, series_code=series,
        retrieved_at=retrieved_at.isoformat(), query_as_of=query_as_of.isoformat(),
        observation_period=str(period), observation_date=observed.isoformat(),
        observation_precision=precision, observation_date_basis="source_period_start",
        published_at=published_at, cadence=cadence, latest_available_at_query_time=latest_verified,
        freshness_state=("CURRENT_SESSION_OR_DATE" if current and latest_verified else
                         "LATEST_PUBLISHED_VERIFIED" if latest_verified else "PUBLICATION_CURRENTNESS_UNPROVEN"),
        response_sha256=hashlib.sha256(response_bytes).hexdigest(),
        direction_eligible=False, display_eligible=bool(latest_verified))


def observed_timestamp(context):
    return datetime.fromisoformat(context["observation_date"]).replace(tzinfo=timezone.utc)
