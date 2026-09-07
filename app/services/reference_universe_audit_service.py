from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree

from pydantic import BaseModel, ConfigDict, Field


CONTRACT_VERSION = "canonical-reference-universe-audit-v1"


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class IdentityResolutionStatus(StrEnum):
    RESOLVED = "IDENTITY_RESOLVED"
    UNRESOLVED = "IDENTITY_UNRESOLVED"
    AMBIGUOUS = "IDENTITY_AMBIGUOUS"


class RoutingSupportStatus(StrEnum):
    SUPPORTED = "ROUTING_SUPPORTED"
    CANDIDATE = "ROUTING_CANDIDATE"
    UNSUPPORTED = "ROUTING_UNSUPPORTED"
    NOT_CHECKED = "ROUTING_NOT_CHECKED"


class CanonicalSecurityReference(FrozenModel):
    contract: str = CONTRACT_VERSION
    market: Literal["kr", "us"]
    canonical_security_id: str | None = None
    canonical_issuer_key: str | None = None
    issuer_key_namespace: str | None = None
    display_symbol: str
    provider_symbol: str | None = None
    provider_aliases: tuple[str, ...] = ()
    issuer_name: str | None = None
    security_name: str
    exchange: str
    provider_exchange: str | None = None
    security_type: str
    is_adr: bool = False
    reference_source: str
    reference_row_id: str
    reference_as_of: str | None = None
    reference_retrieved_at: str
    reference_snapshot_sha256: str
    identity_resolution_status: IdentityResolutionStatus
    routing_support_status: RoutingSupportStatus
    eligibility_decision: str
    eligibility_reasons: tuple[str, ...] = ()
    provenance: dict[str, object] = Field(default_factory=dict)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_us_symbol(value: object) -> str:
    return str(value or "").strip().upper().replace(".", "-")


def us_symbol_aliases(value: object) -> tuple[str, ...]:
    raw = str(value or "").strip().upper()
    normalized = normalize_us_symbol(raw)
    aliases = {raw, normalized}
    if "-" in normalized:
        aliases.add(normalized.replace("-", "."))
    return tuple(sorted(alias for alias in aliases if alias))


