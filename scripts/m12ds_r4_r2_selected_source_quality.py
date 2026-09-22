"""Offline selected-source binding; never grant direction from provider precedence."""
import json
from urllib.parse import urlparse

from app.services.sec_business_field_quality_service import (
    FIELDS, field_errors, reported_comparison_quality, sha,
)

CONTRACT = "m12ds-r4-r2-selected-source-quality-ownership-v1"


def identity(row):
    raw = json.loads(row.raw_financial_fields or "[]")
    return dict(ticker=row.ticker, provider=row.provider, document=row.source_filing_id,
        snapshot_content_sha256=sha(row.model_dump(mode="json", exclude={"id", "created_at"})),
        filing_date=str(row.filing_date), period_end=str(row.financial_period_end),
        period_scope=row.period_scope, period_type=row.period_type, fiscal_year=row.fiscal_year,
        is_cumulative=row.is_cumulative, snapshot_type=row.snapshot_type, currency=row.currency,
        statement_basis=row.fs_div, unit_scale=row.unit_scale,
        raw_fields_sha256=sha(raw),
        fields={m: dict(value=getattr(row, m), raw_rows=[r for r in raw if r.get("field") == m],
                        hard_errors=field_errors(row, m)) for m in FIELDS},
        hard_errors=json.loads(row.financial_hard_errors or "[]"))


def _issuer_errors(row, binding):
    if binding.get("ticker") != row.ticker or binding.get("status") != "PASS":
        return ["selected_issuer_binding_mismatch"]
    raw = json.loads(row.raw_financial_fields or "[]")
    if row.provider == "sec_companyfacts":
        issuers = {str(r.get("issuer_cik")) for r in raw if r.get("issuer_cik")}
        issuers.update(str(r["field_quality"].get("issuer_cik")) for r in raw if r.get("field_quality"))
        expected = binding.get("issuer_id", "").removeprefix("CIK:")
        if not issuers or any(not x.isdigit() or x.zfill(10) != expected for x in issuers):
            return ["selected_issuer_lineage_missing_or_mismatched"]
        for witness in raw:
            if witness.get("field") not in FIELDS:
                continue
            if (witness.get("source_document_id") != row.source_filing_id
                    or witness.get("period_end") != str(row.financial_period_end)
                    or witness.get("source_filing_date") != str(row.filing_date)):
                return ["selected_field_document_period_binding_mismatch"]
    elif row.provider == "sec_foreign_filing":
        url = urlparse(row.source or "")
        parts = url.path.split("/")
        expected = binding.get("issuer_id", "").removeprefix("CIK:")
        if (url.scheme != "https" or url.hostname != "www.sec.gov"
                or parts[1:4] != ["Archives", "edgar", "data"] or len(parts) < 6
                or not parts[4].isdigit() or parts[4].zfill(10) != expected
                or parts[5] != str(row.source_filing_id or "").replace("-", "")):
            return ["selected_foreign_document_issuer_mismatch"]
    return []


