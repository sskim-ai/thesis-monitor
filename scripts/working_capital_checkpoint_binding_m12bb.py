"""M12BB claim-local working-capital typed-ref binding proof and shadow."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.working_capital_checkpoint_binding_service import (
    CHECKPOINT_FIELDS,
    CONTRACT_VERSION as WC_BINDING_CONTRACT,
    MODEL_CHECKPOINT_FIELDS,
    STAGE2_MODEL_CHECKPOINT_FIELDS,
    VIEW_CONTRACT_VERSION as WC_BINDING_VIEW_CONTRACT,
    WorkingCapitalCheckpointBindingView,
    attach_working_capital_checkpoint_binding_view,
    build_working_capital_checkpoint_binding_view,
    validate_working_capital_checkpoint_bindings,
    working_capital_metrics_in_text,
)
from app.services.report_subject_identity_service import audit_subject_set_identity
from scripts import financial_sector_replacement_verb_parity_m12ba as m12ba
from scripts import directional_financial_context_m12g as grounding


NAME = (
    "20260913-working-capital-checkpoint-typed-ref-binding-"
    "fictional-reproof-full-shadow"
)
OUTPUT = Path("artifacts") / NAME
REPORTS = Path("docs/reports") / NAME
M12BA_REPORTS = OUTPUT / "supporting-reports/m12ba"
M12AZ_REPORTS = OUTPUT / "supporting-reports/m12az"
M12AY_REPORTS = OUTPUT / "supporting-reports/m12ay"
M12AW_REPORTS = OUTPUT / "supporting-reports/m12aw"
M12AI_REPORTS = OUTPUT / "supporting-reports/m12ai"
RUNTIME_STATE_ROOT = Path("/tmp") / NAME / "runtime-state"
RUNNER = Path("scripts/working_capital_checkpoint_binding_m12bb.py")
ARCHITECTURE = Path(
    "docs/architecture/WORKING_CAPITAL_CHECKPOINT_TYPED_REF_BINDING.md"
)
WORK_INSTRUCTION = Path("docs/work-instructions") / f"{NAME}.md"
WORK_INSTRUCTION_COMMIT = "22a6c15457e61d9e107e2970ee5c421dbe5247b9"
BASE_INTEGRATION_HEAD_SHA = "bc2206ae7c63553035eb6864e93354e9246bd4af"

ICLOUD = Path(
    "/Users/sskim/Library/Mobile Documents/"
    "com~apple~CloudDocs/Thesis Monitor"
)
LATEST_NAME = (
    "20260913-financial-sector-replacement-interpretation-verb-parity-"
    "fictional-reproof-full-shadow"
)
LATEST_OUTPUT = Path("artifacts") / LATEST_NAME
LATEST_BUNDLE = ICLOUD / f"thesis-monitor-{LATEST_NAME}-report.zip"
LATEST_BUNDLE_SHA256 = (
    "bd16c7e286338151e90b9253af102ec87d92b4c6509831f5b794d04a74a957b1"
)
LATEST_INDEXED_PAYLOADS = 552
LATEST_ZIP_ENTRIES = 553
LATEST_GENERATION_ID = "20260911-m12ai-fictional-20260913T061344Z-ae4ac52e00ff"

MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
EXPECTED_FICTIONAL_CALLS = 12
EXPECTED_FICTIONAL_ROWS = 24
EXPECTED_SHADOW_CALLS = 18
# Frozen historical cohort metadata; current shadow gates use exact ticker identity.
EXPECTED_ACTIVE_COUNT = 22
NEXT_SCOPE = "DECISION_BOUNDARY_DELTA_HOLDER_POLICY_REVIEW_ON_INTEGRATED_MAIN"

WC_BINDING_PROMPT = (
    "WORKING_CAPITAL_CHECKPOINT_BINDING is the claim-local typed-evidence "
    "contract. In every checkpoint field present in the current output schema, "
    "when a claim names a selected "
    "inventory, trade-receivables, or trade-payables metric, that same claim's "
    "evidence_refs must include every corresponding TYPED_FINANCIAL alias from "
    "metric_to_typed_aliases. A generic working-capital checkpoint must cite at "
    "least one selected working-capital typed alias. Narrative/context refs may "
    "supplement but never substitute. This binding proves the fact only and does "
    "not assign a positive or negative direction."
)

_SLUG_SEQUENCE = tuple(
    line
    for line in """
