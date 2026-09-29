"""Source-owned SEC reference groups. Structure grants no financial authority."""

from html.parser import HTMLParser
from typing import Literal
import unicodedata

from pydantic import Field, model_validator

from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_run_artifacts import sha256_bytes

CONTRACT = "sec-logical-cell-reference-v1"
NORMALIZATION = "nfkc-ordered-raw-concatenation-whitespace-v1"
LAYOUT = {"div", "span", "p", "br", "font", "b", "i", "em", "strong", "u", "sup", "sub"}


def normalized_label(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


class ExactReferenceAnchor(ContractModel):
    accession: str
    source_document: str
    anchor_id: str
    row_id: str | None
    cell_id: str | None
    dom_order: int = Field(ge=0)
    canonical_href: str
    document_identity: str
    byte_start: int = Field(ge=0)
    byte_end: int = Field(gt=0)
    exact_html: str
    html_sha256: str
    raw_text: str

    @model_validator(mode="after")
    def exact_span(self):
        if (self.byte_end - self.byte_start != len(self.exact_html.encode())
                or sha256_bytes(self.exact_html.encode()) != self.html_sha256):
            raise ValueError("reference_anchor_span_hash_mismatch")
        return self


class LogicalCellReferenceGroup(ContractModel):
    accession: str
    filing_form: str
    source_document: str
    source_sha256: str
    row_id: str | None
    cell_id: str | None
    canonical_href: str
    document_identity: str
    anchors: tuple[ExactReferenceAnchor, ...] = Field(min_length=1)
    normalized_label: str
    normalization_version: Literal["nfkc-ordered-raw-concatenation-whitespace-v1"] = NORMALIZATION
    normalized_sha256: str
    ambiguity_state: Literal["UNAMBIGUOUS"] = "UNAMBIGUOUS"

    @model_validator(mode="after")
    def exact_membership(self):
        expected = (self.accession, self.source_document, self.row_id, self.cell_id,
                    self.canonical_href, self.document_identity)
        if any((a.accession, a.source_document, a.row_id, a.cell_id, a.canonical_href,
                a.document_identity) != expected for a in self.anchors):
            raise ValueError("reference_group_identity_mismatch")
        if len(self.anchors) > 1 and not (self.row_id and self.cell_id):
            raise ValueError("reference_group_structural_owner_missing")
        if (len({a.anchor_id for a in self.anchors}) != len(self.anchors)
                or any(a.byte_end > b.byte_start or a.dom_order >= b.dom_order
                       for a, b in zip(self.anchors, self.anchors[1:]))):
            raise ValueError("reference_group_order_or_overlap")
        label = normalized_label("".join(a.raw_text for a in self.anchors))
        if self.normalized_label != label or self.normalized_sha256 != sha256_bytes(label.encode()):
            raise ValueError("reference_group_label_mismatch")
        return self

    @property
    def sha256(self):
        return digest(self.model_dump(mode="json"))


class _InventoryParser(HTMLParser):
    def __init__(self, source, resolve):
        super().__init__(convert_charrefs=True)
        self.source, self.resolve = source, resolve
        self.lines = [0]
        for line in source.splitlines(keepends=True):
            self.lines.append(self.lines[-1] + len(line))
        self.tables, self.rows, self.cells = [], [], []
        self.row_tables, self.cell_tables, self.malformed_rows = {}, {}, set()
        self.anchors, self.events, self.ambiguous_cells = [], [], set()
        self.active = None

    def source_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def owners(self):
        return (self.rows[-1] if self.rows else None, self.cells[-1] if self.cells else None)

    def event(self, kind, **data):
        row, cell = self.owners()
        self.events.append(dict(kind=kind, row_id=row, cell_id=cell,
                                char_start=self.source_offset(), **data))

    def ambiguous(self):
        if self.cells:
            self.ambiguous_cells.add(self.cells[-1])
        if self.active is not None:
            self.active["ambiguous"] = True

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in {"table", "tr", "td", "th"}:
            if self.active is not None:
                self.ambiguous()
            self.event("structural_boundary", tag=tag)
            if tag == "table":
                if self.cells:
                    self.ambiguous()
                self.tables.append(self.source_offset())
            elif tag == "tr":
                table = self.tables[-1] if self.tables else None
                row = "tr:" + str(self.source_offset())
                if self.rows and self.row_tables[self.rows[-1]] == table:
                    self.ambiguous()
                    self.malformed_rows.add(row)
                self.rows.append(row)
                self.row_tables[row] = table
            else:
                table = self.tables[-1] if self.tables else None
                nested_cell = bool(self.cells and self.cell_tables[self.cells[-1]] == table)
                if self.cells:
                    self.ambiguous()
                self.cells.append(tag + ":" + str(self.source_offset()))
                self.cell_tables[self.cells[-1]] = table
                if (tag != "td" or not self.rows or nested_cell
                        or self.rows[-1] in self.malformed_rows
                        or self.row_tables[self.rows[-1]] != table):
                    self.ambiguous()
        elif tag == "a":
            if self.active is not None:
                self.ambiguous()
            row, cell = self.owners()
            target = self.resolve(attrs.get("href", "")) if attrs.get("href") else None
            anchor = dict(anchor_id="a:" + str(self.source_offset()), row_id=row, cell_id=cell,
                          dom_order=len(self.anchors), char_start=self.source_offset(), char_end=None,
                          raw_href=attrs.get("href"), target=target, raw_text="", ambiguous=False)
            if self.active is not None:
                anchor["ambiguous"] = True
            self.anchors.append(anchor)
            self.event("anchor", anchor_id=anchor["anchor_id"])
            self.active = anchor
            if len([key for key, _ in attributes if key == "href"]) > 1:
                self.ambiguous()
        elif tag not in LAYOUT:
            self.event("content_boundary", tag=tag)
            if self.active is not None:
                self.ambiguous()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in {"br", "img", "hr", "input", "meta", "link"}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "a":
            if self.active is None:
                self.ambiguous()
                self.event("orphan_anchor_close")
            else:
                self.active["char_end"] = self.source.find(">", self.source_offset()) + 1
                self.active = None
        elif tag in {"td", "th", "tr", "table"}:
            if self.active is not None:
                self.ambiguous()
            self.event("structural_boundary", tag=tag)
            stack = self.cells if tag in {"td", "th"} else self.rows if tag == "tr" else self.tables
            if tag in {"td", "th"} and stack and not stack[-1].startswith(tag + ":"):
                self.ambiguous()
            if not stack or (tag in {"tr", "table"} and self.cells):
                self.ambiguous()
            if stack:
                stack.pop()
        elif tag not in LAYOUT:
            self.event("content_boundary", tag=tag)

    def handle_data(self, text):
        if self.active is not None:
            self.active["raw_text"] += text
        elif text.strip():
            self.event("unlinked_text", text=text)


def logical_reference_inventory(source, *, accession, filing_form, source_document, resolve):
    """Resolve returns (canonical href, document identity), or None for barriers.

    Exact same-cell groups are constructed from the complete event sequence, not
    a target-filtered list that could hide intervening references or plain text.
    """
    parser = _InventoryParser(source, resolve)
    parser.feed(source)
    parser.close()
    parser.ambiguous_cells.update(parser.cells)
    source_hash = sha256_bytes(source.encode())
    positions = sorted({0, len(source), *(a["char_start"] for a in parser.anchors),
                        *(a["char_end"] for a in parser.anchors if a["char_end"]),
                        *(e["char_start"] for e in parser.events)})
    offsets, previous, total = {}, 0, 0
    for position in positions:
        total += len(source[previous:position].encode())
        offsets[position], previous = total, position
    exact, inventory = {}, []
    for anchor in parser.anchors:
        row = dict(anchor)
        row["byte_start"] = offsets[row["char_start"]]
        row["byte_end"] = offsets[row["char_end"]] if row["char_end"] else None
        row["ambiguous"] |= row["cell_id"] in parser.ambiguous_cells or not row["char_end"]
        row["exact_html"] = source[row["char_start"]:row["char_end"]] if row["char_end"] else ""
        row["html_sha256"] = sha256_bytes(row["exact_html"].encode())
        inventory.append(row)
        if row["target"] and not row["ambiguous"]:
            exact[row["anchor_id"]] = ExactReferenceAnchor(
                accession=accession, source_document=source_document,
                canonical_href=row["target"][0], document_identity=row["target"][1],
                **{k: row[k] for k in ("anchor_id", "row_id", "cell_id", "dom_order", "byte_start",
                                      "byte_end", "exact_html", "html_sha256", "raw_text")})
    groups, block = [], []

    def flush():
        if not block:
            return
        first = block[0]
        label = normalized_label("".join(a.raw_text for a in block))
        group = LogicalCellReferenceGroup(accession=accession, filing_form=filing_form,
            source_document=source_document, source_sha256=source_hash,
            row_id=first.row_id, cell_id=first.cell_id, canonical_href=first.canonical_href,
            document_identity=first.document_identity, anchors=tuple(block), normalized_label=label,
            normalized_sha256=sha256_bytes(label.encode()))
        groups.append(dict(**group.model_dump(mode="json"), group_sha256=group.sha256))
        block.clear()

    for event in parser.events:
        anchor = exact.get(event.get("anchor_id"))
        if anchor is None:
            flush()
            continue
        if block and (not anchor.cell_id or not anchor.row_id or any(
                getattr(anchor, key) != getattr(block[0], key)
                for key in ("row_id", "cell_id", "canonical_href", "document_identity"))):
            flush()
        block.append(anchor)
    flush()
    value = dict(contract=CONTRACT, accession=accession, filing_form=filing_form,
        source_document=source_document, source_sha256=source_hash, anchors=inventory,
        events=[dict(**e, byte_start=offsets[e["char_start"]]) for e in parser.events],
        ambiguous_cells=sorted(parser.ambiguous_cells), malformed_rows=sorted(parser.malformed_rows), groups=groups)
    return dict(**value, inventory_sha256=digest(value))