def select_source(*, stock, rows, binding, cutoff):
    """Resolve one frozen packet projection, never a provider-local latest row."""
    facts = [f for f in stock.get("fact_catalog", []) if f.get("fact_type") == "earnings"]
    audit = dict(contract=CONTRACT, ticker=stock["ticker"], selected=None,
        selection_errors=[], alternate_sources=[], selected_field_usability={},
        comparative_attempts=[], directional_source_refs=[])
    if len(facts) != 1:
        audit["selection_errors"] = ["selected_earnings_fact_not_unique"]
        return None, audit
    fact = facts[0]
    source = (fact.get("financial_quality") or {}).get("source_snapshot") or {}
    audit.update(selected_fact_id=fact.get("fact_id"), packet_fact_sha256=sha(fact),
                 packet_source_projection=source)
    columns = {"provider": "provider", "period": "financial_period_end", "filing_date": "filing_date",
        "period_scope": "period_scope", "period_type": "period_type", "source_type": "snapshot_type",
        "fiscal_year": "fiscal_year", "is_cumulative": "is_cumulative"}
    matches = []
    if all(source.get(k) is not None for k in columns):
        for row in rows:
            if (row.ticker != stock["ticker"] or not row.source_filing_id or not row.filing_date
                    or row.filing_date > cutoff
                    or any(str(getattr(row, attr)) != str(source[key]) for key, attr in columns.items())):
                continue
            fields = fact.get("fields") or {}
            if row.provider.startswith("sec_") and any(isinstance(fields.get(m), dict) and (
                fields[m].get("value") != getattr(row, m) or fields[m].get("currency") != row.currency
            ) for m in FIELDS):
                continue
            claimed_docs = {v.get("source_filing_identifier") for v in (fact.get("field_quality") or {}).values()
                            if v.get("source_filing_identifier")}
            if claimed_docs and claimed_docs != {row.source_filing_id}:
                continue
            matches.append(row)
    if len(matches) != 1:
        audit["selection_errors"] = ["selected_source_projection_missing_or_ambiguous"]
    selected = matches[0] if len(matches) == 1 else None
    if selected:
        audit["selection_errors"] = _issuer_errors(selected, binding)
        audit["selected"] = identity(selected)
        audit["selected_identity_sha256"] = sha(audit["selected"])
        audit["selection_basis"] = "UNIQUE_FROZEN_PACKET_PROJECTION_TO_IMMUTABLE_DATABASE_ROW"
        audit["selected_field_usability"] = {m: dict(
            amount_present=getattr(selected, m) is not None,
            hard_errors=field_errors(selected, m),
            source_quality_usable=getattr(selected, m) is not None and not field_errors(selected, m)
                and not audit["selection_errors"],
            directional_by_absolute_amount=False) for m in FIELDS}
    audit["alternate_sources"] = [identity(r) for r in rows if r is not selected]
    return selected if not audit["selection_errors"] else None, audit


def assert_selection(row, audit):
    if audit.get("selection_errors") or sha(identity(row)) != audit.get("selected_identity_sha256"):
        raise ValueError("selected_source_identity_drift")


def comparison_errors(current, prior):
    errors = []
    for attr in ("ticker", "provider", "currency", "period_scope", "period_type", "fs_div", "unit_scale"):
        if getattr(current, attr) != getattr(prior, attr):
            errors.append("comparison_" + attr + "_mismatch")
    if current.provider != prior.provider:
        errors.append("cross_provider_reconciliation_owner_missing")
    if not current.currency or not prior.currency:
        errors.append("comparison_currency_missing")
    if (not current.financial_period_end or not prior.financial_period_end
            or not 330 <= (current.financial_period_end - prior.financial_period_end).days <= 400):
        errors.append("prior_year_comparable_period_missing")
    return errors


