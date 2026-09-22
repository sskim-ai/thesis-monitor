"""Exact, field-owned comparative cells from the existing SEC foreign filing route."""
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from urllib.parse import urlparse

from app.services.sec_business_field_quality_service import FIELDS, field_errors, sha
from app.services.sec_foreign_statement_boundary_service import statement_boundaries, unit_candidates, document_evidence_class

CONTRACT = "m12ds-r4-r3-foreign-filing-comparative-occurrence-lineage-v1"
PROVIDER = "sec_foreign_filing"
PARSE_METHOD = "sec_foreign_spanned_statement_table_v2"


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


class StatementTables(HTMLParser):
    """Keep source cell identities while expanding explicit HTML spans, not column guesses."""
    def __init__(self):
        super().__init__()
        self.tables, self.stack = [], []
        self.cell = None
        self.row = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            if self.stack:
                self.stack[-1]["nested"] = True
            table = dict(index=len(self.tables), rows=[], nested=False)
            self.tables.append(table)
            self.stack.append(table)
        elif self.stack and tag == "tr":
            self.row = []
        elif self.stack and self.row is not None and tag in {"td", "th"}:
            try:
                spans = [int(attrs.get(k, 1)) for k in ("colspan", "rowspan")]
                if any(n < 1 or n > 100 for n in spans):
                    raise ValueError()
            except ValueError:
                self.stack[-1]["nested"] = True
                spans = [1, 1]
            self.cell = dict(text=[], colspan=spans[0], rowspan=spans[1],
                             cell_index=len(self.row), html_id=attrs.get("id"))

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"].append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.cell["text"] = clean(" ".join(self.cell["text"]))
            if self.row is not None:
                self.row.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.stack and self.row is not None:
            self.stack[-1]["rows"].append(self.row)
            self.row = None
        elif tag == "table" and self.stack:
            self.stack.pop()


def grid(table):
    result, occupied = [], {}
    for ri, row in enumerate(table["rows"]):
        col = 0
        for cell in row:
            while (ri, col) in occupied:
                col += 1
            for dr in range(cell["rowspan"]):
                for dc in range(cell["colspan"]):
                    key = ri + dr, col + dc
                    if key in occupied:
                        return []
                    occupied[key] = dict(cell, row_index=ri, column_index=col)
            col += cell["colspan"]
        width = max((c for r, c in occupied if r == ri), default=-1) + 1
        result.append([occupied.get((ri, c)) for c in range(width)])
    return result