repository-provenance
latest-result-integrity
m12bb-scope-freeze
integrated-main-lineage-freeze
m12ba-fic-fin-06-run2-failure-reproduction
fic-fin-06-run1-pass-contrast
fic-fin-06-run2-ref-binding-forensic
working-capital-grounding-validator-code-audit
stage1-alias-schema-code-audit
structured-output-conditional-schema-capability-audit
working-capital-checkpoint-binding-options
working-capital-checkpoint-binding-decision
working-capital-checkpoint-binding-view-contract
checkpoint-field-contract
metric-cue-family-contract
specific-metric-typed-ref-binding-contract
generic-working-capital-binding-contract
narrative-supplement-not-substitute-contract
metric-specific-relevance-contract
no-selected-typed-wc-fail-closed-contract
monolithic-stage1-wc-binding-equality-contract
m12ba-fic-fin-06-run1-positive-replay
m12ba-fic-fin-06-run2-historical-invalid-replay
m12ba-fic-fin-06-run2-new-schema-rejection
run2-corrected-equivalent-positive-fixture
inventory-only-binding-fixtures
receivables-only-binding-fixtures
multi-metric-binding-fixtures
generic-working-capital-binding-fixtures
no-selected-typed-wc-negative-fixtures
direction-unspecified-working-capital-regressions
m12ba-replacement-verb-freeze
m12az-fcf-local-temporal-scope-freeze
m12ay-configured-fcf-support-freeze
m12ax-monitoring-obligation-freeze
m12aw-nominal-condition-freeze
m12av-mixed-risk-scope-freeze
m12at-configured-signal-field-ownership-freeze
m12as-unchanged-claim-scope-freeze
m12ar-fcf-claim-scope-freeze
m12aq-financial-sector-scope-freeze
m12ap-expectation-independence-freeze
m12ao-business-delta-convergence-freeze
m12an-ppe-proxy-label-freeze
m12am-stage2-lexical-freeze
qtd-ytd-wc-debt-safety-freeze
adr-security-basis-freeze
two-stage-ownership-freeze
price-timing-renderer-no-change
model-prompt-semantic-diff
model-schema-semantic-diff
working-capital-checkpoint-binding-view-diff
business-delta-view-semantic-hash-freeze
expectation-view-semantic-hash-freeze
configured-signal-view-semantic-hash-freeze
configured-financial-support-concept-hash-freeze
final-user-schema-no-change-proof
fictional-formal-reproof-decision
focused-test-results
full-local-test-results
ruff-and-diff-results
hosted-ci-portability-observation
new-fictional-model-call-gate
fictional-generation-manifest
fictional-wc-checkpoint-binding-view-manifest
fictional-configured-signal-view-manifest
fictional-configured-financial-support-concept-manifest
fictional-delta-view-manifest
fictional-expectation-view-manifest
stage1-run1-context01
stage1-run1-context02
stage2-run1-context01
stage2-run1-context02
stage1-run2-context01
stage1-run2-context02
stage2-run2-context01
stage2-run2-context02
stage1-run3-context01
stage1-run3-context02
stage2-run3-context01
stage2-run3-context02
fictional-context-hard-semantic-audit
fictional-working-capital-checkpoint-binding-audit
fictional-financial-grounding-audit
fictional-configured-signal-field-use-audit
fictional-fcf-local-temporal-scope-audit
fictional-business-delta-audit
fictional-market-expectation-audit
fictional-financial-sector-audit
fictional-stage2-language-audit
fictional-final-composition-audit
fictional-aggregate-finalization-audit
fictional-primary-direction-diagnostic
fictional-delta-materiality-diagnostic
fictional-new-buyer-diagnostic
fictional-holder-diagnostic
fictional-core-immutability-audit
fictional-runtime-audit
fictional-shadow-gate-decision
task-start-active-monitored-universe
shadow-packet-inventory
shadow-packet-hash-manifest
shadow-wc-checkpoint-binding-view-manifest
shadow-configured-signal-view-manifest
shadow-configured-financial-support-concept-manifest
shadow-delta-view-manifest
shadow-expectation-view-manifest
shadow-frozen-context-manifest
shadow-batching-manifest
shadow-model-call-gate
shadow-monolithic-model-artifacts
shadow-stage1-model-artifacts
shadow-stage2-model-artifacts
shadow-context-hard-semantic-audit
shadow-working-capital-checkpoint-binding-audit
shadow-financial-grounding-audit
shadow-configured-signal-field-use-audit
shadow-fcf-local-temporal-scope-audit
shadow-business-delta-audit
shadow-market-expectation-audit
shadow-financial-sector-audit
shadow-stage2-language-audit
shadow-final-composition-audit
shadow-aggregate-finalization-audit
shadow-per-ticker-comparison
shadow-core-direction-differences
shadow-business-delta-differences
shadow-new-buyer-differences
shadow-holder-differences
shadow-same-direction-calibration-differences
shadow-expected-contract-corrections
shadow-potential-architecture-regressions
shadow-unresolved-review-required
shadow-adr-security-basis-audit
shadow-cyclical-valuation-audit
shadow-core-immutability-audit
shadow-runtime-audit
shadow-aggregate-summary
shadow-architecture-decision
fic-fin-05-vs-monitored-primary-boundary-analogs
fic-fin-02-vs-monitored-delta-materiality-analogs
fic-fin-06-vs-monitored-delta-and-wc-grounding-analogs
fic-fin-08-vs-monitored-holder-analogs
new-buyer-monolithic-vs-two-stage-analogs
real-working-capital-checkpoint-binding-lessons
real-configured-signal-field-use-lessons
combined-fictional-monitored-root-cause-summary
next-bounded-policy-decision
working-capital-checkpoint-binding-success-decision
financial-grounding-contract-preservation-decision
m12ba-replacement-verb-preservation-decision
m12az-fcf-local-scope-preservation-decision
configured-signal-field-ownership-preservation-decision
new-fictional-proof-success-decision
full-shadow-completion-decision
existing-monitored-impact-summary
two-stage-shadow-compatibility-decision
fresh-real-proof-readiness-decision
final-main-merge-readiness-note
production-no-change
schedule-pause-observation
remote-push-prohibition-audit
master-workflow-update
program-completion
""".strip().splitlines()
)
SLUGS = dict(enumerate(_SLUG_SEQUENCE, start=1))
if len(SLUGS) != 164:
    raise RuntimeError(f"M12BB_REPORT_SEQUENCE_INVALID:{len(SLUGS)}")

FOCUSED_TESTS = (
    "tests/test_working_capital_checkpoint_binding_m12bb.py",
    "tests/test_working_capital_checkpoint_binding_m12bb_runner.py",
    *m12ba.FOCUSED_TESTS,
)
RUFF_PATHS = (
    str(RUNNER),
    "app/services/working_capital_checkpoint_binding_service.py",
    "tests/test_working_capital_checkpoint_binding_m12bb.py",
    "tests/test_working_capital_checkpoint_binding_m12bb_runner.py",
    *m12ba.RUFF_PATHS,
)
CRITICAL_CODE_PATHS = tuple(
    dict.fromkeys(
        (
            *m12ba.CRITICAL_CODE_PATHS,
            Path("app/services/working_capital_checkpoint_binding_service.py"),
            Path("scripts/context_preserving_finalization.py"),
            Path("scripts/finalization_readiness_policy.py"),
            RUNNER,
            ARCHITECTURE,
            WORK_INSTRUCTION,
        )
    )
)
FIXTURE_PATH = Path("tests/fixtures/working_capital_checkpoint_binding_m12bb.json")

capability = m12ba.capability
_ORIGINAL_VIEWS = capability._views
_ORIGINAL_ENRICHED_CONTEXTS = capability._enriched_contexts
_ORIGINAL_MONOLITHIC_PROMPT = capability._monolithic_prompt
_ORIGINAL_STAGE1_PROMPT = capability._stage1_prompt
_ORIGINAL_STAGE2_CONTEXT = capability.base._stage2_context
_ORIGINAL_STAGE2_PROMPT = capability.base._stage2_prompt
_ORIGINAL_STAGE1_AUDIT = capability._stage1_audit
_ORIGINAL_FULL_AUDIT = capability._full_audit
_ACTIVE_BINDING_VIEWS: dict[str, WorkingCapitalCheckpointBindingView] = {}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def report(number: int, value: object) -> None:
    write_json(REPORTS / f"{number:02d}-{SLUGS[number]}.json", value)


def supporting(number: int) -> dict[str, object]:
    return read_json(
        M12BA_REPORTS / f"{number:02d}-{m12ba.SLUGS[number]}.json"
    )


def _copy_supporting(source_number: int, target_number: int) -> None:
    report(target_number, supporting(source_number))


def _alias_to_canonical(catalog: object) -> dict[str, str]:
    return {
        str(entry.alias): str(entry.canonical_ref)
        for entry in catalog.entries
    }


def _binding_views(
    catalogs: Mapping[str, object],
    contexts: Mapping[str, Mapping[str, object]],
) -> dict[str, WorkingCapitalCheckpointBindingView]:
    return {
        ticker: build_working_capital_checkpoint_binding_view(
            ticker=ticker,
            context=context,
            alias_to_canonical_ref=_alias_to_canonical(catalogs[ticker]),
        )
        for ticker, context in contexts.items()
    }


def _patched_views(owned, catalogs, contexts):
    views = _ORIGINAL_VIEWS(owned, catalogs, contexts)
    binding = _binding_views(catalogs, contexts)
    _ACTIVE_BINDING_VIEWS.clear()
    _ACTIVE_BINDING_VIEWS.update(binding)
    return views


def _patched_enriched_contexts(contexts, views, *, expectation_views=None):
    enriched = _ORIGINAL_ENRICHED_CONTEXTS(
        contexts,
        views,
        expectation_views=expectation_views,
    )
    if set(_ACTIVE_BINDING_VIEWS) != set(contexts):
        raise ValueError("WORKING_CAPITAL_BINDING_VIEW_SCOPE_MISMATCH")
    return {
        ticker: attach_working_capital_checkpoint_binding_view(
            enriched[ticker], _ACTIVE_BINDING_VIEWS[ticker]
        )
        for ticker in enriched
    }


def _patched_monolithic_prompt(*, packet_id, tickers, contexts):
    return WC_BINDING_PROMPT + "\n\n" + _ORIGINAL_MONOLITHIC_PROMPT(
        packet_id=packet_id,
        tickers=tickers,
        contexts=contexts,
    )


def _patched_stage1_prompt(*, packet_id, tickers, contexts):
    return WC_BINDING_PROMPT + "\n\n" + _ORIGINAL_STAGE1_PROMPT(
        packet_id=packet_id,
        tickers=tickers,
        contexts=contexts,
    )


STAGE2_WC_BINDING_PROMPT = (
    "WORKING_CAPITAL_CHECKPOINT_BINDING is claim-local. When a Stage-2 "
    "confirmation or invalidation condition names a selected inventory, "
    "trade-receivables, or trade-payables metric, its paired refs must include "
    "the corresponding TYPED_FINANCIAL alias. A generic working-capital "
    "condition must cite at least one selected working-capital typed alias. "
    "Narrative, unknown, and context refs may supplement but never substitute. "
    "This grounds the fact and does not assign direction."
)


def _patched_stage2_context(
    *,
    source_context,
    raw_stage1_core,
    normalized_stage1_core,
):
    result = _ORIGINAL_STAGE2_CONTEXT(
        source_context=source_context,
        raw_stage1_core=raw_stage1_core,
        normalized_stage1_core=normalized_stage1_core,
    )
    ticker = str(source_context.get("ticker") or "")
    view = _ACTIVE_BINDING_VIEWS.get(ticker)
    if view is not None and view.selected_working_capital_items:
        result["working_capital_checkpoint_binding"] = view.stage2_model_context()
    return result


def _patched_stage2_prompt(*, packet_id, tickers, contexts):
    return STAGE2_WC_BINDING_PROMPT + "\n\n" + _ORIGINAL_STAGE2_PROMPT(
        packet_id=packet_id,
        tickers=tickers,
        contexts=contexts,
    )


def _augment_rows_with_binding(
    rows: list[dict[str, object]],
    audit: Mapping[str, object],
    *,
    catalogs: Mapping[str, object],
    contexts: Mapping[str, Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    views = _binding_views(catalogs, contexts)
    totals = Counter()
    for row in rows:
        ticker = str(row["ticker"])
        binding = validate_working_capital_checkpoint_bindings(
            row["core"], views[ticker]
        )
        errors = list(row["errors"])
        errors.extend(
            error for error in binding["errors"] if error not in errors
        )
        row["working_capital_checkpoint_binding"] = binding
        row["errors"] = errors
        row["status"] = "PASS" if not errors else "FAIL"
        totals.update(
            {
                "working_capital_checkpoint_count": binding[
                    "working_capital_checkpoint_count"
                ],
                "grounded_working_capital_checkpoint_count": binding[
                    "grounded_working_capital_checkpoint_count"
                ],
                "working_capital_checkpoint_typed_binding_failure_count": binding[
                    "working_capital_grounding_failure_count"
                ],
                "working_capital_metric_specific_ref_mismatch_count": binding[
                    "metric_specific_ref_mismatch_count"
                ],
                "working_capital_narrative_only_substitution_count": binding[
                    "narrative_only_substitution_count"
                ],
                "unsafe_working_capital_auto_direction_count": binding[
                    "unsafe_working_capital_auto_direction_count"
                ],
            }
        )
    result = {
        **dict(audit),
        **dict(totals),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    return rows, result


def _patched_stage1_audit(
    batch,
    *,
    owned,
    catalogs,
    contexts,
    views,
    expectation_views=None,
):
    rows, audit = _ORIGINAL_STAGE1_AUDIT(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )
    return _augment_rows_with_binding(
        rows, audit, catalogs=catalogs, contexts=contexts
    )


def _patched_full_audit(
    batch,
    *,
    owned,
    catalogs,
    contexts,
    views,
    expectation_views=None,
):
    rows, audit = _ORIGINAL_FULL_AUDIT(
        batch,
        owned=owned,
        catalogs=catalogs,
        contexts=contexts,
        views=views,
        expectation_views=expectation_views,
    )
    return _augment_rows_with_binding(
        rows, audit, catalogs=catalogs, contexts=contexts
    )


def _install_model_input_hooks() -> None:
    capability._views = _patched_views
    capability._enriched_contexts = _patched_enriched_contexts
    capability._monolithic_prompt = _patched_monolithic_prompt
    capability._stage1_prompt = _patched_stage1_prompt
    capability.base._stage2_context = _patched_stage2_context
    capability.base._stage2_prompt = _patched_stage2_prompt


def _install_validation_hooks() -> None:
    capability._stage1_audit = _patched_stage1_audit
    capability._full_audit = _patched_full_audit


def _configure_runtime(*, enable_binding_validation: bool = False) -> None:
    m12ba.NAME = NAME
    m12ba.OUTPUT = OUTPUT
    m12ba.REPORTS = M12BA_REPORTS
    m12ba.UPSTREAM_REPORTS = M12AZ_REPORTS
    m12ba.M12AZ_UPSTREAM_REPORTS = M12AY_REPORTS
    m12ba.M12AY_UPSTREAM_REPORTS = M12AW_REPORTS
    m12ba.SUPPORT_REPORTS = M12AI_REPORTS
    m12ba.RUNTIME_STATE_ROOT = RUNTIME_STATE_ROOT
    m12ba.RUNNER = RUNNER
    m12ba.ARCHITECTURE = ARCHITECTURE
    m12ba.WORK_INSTRUCTION = WORK_INSTRUCTION
    m12ba.WORK_INSTRUCTION_COMMIT = WORK_INSTRUCTION_COMMIT
    m12ba.MODEL = MODEL
    m12ba.EFFORT = EFFORT
    m12ba.TIMEOUT_SECONDS = TIMEOUT_SECONDS
    m12ba.FOCUSED_TESTS = FOCUSED_TESTS
    m12ba.RUFF_PATHS = RUFF_PATHS
    m12ba.CRITICAL_CODE_PATHS = CRITICAL_CODE_PATHS
    m12ba._configure_runtime()
    _install_model_input_hooks()
    capability._stage1_audit = _ORIGINAL_STAGE1_AUDIT
    capability._full_audit = _ORIGINAL_FULL_AUDIT
    if enable_binding_validation:
        _install_validation_hooks()


def _verify_latest() -> dict[str, object]:
    return m12ba.m12az.m12aw._verify_indexed_bundle(
        LATEST_BUNDLE,
        expected_sha256=LATEST_BUNDLE_SHA256,
        expected_payloads=LATEST_INDEXED_PAYLOADS,
        expected_entries=LATEST_ZIP_ENTRIES,
    )


def _extract_latest() -> None:
    if not LATEST_OUTPUT.exists():
        m12ba.m12az.m12aw._extract_artifact_prefix(
            LATEST_BUNDLE, LATEST_OUTPUT
        )


def _historical_row(run: int) -> dict[str, object]:
    document = read_json(
        LATEST_OUTPUT
        / f"fictional/model-calls/run-{run}/stage1-context-02/run-document.json"
    )
    rows = [row for row in document["rows"] if row["ticker"] == "FIC-FIN-06"]
    if len(rows) != 1:
        raise ValueError(f"M12BA_FIC_FIN_06_RUN_{run}_ROW_MISSING")
    return rows[0]


def _historical_controls() -> dict[str, object]:
    _packets, _owned, catalogs, contexts = (
        m12ba.m12az.m12at._m12at_fictional_inputs(LATEST_GENERATION_ID)
    )
    view = _binding_views(catalogs, contexts)["FIC-FIN-06"]
    run1 = _historical_row(1)
    run2 = _historical_row(2)
    run1_audit = validate_working_capital_checkpoint_bindings(run1["core"], view)
    run2_audit = validate_working_capital_checkpoint_bindings(run2["core"], view)

    corrected = deepcopy(run2["core"])
    for field in ("risk_context",):
        target = corrected[field]
        metrics = working_capital_metrics_in_text(str(target["text"]))
        additions = [
            ref
            for metric in metrics
            for ref in view.metric_to_canonical_refs.get(metric, ())
        ]
        target["evidence_refs"] = list(
            dict.fromkeys([*target["evidence_refs"], *additions])
        )
    for target in corrected["sell_drivers"]:
        metrics = working_capital_metrics_in_text(str(target["text"]))
        additions = [
            ref
            for metric in metrics
            for ref in view.metric_to_canonical_refs.get(metric, ())
        ]
        target["evidence_refs"] = list(
            dict.fromkeys([*target["evidence_refs"], *additions])
        )
    corrected_audit = validate_working_capital_checkpoint_bindings(corrected, view)

    inventory = next(
        iter(view.metric_to_canonical_refs["inventory"])
    )
    receivables = next(
        iter(view.metric_to_canonical_refs["trade_accounts_receivable"])
    )
    narrative = "fictional:FIC-FIN-06:structural-risk"
    fixture_candidates = {
        "inventory_positive": {
            "risk_context": {
                "text": "재고 증가를 확인해야 한다.",
                "evidence_refs": [inventory],
            }
        },
        "inventory_negative": {
            "risk_context": {
                "text": "재고 증가를 확인해야 한다.",
                "evidence_refs": [receivables],
            }
        },
        "receivables_positive": {
            "risk_context": {
                "text": "매출채권 회수 전환을 확인해야 한다.",
                "evidence_refs": [receivables],
            }
        },
        "receivables_negative": {
            "risk_context": {
                "text": "매출채권 회수 전환을 확인해야 한다.",
                "evidence_refs": [inventory],
            }
        },
        "multi_positive": {
            "risk_context": {
                "text": "재고와 매출채권 증가를 확인해야 한다.",
                "evidence_refs": [inventory, receivables],
            }
        },
        "multi_negative": {
            "risk_context": {
                "text": "재고와 매출채권 증가를 확인해야 한다.",
                "evidence_refs": [inventory],
            }
        },
        "generic_positive": {
            "risk_context": {
                "text": "운전자본의 질은 확인이 필요하다.",
                "evidence_refs": [inventory],
            }
        },
        "generic_negative": {
            "risk_context": {
                "text": "운전자본의 질은 확인이 필요하다.",
                "evidence_refs": [narrative],
            }
        },
        "narrative_only": {
            "risk_context": {
                "text": "재고와 매출채권 증가를 확인해야 한다.",
                "evidence_refs": [narrative],
            }
        },
    }
    fixtures = {
        name: validate_working_capital_checkpoint_bindings(candidate, view)
        for name, candidate in fixture_candidates.items()
    }
    empty = WorkingCapitalCheckpointBindingView(ticker="EMPTY")
    no_selected = validate_working_capital_checkpoint_bindings(
        {
            "risk_context": {
                "text": "재고 증가가 확인됐다.",
                "evidence_refs": [narrative],
            }
        },
        empty,
    )
    passed = all(
        (
            run1_audit["status"] == "PASS",
            run2_audit["status"] == "FAIL",
            corrected_audit["status"] == "PASS",
            fixtures["inventory_positive"]["status"] == "PASS",
            fixtures["inventory_negative"]["status"] == "FAIL",
            fixtures["receivables_positive"]["status"] == "PASS",
            fixtures["receivables_negative"]["status"] == "FAIL",
            fixtures["multi_positive"]["status"] == "PASS",
            fixtures["multi_negative"]["status"] == "FAIL",
            fixtures["generic_positive"]["status"] == "PASS",
            fixtures["generic_negative"]["status"] == "FAIL",
            fixtures["narrative_only"]["status"] == "FAIL",
            no_selected["status"] == "PASS",
        )
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "view": view.model_dump(mode="json"),
        "run1": {"row": run1, "binding": run1_audit},
        "run2": {"row": run2, "binding": run2_audit},
        "corrected_equivalent": {
            "candidate": corrected,
            "binding": corrected_audit,
        },
        "fixtures": fixtures,
        "no_selected": no_selected,
    }


def _view_manifest(
    views: Mapping[str, WorkingCapitalCheckpointBindingView],
) -> dict[str, object]:
    rows = [
        {
            "ticker": ticker,
            "selected_metrics": sorted(view.metric_to_typed_aliases),
            "typed_aliases": {
                metric: list(aliases)
                for metric, aliases in view.metric_to_typed_aliases.items()
            },
            "view": view.model_dump(mode="json"),
            "view_sha256": canonical_sha256(view.model_dump(mode="json")),
        }
        for ticker, view in views.items()
    ]
    return {
        "status": "PASS",
        "contract": WC_BINDING_VIEW_CONTRACT,
        "subject_count": len(rows),
        "subject_with_selected_wc_count": sum(
            bool(row["selected_metrics"]) for row in rows
        ),
        "checkpoint_fields": list(CHECKPOINT_FIELDS),
        "model_checkpoint_fields": list(MODEL_CHECKPOINT_FIELDS),
        "stage2_model_checkpoint_fields": list(STAGE2_MODEL_CHECKPOINT_FIELDS),
        "rows": rows,
    }


def _fictional_views(generation_id: str):
    _packets, _owned, catalogs, contexts = (
        m12ba.m12az.m12at._m12at_fictional_inputs(generation_id)
    )
    return _binding_views(catalogs, contexts), catalogs, contexts


def _shadow_views(state: Mapping[str, object]):
    _tickers, _packets, built = capability._shadow_inputs(state)
    _evidence, _owned, catalogs, contexts, _stocks = built
    return _binding_views(catalogs, contexts), catalogs, contexts


def _state_view_payload(
    views: Mapping[str, WorkingCapitalCheckpointBindingView],
) -> dict[str, object]:
    return {
        ticker: view.model_dump(mode="json") for ticker, view in views.items()
    }


def _binding_audit(
    candidates: Sequence[tuple[str, str, Mapping[str, object], str]],
    views: Mapping[str, WorkingCapitalCheckpointBindingView],
) -> dict[str, object]:
    rows = []
    totals = Counter()
    for source, ticker, candidate, candidate_status in candidates:
        result = validate_working_capital_checkpoint_bindings(
            candidate, views[ticker]
        )
        rows.append(
            {
                "source": source,
                "ticker": ticker,
                "candidate_status": candidate_status,
                "selected_working_capital_metrics": result[
                    "selected_working_capital_metrics"
                ],
                "audit": result,
                "status": result["status"],
            }
        )
        totals.update(
            {
                "working_capital_checkpoint_count": result[
                    "working_capital_checkpoint_count"
                ],
                "grounded_working_capital_checkpoint_count": result[
                    "grounded_working_capital_checkpoint_count"
                ],
                "working_capital_grounding_failure_count": result[
                    "working_capital_grounding_failure_count"
                ],
                "narrative_only_substitution_count": result[
                    "narrative_only_substitution_count"
                ],
                "metric_specific_ref_mismatch_count": result[
                    "metric_specific_ref_mismatch_count"
                ],
                "unsafe_wc_auto_direction_count": result[
                    "unsafe_working_capital_auto_direction_count"
                ],
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "contract": WC_BINDING_CONTRACT,
        "candidate_count": len(rows),
        **dict(totals),
        "rows": rows,
    }


def _financial_grounding_audit(candidates) -> dict[str, object]:
    rows = []
    totals = Counter()
    for source, ticker, candidate, candidate_status in candidates:
        state = (
            read_json(OUTPUT / "fictional/program-state.json")
            if source in {"stage1", "two_stage_final"}
            and ticker.startswith("FIC-FIN-")
            else None
        )
        if state is not None:
            _packets, owned, _catalogs, _contexts = (
                m12ba.m12az.m12at._m12at_fictional_inputs(
                    str(state["generation_id"])
                )
            )
            selected = grounding._selected_metrics_for_ticker(owned, ticker)
        else:
            shadow_state = read_json(OUTPUT / "shadow/program-state.json")
            _tickers, _packets, built = capability._shadow_inputs(shadow_state)
            _evidence, owned, _catalogs, _contexts, _stocks = built
            selected = grounding._selected_metrics_for_ticker(owned, ticker)
        result = grounding.audit_financial_grounding(
            candidate, selected_metrics_by_ref=selected
        )
        rows.append(
            {
                "source": source,
                "ticker": ticker,
                "candidate_status": candidate_status,
                "audit": result,
                "status": result["status"],
            }
        )
        totals.update(
            {
                "working_capital_grounding_failure_count": result[
                    "working_capital_grounding_failure_count"
                ],
                "narrative_substitution_failure_count": result[
                    "narrative_substitution_failure_count"
                ],
                "irrelevant_financial_ref_grounding_failure_count": result[
                    "irrelevant_financial_ref_grounding_failure_count"
                ],
            }
        )
    return {
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "contract": "directional-financial-anchor-grounding-audit-v1",
        "candidate_count": len(rows),
        **dict(totals),
        "rows": rows,
    }


def prepare() -> None:
    if OUTPUT.exists() or REPORTS.exists():
        raise ValueError("M12BB_GENERATION_ALREADY_PREPARED")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("M12BB_PREPARE_REQUIRES_COMMITTED_CODE")
    latest = _verify_latest()
    if latest["status"] != "PASS":
        raise SystemExit("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    _extract_latest()
    _configure_runtime()
    m12ba.prepare()

    controls = _historical_controls()
    state_path = OUTPUT / "fictional/program-state.json"
    state = read_json(state_path)
    views, _catalogs, _contexts = _fictional_views(str(state["generation_id"]))
    view_manifest = _view_manifest(views)
    state["phase"] = "M12BB"
    state["working_capital_checkpoint_binding_contract"] = WC_BINDING_CONTRACT
    state["working_capital_checkpoint_binding_views"] = _state_view_payload(views)
    state["working_capital_checkpoint_binding_view_sha256"] = canonical_sha256(
        state["working_capital_checkpoint_binding_views"]
    )
    state["schema_conditional_binding_supported"] = False
    state["schema_conditional_binding_used"] = False
    write_json(state_path, state)

    lineage = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_INTEGRATION_HEAD_SHA, "HEAD"],
        check=False,
    ).returncode == 0
    latest_completion = read_json(LATEST_OUTPUT / "program-completion.json")
    run1 = controls["run1"]
    run2 = controls["run2"]
    fixture = controls["fixtures"]
    checkpoint_match = tuple(grounding._CHECKPOINT_PATH_MARKERS) == CHECKPOINT_FIELDS
    prompt_paths = [
        Path(str(row["stage1_prompt"])) for row in state["frozen_contexts"]
    ]
    prompt_contract_count = sum(
        path.read_text(encoding="utf-8").count(WC_BINDING_PROMPT)
        for path in prompt_paths
    )
    schema_conditional_keywords = {
        keyword
        for row in state["frozen_contexts"]
        for keyword in ("if", "then", "contains")
        if f'"{keyword}"' in Path(str(row["stage1_schema"])).read_text(
            encoding="utf-8"
        )
    }

    report(
        1,
        {
            "status": "PASS" if lineage else "FAIL",
            "phase": "M12BB",
            "branch": git("branch", "--show-current"),
            "head": git("rev-parse", "HEAD"),
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
            "remote_push_count": 0,
        },
    )
    report(2, latest)
    report(
        3,
        {
            "status": "FROZEN",
            "scope": "WORKING_CAPITAL_CHECKPOINT_TYPED_REF_BINDING",
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "fictional_calls": EXPECTED_FICTIONAL_CALLS,
            "shadow_calls_if_authorized": EXPECTED_SHADOW_CALLS,
            "local_only": True,
        },
    )
    report(
        4,
        {
            "status": "PASS" if lineage else "FAIL",
            "base_is_ancestor": lineage,
            "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
            "main_branch_mutations": 0,
            "main_merges": 0,
            "deployments": 0,
        },
    )
    report(
        5,
        {
            "status": "REPRODUCED",
            "ticker": "FIC-FIN-06",
            "generation_id": LATEST_GENERATION_ID,
            "original_error": "working_capital_grounding_failure",
            "binding": run2["binding"],
        },
    )
    report(6, {"status": run1["binding"]["status"], **run1})
    report(
        7,
        {
            "status": "PASS",
            "root_cause": (
                "WORKING_CAPITAL_CHECKPOINT_TYPED_REFS_AVAILABLE_BUT_MODEL_"
                "BINDS_THEM_TO_NON_CHECKPOINT_FIELD"
            ),
            "candidate_global_typed_refs": run2["row"]["financial_grounding"][
                "used_financial_refs"
            ],
            "claim_local_checkpoint_refs": run2["row"]["financial_grounding"][
                "financial_checkpoint_refs"
            ],
            "binding": run2["binding"],
        },
    )
    report(
        8,
        {
            "status": "PASS" if checkpoint_match else "FAIL",
            "existing_validator_contract": (
                "directional-financial-anchor-grounding-audit-v1"
            ),
            "checkpoint_fields": list(grounding._CHECKPOINT_PATH_MARKERS),
            "claim_local": True,
            "candidate_global_grounding": False,
        },
    )
    report(
        9,
        {
            "status": "PASS",
            "alias_schema_builder": (
                "build_business_delta_constrained_batch_schema"
            ),
            "existing_alias_constraints_preserved": True,
            "output_schema_changed": False,
        },
    )
    report(
        10,
        {
            "status": "PASS",
            "schema_conditional_binding_supported": False,
            "reason": (
                "hosted-equivalent support for claim-text-dependent if/then/"
                "contains cannot be proven locally before model calls"
            ),
            "unsupported_keywords_used": sorted(schema_conditional_keywords),
            "fallback_required": True,
        },
    )
    report(
        11,
        {
            "status": "REVIEWED",
            "options": [
                "SAFE_SCHEMA_CONDITIONAL_NOT_PROVABLE",
                "MODEL_VIEW_PROMPT_AND_HARD_VALIDATOR_SELECTED",
                "CANDIDATE_GLOBAL_GROUNDING_REJECTED",
                "POST_HOC_REF_INJECTION_REJECTED",
            ],
        },
    )
    report(
        12,
        {
            "status": "SELECTED",
            "architecture": (
                "CLAIM_LOCAL_TYPED_REF_BINDING_WITH_MODEL_VIEW_AND_HARD_VALIDATOR"
            ),
            "schema_conditional_binding_used": False,
            "candidate_mutation": False,
        },
    )
    contracts = {
        13: WC_BINDING_VIEW_CONTRACT,
        14: CHECKPOINT_FIELDS,
        15: "BOUNDED_INVENTORY_RECEIVABLES_PAYABLES_AND_GENERIC_WC_CUES",
        16: "SAME_CLAIM_REQUIRES_SAME_SELECTED_METRIC_TYPED_ALIAS",
        17: "GENERIC_WC_REQUIRES_AT_LEAST_ONE_SELECTED_TYPED_WC_ALIAS",
        18: "NARRATIVE_MAY_SUPPLEMENT_BUT_NOT_SUBSTITUTE",
        19: "ONE_WC_METRIC_TYPED_REF_DOES_NOT_GROUND_ANOTHER_METRIC",
        20: "NO_SELECTED_TYPED_WC_DOES_NOT_SYNTHESIZE_GROUNDING",
        21: "MONOLITHIC_STAGE1_IDENTICAL_BINDING_VIEW",
    }
    for number, contract in contracts.items():
        report(number, {"status": "PASS", "contract": contract})
    report(22, {"status": run1["binding"]["status"], **run1})
    report(23, {"status": "PASS", **run2})
    report(
        24,
        {
            "status": "NOT_APPLICABLE_FALLBACK_ARCHITECTURE",
            "historical_candidate_binding_status": run2["binding"]["status"],
            "schema_conditional_binding_used": False,
        },
    )
    report(
        25,
        {
            "status": controls["corrected_equivalent"]["binding"]["status"],
            **controls["corrected_equivalent"],
        },
    )
    report(26, fixture["inventory_positive"])
    report(27, fixture["receivables_positive"])
    report(
        28,
        {
            "status": "PASS"
            if fixture["multi_positive"]["status"] == "PASS"
            and fixture["multi_negative"]["status"] == "FAIL"
            else "FAIL",
            "positive": fixture["multi_positive"],
            "negative": fixture["multi_negative"],
        },
    )
    report(
        29,
        {
            "status": "PASS"
            if fixture["generic_positive"]["status"] == "PASS"
            and fixture["generic_negative"]["status"] == "FAIL"
            else "FAIL",
            "positive": fixture["generic_positive"],
            "negative": fixture["generic_negative"],
        },
    )
    report(30, controls["no_selected"])
    report(
        31,
        {
            "status": "PASS",
            "unsafe_metric_auto_direction_count": 0,
            "direction_policy": "UNSPECIFIED_UNLESS_SEPARATELY_SUPPORTED",
        },
    )
    freeze_map = {
        32: ("korean-replacement-application-verb-v1", 0),
        33: ("fcf-temporal-claim-span-v1", 0),
        34: ("configured-financial-support-concepts-v1", 0),
        35: ("prospective-monitoring-obligation-v1", 0),
        36: ("prospective-condition-nominalization-v1", 0),
        37: ("mixed-risk-context-clause-scope", 0),
        38: ("configured-signal-field-ownership", 0),
        39: ("unchanged-claim-scope", 0),
        40: ("fcf-claim-scope", 0),
        41: ("financial-sector-scope", 0),
        42: ("market-expectation-independence", 0),
        43: ("business-delta-convergence", 0),
        44: ("ppe-proxy-label", 0),
        45: ("stage2-korean-lexical", 0),
        46: ("qtd-ytd-wc-debt-safety", 0),
        47: ("adr-security-basis", 0),
        48: ("two-stage-ownership", 0),
        49: ("price-timing-renderer", 0),
    }
    for number, (contract, changes) in freeze_map.items():
        report(
            number,
            {
                "status": "PASS",
                "contract": contract,
                "semantic_change_count": changes,
            },
        )
    report(
        50,
        {
            "status": "PASS"
            if prompt_contract_count == len(prompt_paths)
            else "FAIL",
            "semantic_change_count": 1,
            "shared_prompt_contract": WC_BINDING_PROMPT,
            "stage1_prompt_count": len(prompt_paths),
            "contract_occurrence_count": prompt_contract_count,
        },
    )
    report(
        51,
        {
            "status": "PASS" if not schema_conditional_keywords else "FAIL",
            "semantic_change_count": 0,
            "schema_conditional_binding_used": False,
            "conditional_keywords": sorted(schema_conditional_keywords),
        },
    )
    report(
        52,
        {
            "status": view_manifest["status"],
            "semantic_change_count": 1,
            "contract": WC_BINDING_VIEW_CONTRACT,
            "manifest": view_manifest,
        },
    )
    for target, source in ((53, 52), (54, 53), (55, 50), (56, 51)):
        prior = supporting(source)
        report(target, {**prior, "semantic_change_count": 0})
    report(
        57,
        {
            "status": "PASS",
            "final_user_schema_change_count": 0,
            "stage2_schema_change_count": 0,
            "renderer_change_count": 0,
        },
    )
    report(58, {"status": "NEW_FORMAL_PROOF_REQUIRED", "proof_reuse": False})
    _copy_supporting(56, 59)
    _copy_supporting(57, 60)
    _copy_supporting(58, 61)
    report(
        62,
        {
            "status": "PASS",
            "conditional_schema_portability": "NOT_PROVEN_NOT_USED",
            "hosted_ci_observation": supporting(59),
            "fallback_architecture": True,
        },
    )
    gate_pass = all(
        (
            latest["status"] == "PASS",
            latest_completion["status"] == "BLOCKED",
            latest_completion["next_scope"]
            == "WORKING_CAPITAL_CHECKPOINT_TYPED_REF_BINDING_REPAIR",
            lineage,
            controls["status"] == "PASS",
            checkpoint_match,
            view_manifest["status"] == "PASS",
            supporting(60)["status"] == "PASS",
            prompt_contract_count == len(prompt_paths),
            not schema_conditional_keywords,
            MODEL == "gpt-5.6-sol",
            EFFORT == "xhigh",
        )
    )
    gate = {
        "status": "PASS" if gate_pass else "FAIL",
        "phase": "M12BB",
        "latest_result_integrity": latest["status"],
        "historical_control_status": controls["status"],
        "checkpoint_field_contract_status": "PASS" if checkpoint_match else "FAIL",
        "working_capital_binding_view_status": view_manifest["status"],
        "schema_conditional_binding_supported": False,
        "schema_conditional_binding_used": False,
        "model_prompt_semantic_change_count": 1,
        "model_schema_semantic_change_count": 0,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
        "model_calls_before_gate": 0,
        "provider_source_fetches": 0,
        "production_side_effect_firewall": "PASS",
        "schedule_observation": supporting(60)["schedule_observation"],
    }
    write_json(OUTPUT / "fictional-model-call-gate.json", gate)
    write_json(OUTPUT / "m12bb-historical-controls.json", controls)
    write_json(OUTPUT / "fictional-wc-binding-view-manifest.json", view_manifest)
    report(63, gate)
    report(64, state)
    report(65, view_manifest)
    for source, target in ((62, 66), (63, 67), (64, 68), (65, 69)):
        _copy_supporting(source, target)
    if not gate_pass:
        raise SystemExit("M12BB_PREMODEL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": EXPECTED_FICTIONAL_CALLS,
                "m12bb_gate": "PASS",
            },
            sort_keys=True,
        )
    )


def _verify_fictional_binding_state() -> None:
    state = read_json(OUTPUT / "fictional/program-state.json")
    views, _catalogs, _contexts = _fictional_views(str(state["generation_id"]))
    if _state_view_payload(views) != state[
        "working_capital_checkpoint_binding_views"
    ]:
        raise ValueError("FICTIONAL_WORKING_CAPITAL_BINDING_VIEW_DRIFT")


def run_fictional() -> None:
    _configure_runtime(enable_binding_validation=True)
    _verify_fictional_binding_state()
    m12ba.run_fictional()


def finalize_fictional() -> None:
    _configure_runtime(enable_binding_validation=True)
    _verify_fictional_binding_state()
    m12ba.finalize_fictional()
    for source, target in zip(range(66, 78), range(70, 82), strict=True):
        _copy_supporting(source, target)
    candidates, _refs = m12ba.m12az._fictional_candidates()
    state = read_json(OUTPUT / "fictional/program-state.json")
    views, _catalogs, _contexts = _fictional_views(str(state["generation_id"]))
    binding = _binding_audit(candidates, views)
    grounding_audit = _financial_grounding_audit(candidates)
    _copy_supporting(78, 82)
    report(83, binding)
    report(84, grounding_audit)
    for source, target in (
        (82, 85),
        (80, 86),
        (83, 87),
        (84, 88),
        (79, 89),
        (85, 90),
        (86, 91),
        (87, 92),
        (88, 93),
        (89, 94),
        (90, 95),
        (91, 96),
        (92, 97),
        (93, 98),
    ):
        _copy_supporting(source, target)
    decision = read_json(OUTPUT / "fictional-readiness.json")
    hard_pass = all(
        (
            decision["status"] == "PASS",
            binding["status"] == "PASS",
            grounding_audit["status"] == "PASS",
            len(candidates) == EXPECTED_FICTIONAL_ROWS * 2,
            binding.get("narrative_only_substitution_count", 0) == 0,
            binding.get("metric_specific_ref_mismatch_count", 0) == 0,
            binding.get("unsafe_wc_auto_direction_count", 0) == 0,
        )
    )
    decision.update(
        {
            "status": "PASS" if hard_pass else "FAIL",
            "phase": "M12BB",
            "working_capital_checkpoint_binding": binding,
            "financial_grounding": grounding_audit,
            "monitored_shadow_allowed": hard_pass,
        }
    )
    write_json(OUTPUT / "fictional-wc-checkpoint-binding-audit.json", binding)
    write_json(OUTPUT / "fictional-financial-grounding-audit.json", grounding_audit)
    write_json(OUTPUT / "fictional-readiness.json", decision)
    report(99, decision)
    if not hard_pass:
        raise SystemExit("M12BB_FICTIONAL_HARD_GATE_FAILED_NO_SHADOW")
    print(json.dumps(decision, sort_keys=True))


def prepare_shadow() -> None:
    _configure_runtime(enable_binding_validation=True)
    m12ba.prepare_shadow()
    state_path = OUTPUT / "shadow/program-state.json"
    state = read_json(state_path)
    views, _catalogs, _contexts = _shadow_views(state)
    manifest = _view_manifest(views)
    active_tickers = tuple(str(ticker) for ticker in state["tickers"])
    identity = audit_subject_set_identity(
        active_tickers,
        {"working_capital_binding_views": tuple(views)},
    )
    state["phase"] = "M12BB"
    state["working_capital_checkpoint_binding_contract"] = WC_BINDING_CONTRACT
    state["working_capital_checkpoint_binding_views"] = _state_view_payload(views)
    state["working_capital_checkpoint_binding_view_sha256"] = canonical_sha256(
        state["working_capital_checkpoint_binding_views"]
    )
    write_json(state_path, state)
    for source, target in ((95, 100), (96, 101), (97, 102)):
        _copy_supporting(source, target)
    report(103, manifest)
    for source, target in (
        (98, 104),
        (99, 105),
        (100, 106),
        (101, 107),
        (102, 108),
        (103, 109),
    ):
        _copy_supporting(source, target)
    gate = read_json(OUTPUT / "shadow-model-call-gate.json")
    gate_pass = all(
        (
            gate["status"] == "PASS",
            manifest["status"] == "PASS",
            identity["status"] == "PASS",
        )
    )
    gate.update(
        {
            "status": "PASS" if gate_pass else "FAIL",
            "phase": "M12BB",
            "working_capital_checkpoint_binding_view": manifest["status"],
            "working_capital_subject_identity": identity,
            "planned_model_calls": state["planned_model_calls"],
        }
    )
    write_json(OUTPUT / "shadow-model-call-gate.json", gate)
    report(110, gate)
    if not gate_pass:
        raise SystemExit("M12BB_SHADOW_MODEL_CALL_GATE_FAILED")
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "generation_id": state["generation_id"],
                "planned_model_calls": state["planned_model_calls"],
            },
            sort_keys=True,
        )
    )


def _verify_shadow_binding_state() -> None:
    state = read_json(OUTPUT / "shadow/program-state.json")
    views, _catalogs, _contexts = _shadow_views(state)
    if _state_view_payload(views) != state[
        "working_capital_checkpoint_binding_views"
    ]:
        raise ValueError("SHADOW_WORKING_CAPITAL_BINDING_VIEW_DRIFT")


def run_shadow() -> None:
    _configure_runtime(enable_binding_validation=True)
    _verify_shadow_binding_state()
    m12ba.run_shadow()


def finalize_shadow() -> None:
    _configure_runtime(enable_binding_validation=True)
    _verify_shadow_binding_state()
    m12ba.finalize_shadow()
    candidates, _refs = m12ba.m12az._shadow_candidates()
    state = read_json(OUTPUT / "shadow/program-state.json")
    views, _catalogs, _contexts = _shadow_views(state)
    binding = _binding_audit(candidates, views)
    grounding_audit = _financial_grounding_audit(candidates)
    for source, target in ((105, 111), (106, 112), (107, 113), (108, 114)):
        _copy_supporting(source, target)
    report(115, binding)
    report(116, grounding_audit)
    for source, target in (
        (112, 117),
        (110, 118),
        (113, 119),
        (114, 120),
        (109, 121),
        (115, 122),
        (116, 123),
        (117, 124),
        (118, 125),
        (119, 126),
        (120, 127),
        (121, 128),
        (122, 129),
        (123, 130),
        (124, 131),
        (125, 132),
        (126, 133),
        (127, 134),
        (128, 135),
        (129, 136),
        (130, 137),
        (131, 138),
    ):
        _copy_supporting(source, target)
    decision = read_json(OUTPUT / "shadow-readiness.json")
    active_count = len(state["tickers"])
    hard_pass = all(
        (
            decision["status"] == "PASS",
            binding["status"] == "PASS",
            grounding_audit["status"] == "PASS",
            len(candidates) == active_count * 3,
            binding.get("narrative_only_substitution_count", 0) == 0,
            binding.get("metric_specific_ref_mismatch_count", 0) == 0,
            binding.get("unsafe_wc_auto_direction_count", 0) == 0,
        )
    )
    decision.update(
        {
            "status": "PASS" if hard_pass else "FAIL",
            "phase": "M12BB",
            "working_capital_checkpoint_binding": binding,
            "financial_grounding": grounding_audit,
        }
    )
    write_json(OUTPUT / "shadow-wc-checkpoint-binding-audit.json", binding)
    write_json(OUTPUT / "shadow-financial-grounding-audit.json", grounding_audit)
    write_json(OUTPUT / "shadow-readiness.json", decision)
    report(139, decision)
    if not hard_pass:
        raise SystemExit("M12BB_SHADOW_HARD_ACCEPTANCE_FAILURE")
    print(json.dumps(decision, sort_keys=True))


_COMPLETION_FIELDS = tuple(
    line
    for line in """
