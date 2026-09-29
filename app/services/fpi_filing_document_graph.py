"""Exact SEC filing relationships and finite content-document slot ownership.

Index media labels describe routing only. Fetched content alone owns facts.
"""

from html.parser import HTMLParser
from pathlib import PurePosixPath
import re
from urllib.parse import urljoin, urlsplit

from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest

CONTRACT = "fpi-filing-document-graph-v1"
FORWARDING = "FORWARDING_COVER_TO_QUALIFIED_FINANCIAL_ATTACHMENT"
EXHAUSTED = "FPI_FINANCIAL_DOCUMENT_CANDIDATE_BOUND_EXHAUSTED"
FINANCIAL = {"FINANCIAL_STATEMENTS", "FINANCIAL_RESULTS_OR_EARNINGS"}
AUXILIARY = {"IMAGE_ASSET", "STYLE_OR_SUPPORT_ASSET", "XBRL_SUPPORT_ASSET"}


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.text = [], []
        self.active = None
        self.hidden = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "ix:header":
            self.hidden = True
        ref = (
            attrs.get("href")
            if tag in {"a", "link"}
            else attrs.get("src")
            if tag in {"img", "script"}
            else None
        )
        if ref:
            row = dict(tag=tag, reference=ref, label="")
            self.links.append(row)
            if tag == "a":
                self.active = row

    def handle_endtag(self, tag):
        if tag == "a":
            self.active = None
        if tag == "ix:header":
            self.hidden = False

    def handle_data(self, value):
        if not self.hidden:
            self.text.append(value)
        if self.active is not None:
            self.active["label"] += value


def asset_class(item, references=()):
    name, media = item["name"], str(item.get("type", "")).lower()
    suffix = PurePosixPath(name).suffix.lower()
    # SEC index.json uses icon names as media hints. A text filename is never
    # discarded solely because a misleading icon claims it is an image.
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".svg"} and (
        media.startswith("image") or any(r["tag"] == "img" for r in references)
    ):
        return "IMAGE_ASSET"
    if suffix in {".css", ".js"} and (
        media in {"text/css", "application/javascript"}
        or any(r["tag"] in {"link", "script"} for r in references)
    ):
        return "STYLE_OR_SUPPORT_ASSET"
    if suffix in {".xsd", ".xml"} and media in {"text/xml", "application/xml", "xbrl", "xbrl.gif"}:
        return "XBRL_SUPPORT_ASSET"
    return "OTHER_TEXT_DOCUMENT"


def declared_nonfinancial_exhibit(references, filing):
    """Annual exhibit descriptions route requests; they never authorize facts."""
    if filing["form"].split("/")[0] not in {"20-F", "40-F"}:
        return False
    label = " ".join(" ".join(r["label"] for r in references).split())
    if re.search(
        r"financial statements|financial results|earnings release|annual report", label, re.I
    ):
        return False
    return bool(
        re.match(
            r"(?:Articles of (?:Incorporation|Association)\b|"
            r"Certification of Chief (?:Executive|Financial) Officer required by Rule 13a-14\b|"
            r"Consent of\b|Description of Securities Registered Under Section 12\b|"
            r"Land Lease with\b|Subsidiaries of\b)",
            label,
            re.I,
        )
    )


