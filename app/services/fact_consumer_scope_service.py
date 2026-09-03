from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum


CONTRACT_VERSION = "packet-fact-consumer-scope-v1"
EXCLUSION_REASON = "NOT_IN_CONSUMER_SCOPE"


class FactConsumer(StrEnum):
    STOCK_V2 = "STOCK_V2"
    DAILY_REVIEW = "DAILY_REVIEW"
    MARKET_RENDERER = "MARKET_RENDERER"
    ARCHIVE_ONLY = "ARCHIVE_ONLY"
    NIGHT_FUTURES_MODULE = "NIGHT_FUTURES_MODULE"


NIGHT_FUTURES_CONSUMER_SCOPES = (
    FactConsumer.ARCHIVE_ONLY,
    FactConsumer.NIGHT_FUTURES_MODULE,
)
MARKET_CONTEXT_CONSUMER_SCOPES = (
    FactConsumer.DAILY_REVIEW,
    FactConsumer.MARKET_RENDERER,
)
STOCK_CONTEXT_CONSUMER_SCOPES = (
    FactConsumer.STOCK_V2,
    FactConsumer.DAILY_REVIEW,
)

_FACT_TYPE_SCOPE_CONTRACT: dict[str, tuple[FactConsumer, ...]] = {
    "night_futures": NIGHT_FUTURES_CONSUMER_SCOPES,
    "night_futures_timeframe": NIGHT_FUTURES_CONSUMER_SCOPES,
}


def _normalized_scopes(value: object) -> tuple[FactConsumer, ...] | None:
    if not isinstance(value, (list, tuple)):
        return None
    scopes: list[FactConsumer] = []
    for item in value:
        try:
            scope = FactConsumer(str(item))
        except ValueError:
            continue
        if scope not in scopes:
            scopes.append(scope)
    return tuple(scopes) if scopes else None


def fact_consumer_scopes(fact: Mapping[str, object]) -> tuple[FactConsumer, ...] | None:
    explicit = _normalized_scopes(fact.get("consumer_scopes"))
    if explicit is not None:
        return explicit
    return _FACT_TYPE_SCOPE_CONTRACT.get(str(fact.get("fact_type") or ""))


def fact_consumer_scope_source(fact: Mapping[str, object]) -> str:
    if _normalized_scopes(fact.get("consumer_scopes")) is not None:
        return "FACT_METADATA"
    if str(fact.get("fact_type") or "") in _FACT_TYPE_SCOPE_CONTRACT:
        return "FACT_TYPE_CONTRACT"
    return "LEGACY_UNCLASSIFIED_STRICT"


def with_fact_consumer_scopes(
    fact: Mapping[str, object],
    scopes: Sequence[FactConsumer | str],
    *,
    user_visible: bool | None = None,
) -> dict[str, object]:
    normalized = _normalized_scopes(tuple(str(scope) for scope in scopes))
    if normalized is None:
        raise ValueError("fact_consumer_scopes_empty")
    result = dict(fact)
    result["consumer_scope_contract"] = CONTRACT_VERSION
    result["consumer_scopes"] = [scope.value for scope in normalized]
    if user_visible is not None:
        result["user_visible"] = user_visible
    return result


def with_added_fact_consumer_scope(
    fact: Mapping[str, object],
    scope: FactConsumer,
) -> dict[str, object]:
    current = list(fact_consumer_scopes(fact) or ())
    if scope not in current:
        current.append(scope)
    return with_fact_consumer_scopes(
        fact,
        current,
        user_visible=(
            fact.get("user_visible") if isinstance(fact.get("user_visible"), bool) else None
        ),
    )


def fact_is_in_consumer_scope(
    fact: Mapping[str, object],
    consumer: FactConsumer,
    *,
    default_scopes: Sequence[FactConsumer | str] | None = None,
) -> bool:
    scopes = fact_consumer_scopes(fact)
    if scopes is None and default_scopes is not None:
        scopes = _normalized_scopes(tuple(str(scope) for scope in default_scopes))
    if scopes is None:
        return True
    return consumer in scopes


def project_fact_catalog_for_consumer(
    facts: Sequence[Mapping[str, object]],
    consumer: FactConsumer,
    *,
    default_scopes: Sequence[FactConsumer | str] | None = None,
) -> list[dict[str, object]]:
    return [
        dict(fact)
        for fact in facts
        if fact_is_in_consumer_scope(fact, consumer, default_scopes=default_scopes)
    ]

