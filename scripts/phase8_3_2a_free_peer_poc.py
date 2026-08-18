from __future__ import annotations

# ruff: noqa: E402

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
import httpx
from sqlmodel import Session, create_engine, select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.company import Company
from app.models.financial import FinancialSnapshot
from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.providers.opendart_corp_codes import load_opendart_companies
from app.services.company_profile_service import read_profile_provenance
from app.services.free_source_peer_service import build_free_source_peer_state


SCHEMA_VERSION = "phase8-3-2a-free-peer-poc-v1"
FREE_POLICY = "FREE_ONLY"
COMMON_SECURITY_TYPES = {"common stock", "common_stock", "ordinary share"}
_BROAD_FINNHUB_INDUSTRIES = {
    "commercial services",
    "consumer cyclical",
    "consumer defensive",
    "financial services",
    "health care",
    "industrials",
    "media",
    "real estate",
    "technology",
    "utilities",
}


def _json_dict(value: str | None) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalized(value: object) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _market(ticker: str) -> str:
    return "kr" if ticker.isdigit() else "us"


def _us_listed_symbol(value: str) -> bool:
    return (
        bool(value)
        and value[0].isalpha()
        and len(value) <= 10
        and all(character.isalpha() or character in {".", "-"} for character in value)
    )


def _framework(profile: dict[str, object], thesis: InvestmentThesis | None) -> str:
    method = _normalized(
        _json_dict(thesis.valuation_framework if thesis else "{}").get("primary_method")
    )
    industry = _normalized(profile.get("industry"))
    taxonomy = _normalized(profile.get("taxonomy_key"))
    thesis_text = _normalized(thesis.core_thesis if thesis else "")
    if "risk adjusted npv" in method or taxonomy == "biotech":
        return "biotech"
    if any(term in method for term in ("stabilized", "계약 mw", "가동 mw", "infrastructure nav")):
        return "hpc_crypto_infrastructure"
    if taxonomy == "insurance" or "p/b roe" in method:
        return "insurance"
    if taxonomy == "automotive" or "automotive" in industry:
        return "automotive"
    if taxonomy == "steel materials" or "steel" in industry:
        return "steel_materials"
    if taxonomy == "shipping" or any(
        term in industry for term in ("transport", "logistics", "shipping")
    ):
        return "transport_logistics"
    if "ev/revenue" in method or "ev revenue" in method:
        return "saas"
    if "sum of the parts" in method or "sotp" in method:
        return "holding_company"
    if (
        "memory" in method
        or "메모리" in method
        or "memory" in thesis_text
        or "메모리" in thesis_text
        or ("hbm" in thesis_text and "dram" in thesis_text)
    ):
        return "memory"
    if taxonomy == "semiconductor" or "semiconductor" in industry:
        return "semiconductor"
    return "general"


def _provider_taxonomy(industry: object) -> str | None:
    value = _normalized(industry)
    rules = (
        (("semiconductor",), "semiconductor"),
        (("auto", "vehicle"), "automotive"),
        (("biotech", "pharma"), "biotech"),
        (("insurance",), "insurance"),
        (("steel", "metal"), "steel_materials"),
        (("transport", "logistics", "shipping"), "shipping"),
    )
    return next(
        (taxonomy for terms, taxonomy in rules if any(term in value for term in terms)),
        None,
    )


def _provider_industry_fields(industry: object) -> tuple[str | None, str | None, str]:
    value = str(industry or "").strip()
    normalized = _normalized(value)
    sector = f"finnhub_group:{normalized or 'unknown'}"
    if not normalized or normalized in _BROAD_FINNHUB_INDUSTRIES:
        return None, None, sector
    return value, value, sector