def document_slot_plan(index, primary_text, plan, filing):
    from app.services.bounded_financial_acquisition import (
        sec_base,
        sec_document_identity,
        AcquisitionDenied,
    )

    base = sec_base(plan, filing)
    primary = base + filing["primaryDocument"]
    parser = References()
    parser.feed(primary_text)
    links, external = {}, []
    for link in parser.links:
        ref = link["reference"]
        absolute = urljoin(primary, ref)
        if not absolute.startswith(base):
            external.append(dict(**link, excluded_reason="OUTSIDE_ACCESSION_NAVIGATION_NO_FETCH"))
            continue
        if (
            any(p in {".", ".."} for p in urlsplit(ref).path.split("/"))
            or "%" in urlsplit(ref).path
        ):
            raise AcquisitionDenied("SEC_DOCUMENT_SOURCE_SCOPE_DENIED")
        identity = sec_document_identity(absolute, plan, filing)
        links.setdefault(identity, []).append(link)
    items = index.get("directory", {}).get("item", [])
    names = [r["name"] for r in items]
    if len(names) != len(set(names)):
        raise AcquisitionDenied("SEC_INDEX_DUPLICATE_DOCUMENT_IDENTITY")
    rows = []
    for item in items:
        identity = sec_document_identity(base + item["name"], plan, filing)
        references = links.get(identity, [])
        cls = "PRIMARY_COVER_DOCUMENT" if identity == primary else asset_class(item, references)
        discovered = bool(references) or bool(
            re.search(r"(?:ex-?99|earn|result|release|financial)", item["name"], re.I)
        )
        nonfinancial = declared_nonfinancial_exhibit(references, filing)
        candidate = identity != primary and discovered and cls not in AUXILIARY and not nonfinancial
        rows.append(
            dict(
                document_identity=identity,
                index_metadata=item,
                exact_references=references,
                asset_class=cls,
                candidate=candidate,
                selected_for_fetch=False,
                slot_class_consumed=None,
                excluded_reason="PRIMARY_RESERVED_SEPARATELY"
                if identity == primary
                else "AUXILIARY_NOT_REQUIRED_BY_EXACT_PARSER"
                if cls in AUXILIARY
                else "OFFICIAL_ANNUAL_EXHIBIT_DESCRIPTION_NON_FINANCIAL_NO_FETCH"
                if nonfinancial
                else "OUTSIDE_FROZEN_LINK_DISCOVERY_RULE"
                if not candidate
                else None,
            )
        )
    if set(links) - {r["document_identity"] for r in rows} - {primary}:
        raise AcquisitionDenied("SEC_REFERENCED_DOCUMENT_NOT_IN_INDEX")
    candidates = [r for r in rows if r["candidate"]]
    cap = plan["limits"]["linked_exhibits"]
    denied = len(candidates) > cap
    for row in candidates:
        row.update(
            selected_for_fetch=not denied,
            slot_class_consumed="ATTACHMENT_CONTENT" if not denied else None,
            excluded_reason=EXHAUSTED if denied else None,
        )
    value = dict(
        contract=CONTRACT,
        accession=filing["accessionNumber"],
        filing=filing,
        index_sha256=digest(index),
        primary_text_sha256=sha256_bytes(primary_text.encode()),
        financial_plan_sha256=digest(plan),
        all_linked_identities=rows,
        total_linked_identities=len(rows),
        external_references=external,
        candidate_count=len(candidates),
        content_slot_limit=cap,
        status="DENIED" if denied else "PASS",
        denial_reason=EXHAUSTED if denied else None,
        selected_urls=sorted(r["document_identity"] for r in candidates) if not denied else [],
        remaining_attachment_slots=cap - (len(candidates) if not denied else 0),
        primary_slot_class="ANNUAL_PRIMARY"
        if filing["form"].split("/")[0] in {"20-F", "40-F"}
        else "BOUNDARY_PRIMARY",
        primary_reserved=True,
        index_reserved=True,
    )
    value["plan_sha256"] = digest(value)
    return value


def terminal_slots(slot_plan, documents, receipts):
    captured = {d["url"]: d for d in documents if d["filing"] == slot_plan["filing"]}
    filing = slot_plan["filing"]
    rows = []
    primary = next(
        (
            r["document_identity"]
            for r in slot_plan["all_linked_identities"]
            if r["asset_class"] == "PRIMARY_COVER_DOCUMENT"
        ),
        None,
    )
    for cls, identity in [
        (slot_plan["primary_slot_class"], primary),
        *[("ATTACHMENT_CONTENT", u) for u in slot_plan["selected_urls"]],
    ]:
        state = "EXECUTED" if identity in captured else "UNAVAILABLE"
        rows.append(
            dict(
                slot_class=cls,
                document_identity=identity,
                state=state,
                artifact=captured.get(identity, {}).get("artifact"),
            )
        )
    indexes = [
        r
        for r in receipts
        if r["stage"] == "index" and r.get("filing") == filing and not r["failure_class"]
    ]
    rows.append(dict(slot_class="INDEX", state="EXECUTED" if len(indexes) == 1 else "UNAVAILABLE"))
    for _ in range(slot_plan["remaining_attachment_slots"]):
        rows.append(
            dict(
                slot_class="ATTACHMENT_CONTENT",
                state="DENIED" if slot_plan["status"] == "DENIED" else "VALID_NOT_SELECTED",
            )
        )
    return dict(accession=slot_plan["accession"], plan_sha256=slot_plan["plan_sha256"], slots=rows)