def comparison_bundle(*, selected, rows, audit, binding, cutoff, generation, database_sha256):
    assert_selection(selected, audit)
    if selected.provider == "sec_foreign_filing":
        from app.services.sec_foreign_comparison_service import foreign_comparison_quality
        candidates = [r for r in rows if r is not selected and r.provider == selected.provider
                      and not _issuer_errors(r, binding)]
        for prior in rows:
            if prior is selected:
                continue
            errors = comparison_errors(selected, prior)
            errors.extend(_issuer_errors(prior, binding))
            if prior.provider == selected.provider:
                errors.append("comparison_delegated_to_exact_occurrence_owner")
            audit["comparative_attempts"].append(dict(source=identity(prior), errors=errors,
                comparison_status="DELEGATED" if prior in candidates else "NOT_ELIGIBLE"))
        quality = foreign_comparison_quality(formal=selected, candidates=candidates,
                                             ticker=selected.ticker, cutoff=cutoff)
        audit["foreign_comparative_lineage"] = quality
        if quality["status"] != "PASS":
            audit["comparison_denial_reasons"] = ["no_exact_compatible_comparison"]
            return None, None
        inputs = dict(ticker=selected.ticker, cutoff=cutoff.isoformat(),
            formal=selected.model_dump(mode="json"),
            foreign_candidates=[r.model_dump(mode="json") for r in candidates])
        from app.services.financial_observation_quality_service import digest
        return dict(source_generation_id=generation, source_inputs=inputs,
            source_inputs_sha256=digest(inputs), frozen_database_sha256=database_sha256,
            selected_source_identity=audit["selected"], selected_packet_fact_sha256=audit["packet_fact_sha256"]), quality
    qualities = []
    for prior in rows:
        if prior is selected:
            continue
        errors = comparison_errors(selected, prior)
        if not prior.filing_date or prior.filing_date > cutoff:
            errors.append("comparison_source_not_available_at_cutoff")
        if not errors:
            errors.extend(_issuer_errors(prior, binding))
        quality = None
        if not errors and selected.provider == "sec_companyfacts":
            quality = reported_comparison_quality(formal=selected, comparison=prior,
                                                  ticker=selected.ticker, cutoff=cutoff)
            if quality["status"] != "PASS":
                errors.append("compatible_exact_comparison_lineage_missing")
        elif not errors:
            # The legacy foreign parser records current absolute values, not exact
            # comparative occurrences. Do not synthesize starts/basis/row identities.
            errors.append("provider_exact_comparison_lineage_owner_missing")
        audit["comparative_attempts"].append(dict(source=identity(prior), errors=errors,
            comparison_status=quality["status"] if quality else "NOT_ELIGIBLE"))
        if quality and not errors:
            qualities.append((prior, quality))
    if len(qualities) != 1:
        audit["comparison_denial_reasons"] = ["no_exact_compatible_comparison" if not qualities
                                              else "ambiguous_exact_comparison"]
        return None, None
    prior, quality = qualities[0]
    inputs = dict(ticker=selected.ticker, cutoff=cutoff.isoformat(),
        formal=selected.model_dump(mode="json"), comparison=prior.model_dump(mode="json"))
    from app.services.financial_observation_quality_service import digest
    return dict(source_generation_id=generation, source_inputs=inputs,
        source_inputs_sha256=digest(inputs), frozen_database_sha256=database_sha256,
        selected_source_identity=audit["selected"], selected_packet_fact_sha256=audit["packet_fact_sha256"]), quality


def apply_selected_gate(row, audit, new_refs):
    """Return only ref-local denials; never erase independent source refs."""
    if not audit:
        return
    selected = audit.get("selected") or {}
    hard = selected.get("hard_errors") or []
    hard = [*hard, *(e for f in selected.get("fields", {}).values()
                    if f["value"] is not None for e in f["hard_errors"])]
    requires_comparison = selected.get("provider") == "sec_foreign_filing" or bool(hard)
    if audit["selection_errors"] or requires_comparison:
        denied = "canonical:" + str(audit.get("selected_fact_id"))
        row["directional_source_refs"] = [r for r in row["directional_source_refs"] if r != denied]
        row["selected_source_denied_directional_refs"] = [denied]
    if audit["selection_errors"]:
        new_refs = []
    row["directional_source_refs"] = sorted(set(row["directional_source_refs"] + new_refs))
    if row.get("binding_error") or row["status"] == "ISSUER_SECURITY_BINDING_UNRESOLVED":
        row["directional_source_refs"] = []
    elif not row["directional_source_refs"]:
        row["status"] = "SOURCE_QUALITY_UNUSABLE" if audit["selection_errors"] else "SOURCE_COMPARISON_UNAVAILABLE"
    else:
        row["status"] = "DIRECTIONAL_BUSINESS_SOURCE_READY"
    row["ready_for_authority_aware_core_preflight"] = row["status"] == "DIRECTIONAL_BUSINESS_SOURCE_READY"
    audit["directional_source_refs"] = row["directional_source_refs"]
    audit["direction_status"] = row["status"]
    row["selected_source_quality"] = {k: audit[k] for k in (
        "selected_identity_sha256", "selection_errors", "comparison_denial_reasons") if k in audit}
