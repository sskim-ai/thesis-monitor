"""Explicit one-issuer acquisition; never issues native financial permissions.

No settings/DB imports or dotenv lookup. Public response provenance and native
source-use authorization are separate. Offline parser output is unqualified.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import html
import http.client
import io
import json
import multiprocessing
import threading
import os
from pathlib import Path
import re
import ssl
import sys
import time
from urllib.parse import urlencode
from urllib.parse import unquote, urljoin, urlsplit, parse_qsl
import xml.etree.ElementTree as ET
import zipfile
from zoneinfo import ZoneInfo

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import sealed_opendart_contract  # noqa: E402

VERSION = "opendart-direct-revenue-capture-v1"
TRANSPORT_VERSION = "opendart-endpoint-request-contract-v2"
HOST = "opendart.fss.or.kr"
STOCK = "005930"  # Acquisition authorization, never an economic selector.
COMPANY_SEED = "00126380"  # Historical diagnostic hint, not issuer authority.
ENDPOINTS = {
    "company.json": {"corp_code"},
    "corpCode.xml": set(),
    "list.json": {
        "corp_code",
        "bgn_de",
        "end_de",
        "pblntf_ty",
        "last_reprt_at",
        "page_no",
        "page_count",
    },
    "fnlttSinglAcntAll.json": {"corp_code", "bsns_year", "reprt_code", "fs_div"},
    "fnlttSinglAcnt.json": {"corp_code", "bsns_year", "reprt_code"},
    "document.xml": {"rcept_no"},
}
MAX_RAW = 24 * 1024 * 1024
MAX_XML = 64 * 1024 * 1024


class PilotError(ValueError):
    """Only fixed, nonsecret error codes cross the acquisition boundary."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def request_contract(endpoint: str) -> dict:
    """Compose the pure provider-owned JSON contract; never import DB owners."""
    if endpoint not in ENDPOINTS:
        raise PilotError("REQUEST_SCOPE_DENIED")
    inherited = sealed_opendart_contract.header_contract()
    headers = sealed_opendart_contract.opendart_headers()
    if inherited["follow_redirects"] is not False or inherited["headers"] != sorted(
        (key.lower(), value) for key, value in headers.items()
    ):
        raise PilotError("PROVIDER_HEADER_CONTRACT_DRIFT")
    if endpoint.endswith(".json"):
        content_types = ["application/json"]
    else:
        # The official guide specifies ZIP bytes and XML error results, not a
        # mandatory Accept value. This is an explicit bounded client policy.
        headers["Accept"] = (
            "application/zip, application/octet-stream;q=0.9, "
            "application/xml;q=0.5, text/xml;q=0.5"
        )
        content_types = ["application/zip", "application/octet-stream", "application/xml", "text/xml"]
    headers["Accept-Encoding"] = "identity"
    return dict(
        version=TRANSPORT_VERSION,
        method="GET",
        scheme="https",
        host=HOST,
        port=443,
        endpoint="/api/" + endpoint,
        parameter_names=sorted(ENDPOINTS[endpoint]),
        provider_header_contract=inherited,
        headers=headers,
        accepted_content_types=content_types,
        follow_redirects=False,
        proxy_environment=False,
        tls_verify=True,
    )


def contract_digest(contract: dict) -> str:
    return digest(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode())


def public_request_identity(endpoint: str, params: dict, contract: dict) -> dict:
    if endpoint not in ENDPOINTS or set(params) != ENDPOINTS[endpoint]:
        raise PilotError("REQUEST_SCOPE_DENIED")
    return dict(
        contract=contract,
        business_parameters=dict(params),
        encoded_business_query=urlencode(params),
        credential_slot="IN_MEMORY_ONLY_NOT_HASHED",
    )


def response_content_type(response) -> tuple[str, bool]:
    values = response.headers.get_all("Content-Type", [])
    if len(values) != 1 or not isinstance(values[0], str) or len(values[0]) > 256:
        return "UNRECOGNIZED_NOT_LOGGED", False
    match = re.fullmatch(
        r'\s*([a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+)'
        r'(?:\s*;\s*charset\s*=\s*(?:"[a-z0-9_-]+"|[a-z0-9_-]+))?\s*',
        values[0], re.I,
    )
    if not match:
        return "UNRECOGNIZED_NOT_LOGGED", False
    mime = match[1].lower()
    known = {"application/json", "application/zip", "application/xml", "text/xml", "application/octet-stream"}
    return (mime if mime in known else "UNRECOGNIZED_NOT_LOGGED"), True


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PilotError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def response_json(raw: bytes) -> dict:
    try:
        value = json.loads(raw, object_pairs_hook=_unique)
    except (UnicodeError, ValueError):
        raise PilotError("INVALID_RESPONSE_JSON") from None
    if not isinstance(value, dict):
        raise PilotError("INVALID_RESPONSE_SHAPE")
    status = value.get("status")
    if status != "000":
        code = status if status in {"013", "020", "010", "011", "012", "800"} else "UNKNOWN"
        raise PilotError("OPENDART_STATUS_" + code)
    return value