class CachedFreeClient:
    def __init__(self, cache_dir: Path, finnhub_key: str, openfigi_key: str) -> None:
        self.cache_dir = cache_dir
        self.finnhub_key = finnhub_key
        self.openfigi_key = openfigi_key
        self.calls: Counter[str] = Counter()
        self.cache_hits: Counter[str] = Counter()
        self.last_finnhub_call = 0.0
        self.client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self.client.close()

    def _cached(self, provider: str, key: str) -> object | None:
        path = self.cache_dir / provider / f"{key}.json"
        if not path.exists():
            return None
        self.cache_hits[provider] += 1
        return json.loads(path.read_text(encoding="utf-8"))

    def _store(self, provider: str, key: str, payload: object) -> object:
        path = self.cache_dir / provider / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return payload

    def finnhub(self, endpoint: str, ticker: str, **params: object) -> object:
        cache_key = f"{endpoint.strip('/').replace('/', '_')}__{ticker}"
        cached = self._cached("finnhub", cache_key)
        if cached is not None:
            return cached
        elapsed = time.monotonic() - self.last_finnhub_call
        if elapsed < 1.05:
            time.sleep(1.05 - elapsed)
        response = self.client.get(
            f"https://finnhub.io/api/v1/{endpoint.lstrip('/')}",
            params={"symbol": ticker, "token": self.finnhub_key, **params},
        )
        self.last_finnhub_call = time.monotonic()
        self.calls["finnhub"] += 1
        if response.status_code in {401, 403}:
            return self._store(
                "finnhub",
                cache_key,
                {"_status": "entitlement_denied", "http_status": response.status_code},
            )
        if response.is_error:
            raise RuntimeError(
                f"Finnhub {endpoint} failed with HTTP {response.status_code}"
            )
        return self._store("finnhub", cache_key, response.json())

    def sec_tickers(self, user_agent: str) -> dict[str, dict[str, object]]:
        cache_key = "company_tickers"
        cached = self._cached("sec", cache_key)
        payload: object
        if cached is not None:
            payload = cached
        else:
            response = self.client.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers={"User-Agent": user_agent},
            )
            self.calls["sec"] += 1
            if response.is_error:
                raise RuntimeError(
                    f"SEC company_tickers failed with HTTP {response.status_code}"
                )
            payload = self._store("sec", cache_key, response.json())
        if not isinstance(payload, dict):
            return {}
        return {
            str(item.get("ticker") or "").upper(): item
            for item in payload.values()
            if isinstance(item, dict) and item.get("ticker")
        }

    def openfigi(self, tickers: list[str]) -> dict[str, dict[str, object]]:
        results: dict[str, dict[str, object]] = {}
        missing: list[str] = []
        for ticker in tickers:
            cached = self._cached("openfigi", ticker)
            if isinstance(cached, dict):
                results[ticker] = cached
            else:
                missing.append(ticker)
        for offset in range(0, len(missing), 100):
            batch = missing[offset : offset + 100]
            response = self.client.post(
                "https://api.openfigi.com/v3/mapping",
                headers={
                    "Content-Type": "application/json",
                    "X-OPENFIGI-APIKEY": self.openfigi_key,
                },
                json=[
                    {"idType": "TICKER", "idValue": ticker, "exchCode": "US"}
                    for ticker in batch
                ],
            )
            self.calls["openfigi"] += 1
            if response.is_error:
                raise RuntimeError(
                    f"OpenFIGI mapping failed with HTTP {response.status_code}"
                )
            for ticker, row in zip(batch, response.json(), strict=True):
                data = row.get("data", []) if isinstance(row, dict) else []
                exact = [
                    item
                    for item in data
                    if isinstance(item, dict)
                    and str(item.get("ticker") or "").upper() == ticker
                    and item.get("marketSector") == "Equity"
                ]
                selected = exact[0] if len(exact) == 1 else {}
                results[ticker] = self._store("openfigi", ticker, selected)
        return results


async def _kr_profiles(
    tickers: list[str],
    *,
    api_key: str,
    client: CachedFreeClient,
) -> dict[str, dict[str, object]]:
    companies = await load_opendart_companies(api_key)
    by_ticker = {item.stock_code: item for item in companies if item.stock_code}
    profiles: dict[str, dict[str, object]] = {}
    for ticker in tickers:
        company = by_ticker.get(ticker)
        if company is None:
            continue
        cache_key = ticker
        cached = client._cached("opendart_company", cache_key)
        payload: object
        if cached is not None:
            payload = cached
        else:
            response = client.client.get(
                "https://opendart.fss.or.kr/api/company.json",
                params={"crtfc_key": api_key, "corp_code": company.corp_code},
            )
            client.calls["opendart_company"] += 1
            if response.is_error:
                raise RuntimeError(
                    f"OpenDART company failed with HTTP {response.status_code}"
                )
            payload = client._store("opendart_company", cache_key, response.json())
        if not isinstance(payload, dict) or payload.get("status") != "000":
            continue
        code = str(payload.get("induty_code") or "").strip()
        if code:
            profiles[ticker] = {
                "ticker": ticker,
                "company_name": payload.get("corp_name") or company.corp_name,
                "corp_code": company.corp_code,
                "industry_code": code,
                "source_as_of": company.modify_date,
            }
    return profiles


