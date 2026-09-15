from __future__ import annotations

from collections import Counter

from scripts import semantic_single_source_convergence_repair_m12bi as m12bi


def test_required_report_matrix_is_complete_and_unique() -> None:
    assert len(m12bi.REPORT_SLUGS) == 96
    assert len(set(m12bi.REPORT_SLUGS)) == 96


def test_unchanged_golden_corpus_converges_on_applicable_surfaces() -> None:
    corpus = m12bi.golden_corpus_after()
    rows = [row for group in corpus.values() for row in group]

    assert len(rows) == 40
    assert all(row["canonical_result"]["status"] == "PASS" for row in rows)
    assert all(row["applicable_surface_result_equality"] for row in rows)
    assert not any(row["cross_path_divergence"] for row in rows)
    assert all(
        surface["proof_critical_legacy_duplicate_participation"] is False
        for row in rows
        for surface in row["surfaces"].values()
    )


def test_after_ownership_map_has_no_proof_critical_bypass() -> None:
    rows = m12bi.ownership_map_after()
    classifications = Counter(
        state for row in rows for state in row["surfaces"].values()
    )

    assert len(rows) == 13
    assert classifications["BYPASS_OF_CANONICAL_SERVICE"] == 0
    assert classifications["CANONICAL_SHARED_SERVICE"] == 23
    assert classifications["THIN_ADAPTER_TO_CANONICAL_SERVICE"] == 43


def test_duplicate_semantic_engines_are_sealed_from_proof_paths() -> None:
    audit = m12bi.duplicate_scan_after()

    assert audit["status"] == "PASS"
    assert audit["legacy_duplicate_divergent_count"] == 0
    assert audit["proof_critical_duplicate_semantic_engine_count"] == 0
    assert audit["proof_critical_fallback_participation_count"] == 0
    assert audit["legacy_duplicate_equivalent_count"] == 1


def test_bundle_inventory_never_adds_frozen_raw_model_artifacts() -> None:
    paths = {str(path) for path in m12bi.artifact_files()}

    assert not any("model-contexts" in path for path in paths)
    assert not any("transport-receipts" in path for path in paths)
    assert not any(path.endswith("output.raw.txt") for path in paths)