def frozen_slot_accounting(plan, filings, slot_plans, receipts):
    """Account for all predeclared requests, including unused filing reserves."""
    from app.services.bounded_financial_acquisition import sec_base

    rows = []

    def add(key, stage, filing=None, selected=True, denied=False, unused=False, artifact=None):
        found = [
            r
            for r in receipts
            if r["stage"] == stage
            and r.get("filing") == filing
            and (artifact is None or r.get("artifact") == artifact)
        ]
        state = (
            "RESERVED_UNUSED"
            if unused
            else "DENIED"
            if denied
            else "VALID_NOT_SELECTED"
            if not selected
            else "EXECUTED"
            if found and not found[-1]["failure_class"]
            else "UNAVAILABLE"
        )
        rows.append(
            dict(slot_id=key, state=state, logical_id=found[-1]["logical_id"] if found else None)
        )

    add("discovery", "discovery")
    add("companyfacts", "companyfacts")
    for i in range(plan["limits"]["current"] + plan["limits"]["prior"]):
        filing = filings[i] if i < len(filings) else None
        slots = next((s for s in slot_plans if s["filing"] == filing), None)
        add(f"filing{i + 1}:index", "index", filing, unused=filing is None)
        docs = [r for r in receipts if r["stage"] == "document" and r.get("filing") == filing]
        # collect always reads the primary before any selected attachments.
        logical = list(dict.fromkeys(r["logical_id"] for r in docs))
        primary = next(
            (r for r in reversed(docs) if logical and r["logical_id"] == logical[0]), None
        )
        add(
            f"filing{i + 1}:primary",
            "document",
            filing,
            unused=filing is None,
            artifact=primary["artifact"] if primary else "__missing_primary__",
        )
        for j in range(plan["limits"]["linked_exhibits"]):
            urls = slots["selected_urls"] if slots else []
            selected = j < len(urls)
            matched = next(
                (
                    r
                    for r in reversed(docs)
                    if len(logical) > j + 1 and r["logical_id"] == logical[j + 1]
                ),
                None,
            )
            add(
                f"filing{i + 1}:exhibit{j + 1}",
                "document",
                filing,
                unused=filing is None,
                selected=selected,
                denied=slots is not None and slots["status"] == "DENIED",
                artifact=matched["artifact"] if matched else "__missing_attachment__",
            )
            rows[-1]["document_identity"] = urls[j] if selected else None
        if filing:
            rows[-plan["limits"]["linked_exhibits"] - 1]["document_identity"] = (
                sec_base(plan, filing) + filing["primaryDocument"]
            )
    if len(rows) != plan["maximum_logical_requests"]:
        raise ValueError("fpi_frozen_slot_accounting_cardinality")
    value = dict(
        contract="fpi-frozen-slot-accounting-v1",
        financial_plan_sha256=digest(plan),
        document_plan_sha256s=[s["plan_sha256"] for s in slot_plans],
        slots=rows,
    )
    value["receipt_sha256"] = digest(value)
    return value


