from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
from fractions import Fraction
from html import unescape
import json
import re

from sqlmodel import Session, select

from app.models.security import ProviderResponseCache, SecurityMaster
from app.services.security_identity_service import (
    TIER_A_AUTHORITATIVE,
    identity_source_tier,
)


OFFICIAL_IDENTITY_PROVIDER = "sec_official_identity"
OFFICIAL_IDENTITY_CACHE_PROVIDER = "official_security_identity"
OFFICIAL_IDENTITY_CONTRACT = "authoritative-security-identity-v1"
ADR_RATIO_DIRECTION = "ordinary_shares_per_adr"


def _clean_text(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _normalized_security_type(title: str) -> tuple[str, str, str | None]:
    normalized = re.sub(r"\s+", " ", title).strip()
    if re.search(r"american\s+depositary\s+(?:share|receipt)s?", normalized, re.I):
        return "ads", "adr", None
    share_class = None
    class_match = re.search(r"\bClass\s+([A-Z0-9]+)\b", normalized, re.I)
    if class_match:
        share_class = f"Class {class_match.group(1).upper()}"
    if re.search(r"\b(?:common|capital)\s+stock\b", normalized, re.I):
        return "common_stock", "domestic_us", share_class
    raise ValueError("official_security_type_not_supported")


def _exchange_code(value: str) -> str:
    normalized = value.strip().lower()
    if "nasdaq" in normalized:
        return "NASDAQ"
    if (
        "new york stock exchange" in normalized
        or normalized in {"nyse", "nysetx"}
    ):
        return "NYSE"
    return value.strip()


def _inline_xbrl_facts(html: str) -> dict[str, dict[str, str]]:
    contexts: dict[str, dict[str, str]] = {}
    pattern = re.compile(
        r"<ix:nonNumeric\b(?P<attrs>[^>]*)>(?P<value>.*?)</ix:nonNumeric>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(html):
        attrs = match.group("attrs")
        name_match = re.search(r'\bname=["\']([^"\']+)["\']', attrs, re.I)
        context_match = re.search(r'\bcontextRef=["\']([^"\']+)["\']', attrs, re.I)
        if not name_match or not context_match:
            continue
        field = name_match.group(1).split(":")[-1]
        contexts.setdefault(context_match.group(1), {})[field] = _clean_text(
            match.group("value")
        )
    return contexts


@dataclass(frozen=True)
class OfficialSecurityIdentityEvidence:
    ticker: str
    issuer_name: str
    security_title: str
    security_type: str
    issuer_type: str
    exchange: str
    source_url: str
    source_form: str
    filing_accession: str
    as_of_date: str
    source_reference: str
    cik: str | None = None
    registration_number: str | None = None
    share_class: str | None = None
    adr_identifier: str | None = None
    ordinary_share_identifier: str | None = None
    adr_ratio: float | None = None
    adr_ratio_direction: str | None = None

    def field_provenance(self) -> dict[str, dict[str, object]]:
        shared: dict[str, object] = {
            "source_tier": TIER_A_AUTHORITATIVE,
            "provider": OFFICIAL_IDENTITY_PROVIDER,
            "source_url": self.source_url,
            "source_reference": self.source_reference,
            "filing_accession": self.filing_accession,
            "as_of": self.as_of_date,
            "verification_status": "verified",
            "resolution_reason": "authoritative_sec_security_identity",
        }
        values = {
            "ticker": self.ticker,
            "issuer_name": self.issuer_name,
            "security_title": self.security_title,
            "security_type": self.security_type,
            "issuer_type": self.issuer_type,
            "exchange": self.exchange,
            "cik": self.cik,
            "registration_number": self.registration_number,
            "share_class": self.share_class,
            "adr_identifier": self.adr_identifier,
            "ordinary_share_identifier": self.ordinary_share_identifier,
            "adr_ratio": self.adr_ratio,
            "adr_ratio_direction": self.adr_ratio_direction,
        }
        return {
            field: {**shared, "value": value}
            for field, value in values.items()
            if value not in (None, "")
        }

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_version": OFFICIAL_IDENTITY_CONTRACT,
            "source_tier": TIER_A_AUTHORITATIVE,
            "provider": OFFICIAL_IDENTITY_PROVIDER,
            "evidence": asdict(self),
            "field_provenance": self.field_provenance(),
            "adr_ratio_direction": self.adr_ratio_direction,
        }

    @classmethod
    def from_payload(cls, value: dict[str, object]) -> "OfficialSecurityIdentityEvidence":
        raw = value.get("evidence") if isinstance(value.get("evidence"), dict) else value
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: raw.get(key) for key in allowed})  # type: ignore[arg-type]