def _kr_reference(reference_dir: Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for path in reference_dir.glob("*isu_base_info.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("rows", []):
            if isinstance(row, dict) and row.get("ISU_SRT_CD"):
                rows[str(row["ISU_SRT_CD"])] = row
    return rows


def _latest_period(metric: dict[str, object], key: str) -> str | None:
    series = metric.get("series")
    quarterly = series.get("quarterly") if isinstance(series, dict) else None
    values = quarterly.get(key) if isinstance(quarterly, dict) else None
    if not isinstance(values, list):
        return None
    periods = [
        str(item.get("period"))
        for item in values
        if isinstance(item, dict) and item.get("period")
    ]
    return max(periods) if periods else None


def _us_fact(
    ticker: str,
    profile: dict[str, object],
    metric_payload: dict[str, object],
    quote: dict[str, object],
    identity_safe: bool,
    target_session: str,
    quote_session: str,
) -> dict[str, object]:
    metric = metric_payload.get("metric")
    values = metric if isinstance(metric, dict) else {}
    quote_timestamp = quote.get("t")
    observed_session = (
        datetime.fromtimestamp(float(quote_timestamp), tz=UTC).date().isoformat()
        if isinstance(quote_timestamp, (int, float)) and quote_timestamp
        else None
    )
    price = quote.get("pc") if observed_session == quote_session else None
    currency = str(profile.get("currency") or "").upper()
    return {
        "ticker": ticker,
        "source": "finnhub_free_basic_financials",
        "source_entitlement": "free_existing",
        "identity_safe": identity_safe,
        "price": price,
        "price_as_of": target_session if price is not None else None,
        "quote_observed_session": observed_session,
        "price_currency": currency,
        "ttm_eps": values.get("epsTTM"),
        "ttm_eps_period_end": _latest_period(metric_payload, "peTTM")
        or _latest_period(metric_payload, "eps"),
        "eps_currency": currency,
        "eps_security_basis": "provider_security_per_share",
        "bvps": values.get("bookValuePerShareQuarterly"),
        "bvps_period_end": _latest_period(metric_payload, "pb")
        or _latest_period(metric_payload, "bookValue"),
        "bvps_currency": currency,
        "bvps_security_basis": "provider_security_per_share",
        "provider_conflict": False,
        "financial_quality_denied": False,
    }


def _subject_snapshot(row: ThesisAssessment) -> dict[str, object]:
    snapshot = _json_dict(row.valuation_snapshot)
    snapshot["price_as_of"] = str(snapshot.get("price_as_of") or "")[:10]
    return snapshot


def _subject_identity(security: SecurityMaster | None) -> bool:
    if security is None:
        return False
    security_type = _normalized(security.security_type)
    return (
        security_type in COMMON_SECURITY_TYPES
        and security.issuer_type not in {"adr", "foreign_private_issuer"}
        and security.identity_quality in {"verified", "inferred"}
    )


def _coverage_summary(states: dict[str, dict[str, object]]) -> dict[str, object]:
    counts = Counter(str(state.get("coverage_state")) for state in states.values())
    meaningful = sum(
        state.get("coverage_state") != "NOT_MEANINGFUL" for state in states.values()
    )
    medium_plus = sum(
        state.get("coverage_state") in {"MEDIUM", "HIGH"} for state in states.values()
    )
    return {
        "state_counts": dict(sorted(counts.items())),
        "medium_plus_count": medium_plus,
        "active_subject_count": len(states),
        "meaningful_subject_count": meaningful,
        "raw_coverage_pct": round(medium_plus / len(states) * 100, 2) if states else 0,
        "meaningful_coverage_pct": (
            round(medium_plus / meaningful * 100, 2) if meaningful else 0
        ),
    }


def build_poc(
    database: Path,
    data_dir: Path,
    assessment_date: date,
    us_target_session: str,
    us_quote_session: str,
    kr_target_session: str,
    krx_reference_dir: Path,
    cache_dir: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    required = {
        "FINNHUB_API_KEY": os.environ.get("FINNHUB_API_KEY"),
        "OPENFIGI_API_KEY": os.environ.get("OPENFIGI_API_KEY"),
        "SEC_USER_AGENT": os.environ.get("SEC_USER_AGENT"),
        "OPENDART_API_KEY": os.environ.get("OPENDART_API_KEY"),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"missing existing free credentials: {', '.join(missing)}")

    client = CachedFreeClient(
        cache_dir,
        str(required["FINNHUB_API_KEY"]),
        str(required["OPENFIGI_API_KEY"]),
    )
    engine = create_engine(f"sqlite:///{database}")
    try:
        with Session(engine) as session:
            assessments = list(
                session.exec(
                    select(ThesisAssessment).where(
                        ThesisAssessment.assessment_date == assessment_date,
                        ThesisAssessment.assessment_state == "final",
                    )
                ).all()
            )
            tickers = {row.ticker for row in assessments}
            companies = {
                row.ticker: row
                for row in session.exec(select(Company).where(Company.ticker.in_(tickers))).all()
            }
            securities = {
                row.ticker: row
                for row in session.exec(
                    select(SecurityMaster).where(SecurityMaster.ticker.in_(tickers))
                ).all()
            }
            theses = {
                (row.ticker, row.version): row
                for row in session.exec(
                    select(InvestmentThesis).where(InvestmentThesis.ticker.in_(tickers))
                ).all()
            }
            kr_pool = sorted(
                {
                    ticker
                    for ticker in session.exec(select(FinancialSnapshot.ticker)).all()
                    if str(ticker).isdigit()
                }
            )

        state_by_ticker: dict[str, dict[str, object]] = {}
        candidate_audit: dict[str, dict[str, object]] = {}
        provider_audit: dict[str, object] = {}

        kr_profiles = asyncio.run(
            # OpenDART corpCode.xml is one read-only request per process.
            _kr_profiles(
                kr_pool,
                api_key=str(required["OPENDART_API_KEY"]),
                client=client,
            )
        )
        client.calls["opendart_corp_code"] += 1
        references = _kr_reference(krx_reference_dir)
        kr_candidates: list[dict[str, object]] = []
        for ticker, profile in kr_profiles.items():
            reference = references.get(ticker, {})
            is_common = (
                reference.get("SECUGRP_NM") == "주권"
                and reference.get("KIND_STKCERT_TP_NM") == "보통주"
            )
            code = str(profile["industry_code"])
            kr_candidates.append(
                {
                    "ticker": ticker,
                    "market": "kr",
                    "issuer_id": f"opendart:{profile['corp_code']}",
                    "security_id": reference.get("ISU_CD"),
                    "issuer_dedup_reliable": bool(profile.get("corp_code")),
                    "identity_conflict": False,
                    "is_depositary_security": False,
                    "security_type": "common_stock" if is_common else "unknown",
                    "profile_quality": "verified",
                    "taxonomy": None,
                    "sub_industry": f"ksic:{code}",
                    "industry": f"ksic:{code}",
                    "sector": f"ksic_division:{code[:2]}",
                    "company_name": profile.get("company_name"),
                    "source": "opendart_company+krx_issue_reference",
                }
            )

        sec_tickers = client.sec_tickers(str(required["SEC_USER_AGENT"]))
        us_subject_rows = [row for row in assessments if _market(row.ticker) == "us"]
        subject_finnhub_profiles: dict[str, dict[str, object]] = {}
        peer_symbols: dict[str, list[str]] = {}
        all_peer_symbols: set[str] = set()
        for row in us_subject_rows:
            profile = client.finnhub("stock/profile2", row.ticker)
            subject_finnhub_profiles[row.ticker] = profile if isinstance(profile, dict) else {}
            peers = client.finnhub(
                "stock/peers", row.ticker, grouping="subIndustry"
            )
            symbols = sorted(
                {
                    str(item).upper()
                    for item in peers
                    if isinstance(item, str)
                    and _us_listed_symbol(str(item).upper())
                    and str(item).upper() != row.ticker
                }
            ) if isinstance(peers, list) else []
            peer_symbols[row.ticker] = symbols
            all_peer_symbols.update(symbols)

        all_us_symbols = sorted(all_peer_symbols | {row.ticker for row in us_subject_rows})
        figi = client.openfigi(all_us_symbols)
        us_profiles: dict[str, dict[str, object]] = {}
        for ticker in all_us_symbols:
            payload = (
                subject_finnhub_profiles[ticker]
                if ticker in subject_finnhub_profiles
                else client.finnhub("stock/profile2", ticker)
            )
            us_profiles[ticker] = payload if isinstance(payload, dict) else {}

        us_candidates: dict[str, list[dict[str, object]]] = {}
        for subject_ticker, symbols in peer_symbols.items():
            rows: list[dict[str, object]] = []
            for ticker in symbols:
                profile = us_profiles.get(ticker, {})
                figi_row = figi.get(ticker, {})
                sec = sec_tickers.get(ticker)
                security_type = str(figi_row.get("securityType") or "unknown")
                sub_industry, industry, sector = _provider_industry_fields(
                    profile.get("finnhubIndustry")
                )
                rows.append(
                    {
                        "ticker": ticker,
                        "market": "us",
                        "issuer_id": (
                            f"sec:{int(sec['cik_str']):010d}" if sec else ""
                        ),
                        "security_id": figi_row.get("figi"),
                        "issuer_dedup_reliable": sec is not None,
                        "identity_conflict": False,
                        "is_depositary_security": security_type in {"ADR", "Depositary Receipt"},
                        "security_type": security_type,
                        "profile_quality": "verified" if profile.get("finnhubIndustry") else "unavailable",
                        "taxonomy": _provider_taxonomy(profile.get("finnhubIndustry")),
                        "sub_industry": sub_industry,
                        "industry": industry,
                        "sector": sector,
                        "company_name": profile.get("name"),
                        "source": "finnhub_free_profile+sec+openfigi",
                    }
                )
            us_candidates[subject_ticker] = rows

        meaningful_us_subjects = {
            row.ticker
            for row in us_subject_rows
            if _framework(
                read_profile_provenance(row.ticker, data_dir),
                theses.get((row.ticker, row.thesis_version)),
            )
            not in {
                "biotech",
                "hpc_crypto_infrastructure",
                "holding_company",
                "saas",
            }
            and _subject_identity(securities.get(row.ticker))
        }
        needed_facts = sorted(
            {
                str(candidate["ticker"])
                for subject_ticker, candidates in us_candidates.items()
                if subject_ticker in meaningful_us_subjects
                for candidate in candidates
                if candidate.get("profile_quality") == "verified"
                and candidate.get("issuer_dedup_reliable") is True
                and candidate.get("security_type") == "Common Stock"
            }
        )
        us_facts: dict[str, dict[str, object]] = {}
        for ticker in needed_facts:
            metric = client.finnhub("stock/metric", ticker, metric="all")
            quote = client.finnhub("quote", ticker)
            us_facts[ticker] = _us_fact(
                ticker,
                us_profiles.get(ticker, {}),
                metric if isinstance(metric, dict) else {},
                quote if isinstance(quote, dict) else {},
                True,
                us_target_session,
                us_quote_session,
            )

        for row in sorted(assessments, key=lambda item: item.ticker):
            ticker = row.ticker
            company = companies[ticker]
            security = securities.get(ticker)
            profile = read_profile_provenance(ticker, data_dir)
            thesis = theses.get((ticker, row.thesis_version))
            framework = _framework(profile, thesis)
            if _market(ticker) == "kr":
                kr_profile = kr_profiles.get(ticker, {})
                code = str(kr_profile.get("industry_code") or profile.get("official_industry_code") or "")
                subject = {
                    "ticker": ticker,
                    "market": "kr",
                    "issuer_id": (
                        f"opendart:{kr_profile.get('corp_code')}"
                        if kr_profile.get("corp_code")
                        else security.canonical_company_id if security else ""
                    ),
                    "identity_safe": _subject_identity(security),
                    "profile_quality": "verified",
                    "taxonomy": profile.get("taxonomy_key"),
                    "sub_industry": f"ksic:{code}",
                    "industry": f"ksic:{code}",
                    "sector": f"ksic_division:{code[:2]}",
                    "framework": framework,
                    "company_name": company.company_name,
                }
                candidates = kr_candidates
                facts: dict[str, dict[str, object]] = {}
                target = kr_target_session
            else:
                finnhub_profile = subject_finnhub_profiles.get(ticker, {})
                provider_taxonomy = _provider_taxonomy(
                    finnhub_profile.get("finnhubIndustry")
                )
                sub_industry, industry, sector = _provider_industry_fields(
                    finnhub_profile.get("finnhubIndustry")
                )
                if framework == "memory":
                    provider_taxonomy = "memory"
                    sub_industry = "memory"
                    industry = "memory"
                subject = {
                    "ticker": ticker,
                    "market": "us",
                    "issuer_id": (
                        f"sec:{int(sec_tickers[ticker]['cik_str']):010d}"
                        if ticker in sec_tickers
                        else security.canonical_company_id if security else ""
                    ),
                    "identity_safe": _subject_identity(security),
                    "profile_quality": "verified",
                    "taxonomy": provider_taxonomy or profile.get("taxonomy_key"),
                    "sub_industry": sub_industry,
                    "industry": industry or profile.get("industry"),
                    "sector": sector,
                    "framework": framework,
                    "company_name": company.company_name,
                }
                candidates = us_candidates.get(ticker, [])
                facts = us_facts
                target = us_target_session
            state = build_free_source_peer_state(
                subject,
                candidates,
                _subject_snapshot(row),
                facts,
                target_session=target,
            )
            state_by_ticker[ticker] = state
            candidate_audit[ticker] = {
                "ticker": ticker,
                "market": subject["market"],
                "company_name": company.company_name,
                "framework": framework,
                "coverage_state": state.get("coverage_state"),
                "selection": state.get("selection"),
            }

        provider_audit = {
            "policy": FREE_POLICY,
            "sources_used": {
                "kr": [
                    "OpenDART company overview and existing financial pool",
                    "KRX archived issue reference",
                    "existing canonical subject valuation snapshots",
                ],
                "us": [
                    "Finnhub free profile/peers/basic-financials/quote",
                    "SEC company ticker identity",
                    "OpenFIGI security mapping",
                    "existing canonical subject valuation snapshots",
                ],
            },
            "network_call_counts": dict(sorted(client.calls.items())),
            "cache_hit_counts": dict(sorted(client.cache_hits.items())),
            "paid_provider_calls": 0,
            "paid_signups": 0,
            "paid_trials": 0,
            "credential_exposure": 0,
            "forward_poc": "DEFERRED_AFTER_TRAILING_POC",
            "historical_peer_pit": "DEFERRED_BY_FREE_ONLY_POLICY",
        }
        audit = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "assessment_date": assessment_date.isoformat(),
            "sessions": {
                "kr": kr_target_session,
                "us": us_target_session,
                "us_quote_observation_session": us_quote_session,
            },
            "provider_policy": FREE_POLICY,
            "coverage": _coverage_summary(state_by_ticker),
            "markets": {
                market: _coverage_summary(
                    {
                        ticker: state
                        for ticker, state in state_by_ticker.items()
                        if _market(ticker) == market
                    }
                )
                for market in ("kr", "us")
            },
            "states": state_by_ticker,
            "provider_audit": provider_audit,
            "safety": {
                "ticker_hard_code_in_selection": 0,
                "historical_peer_pit_claims": 0,
                "telegram_sends": 0,
                "database_mutations": 0,
                "operating_deployment": 0,
            },
        }
        candidates = {
            "schema_version": "phase8-3-2a-peer-candidate-audit-v1",
            "assessment_date": assessment_date.isoformat(),
            "provider_policy": FREE_POLICY,
            "subjects": candidate_audit,
        }
        return audit, candidates
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--assessment-date", type=date.fromisoformat, required=True)
    parser.add_argument("--us-target-session", required=True)
    parser.add_argument("--us-quote-session", required=True)
    parser.add_argument("--kr-target-session", required=True)
    parser.add_argument("--krx-reference-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--valuation-output", type=Path, required=True)
    parser.add_argument("--candidate-output", type=Path, required=True)
    args = parser.parse_args()
    valuation, candidates = build_poc(
        args.database,
        args.data_dir,
        args.assessment_date,
        args.us_target_session,
        args.us_quote_session,
        args.kr_target_session,
        args.krx_reference_dir,
        args.cache_dir,
    )
    for path, payload in (
        (args.valuation_output, valuation),
        (args.candidate_output, candidates),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