def period_from_headers(headers):
    """Explicit start/end or calendar-month duration + end, never a bare Q label."""
    text = clean(" ".join(headers))
    start = end = None
    method = None
    exact = re.search(r"(20\d{2}-\d{2}-\d{2})\s+(?:to|through)\s+(20\d{2}-\d{2}-\d{2})", text, re.I)
    try:
        if exact:
            start, end = [date.fromisoformat(x) for x in exact.groups()]
            method = "explicit_date_range"
        else:
            match = re.search(r"(?:for the )?(three|six|nine|twelve|3|6|9|12) months ended "
                              r"([A-Za-z]+) (\d{1,2})(?:,)? (20\d{2})(?!\d)", text, re.I)
            if match:
                count, month, day, year = match.groups()
                months = {"three": 3, "six": 6, "nine": 9, "twelve": 12}.get(count.lower()) or int(count)
                end = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()
                # A calendar-month header ending mid-month does not prove start day.
                if end.day != monthrange(end.year, end.month)[1]:
                    end = None
                else:
                    offset = end.year * 12 + end.month - months
                    start = date(offset // 12, offset % 12 + 1, 1)
                    method = "explicit_calendar_month_duration_ending_month_end"
    except (ValueError, TypeError):
        start = end = None
    days = (end - start).days + 1 if start and end and start < end else None
    scope = "single-quarter" if days and 80 <= days <= 100 else "half-year" if days and 170 <= days <= 190 else "other-duration" if days else None
    return dict(period_start=start.isoformat() if days else None, period_end=end.isoformat() if days else None,
                duration_days=days, period_scope=scope,
                period_type=f"Q{(end.month - 1) // 3 + 1}" if scope == "single-quarter" else scope,
                is_cumulative=False if scope == "single-quarter" else True if scope == "half-year" else None,
                period_resolution_method=method if days else None)


def table_unit(text):
    values = unit_candidates(text)
    return values[0] if values and len({v[:2] for v in values}) == 1 else (None, None, None)


def semantic(label):
    label = re.sub(r"\s*\(notes? [\d, and]+\)\s*", "", label, flags=re.I).strip().lower()
    if label in {"revenue", "net revenue", "net sales", "total revenue"}:
        return "revenue", "statement_revenue"
    if label in {"income from operations", "operating income", "operating profit"}:
        return "operating_income", "statement_operating_income"
    return None, None


def amount(text):
    value = text.replace("$", "").replace(",", "").replace(" ", "")
    if not re.fullmatch(r"(?:-?\d+(?:\.\d+)?|\(\d+(?:\.\d+)?\))", value):
        return None
    try:
        return Decimal(value) if not value.startswith("(") else -Decimal(value[1:-1])
    except InvalidOperation:
        return None


def extract_occurrences(html, *, issuer_cik, accession, document_type, filing_date, source_url, payload_sha256):
    parser = StatementTables()
    parser.feed(html)
    boundaries = statement_boundaries(html)
    evidence_class = document_evidence_class(html)
    result = []
    for table in parser.tables:
        if table["nested"]:
            continue
        ownership = boundaries[table["index"]]
        if ownership["status"] != "PASS":
            continue
        basis = ownership["statement_basis"]
        currency, scale, unit = (ownership[k] for k in ("currency", "unit_scale", "unit_evidence"))
        rows = grid(table)
        headers = []
        for ri, row in enumerate(rows):
            labels = [c for c in row if c and semantic(c["text"])[0]]
            if not labels:
                if not any(amount(c["text"]) is not None and not re.fullmatch(r"20\d{2}", c["text"]) for c in row if c):
                    headers.append(row)
                continue
            if len({c["cell_index"] for c in labels}) != 1:
                continue
            label = labels[0]
            field, meaning = semantic(label["text"])
            seen = set()
            for ci, cell in enumerate(row):
                if not cell or cell["cell_index"] in seen or ci <= label["column_index"]:
                    continue
                seen.add(cell["cell_index"])
                reported = amount(cell["text"])
                if reported is None:
                    continue
                owners = [h[ci] for h in headers if ci < len(h) and h[ci] and h[ci]["text"]]
                texts = list(dict.fromkeys(c["text"] for c in owners))
                if any("%" in t or re.search(r"\b(yoy|qoq)\b", t, re.I) for t in texts):
                    continue
                period = period_from_headers(texts)
                source_cell = dict(table=table["index"], row=ri, cell=cell["cell_index"], column=ci,
                                   html_id=cell["html_id"], row_label=label["text"], value_text=cell["text"],
                                   headers=[{k: c[k] for k in ("row_index", "column_index", "cell_index", "text")} for c in owners])
                occurrence = dict(contract=CONTRACT, provider=PROVIDER, issuer_cik=str(issuer_cik).zfill(10),
                    accession=accession, document_type=document_type, filing_date=filing_date,
                    source_url=source_url, field=field, semantic=meaning, statement_basis=basis,
                    basis_evidence=ownership["caption"], statement_boundary=ownership, currency=currency,
                    unit_scale=scale, unit_evidence=unit, reported_value=float(reported),
                    value=float(reported * scale) if scale else None,
                    source_payload_sha256=payload_sha256, source_cell=source_cell,
                    source_row_identity=sha(dict(payload=payload_sha256, cell=source_cell)),
                    parse_method=PARSE_METHOD, **period)
                if evidence_class:
                    occurrence['document_evidence_class'] = dict(evidence_class, source_url=source_url,
                                                                source_payload_sha256=payload_sha256)
                occurrence["occurrence_id"] = sha(occurrence)
                result.append(occurrence)
    return list({o["occurrence_id"]: o for o in result}.values())


def occurrence_errors(o, cutoff):
    errors = []
    if o.get("contract") != CONTRACT or o.get("provider") != PROVIDER or o.get("parse_method") != PARSE_METHOD:
        errors.append("foreign_occurrence_owner_missing")
    if sha({k: v for k, v in o.items() if k != "occurrence_id"}) != o.get("occurrence_id"):
        errors.append("foreign_occurrence_identity_mismatch")
    try:
        cell, payload = o["source_cell"], o["source_payload_sha256"]
        if (not re.fullmatch(r"[a-f0-9]{64}", payload) or o["source_row_identity"] != sha(dict(payload=payload, cell=cell))
                or semantic(cell["row_label"]) != (o["field"], o["semantic"])):
            errors.append("foreign_cell_identity_mismatch")
        period = period_from_headers(list(dict.fromkeys(c["text"] for c in cell["headers"])))
        if any(o.get(k) != v for k, v in period.items()) or not period["period_start"]:
            errors.append("exact_period_context_unresolved")
        start, end, filed = [date.fromisoformat(o[k]) for k in ("period_start", "period_end", "filing_date")]
        if not start < end <= filed <= cutoff:
            errors.append("foreign_source_cutoff_or_period_invalid")
        url = urlparse(o["source_url"])
        parts = url.path.split("/")
        if (url.scheme != "https" or url.hostname != "www.sec.gov" or parts[1:4] != ["Archives", "edgar", "data"]
                or int(parts[4]) != int(o["issuer_cik"]) or parts[5] != o["accession"].replace("-", "")
                or o["document_type"] not in {"6-K", "20-F", "6-K/A", "20-F/A"}):
            errors.append("foreign_document_binding_invalid")
        raw = amount(cell["value_text"])
        if (not o["currency"] or table_unit(o["unit_evidence"] or "")[:2] != (o["currency"], o["unit_scale"])
                or raw is None or float(raw) != o["reported_value"] or float(raw * o["unit_scale"]) != o["value"]):
            errors.append("foreign_currency_unit_value_invalid")
        if not o["basis_evidence"].lower().startswith(o["statement_basis"]):
            errors.append("foreign_statement_basis_unresolved")
        boundary = o.get("statement_boundary") or {}
        if (boundary.get("status") != "PASS" or boundary.get("contract") != "foreign-statement-boundary-v1"
                or not boundary.get("table_dom_path") or not boundary.get("section_dom_path")
                or not boundary.get("metadata_dom_paths")
                or boundary.get("table_index") != cell["table"]
                or any(boundary.get(k) != o.get(k) for k in ("currency", "unit_scale", "statement_basis"))):
            errors.append("foreign_statement_boundary_unresolved")
    except (KeyError, TypeError, ValueError, IndexError, InvalidOperation):
        errors.append("exact_foreign_lineage_incomplete")
    return sorted(set(errors))


def occurrences(row):
    return [o for r in json.loads(row.raw_financial_fields or "[]")
            if r.get("field") == "foreign_business_occurrences" for o in r.get("occurrences", [])]


def _lineage(o):
    return dict(amount=o["value"], amount_period_start=o["period_start"], amount_period_end=o["period_end"],
        currency=o["currency"], statement_basis=o["statement_basis"], issuer_cik=o["issuer_cik"],
        source_row_identity=o["source_row_identity"], source_payload_sha256=o["source_payload_sha256"],
        receipt=o["accession"], occurrence=o)


def _duplicate_conflict(candidates):
    groups = {}
    for o in candidates:
        key = tuple(o.get(k) for k in ("provider", "issuer_cik", "accession", "field", "semantic", "period_start",
                                      "period_end", "statement_basis", "currency", "unit_scale"))
        groups.setdefault(key, set()).add(o.get("value"))
    return any(len(values) > 1 for values in groups.values())


def authoritative_prior(current, pool, cutoff):
    """Choose document authority before inspecting values, conflicts or taint."""
    candidates = []
    for row in pool:
        try:
            end, prior, filed = [date.fromisoformat(v) for v in (current["period_end"], row["period_end"], row["filing_date"])]
            compatible = all(current.get(k) == row.get(k) for k in ("provider", "issuer_cik", "period_scope", "period_type"))
            if compatible and 330 <= (end-prior).days <= 400 and filed <= min(cutoff, date.fromisoformat(current["filing_date"])):
                candidates.append(row)
        except (KeyError, TypeError, ValueError):
            continue
    same = [r for r in candidates if r["accession"] == current["accession"]]
    if same:
        return dict(status="PASS", accession=current["accession"], method="selected_document_comparative",
                    candidates=sorted({r["accession"] for r in candidates}), denial_reasons=[])
    documents = {}
    for row in candidates:
        documents.setdefault(row["accession"], []).append(row)
    if len(documents) == 1:
        accession = next(iter(documents))
        return dict(status="PASS", accession=accession, method="unique_prior_document_at_cutoff",
                    candidates=[accession], denial_reasons=[])
    # Explicit supersession must be carried by source metadata, not inferred from recency.
    parents = {}
    invalid = not documents
    identities = set()
    for accession, rows in documents.items():
        versions = {json.dumps(r.get("document_version"), sort_keys=True) for r in rows}
        if len(versions) != 1:
            invalid = True
            continue
        version = rows[0].get("document_version") or {}
        if not version.get("report_identity") or not version.get("source_evidence"):
            invalid = True
        identities.add(version.get("report_identity"))
        parent = version.get("supersedes_accession")
        parents[accession] = parent
        if parent and (parent not in documents or rows[0]["filing_date"] < documents[parent][0]["filing_date"]):
            invalid = True
    heads = set(documents) - {p for p in parents.values() if p}
    if len(identities) != 1 or len(heads) != 1:
        invalid = True
    head = next(iter(heads)) if len(heads) == 1 else None
    seen, cursor = set(), head
    while cursor and cursor not in seen:
        seen.add(cursor)
        cursor = parents.get(cursor)
    if cursor or seen != set(documents):
        invalid = True
    return dict(status="FAIL" if invalid else "PASS", accession=None if invalid else head,
                method="explicit_document_supersession", candidates=sorted(documents),
                denial_reasons=["ambiguous_prior_document_authority"] if invalid else [])


def foreign_comparison_quality(*, formal, candidates, ticker, cutoff):
    """Recompute exact comparisons, preferring same-document then latest comparable filing."""
    fields, comparisons, attempts, version_receipts = {}, [], [], []
    own = occurrences(formal)
    tainted = {o["occurrence_id"] for row in candidates for o in occurrences(row)
               if field_errors(row, o.get("field", ""))}
    pool = list({o["occurrence_id"]: o for row in [formal, *candidates] if row.provider == PROVIDER
                 and row.ticker == ticker for o in occurrences(row)}.values())
    for metric in FIELDS:
        current = [o for o in own if o.get("field") == metric and o.get("accession") == formal.source_filing_id
                   and o.get("period_end") == str(formal.financial_period_end)
                   and o.get("period_scope") == formal.period_scope]
        errors = list(field_errors(formal, metric))
        if not current:
            errors.append("selected_exact_current_occurrence_missing")
        if _duplicate_conflict(current):
            errors.append("current_field_occurrence_conflict")
        viable = []
        for a in current:
            authority = authoritative_prior(a, pool, cutoff)
            version_receipts.append(dict(metric=metric, current_occurrence_id=a["occurrence_id"], **authority))
            current_errors = occurrence_errors(a, cutoff)
            if (formal.ticker != ticker or formal.provider != PROVIDER or a["value"] != getattr(formal, metric)
                    or a["currency"] != formal.currency or a["filing_date"] != str(formal.filing_date)
                    or a["source_url"] != formal.source
                    or formal.normalization_method or formal.financial_statement_basis_warning
                    or formal.period_mapping_validation_failed or formal.margin_quality_review):
                current_errors.append("selected_current_projection_mismatch")
            prior_pool = [b for b in pool if b["field"] == metric and b["period_end"] != a["period_end"]]
            same_document_prior = [b for b in prior_pool if b["accession"] == a["accession"]
                                   and b["period_scope"] == a["period_scope"]
                                   and b["period_type"] == a["period_type"]]
            if _duplicate_conflict(same_document_prior):
                current_errors.append("authoritative_prior_field_conflict")
            for b in prior_pool:
                denials = errors + current_errors + occurrence_errors(b, cutoff)
                denials += authority["denial_reasons"]
                if b["accession"] != authority["accession"]:
                    denials.append("non_authoritative_prior_document")
                checks = {k: a.get(k) is not None and a[k] == b.get(k) for k in (
                    "provider", "issuer_cik", "field", "semantic", "currency", "unit_scale", "statement_basis",
                    "period_scope", "period_type", "is_cumulative", "duration_days")}
                denials += ["comparison_" + k + "_mismatch" for k, ok in checks.items() if not ok]
                if a["period_scope"] != "single-quarter" or b["period_scope"] != "single-quarter":
                    denials.append("discrete_quarter_required")
                try:
                    aend, bend = [date.fromisoformat(o["period_end"]) for o in (a, b)]
                    if not 330 <= (aend - bend).days <= 400:
                        denials.append("prior_year_comparable_period_missing")
                    if b["filing_date"] > a["filing_date"]:
                        denials.append("comparison_later_version_than_selected")
                except (ValueError, TypeError):
                    denials.append("exact_comparison_period_missing")
                group = [o for o in prior_pool if all(o.get(k) == b.get(k) for k in (
                    "provider", "issuer_cik", "accession", "field", "semantic", "period_start", "period_end",
                    "statement_basis", "currency", "unit_scale"))]
                if _duplicate_conflict(group):
                    denials.append("prior_field_occurrence_conflict")
                if b["occurrence_id"] in tainted:
                    denials.append("prior_source_hard_taint")
                attempts.append(dict(metric=metric, current=a, comparison=b, compatibility=checks,
                                     denial_reasons=sorted(set(denials))))
                if not denials:
                    viable.append((a, b))
        if viable:
            if len({(a["value"], b["value"], b["period_start"], b["period_end"]) for a, b in viable}) != 1:
                errors.append("ambiguous_comparison_version")
                viable = []
        if viable:
            a, b = min(viable, key=lambda pair: (pair[0]["occurrence_id"], pair[1]["occurrence_id"]))
            av, bv = a["value"], b["value"]
            comparisons.append(dict(metric=metric, current=dict(lineage=_lineage(a)), comparison=dict(lineage=_lineage(b)),
                delta=av-bv, direction="higher" if av > bv else "lower" if av < bv else "unchanged",
                growth_pct=(av-bv)/bv*100 if bv > 0 else None, formula="current - prior_year_comparable"))
        rejected = [reason for attempt in attempts if attempt["metric"] == metric for reason in attempt["denial_reasons"]]
        fields[metric] = dict(status="PASS" if viable else "FAIL", selected_candidates=current,
                              denial_reasons=sorted(set(errors + ([] if viable else rejected or ["no_exact_compatible_comparison"]))))
    result = dict(contract=CONTRACT, ticker=ticker, cutoff=cutoff.isoformat(), formal_receipt=formal.source_filing_id,
        fields=fields, comparative_observations=comparisons, comparison_attempts=attempts,
        prior_version_authority=version_receipts,
        occurrence_validation=[dict(occurrence_id=o["occurrence_id"], denial_reasons=occurrence_errors(o, cutoff)) for o in pool],
        all_occurrences=pool, status="PASS" if comparisons else "FAIL", quality_reason_codes=[],
        source_use_eligibility=["CONTEXT", "BUSINESS_CONTEXT", "PASS_A_ARCHETYPE", "OVERALL_DIRECTION"] if comparisons else [],
        limitations=["No recurring-profit, security valuation or per-share authority.",
                     "Exact reported discrete periods only; no cumulative subtraction or FX conversion."])
    result["receipt_sha256"] = sha(result)
    return result


def current_projection(occurrence_list):
    """Select the latest explicitly reported discrete statement, never the largest amount."""
    exact = [o for o in occurrence_list if o["period_scope"] == "single-quarter"
             and not occurrence_errors(o, date.max)]
    if not exact:
        return None
    end = max(o["period_end"] for o in exact)
    selected = {}
    for field in FIELDS:
        rows = [o for o in exact if o["period_end"] == end and o["field"] == field]
        if rows and len({(o["value"], o["currency"], o["statement_basis"]) for o in rows}) == 1:
            selected[field] = min(rows, key=lambda o: o["occurrence_id"])
    if not selected or len({o["currency"] for o in selected.values()}) != 1:
        return None
    first = next(iter(selected.values()))
    return dict(period_end=end, currency=first["currency"],
                **{field: o["value"] for field, o in selected.items()},
                foreign_business_occurrences=occurrence_list)


def parse_document(html, *, issuer_cik, accession, document_type, filing_date, source_url, raw_payload):
    return extract_occurrences(html, issuer_cik=issuer_cik, accession=accession,
        document_type=document_type, filing_date=filing_date, source_url=source_url,
        payload_sha256=sha256(raw_payload).hexdigest())