def parse_sec_cover_page_identity(
    html: str,
    *,
    ticker: str,
    source_url: str,
    filing_accession: str,
    filing_date: str,
    cik: str | None = None,
    source_form: str | None = None,
) -> OfficialSecurityIdentityEvidence:
    return _parse_sec_cover_page_identity(html, ticker=ticker, source_url=source_url,
        filing_accession=filing_accession, filing_date=filing_date, cik=cik, source_form=source_form)


def _parse_sec_cover_page_identity(
    html: str, *, ticker: str, source_url: str, filing_accession: str,
    filing_date: str, cik: str | None, source_form: str | None,
    annual_ads_footnote: bool = False,
) -> OfficialSecurityIdentityEvidence:
    contexts = _inline_xbrl_facts(html)
    if source_form is not None:
        def fact_values(key: str) -> set[str]:
            return {row[key] for row in contexts.values() if row.get(key)}

        if not cik or fact_values("EntityCentralIndexKey") != {cik}:
            raise ValueError("official_cover_cik_mismatch")
        if fact_values("DocumentType") != {source_form}:
            raise ValueError("official_cover_document_type_mismatch")
        if len(fact_values("EntityRegistrantName")) != 1:
            raise ValueError("official_cover_issuer_not_unique")
        date.fromisoformat(filing_date)
    matches = [
        fields
        for fields in contexts.values()
        if fields.get("TradingSymbol", "").upper() == ticker.upper()
        and fields.get("Security12bTitle")
        and fields.get("SecurityExchangeName")
    ]
    unique_matches = {
        (
            fields["Security12bTitle"],
            fields["TradingSymbol"],
            fields["SecurityExchangeName"],
        ): fields
        for fields in matches
    }
    matches = list(unique_matches.values())
    if not matches:
        symbol_rows = [
            fields
            for fields in contexts.values()
            if fields.get("TradingSymbol", "").upper() == ticker.upper()
            and fields.get("SecurityExchangeName")
        ]
        exchanges = {
            _exchange_code(fields["SecurityExchangeName"])
            for fields in symbol_rows
        }
        title_rows = [
            fields
            for fields in contexts.values()
            if fields.get("Security12bTitle")
            and not fields.get("TradingSymbol")
            and _exchange_code(fields.get("SecurityExchangeName", "")) in exchanges
        ]
        if len(exchanges) == 1 and len(title_rows) == 1:
            matches = [
                {
                    **title_rows[0],
                    "TradingSymbol": ticker.upper(),
                    "SecurityExchangeName": next(iter(exchanges)),
                }
            ]
    if len(matches) != 1:
        raise ValueError("official_cover_security_not_unique")
    fields = matches[0]
    title = fields["Security12bTitle"]
    annual_ads = annual_ads_footnote and re.search(r"\bcommon shares\b", title, re.I)
    if annual_ads:
        security_type, issuer_type, share_class = "ordinary_shares", "foreign_private_issuer", None
    else:
        security_type, issuer_type, share_class = _normalized_security_type(title)
    issuer_name = next(
        (
            item.get("EntityRegistrantName", "")
            for item in contexts.values()
            if item.get("EntityRegistrantName")
        ),
        "",
    )
    if not issuer_name:
        raise ValueError("official_issuer_name_missing")
    return OfficialSecurityIdentityEvidence(
        ticker=ticker.upper(),
        issuer_name=issuer_name,
        security_title=title,
        security_type=security_type,
        issuer_type=issuer_type,
        exchange=_exchange_code(fields["SecurityExchangeName"]),
        source_url=source_url,
        source_form=source_form or "SEC cover page",
        filing_accession=filing_accession,
        as_of_date=filing_date,
        source_reference=f"SEC accession {filing_accession}",
        cik=cik,
        share_class=share_class,
        adr_identifier=ticker.upper() if security_type == "ads" else None,
    )


