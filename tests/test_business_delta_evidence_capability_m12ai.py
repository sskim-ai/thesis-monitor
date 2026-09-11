from __future__ import annotations

import json
import re

from app.services.business_delta_evidence_service import (
    BusinessDeltaCapability,
    BusinessDeltaEvidenceRole,
    build_business_delta_evidence_view,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
)
from app.services.two_stage_directional_service import (
    CORE_JUDGMENT_OUTPUT_CONTRACT,
    DirectionalCoreJudgment,
)
from scripts import business_delta_evidence_capability_m12ai as task
from scripts import directional_financial_context_m12 as m12
from scripts import main_integration_two_stage_directional_m12ae_r2_runtime as base


def test_required_artifact_names_are_complete_and_unique() -> None:
    assert set(task.SLUGS) == set(range(1, 84))
    assert len(set(task.SLUGS.values())) == 83


def test_frozen_latest_result_identity_and_runtime_contract() -> None:
    assert task.PREVIOUS_BUNDLE_SHA256 == (
        "8bf0c08091100e1ade31a4e8a467368f67c2b0a44cc208ebef3d25abe265a690"
    )
    assert task.PREVIOUS_INDEXED_PAYLOADS == 147
    assert task.PREVIOUS_ZIP_ENTRIES == 148
    assert (task.MODEL, task.EFFORT, task.TIMEOUT_SECONDS) == (
        "gpt-5.6-sol",
        "xhigh",
        1800,
    )
    assert task.FICTIONAL_MODEL_CALLS == 12
    assert task.EXPECTED_SHADOW_MODEL_CALLS == 18


def test_fictional_capabilities_are_derived_before_model_generation() -> None:
    _packets, owned, catalogs, contexts = m12.fictional_inputs("m12ai-test")
    views = {
        ticker: build_business_delta_evidence_view(
            owned[ticker], catalogs[ticker], context=contexts[ticker]
        )
        for ticker in m12.TICKERS
    }
    assert {
        ticker
        for ticker, view in views.items()
        if view.capability == BusinessDeltaCapability.AI_JUDGMENT
    } == {"FIC-FIN-01", "FIC-FIN-02", "FIC-FIN-04", "FIC-FIN-06"}
    assert {
        ticker
        for ticker, view in views.items()
        if view.capability == BusinessDeltaCapability.UNCHANGED_ONLY
    } == {"FIC-FIN-03", "FIC-FIN-05", "FIC-FIN-07", "FIC-FIN-08"}
    assert all(
        view.capability != BusinessDeltaCapability.INPUT_AMBIGUOUS
        for view in views.values()
    )


def test_exact_m12ah_003690_is_unchanged_only_without_ticker_exception() -> None:
    state, packets = task._previous_source_packets()
    tickers = tuple(str(ticker) for ticker in state["tickers"])
    _evidence, owned, catalogs, contexts, _stocks = base._build_shadow_inputs(
        packets, tickers
    )
    view = build_business_delta_evidence_view(
        owned["003690"],
        catalogs["003690"],
        context=contexts["003690"],
    )
    e19 = next(item for item in view.items if item.alias == "E19")
    assert view.capability == BusinessDeltaCapability.UNCHANGED_ONLY
    assert view.eligible_change_refs == ()
    assert e19.role == BusinessDeltaEvidenceRole.THESIS_BASELINE_CONTEXT
    assert "003690" not in task.DELTA_PROMPT


def test_monolithic_and_stage1_receive_identical_view_and_enum() -> None:
    packets, owned, catalogs, contexts = m12.fictional_inputs("m12ai-schema")
    del packets
    views = task._views(owned, catalogs, contexts)
    enriched = task._enriched_contexts(contexts, views)
    tickers = m12.CONTEXTS[0]
    selected = [enriched[ticker] for ticker in tickers]
    monolithic_prompt = task._monolithic_prompt(
        packet_id="m12ai-schema",
        tickers=tickers,
        contexts=selected,
    )
    stage1_prompt = task._stage1_prompt(
        packet_id="m12ai-schema",
        tickers=tickers,
        contexts=selected,
    )
    monolithic_schema = task._batch_schema(
        model=DirectionalCoreCandidate,
        contract=CORE_OUTPUT_CONTRACT,
        packet_id="m12ai-schema",
        tickers=tickers,
        catalogs=catalogs,
        views=views,
    )
    stage1_schema = task._batch_schema(
        model=DirectionalCoreJudgment,
        contract=CORE_JUDGMENT_OUTPUT_CONTRACT,
        packet_id="m12ai-schema",
        tickers=tickers,
        catalogs=catalogs,
        views=views,
    )
    for index, ticker in enumerate(tickers):
        serialized = json.dumps(
            views[ticker].model_context(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        assert serialized in monolithic_prompt
        assert serialized in stage1_prompt
        assert task._schema_enum(monolithic_schema, index) == task._schema_enum(
            stage1_schema, index
        )


def test_task_contains_no_post_model_delta_override_or_score_rule() -> None:
    source = task._runner_path().read_text(encoding="utf-8")
    assert "ticker_specific_delta" not in source
    assert re.search(r'candidate\["business_thesis_change"\]\s*=(?!=)', source) is None
    assert re.search(r"\.business_thesis_change\s*=(?!=)", source) is None
    assert 'model_copy(update={"business_thesis_change"' not in source
    assert "def majority_vote" not in source
    assert "def delta_score" not in source
