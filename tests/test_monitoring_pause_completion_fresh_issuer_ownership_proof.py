from __future__ import annotations

from scripts import monitoring_pause_completion_fresh_issuer_ownership_proof as proof


def test_merge_exposure_registry_preserves_85_and_appends_16() -> None:
    prior = {
        "rows": [
            {"canonical_issuer_key": f"issuer:{index}"} for index in range(85)
        ]
    }
    overlay = {
        "prior_registry_sha256": proof.PRIOR_REGISTRY_SHA256,
        "reconciled_registry_count": 101,
        "rows": [
            {
                "canonical_issuer_key": f"new:{index}",
                "ticker": f"N{index}",
                "market": "us",
                "security_aliases": [f"N{index}"],
                "actual_output_exposure": True,
                "exclusion_reasons": [
                    "ACTUAL_REAL_MODEL_OUTPUT_EXPOSURE",
                    "INCOMPLETE_FIRST_AFTER_FULL_ISSUER_EXPOSURE",
                ],
            }
            for index in range(16)
        ],
    }

    result = proof.merge_exposure_registry(prior, overlay)

    assert result["prior_registry_count"] == 85
    assert result["appended_exposed_issuer_count"] == 16
    assert result["reconciled_registry_count"] == 101
    assert result["exclusion_shrink_count"] == 0
    assert len(result["all_excluded_issuer_keys"]) == 101


def test_filter_candidate_rows_uses_canonical_issuer_and_preserves_order() -> None:
    rows = [
        {
            "display_symbol": ticker,
            "market": "us",
            "canonical_issuer_key": issuer,
            "identity_resolution_status": "IDENTITY_RESOLVED",
            "routing_support_status": "ROUTING_SUPPORTED",
            "eligibility_decision": "ELIGIBLE_SUPPORTED_SECURITY",
        }
        for ticker, issuer in (
            ("OLD", "issuer:old"),
            ("A", "issuer:a"),
            ("A2", "issuer:a"),
            ("B", "issuer:b"),
        )
    ]

    result = proof.filter_candidate_rows(
        ("OLD", "A", "A2", "B"),
        rows,
        {"issuer:old"},
        market="us",
    )

    assert [row["display_symbol"] for row in result] == ["A", "B"]


def test_parse_disabled_labels_only_accepts_true_entries() -> None:
    output = '''
    disabled services = {
        "com.example.paused" => true
        "com.example.also-paused" => disabled
        "com.example.active" => false
        "com.example.also-active" => enabled
    }
    '''

    assert proof.parse_disabled_labels(output) == {
        "com.example.paused",
        "com.example.also-paused",
    }


def test_model_topology_remains_exact() -> None:
    assert proof.runner.MODEL == "gpt-5.6-sol"
    assert proof.runner.EFFORT == "xhigh"
    assert proof.EXPECTED_INVOCATIONS_PER_RUN == 8
    assert proof.EXPECTED_TOTAL_INVOCATIONS == 32