def load_sec_ticker_reference(path: Path) -> dict[str, tuple[dict[str, object], ...]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("sec_company_tickers_mapping_required")
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for source_row_id, raw in document.items():
        if not isinstance(raw, Mapping):
            continue
        ticker = normalize_us_symbol(raw.get("ticker"))
        cik = raw.get("cik_str")
        title = str(raw.get("title") or "").strip()
        if not ticker or not isinstance(cik, int) or cik <= 0 or not title:
            continue
        grouped[ticker].append(
            {
                "source_row_id": str(source_row_id),
                "ticker": ticker,
                "cik": f"{cik:010d}",
                "title": title,
            }
        )
    return {
        ticker: tuple(
            sorted(rows, key=lambda row: (str(row["cik"]), str(row["source_row_id"])))
        )
        for ticker, rows in grouped.items()
    }


def _reference_as_of(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    footer = next((line for line in reversed(lines) if line.startswith("File Creation Time:")), None)
    if footer is None:
        return None
    value = footer.partition(":")[2].strip()
    try:
        return datetime.strptime(value, "%m%d%Y%H:%M").isoformat()
    except ValueError:
        return value or None


def _pipe_rows(path: Path) -> list[tuple[int, dict[str, str]]]:
    lines = [
        line
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line and not line.startswith("File Creation Time:")
    ]
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|")
    return [(number, dict(row)) for number, row in enumerate(reader, start=2)]


_UNSUPPORTED_NAME_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("warrant", re.compile(r"\bwarrants?\b", re.IGNORECASE)),
    ("right", re.compile(r"\brights?\b", re.IGNORECASE)),
    ("unit", re.compile(r"\bunits?\b", re.IGNORECASE)),
    ("preferred", re.compile(r"\bpreferred\b", re.IGNORECASE)),
    ("debt_or_note", re.compile(r"\b(notes?|bonds?|debentures?)\b", re.IGNORECASE)),
    ("fund_or_trust", re.compile(r"\b(fund|trust)\b", re.IGNORECASE)),
    ("spac", re.compile(r"\b(acquisition corp|blank check)\b", re.IGNORECASE)),
    ("reit", re.compile(r"\b(REIT|real estate investment trust)\b", re.IGNORECASE)),
)


def classify_us_security(
    security_name: str,
    *,
    etf: str,
    test_issue: str,
    nextshares: str = "N",
) -> tuple[str, bool, tuple[str, ...]]:
    reasons: list[str] = []
    if etf.strip().upper() == "Y":
        reasons.append("exchange_traded_fund")
    if test_issue.strip().upper() == "Y":
        reasons.append("test_issue")
    if nextshares.strip().upper() == "Y":
        reasons.append("nextshares")
    for label, pattern in _UNSUPPORTED_NAME_PATTERNS:
        if pattern.search(security_name):
            reasons.append(label)
    lower = security_name.lower()
    is_adr = any(
        token in lower
        for token in (
            "american depositary share",
            "american depositary shares",
            "american depository share",
            "american depository shares",
            " adr",
        )
    )
    supported_description = is_adr or any(
        token in lower
        for token in (
            "common stock",
            "common share",
            "ordinary share",
        )
    )
    if not supported_description:
        reasons.append("unsupported_or_unknown_security_description")
    if reasons:
        security_type = reasons[0]
    elif is_adr:
        security_type = "american_depositary_share"
    elif "ordinary share" in lower:
        security_type = "ordinary_share"
    else:
        security_type = "common_stock"
    return security_type, is_adr, tuple(dict.fromkeys(reasons))


def _sec_identity(
    aliases: Sequence[str],
    sec_rows: Mapping[str, Sequence[Mapping[str, object]]],
) -> tuple[IdentityResolutionStatus, Mapping[str, object] | None, tuple[str, ...]]:
    matches: dict[str, Mapping[str, object]] = {}
    for alias in aliases:
        for row in sec_rows.get(normalize_us_symbol(alias), ()):
            matches[str(row["cik"])] = row
    if not matches:
        return IdentityResolutionStatus.UNRESOLVED, None, ("sec_cik_unresolved",)
    if len(matches) != 1:
        return IdentityResolutionStatus.AMBIGUOUS, None, ("sec_cik_ambiguous",)
    return IdentityResolutionStatus.RESOLVED, next(iter(matches.values())), ()


def load_us_reference_universe(
    *,
    sec_company_tickers: Path,
    nasdaq_listed: Path,
    other_listed: Path,
    retrieved_at: str,
) -> list[CanonicalSecurityReference]:
    sec_rows = load_sec_ticker_reference(sec_company_tickers)
    sec_sha = file_sha256(sec_company_tickers)
    results: list[CanonicalSecurityReference] = []
    sources = (
        (
            "nasdaq_trader_nasdaqlisted",
            nasdaq_listed,
            "Symbol",
            "NASDAQ",
            "ND",
        ),
        (
            "nasdaq_trader_otherlisted",
            other_listed,
            "ACT Symbol",
            None,
            None,
        ),
    )
    exchange_names = {"N": "NYSE", "A": "NYSE_AMERICAN", "P": "NYSE_ARCA", "Z": "BATS", "V": "IEX"}
    provider_exchanges = {"N": "NY", "A": "NA"}
    for source_name, path, symbol_field, fixed_exchange, fixed_provider in sources:
        source_sha = file_sha256(path)
        source_as_of = _reference_as_of(path)
        for line_number, raw in _pipe_rows(path):
            symbol = str(raw.get(symbol_field) or "").strip().upper()
            if not symbol:
                continue
            reference_exchange_code = str(raw.get("Exchange") or "").strip().upper()
            exchange = fixed_exchange or exchange_names.get(
                reference_exchange_code, f"UNSUPPORTED_{reference_exchange_code or 'UNKNOWN'}"
            )
            provider_exchange = fixed_provider or provider_exchanges.get(reference_exchange_code)
            aliases = set(us_symbol_aliases(symbol))
            cqs = str(raw.get("CQS Symbol") or "").strip().upper()
            nasdaq_symbol = str(raw.get("NASDAQ Symbol") or "").strip().upper()
            for alias in (cqs, nasdaq_symbol):
                aliases.update(us_symbol_aliases(alias))
            security_name = str(raw.get("Security Name") or "").strip()
            security_type, is_adr, unsupported = classify_us_security(
                security_name,
                etf=str(raw.get("ETF") or ""),
                test_issue=str(raw.get("Test Issue") or ""),
                nextshares=str(raw.get("NextShares") or "N"),
            )
            identity_status, identity, identity_reasons = _sec_identity(
                sorted(aliases), sec_rows
            )
            reasons = [*unsupported, *identity_reasons]
            if provider_exchange is None:
                reasons.append("provider_exchange_route_not_supported")
            eligible_for_route_check = not reasons
            cik = str(identity["cik"]) if identity is not None else None
            canonical_symbol = normalize_us_symbol(symbol)
            results.append(
                CanonicalSecurityReference(
                    market="us",
                    canonical_security_id=(
                        f"us:{provider_exchange.lower()}:{canonical_symbol}"
                        if provider_exchange is not None
                        else None
                    ),
                    canonical_issuer_key=f"sec:cik:{cik}" if cik else None,
                    issuer_key_namespace="SEC_CIK" if cik else None,
                    display_symbol=symbol,
                    provider_symbol=canonical_symbol if provider_exchange else None,
                    provider_aliases=tuple(sorted(aliases)),
                    issuer_name=str(identity["title"]) if identity is not None else None,
                    security_name=security_name,
                    exchange=exchange,
                    provider_exchange=provider_exchange,
                    security_type=security_type,
                    is_adr=is_adr,
                    reference_source=source_name,
                    reference_row_id=f"{path.name}:{line_number}:{symbol}",
                    reference_as_of=source_as_of,
                    reference_retrieved_at=retrieved_at,
                    reference_snapshot_sha256=canonical_sha256(
                        {"listing_sha256": source_sha, "sec_sha256": sec_sha}
                    ),
                    identity_resolution_status=identity_status,
                    routing_support_status=(
                        RoutingSupportStatus.CANDIDATE
                        if eligible_for_route_check
                        else RoutingSupportStatus.UNSUPPORTED
                    ),
                    eligibility_decision=(
                        "IDENTITY_RESOLVED_ROUTE_CHECK_REQUIRED"
                        if eligible_for_route_check
                        else "QUARANTINED"
                    ),
                    eligibility_reasons=tuple(dict.fromkeys(reasons)),
                    provenance={
                        "listing_snapshot_sha256": source_sha,
                        "sec_snapshot_sha256": sec_sha,
                        "sec_source_row_id": identity.get("source_row_id") if identity else None,
                        "reference_exchange_code": reference_exchange_code or None,
                    },
                )
            )
    return sorted(
        results,
        key=lambda row: (
            row.canonical_security_id or "~",
            row.reference_source,
            row.reference_row_id,
        ),
    )


def load_opendart_stock_identities(path: Path) -> dict[str, dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.upper().endswith("CORPCODE.XML")]
        if len(members) != 1:
            raise ValueError("single_opendart_corpcode_xml_required")
        with archive.open(members[0]) as stream:
            tree = ElementTree.parse(stream)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for element in tree.getroot().findall("list"):
        stock_code = str(element.findtext("stock_code") or "").strip()
        corp_code = str(element.findtext("corp_code") or "").strip()
        corp_name = str(element.findtext("corp_name") or "").strip()
        if len(stock_code) == 6 and stock_code.isdigit() and corp_code and corp_name:
            grouped[stock_code].append(
                {
                    "stock_code": stock_code,
                    "corp_code": corp_code,
                    "corp_name": corp_name,
                    "corp_eng_name": str(element.findtext("corp_eng_name") or "").strip(),
                    "modify_date": str(element.findtext("modify_date") or "").strip(),
                }
            )
    ambiguous = [stock_code for stock_code, rows in grouped.items() if len(rows) != 1]
    if ambiguous:
        raise ValueError(f"ambiguous_opendart_stock_codes:{len(ambiguous)}")
    return {stock_code: rows[0] for stock_code, rows in grouped.items()}


def load_kr_reference_universe(
    *,
    sector_map: Path,
    opendart_corp_code: Path,
    retrieved_at: str,
) -> list[CanonicalSecurityReference]:
    identities = load_opendart_stock_identities(opendart_corp_code)
    sector_sha = file_sha256(sector_map)
    dart_sha = file_sha256(opendart_corp_code)
    results: list[CanonicalSecurityReference] = []
    with sector_map.open(encoding="utf-8-sig", newline="") as stream:
        for line_number, raw in enumerate(csv.DictReader(stream), start=2):
            ticker = str(raw.get("code") or "").strip().zfill(6)
            name = str(raw.get("name") or "").strip()
            exchange = str(raw.get("market") or "").strip().upper()
            sector = str(raw.get("sector") or "").strip()
            industry = str(raw.get("industry") or "").strip()
            if exchange not in {"KOSPI", "KOSDAQ"}:
                continue
            if not ticker.isdigit() or len(ticker) != 6 or not name or not sector or not industry:
                continue
            folded = f"{name} {sector} {industry}".upper()
            if any(token in folded for token in ("ETF", "ETN", "스팩", "리츠", "인버스", "레버리지")):
                continue
            identity = identities.get(ticker)
            if identity is None:
                results.append(
                    CanonicalSecurityReference(
                        market="kr",
                        display_symbol=ticker,
                        security_name=name,
                        exchange=exchange,
                        security_type="common_stock",
                        reference_source="ohlcv_sector_map_plus_opendart_corpcode",
                        reference_row_id=f"{sector_map.name}:{line_number}:{ticker}",
                        reference_retrieved_at=retrieved_at,
                        reference_snapshot_sha256=canonical_sha256(
                            {"sector_map_sha256": sector_sha, "opendart_sha256": dart_sha}
                        ),
                        identity_resolution_status=IdentityResolutionStatus.UNRESOLVED,
                        routing_support_status=RoutingSupportStatus.SUPPORTED,
                        eligibility_decision="QUARANTINED",
                        eligibility_reasons=("opendart_corp_code_unresolved",),
                        provenance={"sector": sector, "industry": industry},
                    )
                )
                continue
            corp_code = identity["corp_code"]
            results.append(
                CanonicalSecurityReference(
                    market="kr",
                    canonical_security_id=f"kr:{exchange.lower()}:{ticker}",
                    canonical_issuer_key=f"opendart:corp:{corp_code}",
                    issuer_key_namespace="OPENDART_CORP_CODE",
                    display_symbol=ticker,
                    provider_symbol=ticker,
                    provider_aliases=(ticker, name),
                    issuer_name=identity["corp_name"],
                    security_name=name,
                    exchange=exchange,
                    provider_exchange=exchange,
                    security_type="common_stock",
                    reference_source="ohlcv_sector_map_plus_opendart_corpcode",
                    reference_row_id=f"{sector_map.name}:{line_number}:{ticker}",
                    reference_as_of=identity.get("modify_date") or None,
                    reference_retrieved_at=retrieved_at,
                    reference_snapshot_sha256=canonical_sha256(
                        {"sector_map_sha256": sector_sha, "opendart_sha256": dart_sha}
                    ),
                    identity_resolution_status=IdentityResolutionStatus.RESOLVED,
                    routing_support_status=RoutingSupportStatus.SUPPORTED,
                    eligibility_decision="ELIGIBLE_SUPPORTED_SECURITY",
                    provenance={
                        "sector_map_sha256": sector_sha,
                        "opendart_sha256": dart_sha,
                        "corp_code": corp_code,
                        "sector": sector,
                        "industry": industry,
                    },
                )
            )
    return sorted(results, key=lambda row: row.display_symbol)


def with_routing_result(
    row: CanonicalSecurityReference,
    *,
    supported: bool,
    reason: str | None = None,
    route_provenance: Mapping[str, object] | None = None,
) -> CanonicalSecurityReference:
    if row.identity_resolution_status != IdentityResolutionStatus.RESOLVED:
        raise ValueError("resolved_identity_required_before_routing_result")
    reasons = tuple(
        dict.fromkeys(
            (
                *row.eligibility_reasons,
                *(() if supported or not reason else (reason,)),
            )
        )
    )
    return row.model_copy(
        update={
            "routing_support_status": (
                RoutingSupportStatus.SUPPORTED
                if supported
                else RoutingSupportStatus.UNSUPPORTED
            ),
            "eligibility_decision": (
                "ELIGIBLE_SUPPORTED_SECURITY" if supported else "QUARANTINED"
            ),
            "eligibility_reasons": reasons,
            "provenance": {**row.provenance, "route": dict(route_provenance or {})},
        }
    )


def validate_us_route_response(
    row: CanonicalSecurityReference,
    *,
    status_code: int,
    payload: Mapping[str, object] | None,
) -> tuple[bool, str, dict[str, object]]:
    if row.market != "us" or row.provider_symbol is None or row.provider_exchange is None:
        raise ValueError("us_provider_route_candidate_required")
    if status_code != 200 or not isinstance(payload, Mapping):
        return False, f"provider_http_{status_code}", {"status_code": status_code}
    resolved = payload.get("resolved_symbol")
    if not isinstance(resolved, Mapping):
        return False, "provider_resolved_symbol_missing", {"status_code": status_code}
    code = normalize_us_symbol(resolved.get("code"))
    market = str(resolved.get("market") or "").strip().upper()
    exchange = str(resolved.get("exchange") or "").strip().upper()
    matched_by = str(resolved.get("matched_by") or "").strip()
    evidence = {
        "status_code": status_code,
        "resolved_code": code,
        "resolved_market": market,
        "resolved_exchange": exchange,
        "matched_by": matched_by,
    }
    if code != normalize_us_symbol(row.provider_symbol):
        return False, "provider_route_symbol_mismatch", evidence
    if market not in {"US", "USA"}:
        return False, "provider_route_market_mismatch", evidence
    if exchange != row.provider_exchange.upper():
        return False, "provider_route_exchange_mismatch", evidence
    if matched_by != "us_stock_list_code":
        return False, "provider_route_not_stock_list_verified", evidence
    return True, "provider_route_verified", evidence


def representative_securities(
    rows: Sequence[CanonicalSecurityReference],
    *,
    selection_salt: str,
    excluded_issuer_keys: set[str] | None = None,
    require_routing_supported: bool = True,
) -> list[CanonicalSecurityReference]:
    excluded = excluded_issuer_keys or set()
    grouped: dict[str, list[CanonicalSecurityReference]] = defaultdict(list)
    for row in rows:
        if row.canonical_issuer_key is None or row.canonical_security_id is None:
            continue
        if row.canonical_issuer_key in excluded:
            continue
        if row.identity_resolution_status != IdentityResolutionStatus.RESOLVED:
            continue
        if require_routing_supported:
            if row.routing_support_status != RoutingSupportStatus.SUPPORTED:
                continue
        elif row.routing_support_status not in {
            RoutingSupportStatus.CANDIDATE,
            RoutingSupportStatus.SUPPORTED,
        }:
            continue
        grouped[row.canonical_issuer_key].append(row)

    def preference(row: CanonicalSecurityReference) -> tuple[int, str]:
        return (1 if row.is_adr else 0, str(row.canonical_security_id))

    representatives = [min(issuer_rows, key=preference) for issuer_rows in grouped.values()]
    return sorted(
        representatives,
        key=lambda row: (
            hashlib.sha256(
                "|".join(
                    (
                        selection_salt,
                        row.market,
                        str(row.canonical_issuer_key),
                        str(row.canonical_security_id),
                    )
                ).encode()
            ).hexdigest(),
            str(row.canonical_security_id),
        ),
    )


def reconcile_membership_sets(
    rows: Sequence[CanonicalSecurityReference],
    exclusion_reasons_by_issuer: Mapping[str, Sequence[str]],
) -> dict[str, object]:
    supported_rows = [
        row
        for row in rows
        if row.eligibility_decision == "ELIGIBLE_SUPPORTED_SECURITY"
        and row.canonical_security_id is not None
        and row.canonical_issuer_key is not None
    ]
    security_ids = {str(row.canonical_security_id) for row in supported_rows}
    issuer_keys = {str(row.canonical_issuer_key) for row in supported_rows}
    exclusions = {
        issuer: tuple(sorted(set(reasons)))
        for issuer, reasons in exclusion_reasons_by_issuer.items()
    }
    exclusion_keys = set(exclusions)
    within = issuer_keys & exclusion_keys
    unseen = issuer_keys - exclusion_keys
    ambiguous = [
        row.reference_row_id
        for row in rows
        if row.identity_resolution_status != IdentityResolutionStatus.RESOLVED
    ]
    if len(issuer_keys) > len(security_ids):
        raise ValueError("issuer_count_exceeds_security_count")
    if len(unseen) > len(issuer_keys):
        raise ValueError("unseen_issuer_count_exceeds_supported_issuer_count")
    if unseen & exclusion_keys:
        raise ValueError("unseen_exclusion_intersection_nonempty")
    return {
        "raw_reference_row_count": len(rows),
        "supported_security_count": len(security_ids),
        "supported_issuer_count": len(issuer_keys),
        "global_exclusion_issuer_count": len(exclusion_keys),
        "within_universe_exclusion_issuer_count": len(within),
        "unseen_supported_issuer_count": len(unseen),
        "supported_security_ids": sorted(security_ids),
        "supported_issuer_keys": sorted(issuer_keys),
        "global_exclusion_issuer_keys": sorted(exclusion_keys),
        "within_universe_exclusion_issuer_keys": sorted(within),
        "unseen_supported_issuer_keys": sorted(unseen),
        "exclusion_reasons_by_issuer": exclusions,
        "ambiguous_or_unresolved_reference_rows": sorted(ambiguous),
        "invariants": {
            "issuer_lte_security": True,
            "unseen_lte_supported_issuer": True,
            "unseen_intersection_exclusions_empty": True,
            "unseen_equals_supported_minus_exclusions": unseen == issuer_keys - exclusion_keys,
        },
    }


def canonical_market_mix(
    subjects: Sequence[str],
    market_by_subject: Mapping[str, object],
    *,
    corroborating_market_by_subject: Mapping[str, object] | None = None,
) -> dict[str, int]:
    ordered = tuple(str(subject) for subject in subjects)
    if len(set(ordered)) != len(ordered):
        raise ValueError("duplicate_subject_identity_in_market_manifest")
    missing = [subject for subject in ordered if subject not in market_by_subject]
    if missing:
        raise ValueError(f"canonical_market_metadata_missing:{','.join(missing)}")
    counts = {"us": 0, "kr": 0}
    for subject in ordered:
        market = str(market_by_subject[subject]).strip().lower()
        if market not in counts:
            raise ValueError(f"canonical_market_metadata_invalid:{subject}:{market}")
        if corroborating_market_by_subject is not None:
            if subject not in corroborating_market_by_subject:
                raise ValueError(f"corroborating_market_metadata_missing:{subject}")
            corroborating = str(corroborating_market_by_subject[subject]).strip().lower()
            if corroborating != market:
                raise ValueError(
                    f"canonical_market_metadata_conflict:{subject}:{market}:{corroborating}"
                )
        counts[market] += 1
    if sum(counts.values()) != len(ordered):
        raise ValueError("market_manifest_subject_count_mismatch")
    return counts