def build_graph(*, documents, source_documents, indexes, plan):
    from app.services.bounded_financial_acquisition import sec_base

    by_url = {d["source_url"]: d for d in documents}
    raw_by_url = {d["url"]: d for d in source_documents}
    nodes, edges, conflicts = [], [], []
    for source in source_documents:
        doc, filing = by_url[source["url"]], source["filing"]
        if (
            doc["source_payload_sha256"] != sha256_bytes(source["raw"])
            or doc["accession"] != filing["accessionNumber"]
            or doc["receipt_sha256"]
            != digest({k: v for k, v in doc.items() if k != "receipt_sha256"})
        ):
            raise ValueError("fpi_graph_source_identity_mismatch")
        index_record = indexes.get(filing["accessionNumber"])
        rows = index_record["payload"].get("directory", {}).get("item", []) if index_record else []
        item = next((r for r in rows if sec_base(plan, filing) + r["name"] == source["url"]), None)
        refs = References()
        refs.feed(source["raw"].decode("utf-8", errors="replace"))
        nodes.append(
            dict(
                accession=filing["accessionNumber"],
                form=filing["form"],
                document_identity=source["url"],
                primary=source["url"] == sec_base(plan, filing) + filing["primaryDocument"],
                index_metadata=item,
                raw_sha256=sha256_bytes(source["raw"]),
                purpose=doc["purpose"],
                exact_link_references=refs.links,
                asset_class=asset_class(item) if item else "INDEX_IDENTITY_UNAVAILABLE",
                media_metadata=(item or {}).get("type"),
                sec_document_type=(item or {}).get("document_type"),
                economic_periods=doc["economic_periods"],
                purpose_receipt_sha256=doc["receipt_sha256"],
                auxiliary_verified=bool(
                    item
                    and asset_class(item) == "IMAGE_ASSET"
                    and source["raw"].startswith(
                        (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a")
                    )
                ),
            )
        )
    for source in source_documents:
        cover, filing = by_url[source["url"]], source["filing"]
        if (
            filing["form"].split("/")[0] != "6-K"
            or cover["purpose"] != "UNKNOWN_PURPOSE"
            or cover["occurrences"]
            or source["url"] != sec_base(plan, filing) + filing["primaryDocument"]
        ):
            continue
        parser = References()
        parser.feed(source["raw"].decode("utf-8", errors="replace"))
        text = " ".join(" ".join(parser.text).split())
        if not re.search(r"FORM\s+6-K", text, re.I) or not re.search(r"\bEXHIBITS?\b", text, re.I):
            continue
        if re.search(
            r"(?i)unrelated\s+(?:financial|attachment)|does not relate to (?:the|this) (?:issuer|report)|historical only",
            text,
        ):
            continue
        record = indexes.get(filing["accessionNumber"])
        if not record:
            continue
        names = {sec_base(plan, filing) + r["name"] for r in record["payload"]["directory"]["item"]}
        if source["url"] not in names:
            continue
        proposed = []
        for link in parser.links:
            target = urljoin(source["url"], link["reference"]).split("#", 1)[0]
            child = by_url.get(target)
            label = " ".join(link["label"].split())
            if (
                link["tag"] != "a"
                or target not in names
                or not child
                or child["accession"] != cover["accession"]
                or child["purpose"] not in FINANCIAL
                or not child["financial_authority"]
                or not child["economic_periods"]
                or not re.search(
                    r"(?i)financial\s+(?:statements?|results|report)|interim\s+report|earnings",
                    label,
                )
                or re.search(r"(?i)unrelated|not\s+(?:part|included)|historical\s+only", label)
            ):
                continue
            if filing.get("reportDate") not in {p["end"] for p in child["economic_periods"]}:
                continue
            proposed.append(
                dict(
                    relation=FORWARDING,
                    accession=cover["accession"],
                    cover=source["url"],
                    attachment=target,
                    exact_reference=link,
                    index_artifact_sha256=record["raw_sha256"],
                    cover_sha256=sha256_bytes(source["raw"]),
                    attachment_sha256=sha256_bytes(raw_by_url[target]["raw"]),
                    economic_periods=child["economic_periods"],
                )
            )
        # Conflicting qualified peers anywhere in the accession remain visible.
        amounts = {}
        for doc in documents:
            if doc["accession"] != cover["accession"]:
                continue
            for o in doc["occurrences"]:
                if o["occurrence_id"] not in doc["valid_occurrence_ids"]:
                    continue
                key = tuple(
                    o.get(k)
                    for k in (
                        "field",
                        "semantic",
                        "statement_basis",
                        "currency",
                        "period_start",
                        "period_end",
                    )
                )
                amounts.setdefault(key, set()).add(o["value"])
        if any(len(v) > 1 for v in amounts.values()):
            conflicts.append(
                dict(accession=cover["accession"], reason="CONFLICTING_FINANCIAL_ATTACHMENTS")
            )
            continue
        edges.extend({digest(e): e for e in proposed}.values())
    graph = dict(
        contract=CONTRACT,
        nodes=nodes,
        edges=edges,
        conflicts=conflicts,
        financial_plan_sha256=digest(plan),
    )
    graph["receipt_sha256"] = digest(graph)
    return graph


def bind_graph(documents, graph):
    for doc in documents:
        node = next(n for n in graph["nodes"] if n["document_identity"] == doc["source_url"])
        if node["auxiliary_verified"] and not doc["occurrences"]:
            doc.update(
                purpose="OFFICIAL_AUXILIARY_ASSET",
                original_purpose=doc["purpose"],
                document_graph_sha256=graph["receipt_sha256"],
                auxiliary_verified=True,
                financial_authority=False,
                unresolved_financial_content=False,
            )
        relations = [e for e in graph["edges"] if e["cover"] == doc["source_url"]]
        if relations:
            doc.update(
                purpose="FORWARDING_COVER",
                original_purpose=doc["purpose"],
                forwarding_relations=relations,
                document_graph_sha256=graph["receipt_sha256"],
                financial_authority=False,
                unresolved_financial_content=False,
            )
        if any(c["accession"] == doc["accession"] for c in graph["conflicts"]):
            doc["document_graph_conflict"] = True
        doc["receipt_sha256"] = digest({k: v for k, v in doc.items() if k != "receipt_sha256"})
