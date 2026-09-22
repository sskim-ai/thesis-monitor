"""Structural ownership of foreign statement captions; no rolling text prefix."""
from html.parser import HTMLParser
import re

CONTRACT = "foreign-statement-boundary-v1"
TITLE = re.compile(r"(?:consolidated|separate) statements? of (?:comprehensive income|income|operations)|consolidated results\s*:", re.I)
ANY_STATEMENT = re.compile(r"(?:consolidated|separate) (?:statements?|balance sheets?|results)", re.I)
UNITS = re.compile(r"(?:in |unit\s*:\s*)(thousands|millions|billions) of (new taiwan dollars|us dollars)|unit\s*:\s*(NT\$|TWD|US\$|USD)\s*(thousand|million|billion)", re.I)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def text(node):
    return re.sub(r"\s+", " ", " ".join(node["text"])).strip()


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = dict(tag="document", path="/document", attrs={}, children=[], text=[], parent=None)
        self.stack, self.tables = [self.root], []

    def handle_starttag(self, tag, attrs):
        parent = self.stack[-1]
        index = sum(c["tag"] == tag for c in parent["children"]) + 1
        node = dict(tag=tag, attrs=dict(attrs), parent=parent, children=[], text=[], path=f"{parent['path']}/{tag}[{index}]")
        parent["children"].append(node)
        if tag == "table":
            node["table_index"] = len(self.tables)
            self.tables.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i]["tag"] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        for node in self.stack:
            node["text"].append(data)


def unit_candidates(value):
    result = []
    for match in UNITS.finditer(value):
        scale, currency, symbol, suffix = match.groups()
        result.append(("TWD" if (currency or symbol).lower() in {"new taiwan dollars", "nt$", "twd"} else "USD",
                       {"thousand":1000,"million":1000000,"billion":1000000000}[(scale or suffix).lower().rstrip("s")], match[0]))
    return result


def has_data_table(node):
    if node["tag"] == "table":
        # An explicit title/unit layout table is a caption, not a prior financial table.
        def numeric_cell(n):
            value = text(n).replace(',', '').replace('$', '').strip()
            return (n['tag'] in {'td', 'th'} and bool(re.fullmatch(r'-?\d+(?:\.\d+)?|\(\d+(?:\.\d+)?\)', value))) or any(numeric_cell(c) for c in n['children'])
        return numeric_cell(node) or not (TITLE.search(text(node)) and UNITS.search(text(node)))
    return any(has_data_table(child) for child in node["children"])


def explicit_section(node):
    return node["tag"] in {"section", "article"} or node["attrs"].get("role") == "region"


def boundary(table):
    fragments, method, owner = [], "structural_preceding_caption", None
    local = [c for c in table["children"] if c["tag"] == "caption"]
    if local and any(TITLE.search(text(c)) for c in local):
        fragments, method, owner = local, "table_caption", table
    else:
        branch = table
        while branch["parent"]:
            parent = branch["parent"]
            previous = parent["children"][:next(i for i, n in enumerate(parent["children"]) if n is branch)]
            blocked = False
            for sibling in reversed(previous):
                value = text(sibling)
                if has_data_table(sibling):
                    if ANY_STATEMENT.search(value):
                        blocked = True
                        break
                    if explicit_section(parent):
                        # Shared captions are allowed only inside an explicit section.
                        continue
                    blocked = True
                    break
                if value:
                    fragments.insert(0, sibling)
                if ANY_STATEMENT.search(value):
                    owner = parent
                    break
            if owner or blocked:
                break
            if explicit_section(parent):
                break
            branch = parent
    joined = " ".join(text(n) for n in fragments)
    titles = list(TITLE.finditer(joined))
    units = unit_candidates(joined)
    errors = []
    if len(titles) != 1:
        errors.append("statement_caption_ownership_unresolved")
    if len({u[:2] for u in units}) != 1:
        errors.append("statement_unit_ownership_unresolved")
    title = titles[0][0] if len(titles) == 1 else None
    currency, scale, unit = units[0] if units and len({u[:2] for u in units}) == 1 else (None,None,None)
    return dict(contract=CONTRACT, table_index=table["table_index"], table_dom_path=table["path"],
        table_html_id=table["attrs"].get("id"), section_dom_path=owner["path"] if owner else None,
        metadata_dom_paths=[n["path"] for n in fragments], method=method, caption=title,
        statement_basis=("consolidated" if title.lower().startswith("consolidated") else "separate") if title else None,
        currency=currency, unit_scale=scale, unit_evidence=unit,
        status="FAIL" if errors else "PASS", denial_reasons=errors)


def statement_boundaries(html):
    document = Document()
    document.feed(html)
    return [boundary(t) for t in document.tables]


def document_evidence_class(html):
    """A review report is not an annual audit or a preliminary earnings release."""
    document = Document()
    document.feed(html)
    value = text(document.root)
    patterns = (
        r"independent auditors[’']? review report",
        r"we have reviewed the accompanying consolidated",
        r"interim financial reporting",
    )
    matches = [re.search(p, value, re.I) for p in patterns]
    if not all(matches):
        return None
    return dict(contract='foreign-document-evidence-class-v1',
                evidence_class='AUDITOR_REVIEWED_INTERIM_STATEMENT',
                evidence_fragments=[m[0] for m in matches],
                annual_audit_claim=False, scope='DOCUMENT_DESCRIPTION_ONLY')
