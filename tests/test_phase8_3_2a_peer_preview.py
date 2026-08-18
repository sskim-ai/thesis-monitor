from scripts.phase8_3_2a_peer_preview import build_preview


def test_preview_changes_only_available_peer_message() -> None:
    source = """# Source

## US

### TSLA

#### AFTER - Phase 8.5.3.1

Header

📐 Valuation
Current valuation.

Next section.

### RXRX

#### AFTER - Phase 8.5.3.1

Header

📐 Valuation
Biotech valuation.

Next section.
"""
    audit = {
        "states": {
            "TSLA": {
                "available": True,
                "display_metric": "trailing_pe",
                "framework": "automotive",
                "metrics": {
                    "trailing_pe": {
                        "available": True,
                        "company_value": 100.0,
                        "median": 20.0,
                        "sample_count": 3,
                        "company_vs_median_pct": 400.0,
                    }
                },
            },
            "RXRX": {"available": False, "metrics": {}},
        }
    }

    preview = build_preview(source, audit)

    assert "Peer context added: 1 / 2" in preview
    assert "| US | RXRX | UNCHANGED |" in preview
    assert preview.count("Biotech valuation.") == 2
    assert "3개 peer PER 중앙값" in preview