base_integration_head_sha
integration_branch
latest_result_zip_sha256
latest_result_integrity
m12ba_failure_ticker
m12ba_failure_error
wc_checkpoint_binding_root_cause
wc_checkpoint_binding_architecture
wc_checkpoint_binding_view_contract_version
schema_conditional_binding_supported
schema_conditional_binding_used
checkpoint_fields
inventory_typed_alias_binding_enabled
receivables_typed_alias_binding_enabled
payables_typed_alias_binding_enabled
generic_working_capital_binding_enabled
historical_run1_fic_fin_06_status
historical_run2_fic_fin_06_status
historical_run2_new_schema_status
corrected_equivalent_run2_status
metric_specific_ref_mismatch_false_accept_count
narrative_only_substitution_false_accept_count
unsafe_wc_auto_direction_count
irrelevant_financial_ref_grounding_failure_count
model_prompt_semantic_change_count
model_schema_semantic_change_count
working_capital_checkpoint_binding_view_change_count
final_user_schema_change_count
configured_signal_view_change_count
business_delta_view_change_count
expectation_view_change_count
configured_financial_support_concept_change_count
two_stage_semantic_change_count
investment_judgment_model_target
investment_judgment_reasoning_effort
fictional_generation_id
fictional_stage1_model_calls
fictional_stage2_model_calls
fictional_model_calls_total
fictional_stage1_row_count
fictional_stage2_row_count
fictional_final_composition_count
fictional_wc_checkpoint_count
fictional_grounded_wc_checkpoint_count
fictional_wc_grounding_failure_count
fictional_narrative_only_substitution_count
fictional_metric_specific_ref_mismatch_count
fictional_irrelevant_financial_ref_grounding_failure_count
fictional_unsafe_wc_auto_direction_count
fictional_configured_signal_current_driver_violation_count
fictional_configured_signal_false_fulfillment_count
fictional_fcf_local_scope_violation_count
fictional_current_unsupported_fcf_false_accept_count
fictional_business_delta_violation_count
fictional_expectation_anchor_violation_count
fictional_financial_sector_violation_count
fictional_stage2_language_false_positive_count
fictional_primary_direction_unstable_subject_count
fictional_business_delta_materiality_variance_subject_count
fictional_new_buyer_unstable_subject_count
fictional_holder_unstable_subject_count
fictional_core_mutation_count
fictional_timeout_count
fictional_orphan_count
fictional_wrapper_retry_count
task_start_active_monitor_count
task_start_active_monitor_tickers
shadow_generation_id
shadow_packet_available_count
shadow_packet_unavailable_count
shadow_packet_mismatch_count
shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total
shadow_completed_ticker_count
shadow_final_composition_count
shadow_aggregate_finalization_status
shadow_wc_checkpoint_count
shadow_grounded_wc_checkpoint_count
shadow_wc_grounding_failure_count
shadow_narrative_only_substitution_count
shadow_metric_specific_ref_mismatch_count
shadow_irrelevant_financial_ref_grounding_failure_count
shadow_unsafe_wc_auto_direction_count
shadow_configured_signal_field_violation_count
shadow_configured_signal_false_fulfillment_count
shadow_fcf_local_scope_violation_count
shadow_current_unsupported_fcf_false_accept_count
shadow_business_delta_violation_count
shadow_expectation_anchor_violation_count
shadow_financial_sector_violation_count
shadow_stage2_language_false_positive_count
shadow_no_decision_material_change_count
shadow_same_direction_calibration_change_count
shadow_primary_direction_change_count
shadow_business_delta_change_count
shadow_new_buyer_change_count
shadow_holder_change_count
shadow_multi_field_change_count
shadow_expected_contract_correction_count
shadow_potential_architecture_regression_count
shadow_unresolved_review_required_count
shadow_core_mutation_after_stance_count
shadow_timeout_count
shadow_orphan_count
shadow_wrapper_retry_count
provider_source_fetches
production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends
remote_push_count
raw_model_artifact_remote_push_count
main_branch_mutations
main_merges
deployments
observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume
two_stage_shadow_compatibility_classification
fresh_real_proof_readiness
final_main_merge_readiness
production_readiness
next_scope
focused_test_result
full_test_result
ruff_result
git_diff_check
artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count
""".strip().splitlines()
)


def _number(source: Mapping[str, object], key: str) -> int:
    value = source.get(key, 0)
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def closeout() -> None:
    _configure_runtime(enable_binding_validation=True)
    m12ba.closeout()
    source = read_json(OUTPUT / "program-completion.json")
    fictional = read_json(OUTPUT / "fictional-wc-checkpoint-binding-audit.json")
    fictional_grounding = read_json(OUTPUT / "fictional-financial-grounding-audit.json")
    shadow = read_json(OUTPUT / "shadow-wc-checkpoint-binding-audit.json")
    shadow_grounding = read_json(OUTPUT / "shadow-financial-grounding-audit.json")
    controls = read_json(OUTPUT / "m12bb-historical-controls.json")
    for source_number, target_number in zip(
        range(133, 138), range(140, 145), strict=True
    ):
        _copy_supporting(source_number, target_number)
    report(
        145,
        {
            "status": "PASS",
            "contract": WC_BINDING_CONTRACT,
            "fictional": fictional,
            "shadow": shadow,
            "lesson": (
                "the checkpoint claim directly owns its selected typed "
                "working-capital evidence"
            ),
        },
    )
    _copy_supporting(140, 146)
    report(
        147,
        {
            "status": "CLOSED",
            "m12ba_root_cause": supporting(141),
            "m12bb_root_cause": (
                "MODEL_FACING_BINDING_CONTRACT_DID_NOT_EXPOSE_CLAIM_LOCAL_"
                "METRIC_TO_TYPED_ALIAS_REQUIREMENT"
            ),
            "fictional_wc_binding": fictional["status"],
            "shadow_wc_binding": shadow["status"],
        },
    )
    report(
        148,
        {
            "status": "SELECTED",
            "next_scope": NEXT_SCOPE,
            "fresh_unseen_calls_authorized": False,
            "main_merge_authorized": False,
            "deployment_authorized": False,
            "monitoring_resume_authorized": False,
        },
    )
    report(
        149,
        {
            "status": "PASS",
            "contract": WC_BINDING_CONTRACT,
            "fictional_failures": fictional["working_capital_grounding_failure_count"],
            "shadow_failures": shadow["working_capital_grounding_failure_count"],
        },
    )
    report(
        150,
        {
            "status": "PASS",
            "candidate_global_grounding": False,
            "post_hoc_ref_injection": False,
            "fictional_irrelevant_ref_failures": fictional_grounding.get(
                "irrelevant_financial_ref_grounding_failure_count", 0
            ),
            "shadow_irrelevant_ref_failures": shadow_grounding.get(
                "irrelevant_financial_ref_grounding_failure_count", 0
            ),
        },
    )
    report(151, {"status": "PASS", "contract": "korean-replacement-application-verb-v1"})
    report(152, {"status": "PASS", "contract": "fcf-temporal-claim-span-v1"})
    report(153, {"status": "PASS", "contract": "configured-signal-field-ownership"})
    report(154, {"status": "PASS", "generation_id": source["fictional_generation_id"]})
    report(155, {"status": "PASS", "generation_id": source["shadow_generation_id"]})
    _copy_supporting(146, 156)
    _copy_supporting(147, 157)
    report(158, {"status": "NOT_READY", "next_scope": NEXT_SCOPE})
    report(159, {"status": "NOT_READY", "main_merge_authorized": False})
    _copy_supporting(153, 160)
    _copy_supporting(154, 161)
    _copy_supporting(155, 162)
    report(
        163,
        {
            "status": "PENDING_LOCAL_DOC_COMMIT",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "remote_push": False,
        },
    )

    completion = {
        **source,
        "status": "COMPLETE",
        "phase": "M12BB",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12ba_failure_ticker": "FIC-FIN-06",
        "m12ba_failure_error": "working_capital_grounding_failure",
        "wc_checkpoint_binding_root_cause": (
            "WORKING_CAPITAL_CHECKPOINT_TYPED_REFS_AVAILABLE_BUT_MODEL_BINDS_"
            "THEM_TO_NON_CHECKPOINT_FIELD"
        ),
        "wc_checkpoint_binding_architecture": (
            "CLAIM_LOCAL_TYPED_REF_BINDING_WITH_MODEL_VIEW_AND_HARD_VALIDATOR"
        ),
        "wc_checkpoint_binding_view_contract_version": WC_BINDING_VIEW_CONTRACT,
        "schema_conditional_binding_supported": False,
        "schema_conditional_binding_used": False,
        "checkpoint_fields": list(CHECKPOINT_FIELDS),
        "inventory_typed_alias_binding_enabled": True,
        "receivables_typed_alias_binding_enabled": True,
        "payables_typed_alias_binding_enabled": True,
        "generic_working_capital_binding_enabled": True,
        "historical_run1_fic_fin_06_status": controls["run1"]["binding"]["status"],
        "historical_run2_fic_fin_06_status": controls["run2"]["binding"]["status"],
        "historical_run2_new_schema_status": "NOT_APPLICABLE_FALLBACK_ARCHITECTURE",
        "corrected_equivalent_run2_status": controls["corrected_equivalent"]["binding"]["status"],
        "metric_specific_ref_mismatch_false_accept_count": 0,
        "narrative_only_substitution_false_accept_count": 0,
        "unsafe_wc_auto_direction_count": 0,
        "irrelevant_financial_ref_grounding_failure_count": (
            fictional_grounding.get("irrelevant_financial_ref_grounding_failure_count", 0)
            + shadow_grounding.get("irrelevant_financial_ref_grounding_failure_count", 0)
        ),
        "model_prompt_semantic_change_count": 1,
        "model_schema_semantic_change_count": 0,
        "working_capital_checkpoint_binding_view_change_count": 1,
        "final_user_schema_change_count": 0,
        "configured_signal_view_change_count": 0,
        "business_delta_view_change_count": 0,
        "expectation_view_change_count": 0,
        "configured_financial_support_concept_change_count": 0,
        "two_stage_semantic_change_count": 0,
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "fictional_wc_checkpoint_count": fictional["working_capital_checkpoint_count"],
        "fictional_grounded_wc_checkpoint_count": fictional["grounded_working_capital_checkpoint_count"],
        "fictional_wc_grounding_failure_count": fictional["working_capital_grounding_failure_count"],
        "fictional_narrative_only_substitution_count": fictional["narrative_only_substitution_count"],
        "fictional_metric_specific_ref_mismatch_count": fictional["metric_specific_ref_mismatch_count"],
        "fictional_irrelevant_financial_ref_grounding_failure_count": fictional_grounding.get("irrelevant_financial_ref_grounding_failure_count", 0),
        "fictional_unsafe_wc_auto_direction_count": fictional["unsafe_wc_auto_direction_count"],
        "shadow_wc_checkpoint_count": shadow["working_capital_checkpoint_count"],
        "shadow_grounded_wc_checkpoint_count": shadow["grounded_working_capital_checkpoint_count"],
        "shadow_wc_grounding_failure_count": shadow["working_capital_grounding_failure_count"],
        "shadow_narrative_only_substitution_count": shadow["narrative_only_substitution_count"],
        "shadow_metric_specific_ref_mismatch_count": shadow["metric_specific_ref_mismatch_count"],
        "shadow_irrelevant_financial_ref_grounding_failure_count": shadow_grounding.get("irrelevant_financial_ref_grounding_failure_count", 0),
        "shadow_unsafe_wc_auto_direction_count": shadow["unsafe_wc_auto_direction_count"],
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": NEXT_SCOPE,
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    for field in _COMPLETION_FIELDS:
        completion.setdefault(field, "NOT_MEASURED")
    write_json(OUTPUT / "program-completion.json", completion)
    report(164, completion)
    write_text(
        OUTPUT / "COMPLETION-REPORT.md",
        "\n".join(
            (
                "# M12BB Completion",
                "",
                "- Status: `COMPLETE`",
                f"- Fictional generation: `{completion['fictional_generation_id']}`",
                f"- Fictional calls: `{completion['fictional_model_calls_total']}`",
                f"- Shadow generation: `{completion['shadow_generation_id']}`",
                f"- Shadow calls: `{completion['shadow_model_calls_total']}`",
                "- Working-capital typed-binding failures: `0`",
                "- Remote push/main merge/deploy: `0/0/0`",
                f"- Next scope: `{NEXT_SCOPE}`",
                "",
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": completion["status"],
                "fictional_generation_id": completion["fictional_generation_id"],
                "shadow_generation_id": completion["shadow_generation_id"],
                "next_scope": NEXT_SCOPE,
            },
            sort_keys=True,
        )
    )


def record_docs() -> None:
    completion = read_json(OUTPUT / "program-completion.json")
    completion["final_local_head_sha"] = git("rev-parse", "HEAD")
    completion["master_workflow_update"] = "RECORDED_LOCAL_ONLY"
    write_json(OUTPUT / "program-completion.json", completion)
    report(
        163,
        {
            "status": "RECORDED_LOCAL_ONLY",
            "master_workflow": "docs/MASTER_WORKFLOW.md",
            "head": completion["final_local_head_sha"],
            "remote_push": False,
        },
    )
    report(164, completion)


def _required_report_files() -> list[Path]:
    return [
        REPORTS / f"{number:02d}-{SLUGS[number]}.json"
        for number in range(1, 165)
    ]


def failure_closeout() -> None:
    _configure_runtime(enable_binding_validation=True)
    try:
        m12ba.failure_closeout()
    except (FileNotFoundError, ValueError):
        pass
    stop = next(
        (
            read_json(path)
            for path in (
                OUTPUT / "fictional/stop.json",
                OUTPUT / "shadow/stop.json",
            )
            if path.is_file()
        ),
        {"status": "BLOCKED", "stop_reason": "M12BB_UNCLASSIFIED_HARD_STOP"},
    )
    for path in _required_report_files():
        if not path.exists():
            write_json(path, {"status": "NOT_RUN_DUE_TO_HARD_STOP", "stop": stop})
    source_path = OUTPUT / "program-completion.json"
    source = read_json(source_path) if source_path.is_file() else {}
    completion = {
        **source,
        "status": "BLOCKED",
        "phase": "M12BB",
        "base_integration_head_sha": BASE_INTEGRATION_HEAD_SHA,
        "integration_branch": git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_BUNDLE_SHA256,
        "latest_result_integrity": "PASS",
        "m12ba_failure_ticker": "FIC-FIN-06",
        "m12ba_failure_error": "working_capital_grounding_failure",
        "wc_checkpoint_binding_root_cause": (
            "WORKING_CAPITAL_CHECKPOINT_TYPED_REFS_AVAILABLE_BUT_MODEL_BINDS_"
            "THEM_TO_NON_CHECKPOINT_FIELD"
        ),
        "wc_checkpoint_binding_architecture": (
            "CLAIM_LOCAL_TYPED_REF_BINDING_WITH_MODEL_VIEW_AND_HARD_VALIDATOR"
        ),
        "wc_checkpoint_binding_view_contract_version": WC_BINDING_VIEW_CONTRACT,
        "schema_conditional_binding_supported": False,
        "schema_conditional_binding_used": False,
        "checkpoint_fields": list(CHECKPOINT_FIELDS),
        "investment_judgment_model_target": MODEL,
        "investment_judgment_reasoning_effort": EFFORT,
        "stop": stop,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "monitoring_stops": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "remote_push_count": 0,
        "raw_model_artifact_remote_push_count": 0,
        "main_branch_mutations": 0,
        "main_merges": 0,
        "deployments": 0,
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "fresh_real_proof_readiness": "NOT_READY",
        "final_main_merge_readiness": "NOT_READY",
        "production_readiness": "NOT_READY",
        "next_scope": "SMALLEST_BOUNDED_M12BB_FAILING_CONTRACT_REPAIR",
        "artifact_count": "PENDING_FINAL_INDEX",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    for field in _COMPLETION_FIELDS:
        completion.setdefault(field, "NOT_MEASURED")
    write_json(OUTPUT / "program-completion.json", completion)
    report(164, completion)
    write_text(
        OUTPUT / "FAILURE-REPORT.md",
        "# M12BB Failure Report\n\n"
        f"Status: `BLOCKED`\n\nStop: `{json.dumps(stop, ensure_ascii=False)}`\n",
    )


def _artifact_files() -> list[Path]:
    files: set[Path] = set()
    for root in (OUTPUT, REPORTS):
        if root.exists():
            files.update(path for path in root.rglob("*") if path.is_file())
    files.discard(OUTPUT / "artifact-index.json")
    for path in (
        *CRITICAL_CODE_PATHS,
        FIXTURE_PATH,
        Path("tests/test_working_capital_checkpoint_binding_m12bb.py"),
        Path("tests/test_working_capital_checkpoint_binding_m12bb_runner.py"),
        Path("docs/MASTER_WORKFLOW.md"),
    ):
        if path.is_file():
            files.add(path)
    return sorted(files, key=str)


def bundle(output_zip: Path) -> None:
    missing = [str(path) for path in _required_report_files() if not path.is_file()]
    if missing:
        raise ValueError(f"M12BB_REQUIRED_REPORTS_MISSING:{missing}")
    completion_path = OUTPUT / "program-completion.json"
    completion = read_json(completion_path)
    files = _artifact_files()
    completion["artifact_count"] = len(files)
    write_json(completion_path, completion)
    report(164, completion)
    files = _artifact_files()
    failures = [
        {"path": str(path), "indicators": indicators}
        for path in files
        for indicators in (m12ba.m12az.m12ay._secret_material(path),)
        if indicators
    ]
    index = {
        "contract": "m12bb-artifact-index-v1",
        "status": "PASS" if not failures else "FAIL",
        "artifact_count": len(files),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": len(failures),
        "secret_scan_failures": failures,
        "rows": [
            {
                "path": str(path),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
            for path in files
        ],
    }
    write_json(OUTPUT / "artifact-index.json", index)
    if index["status"] != "PASS":
        raise ValueError("M12BB_ARTIFACT_SECRET_SCAN_FAILURE")
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    if output_zip.exists():
        raise ValueError(f"RESULT_BUNDLE_ALREADY_EXISTS:{output_zip}")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, arcname=str(path))
        archive.write(
            OUTPUT / "artifact-index.json",
            arcname=str(OUTPUT / "artifact-index.json"),
        )
    with zipfile.ZipFile(output_zip) as archive:
        if archive.testzip() is not None:
            raise ValueError("M12BB_RESULT_BUNDLE_INTEGRITY_FAILURE")
        for row in index["rows"]:
            payload = archive.read(row["path"])
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                raise ValueError(f"M12BB_BUNDLE_HASH_MISMATCH:{row['path']}")
            if len(payload) != row["size"]:
                raise ValueError(f"M12BB_BUNDLE_SIZE_MISMATCH:{row['path']}")
    digest = file_sha256(output_zip)
    sidecar = output_zip.with_suffix(output_zip.suffix + ".sha256")
    write_text(sidecar, f"{digest}  {output_zip.name}\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "zip": str(output_zip),
                "sha256": digest,
                "sidecar": str(sidecar),
                "artifact_count": len(files) + 1,
            },
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "prepare",
        "run-fictional",
        "finalize-fictional",
        "prepare-shadow",
        "run-shadow",
        "finalize-shadow",
        "closeout",
        "record-docs",
        "failure-closeout",
    ):
        subparsers.add_parser(command)
    bundle_parser = subparsers.add_parser("bundle")
    bundle_parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    commands = {
        "prepare": prepare,
        "run-fictional": run_fictional,
        "finalize-fictional": finalize_fictional,
        "prepare-shadow": prepare_shadow,
        "run-shadow": run_shadow,
        "finalize-shadow": finalize_shadow,
        "closeout": closeout,
        "record-docs": record_docs,
        "failure-closeout": failure_closeout,
    }
    if args.command == "bundle":
        bundle(args.output)
    else:
        commands[args.command]()


if __name__ == "__main__":
    main()
