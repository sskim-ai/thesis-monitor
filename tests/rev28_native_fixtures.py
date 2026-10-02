"""Fictional wire inputs for the production snapshot owner, never live proof."""

from datetime import datetime, timedelta, timezone

from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
from app.services.provider_native_valuation_snapshot import (
    INPUT_CONTRACT,
    FINNHUB_BASE,
    KIWOOM_ROUTE,
)
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_source_policy import UnifiedSourcePolicy

START = datetime(2026, 9, 30, 2, tzinfo=timezone.utc)


def security(ticker="IBM"):
    kr = ticker.isdigit()
    return dict(
        ticker=ticker,
        canonical_security_id="fixture-" + ticker,
        company_name="Fixture " + ticker,
        country="KR" if kr else "US",
        exchange="KRX" if kr else "NYSE",
        security_type="Common Stock" if kr else "common_stock",
        issuer_type="krx" if kr else "domestic_us",
        cik=None if kr else "0000001234",
        share_class=None,
        identity_provider="local" if kr else "sec_official_identity",
        identity_quality="inferred" if kr else "verified",
    )


def native_input(sec, *, start=START, run="fictional-snapshot", policy=None, negative=False):
    ticker = sec["ticker"]
    kr = sec["country"] == "KR"
    provider = "kiwoom" if kr else "finnhub"
    result = dict(
        contract=INPUT_CONTRACT,
        run_started_at=start,
        cutoff=start + timedelta(seconds=8),
        policy=policy or UnifiedSourcePolicy(frozenset({"kiwoom_rest", "finnhub"})),
    )

    def source(body, request):
        raw = encoded(body)
        return dict(
            raw=raw,
            receipt=dict(
                provider=provider,
                run_id=run,
                security_sha256=digest(sec),
                acquisition_class="FRESH_CURRENT_RUN",
                http_status=200,
                source_sha256=sha256_bytes(raw),
                requested_at=start.isoformat(),
                received_at=(start + timedelta(seconds=1)).isoformat(),
                request=request,
                response_headers={"cont-yn": "N", "next-key": ""},
            ),
        )

    if kr:
        result.update(
            source(
                dict(
                    return_code=0,
                    stk_cd=ticker,
                    stk_nm=sec["company_name"],
                    per="12.3",
                    pbr="1.5",
                    eps="-99",
                    bps="0",
                    cur_prc="-9999",
                ),
                dict(method="POST", route=KIWOOM_ROUTE, api_id="ka10001", body={"stk_cd": ticker}),
            )
        )
        page = source(
            dict(
                return_code=0,
                list=[
                    dict(code=ticker, name=sec["company_name"], marketCode="0", marketName="KOSPI")
                ],
            ),
            dict(
                method="POST",
                route=KIWOOM_ROUTE,
                api_id="ka10099",
                body={"mrkt_tp": "0"},
                continuation={},
            ),
        )
        result["identity_inputs"] = dict(market_type="0", list_pages=[page])
    else:
        result.update(
            source(
                dict(
                    symbol=ticker,
                    metric=dict(
                        peTTM=None if negative else 12.3, pbQuarterly=1.5, epsTTM=-99, forwardPE=7
                    ),
                ),
                dict(
                    method="GET",
                    route=FINNHUB_BASE + "metric",
                    params={"symbol": ticker, "metric": "all"},
                ),
            )
        )
        profile = source(
            dict(ticker=ticker, exchange=sec["exchange"], currency="USD", country="US"),
            dict(method="GET", route=FINNHUB_BASE + "profile2", params={"symbol": ticker}),
        )
        official = OfficialSecurityIdentityEvidence(
            ticker=ticker,
            issuer_name="Fictional issuer",
            security_title="Common Stock",
            security_type="common_stock",
            issuer_type="domestic_us",
            exchange=sec["exchange"],
            source_url="https://www.sec.gov/Archives/edgar/data/1234/000000123426000001/fixture.htm",
            source_form="SEC cover page",
            filing_accession="0000001234-26-000001",
            as_of_date="2026-01-01",
            source_reference="FICTIONAL CONTRACT TEST ONLY",
            cik=sec.get("cik"),
            share_class=sec.get("share_class"),
        ).to_payload()
        result["identity_inputs"] = dict(
            profile=profile, official_identity=official, official_identity_sha256=digest(official)
        )
    return result