_CARDINALS = {word: i for i, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split()
)}
_TENS = {word: 10 * i for i, word in enumerate(
    "twenty thirty forty fifty sixty seventy eighty ninety".split(), 2
)}
_FRACTION_DENOMINATORS = dict(half=2, third=3, fourth=4, fifth=5, sixth=6,
    seventh=7, eighth=8, ninth=9, tenth=10, twentieth=20)


def _ratio_number(value: str) -> Fraction:
    value = value.lower().strip()
    if re.fullmatch(r"[+-]?\d{1,8}(?:\s*/\s*\d{1,8})?", value):
        try:
            return Fraction(re.sub(r"\s+", "", value))
        except ZeroDivisionError as exc:
            raise ValueError("official_ads_ratio_invalid") from exc
    parts = re.split(r"[ -]+", value)
    if len(parts) == 2 and parts[0] == "one" and parts[1] in _FRACTION_DENOMINATORS:
        return Fraction(1, _FRACTION_DENOMINATORS[parts[1]])
    if value in _CARDINALS:
        return Fraction(_CARDINALS[value])
    if parts[0] in _TENS and (len(parts) == 1 or len(parts) == 2
            and 0 < _CARDINALS.get(parts[1], 0) < 10):
        return Fraction(_TENS[parts[0]] + (_CARDINALS[parts[1]] if len(parts) == 2 else 0))
    raise ValueError("official_ads_ratio_invalid")


def _ads_ratio(text: str) -> float | None:
    matches = re.finditer(
        r"\bEach\s+(?:ADS|American\s+Depositary\s+Share)(?:\s+\(ADS\))?\s+represents?\s+"
        r"(?P<amount>[\w+/-]+(?:[ /-][\w/-]+){0,4}?)"
        r"(?:\s+\((?P<check>[+-]?\d{1,8}(?:\s*/\s*\d{1,8})?)\))?\s+"
        r"(?:of\s+(?:a|one)\s+)?(?:common\s+shares?|shares?\s+of\s+(?:our\s+)?common\s+stock)\b",
        text, re.I,
    )
    values = set()
    for match in matches:
        ratio = _ratio_number(match["amount"])
        if ratio <= 0 or (match["check"] and _ratio_number(match["check"]) != ratio):
            raise ValueError("official_ads_ratio_invalid")
        values.add(ratio)
    if len(values) > 1:
        raise ValueError("official_ads_ratio_conflict")
    return float(next(iter(values))) if values else None


def parse_sec_annual_ads_identity(
    html: str, *, ticker: str, source_url: str, filing_accession: str,
    filing_date: str, cik: str,
) -> OfficialSecurityIdentityEvidence:
    cover = _parse_sec_cover_page_identity(html, ticker=ticker, source_url=source_url,
        filing_accession=filing_accession, filing_date=filing_date, cik=cik,
        source_form="20-F", annual_ads_footnote=True)
    text = _clean_text(html)
    # Some covers tag the underlying class; its footnote identifies what trades.
    if cover.security_type != "ads":
        before_contents = re.split(r"\bTABLE OF CONTENTS\b", text, maxsplit=1, flags=re.I)[0]
        if not re.search(r"not for trading,? but only in connection with the listing"
                r".{0,150}American Depositary Shares.{0,60}representing such Common Shares",
                before_contents, re.I):
            raise ValueError("official_annual_cover_ads_basis_missing")
    exchanges = {
        _exchange_code(m.group(1))
        for m in re.finditer(
            rf"\bADSs? have been listed on the (NYSE|New York Stock Exchange|Nasdaq)"
            rf" under the symbol [^\w]{{0,2}}{re.escape(ticker)}\b", text, re.I)
    }
    if exchanges != {cover.exchange}:
        raise ValueError("official_annual_ads_listing_mismatch")
    ratio = _ads_ratio(text)
    symbols = set(re.findall(
        r"\bcommon shares have been listed on the Taiwan Stock Exchange under the symbol [^\w]{0,2}(\d{4,6})\b",
        text, re.I))
    if len(symbols) > 1:
        raise ValueError("official_annual_underlying_conflict")
    return replace(cover, issuer_type="adr", security_type="ads",
        security_title="American Depositary Shares", adr_identifier=ticker.upper(),
        ordinary_share_identifier=f"TWSE:{next(iter(symbols))}" if symbols else None,
        adr_ratio=ratio, adr_ratio_direction=ADR_RATIO_DIRECTION if ratio is not None else None)


