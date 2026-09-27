"""Opt-in SEC/OpenDART acquisition plans. No production registration or DB access.

Discovery and document slots have separate budgets. Every response-dependent
request is durably frozen before dispatch; exhausted discovery is never complete.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
import json
import re
from urllib.parse import urlsplit

import httpx

from app.services.opendart_financial_recovery_service import (
    LIST_ENDPOINT, STATEMENT_ENDPOINT, authoritative_filings,
)
from app.services.sec_financial_snapshot_service import _linked_documents
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = "bounded-official-financial-acquisition-v1"
RETAINED = frozenset({"SNDK", "005930", "047810"})


class AcquisitionDenied(ValueError):
    pass


class SystemicStop(AcquisitionDenied):
    pass


@dataclass(frozen=True)
class Limits:
    discovery: int
    candidates: int
    current: int
    prior: int
    documents_per_filing: int
    linked_exhibits: int
    indexes_per_filing: int
    companyfacts: int

    @property
    def maximum_logical(self):
        return self.discovery + self.companyfacts + (self.current + self.prior) * (
            self.documents_per_filing + self.indexes_per_filing)


# Class-level resource limits, not coverage targets. Overflow is an explicit denial.
DOMESTIC = Limits(1, 32, 1, 1, 1, 0, 0, 1)
FOREIGN = Limits(1, 128, 2, 2, 3, 2, 1, 1)
DART = Limits(2, 200, 1, 1, 2, 0, 0, 0)


def make_plan(security, *, market, cutoff, run_id):
    if cutoff.utcoffset() is None or security["ticker"] in RETAINED:
        raise AcquisitionDenied("retained_or_naive_cutoff")
    if not all(security.get(k) for k in ("canonical_company_id", "canonical_security_id", "identity_provider")):
        raise AcquisitionDenied("SECURITY_IDENTITY_UNRESOLVED")
    if market == "us":
        issuer = str(security.get("cik") or "")
        kind = security.get("issuer_type")
        if kind not in {"domestic_us", "foreign_private_issuer", "adr"} or not re.fullmatch(r"\d{1,10}", issuer):
            raise AcquisitionDenied("SECURITY_IDENTITY_UNRESOLVED")
        limits = DOMESTIC if kind == "domestic_us" else FOREIGN
        forms = ["10-Q", "10-K", "10-Q/A", "10-K/A"] if limits == DOMESTIC else ["6-K", "20-F", "6-K/A", "20-F/A"]
        provider = "sec_edgar"
        issuer = issuer.zfill(10)
    elif market == "kr":
        issuer = str(security.get("corp_code") or "")
        if not re.fullmatch(r"\d{8}", issuer):
            raise AcquisitionDenied("SECURITY_IDENTITY_UNRESOLVED")
        limits, forms, provider = DART, ["11013", "11012", "11014", "11011"], "opendart"
    else:
        raise AcquisitionDenied("unsupported_market")
    names = ({'SEC_MAX_DISCOVERY_REQUESTS':limits.discovery,
        'SEC_MAX_DISCOVERY_PAGES_OR_INDEX_FILES':limits.discovery + (limits.current+limits.prior)*limits.indexes_per_filing,
        'SEC_MAX_CANDIDATE_FILINGS':limits.candidates, 'SEC_MAX_SELECTED_CURRENT_FILINGS':limits.current,
        'SEC_MAX_SELECTED_PRIOR_FILINGS':limits.prior, 'SEC_MAX_DOCUMENTS_PER_FILING':limits.documents_per_filing,
        'SEC_MAX_LINKED_EXHIBITS_PER_FILING':limits.linked_exhibits,
        'SEC_MAX_TOTAL_LOGICAL_REQUESTS_PER_SUBJECT':limits.maximum_logical} if market=='us' else {
        'DART_MAX_DISCOVERY_PAGES':limits.discovery, 'DART_MAX_CANDIDATE_FILINGS':limits.candidates,
        'DART_MAX_SELECTED_CURRENT_FILINGS':limits.current, 'DART_MAX_SELECTED_PRIOR_FILINGS':limits.prior,
        'DART_MAX_STATEMENT_REQUESTS_PER_FILING':limits.documents_per_filing,
        'DART_MAX_TOTAL_LOGICAL_REQUESTS_PER_SUBJECT':limits.maximum_logical})
    return {"contract": CONTRACT, "run_id": run_id, "ticker": security["ticker"],
        "market": market, "provider": provider, "issuer": issuer,
        "security": security, "identity_sha256": digest(security),
        "cutoff": cutoff.isoformat(), "begin": (cutoff.date() - timedelta(days=550)).isoformat(),
        "forms": forms, "limits": asdict(limits), "named_caps": names, "timeout_seconds": 600,
        "maximum_retries_per_request": 2, "maximum_attempts_per_request": 3,
        "planned_logical_requests": limits.discovery + limits.companyfacts,
        "maximum_logical_requests": limits.maximum_logical,
        "maximum_HTTP_attempts": limits.maximum_logical * 3,
        "planned_retry_attempts": 0, "redirects": False,
        "selection": "latest_period_current_and_prior_year_comparable_no_value_ranking",
        "scope": "reported_revenue_operating_income_net_income_only"}


def sec_selection(payload, plan):
    if str(payload.get("cik", "")).lstrip("0") != plan["issuer"].lstrip("0"):
        raise AcquisitionDenied("SECURITY_IDENTITY_UNRESOLVED")
    recent = payload.get("filings", {}).get("recent", {})
    names = ("form", "accessionNumber", "primaryDocument", "filingDate", "reportDate")
    if not all(isinstance(recent.get(k), list) for k in names):
        raise AcquisitionDenied("DOCUMENT_UNAVAILABLE")
    if len({len(recent[k]) for k in names}) != 1:
        raise AcquisitionDenied("LINEAGE_UNRESOLVED")
    rows = [dict(zip(names, values, strict=True)) for values in zip(*(recent[k] for k in names), strict=True)]
    cutoff = plan["cutoff"][:10]
    candidates = [r for r in rows if r["form"] in plan["forms"] and plan["begin"] <= r["filingDate"] <= cutoff]
    # Historical submission files may contain filings in the requested window.
    # This route authorizes recent only, so it cannot silently claim full discovery.
    archived = payload.get("filings", {}).get("files", [])
    if any(not f.get("filingTo") or f["filingTo"] >= plan["begin"] for f in archived):
        raise AcquisitionDenied("SEC_DISCOVERY_BOUND_EXHAUSTED")
    if len(candidates) > plan["limits"]["candidates"]:
        raise AcquisitionDenied("SEC_DISCOVERY_BOUND_EXHAUSTED")
    for r in candidates:
        if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", r["accessionNumber"]):
            raise AcquisitionDenied("LINEAGE_UNRESOLVED")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", r["primaryDocument"]):
            raise AcquisitionDenied("DOCUMENT_UNAVAILABLE")
    selected = []
    groups = [candidates] if '10-Q' in plan['forms'] else [
        [r for r in candidates if r["form"].split('/')[0] == form] for form in ('6-K','20-F')]
    for group in groups:
        if not group:
            continue
        # An absent report date is not fabricated. Filing date selects discovery,
        # while extraction must still prove the economic period independently.
        current = max(group, key=lambda r: (r["reportDate"] or r["filingDate"], r["filingDate"], r["accessionNumber"]))
        selected.append({**current, "role": "current"})
        if current["reportDate"]:
            end = date.fromisoformat(current["reportDate"])
            peers = [r for r in group if r["reportDate"] and r["form"].split('/')[0] == current["form"].split('/')[0]
                     and 330 <= (end - date.fromisoformat(r["reportDate"])).days <= 400]
            if peers:
                prior = max(peers, key=lambda r: (r["reportDate"], r["filingDate"], r["accessionNumber"]))
                selected.append({**prior, "role": "prior"})
    return selected


def sec_base(plan, filing):
    return f'https://www.sec.gov/Archives/edgar/data/{int(plan["issuer"])}/{filing["accessionNumber"].replace("-", "")}/'


def exhibit_selection(index, primary_text, plan, filing):
    base = sec_base(plan, filing)
    primary = base + filing["primaryDocument"]
    urls = set()
    for item in index.get("directory", {}).get("item", []):
        name = str(item.get("name", ""))
        if re.search(r"(?:ex-?99|earn|result|release|financial)", name.lower()):
            urls.add(base + name)
    for href, _label in _linked_documents(primary_text):
        urls.add(str(httpx.URL(primary).join(href)))
    urls.discard(primary)
    if any(not u.startswith(base) or not re.fullmatch(r"[A-Za-z0-9_.-]+", u[len(base):]) for u in urls):
        raise AcquisitionDenied("SEC_DOCUMENT_SOURCE_SCOPE_DENIED")
    if len(urls) > plan["limits"]["linked_exhibits"]:
        raise AcquisitionDenied("SEC_DOCUMENT_BOUND_EXHAUSTED")
    return sorted(urls)


def dart_selection(rows, plan):
    if len(rows) > plan["limits"]["candidates"]:
        raise AcquisitionDenied("OPENDART_DISCOVERY_BOUND_EXHAUSTED")
    if any(r.get("corp_code") != plan["issuer"] for r in rows):
        raise AcquisitionDenied("SECURITY_IDENTITY_UNRESOLVED")
    if any(not re.fullmatch(r'\d{8}', str(r.get('rcept_dt') or '')) or
           not plan['begin'].replace('-','') <= r['rcept_dt'] <= plan['cutoff'][:10].replace('-','') for r in rows):
        raise AcquisitionDenied('DISCOVERY_DATE_WINDOW_MISMATCH')
    selected, history = authoritative_filings(rows, ticker=plan["ticker"], corp_code=plan["issuer"], limit=1)
    if not selected:
        return []
    current = selected[0]
    prior = [r for r in history if r.report_code == current.report_code and r.business_year == current.business_year - 1]
    return [("current", current)] + ([("prior", max(prior, key=lambda r: (r.receipt_date, r.correction, r.receipt_no)))] if prior else [])


def retryable(exc=None, status=None, provider_status=None):
    if provider_status is not None:
        return provider_status == "800"
    return isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, TimeoutError)) or status in {408, 429, 500, 502, 503, 504}


class BoundedReader:
    def __init__(self, plan, output, *, api_key=None, user_agent=None, transport=None, guard=None):
        self.plan = json.loads(json.dumps(plan))
        self.plan_sha = digest(plan)
        self.output = output
        self.api_key = api_key
        self.user_agent = user_agent
        self.transport = transport
        self.guard = guard
        self.logical = 0
        self.attempts = 0
        self.stage_counts = {}
        self.receipts = []
        self.filings = []
        self.filing_counts = {}

    def select(self, filings):
        if self.filings:
            raise SystemicStop("filing_selection_already_frozen")
        for role in ('current', 'prior'):
            if sum(r['role'] == role for r in filings) > self.plan['limits'][role]:
                raise SystemicStop("filing_selection_budget_exceeded")
        self.filings = json.loads(json.dumps(filings))
        durable_json(self.output / 'selected-filings.json', self.filings, exclusive=True)

    def _scope(self, stage, url, params):
        plan = self.plan
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.query or parsed.fragment or parsed.username:
            raise SystemicStop("unexpected_provider_request")
        if plan["provider"] == "sec_edgar":
            allowed = {"discovery": f'https://data.sec.gov/submissions/CIK{plan["issuer"]}.json',
                "companyfacts": f'https://data.sec.gov/api/xbrl/companyfacts/CIK{plan["issuer"]}.json'}
            if params or (stage in allowed and url != allowed[stage]):
                raise SystemicStop("unexpected_provider_request")
            if stage not in allowed and (stage not in {"index", "document"} or not re.fullmatch(
                    rf'https://www\.sec\.gov/Archives/edgar/data/{int(plan["issuer"])}/\d{{18}}/[A-Za-z0-9_.-]+', url)):
                raise SystemicStop("unexpected_provider_request")
        else:
            if stage not in {"discovery", "statement"} or url != {"discovery": LIST_ENDPOINT, "statement": STATEMENT_ENDPOINT}[stage]:
                raise SystemicStop("unexpected_provider_request")
            if params.get("corp_code") != plan["issuer"] or "crtfc_key" in params:
                raise SystemicStop("unexpected_issuer_or_secret_in_plan")

    async def read(self, stage, url, params=None, *, filing=None):
        params = dict(params or {})
        self._scope(stage, url, params)
        if digest(self.plan) != self.plan_sha:
            raise SystemicStop("plan_drift")
        limits = self.plan["limits"]
        if stage in {'document', 'index', 'statement'}:
            if stage == 'statement':
                selected = [r for r in self.filings if r['receipt_no'] == (filing or {}).get('receipt_no')]
                if len(selected) != 1 or filing.get('basis') not in {'CFS', 'OFS'} or params != {
                        'corp_code': self.plan['issuer'], 'bsns_year': selected[0]['business_year'],
                        'reprt_code': selected[0]['report_code'], 'fs_div': filing['basis']}:
                    raise SystemicStop('statement_not_in_frozen_selection')
                key = filing['receipt_no']
            else:
                if filing not in self.filings or not url.startswith(sec_base(self.plan, filing)):
                    raise SystemicStop('document_not_in_frozen_selection')
                key = filing['accessionNumber']
            field = (key, stage)
            limit = limits['indexes_per_filing'] if stage == 'index' else limits['documents_per_filing']
            if self.filing_counts.get(field, 0) >= limit:
                raise SystemicStop('per_filing_document_budget_exceeded')
            self.filing_counts[field] = self.filing_counts.get(field, 0) + 1
        if self.plan['provider'] == 'opendart' and stage == 'discovery':
            page = self.stage_counts.get(stage, 0) + 1
            if params != {'corp_code': self.plan['issuer'], 'bgn_de': self.plan['begin'].replace('-', ''),
                    'end_de': self.plan['cutoff'][:10].replace('-', ''), 'pblntf_ty': 'A',
                    'last_reprt_at': 'N', 'page_count': 100, 'page_no': page}:
                raise SystemicStop('discovery_outside_frozen_window')
        maximum = {"discovery": limits["discovery"], "companyfacts": limits["companyfacts"],
            "index": (limits["current"] + limits["prior"]) * limits["indexes_per_filing"],
            "document": (limits["current"] + limits["prior"]) * limits["documents_per_filing"],
            "statement": (limits["current"] + limits["prior"]) * limits["documents_per_filing"]}[stage]
        if self.logical >= self.plan["maximum_logical_requests"] or self.stage_counts.get(stage, 0) >= maximum:
            raise SystemicStop("request_budget_enforcement_stop")
        self.logical += 1
        self.stage_counts[stage] = self.stage_counts.get(stage, 0) + 1
        name = f'request-{self.logical:03d}'
        frozen = {"stage": stage, "method": "GET", "url": url, "params": params, "filing": filing,
            "plan_sha256": self.plan_sha, "logical_id": self.plan["ticker"] + ":" + name}
        durable_json(self.output / (name + '.plan.json'), frozen, exclusive=True)
        request_sha = digest(frozen)
        wire_params = {**params, "crtfc_key": self.api_key} if self.plan["provider"] == "opendart" else params
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"} if self.user_agent else {}
        for attempt in range(1, 4):
            if self.guard:
                self.guard()
            self.attempts += 1
            started = datetime.now(timezone.utc).isoformat()
            receipt = {"logical_id": frozen["logical_id"], "stage": stage, "plan_sha256": self.plan_sha,
                "request_sha256": request_sha, "attempt": attempt, "attempt_ordinal": self.attempts,
                "started_at": started, "timeout_seconds": 600, "retry": attempt > 1,
                "retry_reason": self.receipts[-1]["failure_class"] if attempt > 1 else None,
                "page": params.get("page_no"), "filing": filing}
            artifact_name = f'{name}-attempt-{attempt}'
            durable_json(self.output / (artifact_name + '.start.json'), receipt, exclusive=True)
            raw, status, provider_status, error, systemic = None, None, None, None, None
            try:
                async with httpx.AsyncClient(timeout=600, follow_redirects=False, headers=headers, transport=self.transport) as client:
                    response = await asyncio.wait_for(client.get(url, params=wire_params), timeout=600)
                raw, status = response.content, response.status_code
                if self.api_key and self.api_key.encode() in raw:
                    raise SystemicStop("provider_response_secret_echo")
                if status in {401, 403}:
                    raise SystemicStop("provider_authorization_denied")
                if self.plan["provider"] == "opendart" and status == 200:
                    provider_status = response.json().get("status")
                failed = status != 200 or (provider_status not in {None, "000", "013"})
                transient = retryable(status=status, provider_status=provider_status)
                failure = "TRANSIENT_PROVIDER" if failed and transient else "PROVIDER_DENIAL" if failed else None
            except SystemicStop as exc:
                systemic, transient, failure = str(exc), False, 'SYSTEMIC_STOP'
                if systemic == 'provider_response_secret_echo':
                    raw = None
            except (httpx.HTTPError, TimeoutError, ValueError) as exc:
                error = type(exc).__name__
                transient = retryable(exc=exc)
                failure = "TRANSIENT_TRANSPORT" if transient else "NONRETRYABLE_TRANSPORT_OR_SCHEMA"
            receipt.update(finished_at=datetime.now(timezone.utc).isoformat(), HTTP_status=status,
                provider_status=provider_status, error_type=error, failure_class=failure,
                systemic_reason=systemic,
                raw_sha256=sha256_bytes(raw) if raw is not None else None,
                artifact=artifact_name + '.body' if raw is not None else None)
            if raw is not None:
                durable_bytes(self.output / receipt['artifact'], raw, exclusive=True)
            durable_json(self.output / (artifact_name + '.receipt.json'), receipt, exclusive=True)
            self.receipts.append(receipt)
            if systemic:
                raise SystemicStop(systemic)
            if not failure:
                return raw, receipt
            if not transient or attempt == 3:
                raise AcquisitionDenied(failure)
            await asyncio.sleep(attempt)
        raise AssertionError("unreachable")


async def collect(reader):
    plan = reader.plan
    output = {"plan_sha256": reader.plan_sha, "selected_filings": [], "documents": [], "denials": []}
    reader.output_state = output
    if plan["provider"] == "sec_edgar":
        raw, _receipt = await reader.read("discovery", f'https://data.sec.gov/submissions/CIK{plan["issuer"]}.json')
        filings = sec_selection(json.loads(raw), plan)
        output["selected_filings"] = filings
        reader.select(filings)
        try:
            raw, receipt = await reader.read("companyfacts", f'https://data.sec.gov/api/xbrl/companyfacts/CIK{plan["issuer"]}.json')
        except SystemicStop:
            raise
        except AcquisitionDenied as exc:
            output['source_notes']=[{'stage':'companyfacts','reason':str(exc)}]
        else:
            payload = json.loads(raw)
            if str(payload.get("cik", "")).lstrip("0") != plan["issuer"].lstrip("0"):
                raise AcquisitionDenied("SECURITY_IDENTITY_UNRESOLVED")
            output["companyfacts_artifact"] = receipt["artifact"]
        for filing in filings:
            base = sec_base(plan, filing)
            index = {}
            if plan["limits"]["indexes_per_filing"]:
                raw, _ = await reader.read("index", base + 'index.json', filing=filing)
                index = json.loads(raw)
            raw, receipt = await reader.read("document", base + filing["primaryDocument"], filing=filing)
            output["documents"].append({"filing": filing, "artifact": receipt["artifact"], "url": base + filing["primaryDocument"]})
            if plan["limits"]["linked_exhibits"]:
                try:
                    exhibits = exhibit_selection(index, raw.decode('utf-8', errors='replace'), plan, filing)
                except AcquisitionDenied as exc:
                    output["denials"].append(str(exc))
                    continue
                for url in exhibits:
                    raw, receipt = await reader.read("document", url, filing=filing)
                    output["documents"].append({"filing": filing, "artifact": receipt["artifact"], "url": url})
    else:
        rows = []
        for page in range(1, plan["limits"]["discovery"] + 1):
            params = {"corp_code": plan["issuer"], "bgn_de": plan["begin"].replace('-', ''),
                "end_de": plan["cutoff"][:10].replace('-', ''), "pblntf_ty": "A", "last_reprt_at": "N",
                "page_count": 100, "page_no": page}
            raw, _ = await reader.read("discovery", LIST_ENDPOINT, params)
            payload = json.loads(raw)
            rows.extend(payload.get("list", []))
            total = int(payload.get("total_page") or 1)
            if total > plan["limits"]["discovery"]:
                raise AcquisitionDenied("OPENDART_DISCOVERY_BOUND_EXHAUSTED")
            if page >= total:
                break
        filings = dart_selection(rows, plan)
        output["selected_filings"] = [{"role": role, **asdict(filing), "receipt_date": filing.receipt_date.isoformat()} for role, filing in filings]
        reader.select(output["selected_filings"])
        for role, filing in filings:
            for basis in ('CFS', 'OFS'):
                params = {"corp_code": plan["issuer"], "bsns_year": filing.business_year,
                    "reprt_code": filing.report_code, "fs_div": basis}
                metadata = {"role": role, "receipt_no": filing.receipt_no, "basis": basis}
                raw, receipt = await reader.read("statement", STATEMENT_ENDPOINT, params, filing=metadata)
                output["documents"].append({"filing": metadata, "artifact": receipt["artifact"]})
    return output
