from pathlib import Path

from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from scripts import synthetic_canary_fixture_repair_ownership_resume as resume


def test_fictional_fixture_separates_identity_from_routing_market() -> None:
    us = resume.fictional_owned("SYNTHETIC_US_TEST", market="us")
    kr = resume.fictional_owned("SYNTHETIC_KR_TEST", market="kr")

    assert us.source_packet.market == "us"
    assert kr.source_packet.market == "kr"
    assert us.source_packet.ticker.startswith("SYNTHETIC_")
    assert kr.source_packet.ticker.startswith("SYNTHETIC_")
    assert not ({us.source_packet.ticker, kr.source_packet.ticker} & set(resume.CURRENT_HOLDOUT))


def test_synthetic_packet_preflight_covers_all_frozen_shapes() -> None:
    proof = resume.preflight_document()

    assert proof["synthetic_packet_schema_preflight"] == "PASS"
    assert proof["production_market_enum_mutation"] == 0
    assert proof["production_packet_schema_mutation"] == 0
    assert proof["real_issuer_used_as_canary"] == 0
    assert {
        (row["case"], row["market"], row["subject_count"])
        for row in proof["cases"]
    } == {
        ("us_single", "us", 1),
        ("kr_single", "kr", 1),
        ("us4", "us", 4),
        ("kr4", "kr", 4),
        ("timing_us", "us", 1),
        ("timing_kr", "kr", 1),
    }


def test_production_packet_schema_and_transport_topology_remain_frozen() -> None:
    assert resume.packet_schema_sha256() == resume.EXPECTED_PACKET_SCHEMA_SHA256
    assert resume.transport_hashes(Path.cwd()) == resume.EXPECTED_TRANSPORT_HASHES
    market_schema = DecisionEvidencePacket.model_json_schema()["properties"]["market"]

    assert market_schema["enum"] == ["kr", "us"]
    assert "synthetic" not in market_schema["enum"]


def test_timeout_batch_and_consumed_cohort_gates_are_frozen() -> None:
    assert resume.MODEL_TIMEOUT_SECONDS == 1800
    assert resume.MODEL_CONTEXT_BATCH_SIZE == 4
    assert resume.MAX_CANARY_MODEL_CALLS == 7
    assert not (set(resume.CONSUMED_LATEST_HOLDOUT16) & set(resume.CURRENT_HOLDOUT))