def parse_sec_ads_prospectus_identity(
    html: str,
    *,
    ticker: str,
    issuer_name: str,
    source_url: str,
    filing_accession: str,
    filing_date: str,
    cik: str | None = None,
    registration_number: str | None = None,
) -> OfficialSecurityIdentityEvidence:
    text = _clean_text(html)
    ticker_pattern = re.compile(
        rf"(?:symbol|ticker)\W+{re.escape(ticker)}\b", re.I
    )
    if not ticker_pattern.search(text):
        raise ValueError("official_ads_ticker_missing")
    if not re.search(r"American\s+Depositary\s+Shares?", text, re.I):
        raise ValueError("official_ads_security_type_missing")
    exchange_match = re.search(
        rf"(?:list|listed|approved\s+to\s+list).*?"
        rf"(Nasdaq(?:\s+Global\s+Select\s+Market)?|New\s+York\s+Stock\s+Exchange)"
        rf".*?(?:symbol|ticker)\W+{re.escape(ticker)}\b",
        text,
        re.I,
    )
    if not exchange_match:
        raise ValueError("official_ads_exchange_missing")
    ratio = _ads_ratio(text)
    ordinary_match = re.search(
        r"KRX\s+KOSPI\s+Market.*?(?:identification\s+code|code)\D+(\d{6})",
        text,
        re.I,
    )
    return OfficialSecurityIdentityEvidence(
        ticker=ticker.upper(),
        issuer_name=issuer_name,
        security_title="American Depositary Shares",
        security_type="ads",
        issuer_type="adr",
        exchange=_exchange_code(exchange_match.group(1)),
        source_url=source_url,
        source_form="424(b)(4)",
        filing_accession=filing_accession,
        as_of_date=filing_date,
        source_reference=(
            f"SEC registration {registration_number}; accession {filing_accession}"
            if registration_number
            else f"SEC accession {filing_accession}"
        ),
        cik=cik,
        registration_number=registration_number,
        adr_identifier=ticker.upper(),
        ordinary_share_identifier=(ordinary_match.group(1) if ordinary_match else None),
        adr_ratio=ratio,
        adr_ratio_direction=ADR_RATIO_DIRECTION if ratio is not None else None,
    )


def _security_snapshot(row: SecurityMaster) -> dict[str, object]:
    return {
        "ticker": row.ticker,
        "exchange": row.exchange,
        "country": row.country,
        "cik": row.cik,
        "security_type": row.security_type,
        "share_class": row.share_class,
        "issuer_type": row.issuer_type,
        "ordinary_share_identifier": row.ordinary_share_identifier,
        "adr_identifier": row.adr_identifier,
        "adr_ratio": row.adr_ratio,
        "adr_ratio_source": row.adr_ratio_source,
        "adr_ratio_as_of": row.adr_ratio_as_of.isoformat() if row.adr_ratio_as_of else None,
        "identity_quality": row.identity_quality,
        "identity_provider": row.identity_provider,
        "identity_warnings": row.identity_warnings,
    }


def load_official_identity_provenance(
    session: Session, ticker: str
) -> dict[str, object]:
    row = session.exec(
        select(ProviderResponseCache).where(
            ProviderResponseCache.provider == OFFICIAL_IDENTITY_CACHE_PROVIDER,
            ProviderResponseCache.ticker == ticker.upper(),
            ProviderResponseCache.data_type == "identity_evidence",
        )
    ).first()
    if row is None:
        return {}
    try:
        payload = json.loads(row.payload)
    except json.JSONDecodeError:
        return {}
    evidence = payload.get("evidence_payload") if isinstance(payload, dict) else None
    return dict(evidence) if isinstance(evidence, dict) else {}


