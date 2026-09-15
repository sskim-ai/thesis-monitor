from __future__ import annotations

from scripts import fresh_monitored_semantic_convergence_m12bh as audit


def test_required_golden_corpus_is_complete() -> None:
    corpus = audit.golden_corpus()

    assert {name: len(rows) for name, rows in corpus.items()} == {
        "fcf": 10,
        "net_debt": 6,
        "working_capital": 7,
        "financial_sector": 4,
        "configured_signal": 5,
        "business_delta": 5,
        "market_expectation": 3,
    }
    assert sum(len(rows) for rows in corpus.values()) == 40
    assert all(
        row["canonical_result"]["status"] == "PASS" for rows in corpus.values() for row in rows
    )


def test_fcf_current_and_prospective_roles_remain_contrastive() -> None:
    rows = {row["case_id"]: row for row in audit.golden_corpus()["fcf"]}

    assert rows["FCF-G01"]["canonical_result"]["observed"]["current_safe_fcf_evidence_required"]
    assert not rows["FCF-G03"]["canonical_result"]["observed"]["current_safe_fcf_evidence_required"]
    assert rows["FCF-G09"]["canonical_result"]["observed"]["proxy_as_fcf_hard_failure"]
    assert rows["FCF-G10"]["canonical_result"]["observed"]["explicit_not_fcf_disclaimer"]


def test_fresh_surface_probe_exposes_canonical_bypass() -> None:
    probe = audit._fresh_bypass_probe("FCF-G01")

    assert probe == {
        "surface": "fresh/new-issuer",
        "status": "BYPASS_NO_CANONICAL_ROLE",
        "partial_audit_status": "PASS",
        "canonical_service_identity": False,
        "classification": "BYPASS_OF_CANONICAL_SERVICE",
    }


def test_call_graph_records_shared_orchestrator_after_convergence_repair() -> None:
    graph = audit._entrypoint_map()["call_sites"]
    fresh = graph["scripts/new_issuer_holdout_selection_ownership_proof.py"]
    monitored = graph["scripts/directional_financial_context_m12.py"]

    assert not fresh["validate_directional_financial_semantics"]
    assert not fresh["validate_qtd_ytd_conflict_semantics"]
    assert monitored["validate_directional_financial_semantics"]
    assert not monitored["validate_qtd_ytd_conflict_semantics"]
    assert fresh["audit_owned_directional_core_semantics"]
    assert monitored["audit_owned_directional_core_semantics"]


def test_ownership_map_requires_stop_before_shadow() -> None:
    rows = audit._ownership_rows()

    assert len(rows) == 13
    assert any(row["fresh_consumers"] == ["BYPASS_OF_CANONICAL_SERVICE"] for row in rows)
    assert any(row["status"] == "CONVERGENCE_DEBT_PRESENT" for row in rows)


def test_required_report_numbering_is_exact() -> None:
    assert len(audit.BASE_REPORT_SLUGS) == 39
    assert len(audit.DEBT_REPORT_SLUGS) == 6
    assert len(audit.COMPLETION_REPORT_SLUGS) == 13
    assert audit.BASE_REPORT_SLUGS[0] == "repository-provenance"
    assert audit.BASE_REPORT_SLUGS[-1] == "cross-path-golden-corpus-equality-summary"
    assert audit.DEBT_REPORT_SLUGS[0] == "divergent-duplicate-classifier-list"
    assert audit.COMPLETION_REPORT_SLUGS[-1] == "program-completion"