def safe_text(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError:
        raise PilotError("UNSUPPORTED_TEXT_ENCODING") from None
    if "\x00" in text or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise PilotError("XML_ENTITY_OR_ENCODING_DENIED")
    declaration = re.search(r"<\?xml[^>]*encoding\s*=\s*[\'\"]([^\'\"]+)", text, re.I)
    if declaration and declaration[1].lower() not in {"utf-8", "utf8"}:
        raise PilotError("UNSUPPORTED_TEXT_ENCODING")
    return text


def screen_response(raw: bytes, key: str, endpoint: str) -> None:
    """Inspect supported encodings before persistence; unknown formats reject."""
    if key.encode() in raw:
        raise PilotError("SECRET_REFLECTION_DENIED")
    bodies = [raw]
    if raw.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                members = archive.infolist()
                if archive.comment or any(item.comment for item in members):
                    raise PilotError("SECRET_SCAN_UNSUPPORTED_ARCHIVE_COMMENT")
                if len(members) > 2000 or sum(item.file_size for item in members) > MAX_XML:
                    raise PilotError("SECRET_SCAN_ARCHIVE_SIZE_LIMIT")
                bodies = []
                for member in members:
                    if member.is_dir():
                        continue
                    if Path(member.filename).suffix.lower() not in {
                        ".xml",
                        ".html",
                        ".htm",
                        ".txt",
                        ".xsd",
                    }:
                        raise PilotError("SECRET_SCAN_UNSUPPORTED_MEMBER")
                    bodies.append(archive.read(member))
        except (zipfile.BadZipFile, RuntimeError):
            raise PilotError("SECRET_SCAN_INVALID_ARCHIVE") from None

    def inspect_string(text):
        for _ in range(5):
            if key in text:
                raise PilotError("SECRET_REFLECTION_DENIED")
            normalized = html.unescape(unquote(text))
            if normalized == text:
                return
            text = normalized
        raise PilotError("SECRET_SCAN_ENCODING_DEPTH_UNRESOLVED")

    def inspect_value(value):
        if isinstance(value, str):
            inspect_string(value)
        elif isinstance(value, list):
            for item in value:
                inspect_value(item)
        elif isinstance(value, dict):
            for name, item in value.items():
                inspect_string(name)
                inspect_value(item)

    for body in bodies:
        text = safe_text(body)
        inspect_string(text)
        if endpoint.endswith(".json"):
            try:
                value = json.loads(text, object_pairs_hook=_unique)
            except ValueError:
                raise PilotError("INVALID_RESPONSE_JSON") from None
            inspect_value(value)


def redirect_metadata(locations, endpoint, key, params=None):
    """Classify in memory; output only fixed public names and bounded flags."""
    result = dict(
        present=bool(locations),
        classification="UNKNOWN_LOCATION",
        followed=False,
        credential_replayed=False,
    )
    if len(locations) != 1 or endpoint not in ENDPOINTS:
        return result
    location = locations[0]
    if not isinstance(location, str) or len(location) > 8192:
        return result
    # No untrusted URL component is returned, even when a key is reflected.
    public_paths = {"/", "/index.jsp", "/error.jsp", "/error.html", "/error1.html"} | {
        "/api/" + name for name in ENDPOINTS
    }
    public_hosts = {HOST, "dart.fss.or.kr", "www.fss.or.kr", "fss.or.kr"}
    try:
        if any(ord(char) < 32 or ord(char) == 127 for char in location) or "\\" in location:
            return result
        decoded = location
        for _ in range(5):
            normalized = html.unescape(unquote(decoded))
            if normalized == decoded:
                break
            decoded = normalized
        else:
            return result
        source_uri = (
            "https://"
            + HOST
            + "/api/"
            + endpoint
            + "?"
            + urlencode({**(params or {}), "crtfc_key": key})
        )
        destination = urlsplit(urljoin(source_uri, location))
        hostname = (destination.hostname or "").encode("idna").decode("ascii").lower()
        port = destination.port
        pairs = parse_qsl(destination.query, keep_blank_values=True, max_num_fields=64)
        names = {name.lower() for name, _ in pairs}
        credential_names = {
            "crtfc_key",
            "api_key",
            "apikey",
            "key",
            "token",
            "access_token",
            "authorization",
        }
        credential_present = bool(
            (key and (key in decoded or key in unquote(destination.query)))
            or names & credential_names
            or destination.username is not None
            or destination.password is not None
        )
        scheme = destination.scheme.lower()
        allowed_path = destination.path == "/api/" + endpoint
        same_origin = scheme == "https" and hostname == HOST and port in {None, 443}
        result.update(
            classification="CLASSIFIED_NO_FOLLOW",
            scheme=scheme if scheme in {"https", "http"} else "UNRECOGNIZED_NOT_LOGGED",
            hostname=hostname if hostname in public_hosts else "UNRECOGNIZED_NOT_LOGGED",
            explicit_port=port,
            canonical_path=destination.path
            if destination.path in public_paths
            else "UNRECOGNIZED_NOT_LOGGED",
            known_key_parameter_present="crtfc_key" in names,
            unexpected_parameters_present=bool(names - {"crtfc_key"}),
            query_present=bool(destination.query),
            fragment_present=bool(destination.fragment),
            same_origin=same_origin,
            tls_downgrade=scheme == "http",
            allowed_path=allowed_path,
            credential_in_redirect=credential_present,
            policy="STOP_REQUIRES_INDEPENDENT_REVIEW",
        )
        if not same_origin or not allowed_path or credential_present:
            result["policy"] = "REFUSE_REDIRECT"
        if (
            result["canonical_path"] == "UNRECOGNIZED_NOT_LOGGED"
            or result["hostname"] == "UNRECOGNIZED_NOT_LOGGED"
        ):
            result["classification"] = "UNKNOWN_LOCATION_COMPONENT_REDACTED"
        return result
    except (ValueError, UnicodeError, TypeError):
        return result


def _transport_worker(pipe, endpoint, params, key, timeout, frozen_request=None):
    # Child carries bytes only. Parent owns time budget, persistence and receipts.
    connection = None
    try:
        params = dict(params)
        descriptor = request_contract(endpoint)
        expected = public_request_identity(endpoint, params, descriptor)
        if frozen_request is not None and frozen_request != expected:
            raise PilotError("REQUEST_DESCRIPTOR_DRIFT")
        if set(params) != ENDPOINTS[endpoint]:
            raise PilotError("REQUEST_SCOPE_DENIED")
        public_request = public_request_identity(endpoint, params, descriptor)
        null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null, 1)
        os.dup2(null, 2)
        os.close(null)
        connection = http.client.HTTPSConnection(
            HOST, timeout=timeout, context=ssl.create_default_context()
        )
        connection.set_debuglevel(0)
        connection.request(
            "GET",
            "/api/" + endpoint + "?" + urlencode({**params, "crtfc_key": key}),
            headers=descriptor["headers"],
        )
        response = connection.getresponse()
        content_type, unambiguous_type = response_content_type(response)
        if response.status != 200:
            redirect = (
                redirect_metadata(response.headers.get_all("Location", []), endpoint, key, params)
                if 300 <= response.status < 400
                else None
            )
            pipe.send(
                dict(
                    error="HTTP_STATUS_REJECTED",
                    transient=False,
                    http_status=response.status,
                    content_type=content_type,
                    redirect=redirect,
                    request_contract_sha256=contract_digest(descriptor),
                    public_request_sha256=contract_digest(public_request),
                )
            )
            return
        if not unambiguous_type or content_type not in descriptor["accepted_content_types"]:
            raise PilotError("RESPONSE_CONTENT_TYPE_DENIED")
        chunks = []
        size = 0
        while True:
            chunk = response.read1(min(65536, MAX_RAW + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_RAW:
                raise PilotError("RESPONSE_SIZE_LIMIT")
            chunks.append(chunk)
        pipe.send(
            dict(
                raw=b"".join(chunks),
                http_status=200,
                content_type=content_type,
                error=None,
                transient=False,
                request_contract_sha256=contract_digest(descriptor),
                public_request_sha256=contract_digest(public_request),
            )
        )
    except (TimeoutError, ConnectionError, ssl.SSLError):
        pipe.send(dict(error="TRANSIENT_TRANSPORT_FAILURE", transient=True))
    except PilotError as exc:
        pipe.send(dict(error=str(exc), transient=False))
    except Exception:
        pipe.send(dict(error="TRANSPORT_FAILURE", transient=False))
    finally:
        if connection is not None:
            connection.close()
        pipe.close()


def bounded_exchange(endpoint, params, key, timeout, *, frozen_request=None):
    """A supervised process bounds DNS/TLS/headers/body, not socket phases alone."""
    params = dict(params)
    expected = public_request_identity(endpoint, params, request_contract(endpoint))
    frozen_request = deepcopy(expected if frozen_request is None else frozen_request)
    if frozen_request != expected:
        raise PilotError("REQUEST_DESCRIPTOR_DRIFT")
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_transport_worker,
        args=(child, endpoint, params, key, timeout, frozen_request),
    )
    process.start()
    child.close()
    result = dict(error="TRANSIENT_TRANSPORT_FAILURE", transient=True)
    completed = threading.Event()
    received = []

    def receive():
        try:
            received.append(parent.recv())
        except (EOFError, OSError, ValueError):
            received.append(dict(error="TRANSPORT_WORKER_FAILED", transient=False))
        finally:
            completed.set()

    reader = threading.Thread(target=receive, daemon=True)
    reader.start()
    try:
        if completed.wait(timeout):
            result = received[0]
        else:
            result["deadline_expired"] = True
    finally:
        if not result.get("deadline_expired"):
            process.join(0.2)
        if process.is_alive():
            process.terminate()
        process.join(1)
        if process.is_alive():
            process.kill()
            process.join(1)
        reader.join(1)
        parent.close()
        result.update(
            child_pid=process.pid,
            child_exit=process.exitcode,
            lifecycle="DEADLINE_TERMINATED"
            if result.get("deadline_expired")
            else "RESPONSE_RETURNED",
            reader_terminated=not reader.is_alive(),
        )
        if process.is_alive() or reader.is_alive():
            raise PilotError("TRANSPORT_PROCESS_CLOSURE_GAP")
    return result


def resolve_company(raw: bytes) -> dict:
    if len(raw) > MAX_RAW:
        raise PilotError("SIZE_LIMIT")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.infolist()
            if (
                len(members) != 1
                or members[0].filename != "CORPCODE.xml"
                or members[0].file_size > MAX_XML
            ):
                raise PilotError("CORP_ARCHIVE_SHAPE")
            xml = archive.read(members[0])
        root = ET.fromstring(safe_text(xml))
    except (zipfile.BadZipFile, ET.ParseError, RuntimeError):
        raise PilotError("INVALID_CORP_ARCHIVE") from None
    matches = [
        {child.tag: (child.text or "").strip() for child in row}
        for row in root.findall("list")
        if row.findtext("stock_code", "").strip() == STOCK
    ]
    if len(matches) != 1 or not re.fullmatch(r"\d{8}", matches[0].get("corp_code", "")):
        raise PilotError("ISSUER_IDENTITY_AMBIGUOUS")
    if matches[0].get("corp_name") != "\uc0bc\uc131\uc804\uc790":
        raise PilotError("ISSUER_NAME_MISMATCH")
    return {
        **matches[0],
        "mapping_sha256": digest(raw),
        "status": "PARSED_NOT_INDEPENDENTLY_QUALIFIED",
    }


def resolve_company_json(raw: bytes, candidate: str) -> dict:
    """Confirm response identity, without upgrading it to D01 source authority."""
    value = response_json(raw)
    if candidate != COMPANY_SEED or any(
        value.get(name) != expected
        for name, expected in {
            "corp_code": candidate, "stock_code": STOCK, "corp_name": "\uc0bc\uc131\uc804\uc790"
        }.items()
    ):
        raise PilotError("COMPANY_RESPONSE_IDENTITY_MISMATCH")
    return dict(
        corp_code=value["corp_code"],
        stock_code=value["stock_code"],
        corp_name=value["corp_name"],
        mapping_sha256=digest(raw),
        mapping_endpoint="/api/company.json",
        candidate_origin="HISTORICAL_HINT_ONLY",
        status="PARSED_NOT_INDEPENDENTLY_QUALIFIED",
    )


def select_filing(raw: bytes, company: dict, cutoff: date) -> dict:
    value = response_json(raw)
    if value.get("total_page") != 1 or len(value.get("list", [])) != value.get("total_count"):
        raise PilotError("INCOMPLETE_FILING_SEARCH")
    candidates = []
    for row in value["list"]:
        if row.get("corp_code") != company["corp_code"] or row.get("stock_code") != STOCK:
            raise PilotError("FILING_ISSUER_MISMATCH")
        try:
            received = datetime.strptime(row["rcept_dt"], "%Y%m%d").date()
        except (KeyError, ValueError, TypeError):
            raise PilotError("FILING_DATE_INVALID") from None
        if received > cutoff or not re.fullmatch(r"\d{14}", row.get("rcept_no", "")):
            raise PilotError("FILING_CUTOFF_OR_RECEIPT_INVALID")
        match = re.fullmatch(
            r"(\[[^\]]+\])?\s*(\ubd84\uae30\ubcf4\uace0\uc11c|\ubc18\uae30\ubcf4\uace0\uc11c|\uc0ac\uc5c5\ubcf4\uace0\uc11c)\s*\((\d{4})\.(\d{2})\)",
            row.get("report_nm", ""),
        )
        if not match:
            raise PilotError("UNCLASSIFIED_PERIODIC_FILING")
        correction, kind, year, month = match.groups()
        expected = {
            "03": ("\ubd84\uae30\ubcf4\uace0\uc11c", "11013"),
            "06": ("\ubc18\uae30\ubcf4\uace0\uc11c", "11012"),
            "09": ("\ubd84\uae30\ubcf4\uace0\uc11c", "11014"),
            "12": ("\uc0ac\uc5c5\ubcf4\uace0\uc11c", "11011"),
        }
        if month not in expected or kind != expected[month][0]:
            raise PilotError("REPORT_CALENDAR_UNRESOLVED")
        if year + month > received.strftime("%Y%m"):
            raise PilotError("FUTURE_REPORT_PERIOD")
        candidates.append(
            {
                **row,
                "bsns_year": year,
                "reprt_code": expected[month][1],
                "period_key": year + month,
                "correction": correction or None,
            }
        )
    if not candidates:
        raise PilotError("NO_ELIGIBLE_FILING")
    latest = max(row["period_key"] for row in candidates)
    versions = [row for row in candidates if row["period_key"] == latest]
    # An amendment chain needs independent reconciliation, not newest-wins.
    if len(versions) != 1 or versions[0]["correction"]:
        raise PilotError("CORRECTION_CHAIN_REVIEW_REQUIRED")
    return {
        **versions[0],
        "all_search_rows": candidates,
        "search_sha256": digest(raw),
        "release_time": None,
        "release_precision": "DATE_ONLY",
        "fs_div": "CFS",
    }


def _row_span(raw: bytes, index: int) -> tuple[int, int]:
    """Use the JSON decoder's offsets, preserving the original lexical row."""
    text = raw.decode("utf-8")
    decoder = json.JSONDecoder(object_pairs_hook=_unique)
    pos = text.index("{") + 1
    while True:
        pos = _whitespace(text, pos)
        key, pos = decoder.raw_decode(text, pos)
        pos = _whitespace(text, pos)
        if text[pos] != ":":
            raise PilotError("INVALID_ROW_SPAN")
        pos = _whitespace(text, pos + 1)
        if key == "list":
            if text[pos] != "[":
                raise PilotError("INVALID_ROW_SPAN")
            pos += 1
            for item in range(index + 1):
                start = _whitespace(text, pos)
                _, end = decoder.raw_decode(text, start)
                if item == index:
                    return len(text[:start].encode()), len(text[:end].encode())
                pos = _whitespace(text, end) + 1
        _, pos = decoder.raw_decode(text, pos)
        pos = _whitespace(text, pos)
        if text[pos] != ",":
            raise PilotError("MISSING_ROW")
        pos += 1


def _whitespace(text, pos):
    while pos < len(text) and text[pos] in " \r\n\t":
        pos += 1
    return pos


def amount_column_semantics(reprt_code: str, sj_div: str, field: str) -> str:
    """Classify documented income columns, never infer fiscal dates or scale."""
    if sj_div not in {"IS", "CIS"}:
        return "UNKNOWN_PERIOD"
    if reprt_code == "11011" and field == "thstrm_amount":
        return "annual"
    if reprt_code in {"11013", "11012", "11014"}:
        if field == "thstrm_amount":
            return "quarter_3_month"
        if field == "thstrm_add_amount":
            return "year_to_date"
    return "UNKNOWN_PERIOD"


def parse_revenue(raw: bytes, company: dict, filing: dict, generation: str) -> dict:
    if company.get("stock_code") != STOCK or filing.get("stock_code") != STOCK:
        raise PilotError("STOCK_IDENTITY_MISMATCH")
    rows = response_json(raw).get("list")
    if not isinstance(rows, list) or not rows:
        raise PilotError("MISSING_FINANCIAL_ROWS")
    selected = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise PilotError("INVALID_FINANCIAL_ROW")
        for key, expected in {
            "corp_code": company["corp_code"],
            "rcept_no": filing["rcept_no"],
            "bsns_year": filing["bsns_year"],
            "reprt_code": filing["reprt_code"],
        }.items():
            if row.get(key) != expected:
                raise PilotError("FINANCIAL_VERSION_MISMATCH")
        if row.get("fs_div", "CFS") != "CFS" or filing.get("fs_div") != "CFS":
            raise PilotError("STATEMENT_BASIS_MISMATCH")
        if row.get("account_id") in {"ifrs-full_Revenue", "ifrs_Revenue"}:
            selected.append((index, row))
    if len(selected) != 1:
        raise PilotError("REVENUE_ACCOUNT_AMBIGUOUS_OR_MISSING")
    index, row = selected[0]
    if row.get("sj_div") not in {"IS", "CIS"} or row.get("account_detail") != "-":
        raise PilotError("REVENUE_VARIANT_UNQUALIFIED")
    if row.get("currency") != "KRW":
        raise PilotError("CURRENCY_UNQUALIFIED")
    original = row.get("thstrm_amount")
    if (
        not isinstance(original, str)
        or not re.fullmatch(r"-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?", original)
        or len(original) > 48
    ):
        raise PilotError("DECIMAL_TEXT_INVALID")
    try:
        number = Decimal(original.replace(",", ""))
    except InvalidOperation:
        raise PilotError("DECIMAL_TEXT_INVALID") from None
    if number < 0 or number.adjusted() > 30:
        raise PilotError("REVENUE_RANGE_UNQUALIFIED")
    if not generation or not row.get("ord") or not row.get("thstrm_nm"):
        raise PilotError("OCCURRENCE_IDENTITY_MISSING")
    start, end = _row_span(raw, index)
    if json.loads(raw[start:end]) != row:
        raise PilotError("ROW_RECONSTRUCTION_FAILED")
    # No inferred fiscal dates or scale. A raw integer and KRW alone do not
    # independently prove the reporting calendar or display multiplier.
    return dict(
        contract=VERSION,
        producer=VERSION,
        generation=generation,
        stock_code=STOCK,
        corp_code=company["corp_code"],
        rcept_no=filing["rcept_no"],
        response_sha256=digest(raw),
        json_pointer=f"/list/{index}",
        row_byte_start=start,
        row_byte_end=end,
        row_sha256=digest(raw[start:end]),
        original_row=row,
        original_decimal_text=original,
        parsed_decimal=str(number),
        currency="KRW",
        statement_basis_query="CFS",
        unit_scale=None,
        canonical_value=None,
        current_period_start=None,
        current_period_end=None,
        amount_semantics_contract="opendart-income-column-semantics-v1",
        amount_field="thstrm_amount",
        amount_semantics=amount_column_semantics(
            row["reprt_code"], row["sj_div"], "thstrm_amount"
        ),
        cumulative_amount_semantics=amount_column_semantics(
            row["reprt_code"], row["sj_div"], "thstrm_add_amount"
        ),
        cumulative_field_not_substituted="thstrm_add_amount",
        prior_comparison="NOT_ADMITTED",
        source_status="CAPTURED_UNQUALIFIED",
        core_permission="NOT_ISSUED",
        unresolved=[
            "UNIT_SCALE_SOURCE_CONFIRMATION",
            "EXACT_FISCAL_PERIOD_CONFIRMATION",
            "INDEPENDENT_SOURCE_POLICY_REVIEW",
            "NATIVE_CONSUMER_AUTHORIZATION",
        ],
    )


def deny_native_use(_capture: dict, **_caller_grant) -> None:
    """There is no issuing authority in this acquisition-only module."""
    raise PilotError("NATIVE_CONSUMER_AUTHORITY_NOT_ISSUED")


class Collector:
    def __init__(self, key: str, root: Path, cutoff: datetime, *, route="legacy_zip"):
        if not key or not re.fullmatch(r"[A-Za-z0-9]{40}", key):
            raise PilotError("R15_OPENDART_AUTH_KEY_UNAVAILABLE")
        if cutoff.tzinfo is None:
            raise PilotError("CUTOFF_TIMEZONE_REQUIRED")
        if route not in {"legacy_zip", "json"}:
            raise PilotError("REQUEST_ROUTE_DENIED")
        root.mkdir(parents=True, exist_ok=False)
        self._key, self.root, self.cutoff = key, root, cutoff.astimezone(timezone.utc)
        self.generation = "opendart-pilot-" + self.cutoff.strftime("%Y%m%dT%H%M%SZ")
        self.route = route
        self.max_requests, self.max_retries = (4, 0) if route == "json" else (12, 2)
        self._contracts = {name: contract_digest(request_contract(name)) for name in ENDPOINTS}
        self._company_response = None
        self._company_confirmed = False
        self.started, self.count, self.retries = time.monotonic(), 0, 0
        self.corp_code = self.rcept_no = None
        self.financial_plan = None
        self.halted = False

    def _params(self, endpoint: str, params: dict):
        if endpoint not in ENDPOINTS or set(params) != ENDPOINTS[endpoint]:
            raise PilotError("REQUEST_SCOPE_DENIED")
        if self.route == "json":
            if endpoint not in {"company.json", "list.json", "fnlttSinglAcntAll.json"}:
                raise PilotError("REQUEST_ROUTE_DENIED")
            if endpoint == "company.json":
                if params["corp_code"] != COMPANY_SEED or self.count != 0:
                    raise PilotError("REQUEST_COMPANY_CANDIDATE_DENIED")
            elif not self._company_confirmed:
                raise PilotError("OFFICIAL_COMPANY_RESPONSE_REQUIRED")
        elif endpoint == "company.json":
            raise PilotError("REQUEST_ROUTE_DENIED")
        if "corp_code" in params and endpoint != "company.json" and (
            self.corp_code is None or params["corp_code"] != self.corp_code
        ):
            raise PilotError("REQUEST_ISSUER_DENIED")
        if endpoint == "document.xml" and (
            self.rcept_no is None or params["rcept_no"] != self.rcept_no
        ):
            raise PilotError("REQUEST_FILING_DENIED")
        if endpoint == "list.json" and (
            params["pblntf_ty"] != "A"
            or params["last_reprt_at"] != "N"
            or params["end_de"] != self.cutoff.astimezone(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
        ):
            raise PilotError("REQUEST_SEARCH_SCOPE_DENIED")
        if "fs_div" in params and params["fs_div"] != "CFS":
            raise PilotError("REQUEST_STATEMENT_DENIED")
        if endpoint in {"fnlttSinglAcntAll.json", "fnlttSinglAcnt.json"}:
            if (
                self.financial_plan is None
                or (params["bsns_year"], params["reprt_code"]) != self.financial_plan
            ):
                raise PilotError("REQUEST_REPORT_PLAN_MISMATCH")
        if endpoint == "list.json":
            day = self.cutoff.astimezone(ZoneInfo("Asia/Seoul")).date()
            if (
                params["bgn_de"] != f"{day.year}0101"
                or params["page_no"] != "1"
                or params["page_count"] != "100"
            ):
                raise PilotError("REQUEST_SEARCH_PLAN_MISMATCH")

    def get(self, endpoint: str, params: dict) -> bytes:
        params = dict(params)
        self._params(endpoint, params)
        if self.halted or self.count >= self.max_requests or time.monotonic() - self.started >= 300:
            raise PilotError("REQUEST_BUDGET_OR_STOP")
        descriptor = request_contract(endpoint)
        if contract_digest(descriptor) != self._contracts[endpoint]:
            self.halted = True
            raise PilotError("PROVIDER_HEADER_CONTRACT_DRIFT")
        self.count += 1
        public_request = public_request_identity(endpoint, params, descriptor)
        receipt = dict(
            sequence=self.count,
            method="GET",
            host=HOST,
            endpoint="/api/" + endpoint,
            params_sha256=digest(json.dumps(params, sort_keys=True).encode()),
            started_at=datetime.now(timezone.utc).isoformat(),
            raw_saved=False,
            request_contract=descriptor,
            request_contract_sha256=contract_digest(descriptor),
            public_request=public_request,
            public_request_sha256=contract_digest(public_request),
            source_generation=self.generation,
            request_budget=self.max_requests,
            transient_retry_budget=self.max_retries,
            wall_budget_seconds=300,
            maximum_request_timeout_seconds=30,
        )
        raw, transient, error = b"", False, None
        try:
            remaining = 300 - (time.monotonic() - self.started)
            exchange = bounded_exchange(
                endpoint, params, self._key, min(30, remaining), frozen_request=public_request
            )
            raw = exchange.pop("raw", b"")
            receipt.update(exchange)
            transient = exchange.get("transient", False)
            if exchange.get("error"):
                raise PilotError(exchange["error"])
            if exchange.get("request_contract_sha256") != self._contracts[endpoint]:
                raise PilotError("RESPONSE_REQUEST_CONTRACT_MISMATCH")
            if exchange.get("public_request_sha256") != contract_digest(public_request):
                raise PilotError("RESPONSE_PUBLIC_REQUEST_MISMATCH")
            screen_response(raw, self._key, endpoint)
            path = self.root / f"{self.count:02d}-{endpoint}.raw"
            with path.open("xb") as stream:
                stream.write(raw)
            receipt.update(raw_saved=True, raw_name=path.name, bytes=len(raw), sha256=digest(raw))
            if endpoint.endswith(".json"):
                response_json(raw)
                if endpoint == "company.json":
                    self._company_response = digest(raw)
            elif not raw.startswith(b"PK"):
                try:
                    status = ET.fromstring(safe_text(raw)).findtext("status")
                except ET.ParseError:
                    status = None
                if status in {"013", "020", "010", "011", "012", "800"}:
                    raise PilotError("OPENDART_STATUS_" + status)
                raise PilotError("XML_OR_PROVIDER_ERROR_NOT_ZIP")
        except (TimeoutError, ConnectionError, ssl.SSLError):
            error, transient = "TRANSIENT_TRANSPORT_FAILURE", True
        except PilotError as exc:
            error = str(exc)
        except Exception:
            error = "TRANSPORT_OR_WRITE_FAILURE"
        finally:
            receipt.update(ended_at=datetime.now(timezone.utc).isoformat(), error=error)
            write_json(self.root / f"{self.count:02d}-request.json", receipt)
        if error:
            if (
                transient
                and self.retries < self.max_retries
                and self.count < self.max_requests
                and time.monotonic() - self.started < 300
            ):
                self.retries += 1
                return self.get(endpoint, params)
            self.halted = True
            raise PilotError(error) from None
        return raw

    def confirm_company(self, raw: bytes) -> dict:
        if self.halted or self.route != "json" or self._company_response != digest(raw):
            raise PilotError("OFFICIAL_COMPANY_RESPONSE_REQUIRED")
        try:
            company = resolve_company_json(raw, COMPANY_SEED)
        except PilotError:
            self.halted = True
            raise
        self.corp_code = company["corp_code"]
        self._company_confirmed = True
        return company


def write_json(path: Path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=True, sort_keys=True, indent=2)
        stream.write("\n")


def acquire(root: Path, key: str, cutoff: datetime, *, route="legacy_zip") -> dict:
    collector = Collector(key, root, cutoff, route=route)
    cutoff = collector.cutoff
    result = dict(
        status="R17_OFFICIAL_JSON_RESPONSE_UNAVAILABLE" if route == "json" else "R15_OFFICIAL_RESPONSE_UNAVAILABLE",
        provider_gets=0,
        as_of_utc=cutoff.astimezone(timezone.utc).isoformat(),
        as_of_kst=cutoff.astimezone(ZoneInfo("Asia/Seoul")).isoformat(),
        source_status="NOT_CAPTURED",
        core_grants=0,
        source_policy="UNAPPROVED",
        route=route,
        request_budget=collector.max_requests,
        retry_budget=collector.max_retries,
    )
    try:
        if route == "json":
            company = collector.confirm_company(
                collector.get("company.json", dict(corp_code=COMPANY_SEED))
            )
        else:
            company = resolve_company(collector.get("corpCode.xml", {}))
        collector.corp_code = company["corp_code"]
        write_json(root / "company.json", company)
        day = cutoff.astimezone(ZoneInfo("Asia/Seoul")).date()
        params = dict(
            corp_code=collector.corp_code,
            bgn_de=f"{day.year}0101",
            end_de=day.strftime("%Y%m%d"),
            pblntf_ty="A",
            last_reprt_at="N",
            page_no="1",
            page_count="100",
        )
        filing = select_filing(collector.get("list.json", params), company, day)
        collector.rcept_no = filing["rcept_no"]
        collector.financial_plan = (filing["bsns_year"], filing["reprt_code"])
        write_json(root / "filing.json", filing)
        raw = collector.get(
            "fnlttSinglAcntAll.json",
            dict(
                corp_code=collector.corp_code,
                bsns_year=filing["bsns_year"],
                reprt_code=filing["reprt_code"],
                fs_div="CFS",
            ),
        )
        occurrence = parse_revenue(
            raw, company, filing, collector.generation
        )
        write_json(root / "revenue-occurrence.json", occurrence)
        result.update(
            status="R17_JSON_SOURCE_CAPTURED_UNQUALIFIED" if route == "json" else "R15_SOURCE_CAPTURED_PRIMARY_SPAN_PENDING",
            source_status="CAPTURED_UNQUALIFIED",
            unresolved=occurrence["unresolved"],
            original_document="SOURCE_ORIGINAL_DOCUMENT_NOT_CROSSCHECKED",
        )
        if route == "legacy_zip":
            try:
                collector.get("document.xml", dict(rcept_no=collector.rcept_no))
                result["original_document"] = "CAPTURED_NOT_YET_CROSSCHECKED"
            except PilotError as exc:
                result["document_error"] = str(exc)
    except PilotError as exc:
        result["error"] = str(exc)
    finally:
        result["provider_gets"] = collector.count
        write_json(root / "acquisition-result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--acquire", action="store_true", help="Explicit authorized live capture; default off"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--route", choices=("json", "legacy_zip"), default="json")
    args = parser.parse_args()
    if not args.acquire:
        parser.error("explicit --acquire required; no default network execution")
    key = os.environ.get("OPENDART_API_KEY", "")
    if not key:
        print(
            json.dumps(
                dict(
                    status="R15_OPENDART_AUTH_KEY_UNAVAILABLE",
                    binding="OPENDART_API_KEY",
                    provider_gets=0,
                )
            )
        )
        return 2
    try:
        result = acquire(args.output, key, datetime.now(timezone.utc), route=args.route)
    except Exception:
        print(
            json.dumps(
                dict(status="R15_OFFICIAL_RESPONSE_UNAVAILABLE", error="SAFE_ENTRYPOINT_FAILURE")
            )
        )
        return 2
    print(json.dumps(result))
    return 2  # Acquisition is not native consumer acceptance.


if __name__ == "__main__":
    raise SystemExit(main())