class OfficialSecurityIdentityService:
    def plan(
        self,
        security: SecurityMaster,
        evidence: OfficialSecurityIdentityEvidence,
    ) -> dict[str, object]:
        if security.ticker.upper() != evidence.ticker.upper():
            raise ValueError("official_identity_ticker_mismatch")
        before = _security_snapshot(security)
        current_tier = identity_source_tier(
            security.identity_provider, security.identity_quality
        )
        target = {
            **before,
            "exchange": evidence.exchange,
            "country": security.country or "US",
            "cik": evidence.cik or security.cik,
            "security_type": evidence.security_type,
            "share_class": evidence.share_class,
            "issuer_type": evidence.issuer_type,
            "ordinary_share_identifier": evidence.ordinary_share_identifier,
            "adr_identifier": evidence.adr_identifier,
            "adr_ratio": evidence.adr_ratio,
            "adr_ratio_source": evidence.source_url if evidence.adr_ratio is not None else None,
            "adr_ratio_as_of": evidence.as_of_date if evidence.adr_ratio is not None else None,
            "identity_quality": "verified",
            "identity_provider": OFFICIAL_IDENTITY_PROVIDER,
            "identity_warnings": "[]",
        }
        if current_tier == TIER_A_AUTHORITATIVE:
            comparable = {
                key: before.get(key)
                for key in target
                if key not in {"adr_ratio_as_of"}
            }
            target_comparable = {
                key: target.get(key)
                for key in comparable
            }
            if comparable == target_comparable:
                action = "no_op_already_authoritative"
            else:
                action = "conflict_no_write_existing_authoritative"
        else:
            action = "apply_authoritative_identity"
        return {
            "contract_version": OFFICIAL_IDENTITY_CONTRACT,
            "ticker": security.ticker,
            "action": action,
            "before": before,
            "after": target,
            "rollback_snapshot": before,
            "evidence_payload": evidence.to_payload(),
            "resolution_reason": action,
        }

    def _cache_plan(
        self,
        session: Session,
        *,
        ticker: str,
        data_type: str,
        status: str,
        plan: dict[str, object],
    ) -> None:
        now = datetime.now(timezone.utc)
        cache = session.exec(
            select(ProviderResponseCache).where(
                ProviderResponseCache.provider == OFFICIAL_IDENTITY_CACHE_PROVIDER,
                ProviderResponseCache.ticker == ticker,
                ProviderResponseCache.data_type == data_type,
            )
        ).first() or ProviderResponseCache(
            provider=OFFICIAL_IDENTITY_CACHE_PROVIDER,
            ticker=ticker,
            data_type=data_type,
        )
        cache.status = status
        cache.payload = json.dumps(plan, ensure_ascii=False, sort_keys=True)
        cache.fetched_at = now
        cache.last_success_at = now if status == "success" else cache.last_success_at
        cache.last_error = None if status == "success" else status
        session.add(cache)
        session.flush()

    def ingest(
        self,
        session: Session,
        evidence: OfficialSecurityIdentityEvidence,
        *,
        dry_run: bool = True,
    ) -> dict[str, object]:
        security = session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker == evidence.ticker.upper())
        ).first()
        if security is None:
            raise ValueError("official_identity_security_master_missing")
        plan = self.plan(security, evidence)
        if dry_run:
            return {**plan, "dry_run": dry_run, "mutated": False}
        if plan["action"] == "conflict_no_write_existing_authoritative":
            self._cache_plan(
                session,
                ticker=evidence.ticker.upper(),
                data_type="identity_evidence_conflict",
                status="conflict",
                plan=plan,
            )
            return {**plan, "dry_run": False, "mutated": False}
        if plan["action"] != "apply_authoritative_identity":
            return {**plan, "dry_run": False, "mutated": False}

        after = dict(plan["after"])
        for field in (
            "exchange",
            "country",
            "cik",
            "security_type",
            "share_class",
            "issuer_type",
            "ordinary_share_identifier",
            "adr_identifier",
            "adr_ratio",
            "adr_ratio_source",
            "identity_quality",
            "identity_provider",
            "identity_warnings",
        ):
            setattr(security, field, after[field])
        security.adr_ratio_as_of = (
            date.fromisoformat(evidence.as_of_date)
            if evidence.adr_ratio is not None
            else None
        )
        security.updated_at = datetime.now(timezone.utc)
        session.add(security)
        session.flush()

        self._cache_plan(
            session,
            ticker=evidence.ticker.upper(),
            data_type="identity_evidence",
            status="success",
            plan=plan,
        )
        return {**plan, "dry_run": False, "mutated": True}
