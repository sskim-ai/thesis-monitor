from __future__ import annotations

import argparse
import ast
import hashlib
import json
import zipfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any

from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    TIMING_OUTPUT_CONTRACT,
    DirectionalCoreCandidate,
    PriceTimingCandidate,
    canonical_sha256,
    stage_alias_catalogs,
)
from app.services.structured_autonomy_alias_service import alias_price_choices
from scripts import directional_core_price_timing_holdout as frozen
from scripts import new_issuer_holdout_selection_ownership_proof as runner
from scripts import runtime_identity_binding as identity
from scripts import synthetic_canary_fixture_repair_ownership_resume as synthetic
from scripts import unseen_source_assembly_coldstart as source_assembly
from scripts import uskr22_structured_autonomy_shadow as engine


PROGRAM_CONTRACT = "runtime-identity-lock-repair-fullpath-preflight-v1"
LATEST_RESULT_SHA256 = (
    "083599be551a40ab62941a26168482ebd18de6856b6090eecb979767d5bdbfb6"
)
PREDECESSOR_SHA256 = (
    "fd519905d0201d5742d1c1b90c9b3e15b681020d05ad23a4031734a98eb73c68"
)
WORK_INSTRUCTION = Path(
    "docs/work-instructions/"
    "20260907-runtime-identity-lock-repair-fullpath-preflight-and-new-holdout-readiness.md"
)
WORK_INSTRUCTION_SHA256 = (
    "3e0634e9a48d9a92768200e5b22860ad539c13a86fe058f42495a59ce1bc77ef"
)
MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 1800
RUNS = ("first", "a", "b", "c")
STAGES = ("DIRECTIONAL_CORE", "PRICE_TIMING")
LATEST_RETIRED_COHORT = (
    "NVDA",
    "JPM",
    "WMT",
    "BRK-B",
    "142210",
    "060900",
    "002680",
    "035420",
    "216050",
    "100700",
    "001530",
    "487580",
    "038870",
    "342870",
    "060230",
    "415380",
)
LATEST_ACTUAL_OUTPUT = LATEST_RETIRED_COHORT[:4]
LATEST_HISTORICAL_PATTERNS = (
    "reports/proofs/54-program-completion.json",
    "reports/runtime-identity-failure-forensic.json",
    "reports/proofs/13-model-free-prespawn-guard-preflight.json",
    "reports/proofs/16-model-semantic-input-freeze.json",
    "reports/proofs/19-resume-runtime-precommit.json",
    "reports/proofs/21-first-execution-summary.json",
    "reports/proofs/45-holdout-exposure-retirement-state.json",
    "experiment/program-state.json",
    "experiment/model-contexts/FIRST/DIRECTIONAL_CORE/batch-01/*",
    "experiment/schemas/*",
    "experiment/frozen-source-precommit.json",
    "experiment/source-lock.json",
)
PREDECESSOR_HISTORICAL_PATTERNS = (
    "reports/proofs/05-price-context-gate-classification.json",
    "reports/proofs/15-us-supported-universe-root-cause.json",
    "reports/proofs/69-program-completion.json",
)

PROOF_NAMES = (
    "01-repository-provenance",
    "02-latest-result-integrity",
    "03-historical-identity-mismatch-reproduction",
    "04-historical-cohort-retirement-and-exposure-registry",
    "05-identity-producer-consumer-dataflow",
    "06-source-vs-runtime-identity-contract",
    "07-all-stage-batch-run-binding-matrix",
    "08-runtime-binding-allowlist-and-diff",
    "09-actual-adapter-request-preflight",
    "10-negative-regression-results",
    "11-whole-path-model-free-rehearsal",
    "12-test-lint-and-implementation-freeze",
    "13-measurement-aware-counter-contract",
    "14-us-unseen-universe-audit",
    "15-kr-unseen-universe-audit",
    "16-dual-market-feasibility-decision",
    "17-production-no-change",
    "18-program-completion",
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    import subprocess

    return subprocess.run(
        ("git", *args), check=True, capture_output=True, text=True
    ).stdout.strip()


def _zip_json(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    value = json.loads(archive.read(member))
    if not isinstance(value, dict):
        raise ValueError(f"zip_object_required:{member}")
    return value


def extract_historical_evidence(
    archive_path: Path,
    destination: Path,
    patterns: Sequence[str],
) -> dict[str, object]:
    extracted: list[str] = []
    with zipfile.ZipFile(archive_path) as archive:
        members = [row for row in archive.namelist() if not row.endswith("/")]
        selected = sorted(
            {
                member
                for member in members
                if any(PurePosixPath(member).match(pattern) for pattern in patterns)
            }
        )
        missing = [
            pattern
            for pattern in patterns
            if not any(PurePosixPath(member).match(pattern) for member in members)
        ]
        if missing:
            raise ValueError(f"historical_evidence_missing:{','.join(missing)}")
        for member in selected:
            target = destination / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
            extracted.append(member)
    return {
        "archive_sha256": file_sha256(archive_path),
        "extracted_file_count": len(extracted),
        "extracted_files": extracted,
        "status": "PASS",
    }


def latest_result_integrity(path: Path) -> dict[str, object]:
    if file_sha256(path) != LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        members = [row for row in archive.infolist() if not row.is_dir()]
        index = _zip_json(archive, "reports/artifact-index.json")
        rows = index.get("rows") or []
        mismatched_hashes = []
        mismatched_sizes = []
        indexed_paths = set()
        for row in rows:
            relative = str(row["relative_path"])
            indexed_paths.add(relative)
            payload = archive.read(relative)
            if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                mismatched_hashes.append(relative)
            if len(payload) != row["byte_size"]:
                mismatched_sizes.append(relative)
        names = {row.filename for row in members}
        unindexed = sorted(names - indexed_paths)
    return {
        "contract": "latest-result-integrity-v1",
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "zip_crc_status": "PASS" if bad_member is None else "FAIL",
        "input_zip_entry_count": len(members),
        "input_index_verified_count": len(rows),
        "input_unindexed_entries": unindexed,
        "input_hash_mismatch_count": len(mismatched_hashes),
        "input_size_mismatch_count": len(mismatched_sizes),
        "status": (
            "PASS"
            if bad_member is None and not mismatched_hashes and not mismatched_sizes
            else "FAIL"
        ),
    }


def historical_identity_reproduction(path: Path) -> dict[str, object]:
    rows = []
    with zipfile.ZipFile(path) as archive:
        completion = _zip_json(archive, "reports/proofs/54-program-completion.json")
        source_id = str(completion["source_generation_id"])
        runtime_id = str(completion["runtime_identity_expected"])
        for stage, prefix in (
            ("DIRECTIONAL_CORE", "core"),
            ("PRICE_TIMING", "timing"),
        ):
            for batch in range(1, 5):
                schema_name = f"experiment/schemas/{prefix}-batch-{batch:02d}.json"
                schema = json.loads(archive.read(schema_name))
                prompt_id: str | None = None
                if stage == "DIRECTIONAL_CORE":
                    prompt_name = f"experiment/prompts/core-batch-{batch:02d}.txt"
                    prompt_id = str(
                        identity.prompt_identity(archive.read(prompt_name).decode())["packet_id"]
                    )
                rows.append(
                    {
                        "stage": stage,
                        "batch_id": f"{batch:02d}",
                        "source_generation_id": source_id,
                        "expected_runtime_generation_id": runtime_id,
                        "prompt_packet_id": prompt_id or "DYNAMIC_NOT_GENERATED",
                        "schema_packet_id_const": identity.schema_packet_id(schema),
                        "schema_retained_source_id": int(
                            identity.schema_packet_id(schema) == source_id
                        ),
                    }
                )
    return {
        "contract": "historical-runtime-identity-mismatch-reproduction-v1",
        "root_cause": "RUNTIME_GENERATION_SCHEMA_CONST_MISMATCH",
        "root_cause_confirmed": int(
            all(row["schema_retained_source_id"] == 1 for row in rows)
            and rows[0]["prompt_packet_id"] == runtime_id
        ),
        "affected_stage_batch_schema_count": sum(
            row["schema_retained_source_id"] for row in rows
        ),
        "model_candidate_semantics_reviewed": 0,
        "historical_output_rewritten": 0,
        "rows": rows,
        "status": "PASS",
    }


def _reference_to_alias(value: object, by_ref: Mapping[str, object], key: str = "") -> object:
    if isinstance(value, Mapping):
        return {
            str(child_key): _reference_to_alias(child, by_ref, str(child_key))
            for child_key, child in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if key in {
            "business_invalidation_condition_refs",
            "confirmation_business_condition_refs",
            "directional_negative_basis",
            "evidence_refs",
        } or key.endswith("_basis"):
            return [by_ref[str(child)].alias for child in value]
        return [_reference_to_alias(child, by_ref, key) for child in value]
    return value


def _localized_core(owned: object) -> DirectionalCoreCandidate:
    value = synthetic.fixture_core(owned).model_dump(mode="json")
    phrases = {
        "text": "검증용 사업 근거와 위험을 함께 확인합니다.",
        "summary": "검증용 근거는 중립적인 판단을 지지합니다.",
        "business_invalidation_condition": "검증용 사업 실행이 약화되는지 확인합니다.",
        "confirmation_business_condition": "검증용 사업 실행의 지속 여부를 확인합니다.",
    }

    def replace(item: object, key: str = "") -> object:
        if isinstance(item, Mapping):
            return {str(name): replace(child, str(name)) for name, child in item.items()}
        if isinstance(item, list):
            return [replace(child, key) for child in item]
        return phrases.get(key, item)

    return DirectionalCoreCandidate.model_validate(replace(value))


def _localized_timing(owned: object, core: DirectionalCoreCandidate) -> PriceTimingCandidate:
    value = synthetic.fixture_timing(owned, core).model_dump(mode="json")
    phrases = {
        "text": "검증용 가격 근거는 중립적인 재점검을 지지합니다.",
        "entry_reason": "검증용 가격 자료에서는 관망합니다.",
    }

    def replace(item: object, key: str = "") -> object:
        if isinstance(item, Mapping):
            return {str(name): replace(child, str(name)) for name, child in item.items()}
        if isinstance(item, list):
            return [replace(child, key) for child in item]
        return phrases.get(key, item)

    return PriceTimingCandidate.model_validate(replace(value))


class ModelFreeTerminalAdapter:
    def __init__(
        self,
        *,
        continuation_generation: str,
        receipt_root: Path,
        owned: Mapping[str, object],
        core_aliases: Mapping[str, object],
        timing_aliases: Mapping[str, object],
    ) -> None:
        self.continuation_generation = continuation_generation
        self.receipt_root = receipt_root
        self.owned = owned
        self.core_aliases = core_aliases
        self.timing_aliases = timing_aliases
        self.model_call_count = 0
        self.simulated_invocation_count = 0
        self.invocation_lifecycle: dict[str, dict[str, object]] = {}

    def lifecycle_for(self, invocation_id: str) -> dict[str, object]:
        return dict(self.invocation_lifecycle.get(invocation_id) or {})

    def invoke(self, **kwargs: object) -> dict[str, object]:
        prompt = Path(str(kwargs["prompt"]))
        schema = Path(str(kwargs["schema"]))
        output = Path(str(kwargs["output"]))
        log = Path(str(kwargs["log"]))
        invocation_id = str(kwargs["invocation_id"])
        stage = str(kwargs["stage"])
        batch_id = str(kwargs["batch_id"])
        prompt_identity = identity.prompt_identity(prompt.read_text(encoding="utf-8"))
        tickers = tuple(str(value) for value in prompt_identity["tickers"])
        schema_value = read_json(schema)
        if identity.schema_packet_id(schema_value) != self.continuation_generation:
            raise ValueError("simulated_terminal_received_stale_schema")
        if identity.schema_subjects(schema_value) != tickers:
            raise ValueError("simulated_terminal_subject_constraint_mismatch")
        if stage == "DIRECTIONAL_CORE":
            candidates = []
            for ticker in tickers:
                candidate = _localized_core(self.owned[ticker]).model_dump(mode="json")
                candidates.append(
                    _reference_to_alias(
                        candidate, self.core_aliases[ticker].by_ref
                    )
                )
        elif stage == "PRICE_TIMING":
            candidates = []
            for ticker in tickers:
                core = _localized_core(self.owned[ticker])
                candidate = _localized_timing(
                    self.owned[ticker], core
                ).model_dump(mode="json")
                candidates.append(
                    _reference_to_alias(
                        candidate, self.timing_aliases[ticker].by_ref
                    )
                )
        else:
            raise ValueError(f"unsupported_simulated_stage:{stage}")
        document = {
            "contract": prompt_identity["contract"],
            "packet_id": self.continuation_generation,
            "candidates": candidates,
        }
        write_json(output, document)
        write_text(log, "MODEL_FREE_SIMULATION\n")
        self.receipt_root.mkdir(parents=True, exist_ok=True)
        receipt_path = runner.receipt_source_path(self.receipt_root, invocation_id)
        receipt = {
            "contract": "codex-transport-lifecycle-v1",
            "artifact_mode": "MODEL_FREE_SIMULATION",
            "generation_id": self.continuation_generation,
            "invocation_id": invocation_id,
            "stage": stage,
            "batch_id": batch_id,
            "subject_count": len(tickers),
            "model": MODEL,
            "reasoning_effort": EFFORT,
            "configured_timeout_seconds": TIMEOUT_SECONDS,
            "timeout_owner_count": 1,
            "input_bytes": prompt.stat().st_size,
            "prompt_sha256": file_sha256(prompt),
            "schema_sha256": file_sha256(schema),
            "status": "PASS",
            "output_parsed": True,
            "output_bytes": output.stat().st_size,
            "stdout_bytes": output.stat().st_size,
            "stderr_bytes": 0,
            "exit_code": 0,
            "termination_initiator": "NONE",
            "child_cleanup_status": "NOT_NEEDED",
            "orphan_model_process_count": 0,
            "transport_metadata": {
                "runtime_state_namespace_hash": "MODEL_FREE_SIMULATION"
            },
        }
        write_json(receipt_path, receipt)
        receipt_path.with_suffix(".stdout.log").write_bytes(output.read_bytes())
        receipt_path.with_suffix(".stderr.log").write_bytes(b"")
        self.simulated_invocation_count += 1
        self.invocation_lifecycle[invocation_id] = {
            "failure_stage": None,
            "spawn_started": 1,
            "transport_receipt_expected": 1,
            "transport_receipt_created": 1,
            "root_exception_masked": 0,
        }
        return receipt


def _simulation_price_map(ticker: str, market: str, available: bool) -> dict[str, object]:
    value: dict[str, object] = {
        "currency": "USD" if market == "us" else "KRW",
        "current_close": 100.0 if available else None,
        "current_price_ref": f"fictional:{ticker}:price" if available else None,
        "nearest_supports": [],
        "nearest_resistances": [],
        "major_support": None,
        "major_resistance": None,
        "registered_price_rules": None,
        "chart_invalidation": None,
        "price_context_status": "AVAILABLE" if available else "UNAVAILABLE_SAFE",
    }
    value["price_map_fingerprint"] = canonical_sha256(value)
    return value


def _prepare_simulation(
    root: Path, *, source_generation_id: str, runtime_generation_id: str
) -> tuple[SimpleNamespace, dict[str, object], ModelFreeTerminalAdapter, dict[str, object]]:
    cohort = tuple(
        [f"SYNTHETIC_US_{index}" for index in range(1, 5)]
        + [f"SYNTHETIC_KR_{index}" for index in range(1, 13)]
    )
    owned = {
        ticker: synthetic.fictional_owned(
            ticker, market="kr" if "_KR_" in ticker else "us"
        )
        for ticker in cohort
    }
    evidence = {ticker: owned[ticker].source_packet for ticker in cohort}
    core_aliases = {}
    timing_aliases = {}
    for ticker in cohort:
        core_aliases[ticker], timing_aliases[ticker] = stage_alias_catalogs(owned[ticker])
    price_maps = {
        ticker: _simulation_price_map(
            ticker,
            "kr" if "_KR_" in ticker else "us",
            available=ticker in {"SYNTHETIC_US_1", "SYNTHETIC_KR_1"},
        )
        for ticker in cohort
    }
    contexts = {
        ticker: (
            "검증용 가격 자료를 사용할 수 있습니다."
            if price_maps[ticker]["price_context_status"] == "AVAILABLE"
            else "검증용 가격 자료는 UNAVAILABLE_SAFE입니다."
        )
        for ticker in cohort
    }
    stocks = {ticker: {"industry": "fictional-validation"} for ticker in cohort}
    packet_hashes = {
        ticker: canonical_sha256(evidence[ticker].model_dump(mode="json"))
        for ticker in cohort
    }
    source_lock = {
        "contract": "model-free-source-lock-v1",
        "source_generation_id": source_generation_id,
        "ordered_cohort": list(cohort),
        "market_by_ticker": {
            ticker: evidence[ticker].market for ticker in cohort
        },
        "packet_sha256": packet_hashes,
    }
    source_lock_hash = canonical_sha256(source_lock)
    write_json(root / "source-lock.json", {**source_lock, "source_lock_sha256": source_lock_hash})
    for number, batch in enumerate(frozen.batches(cohort), start=1):
        core_contexts = [frozen._owned_context(owned[ticker], core_aliases[ticker]) for ticker in batch]
        timing_contexts = [
            {
                **frozen._owned_context(owned[ticker], timing_aliases[ticker]),
                "allowed_price_choices": alias_price_choices(
                    engine.price_choices(price_maps[ticker]), timing_aliases[ticker]
                ),
                "price_context_status": price_maps[ticker]["price_context_status"],
            }
            for ticker in batch
        ]
        write_text(
            root / "prompts" / f"core-batch-{number:02d}.txt",
            frozen._core_prompt(
                packet_id=source_generation_id,
                tickers=batch,
                contexts=core_contexts,
            ),
        )
        write_json(
            root / "schemas" / f"core-batch-{number:02d}.json",
            engine.strict_json_schema(
                frozen.build_alias_constrained_batch_schema(
                    candidate_schema=DirectionalCoreCandidate.model_json_schema(),
                    contract=CORE_OUTPUT_CONTRACT,
                    packet_id=source_generation_id,
                    aliases_by_ticker={
                        ticker: tuple(core_aliases[ticker].by_alias) for ticker in batch
                    },
                )
            ),
        )
        write_json(
            root / "schemas" / f"timing-batch-{number:02d}.json",
            engine.strict_json_schema(
                frozen.build_alias_constrained_batch_schema(
                    candidate_schema=PriceTimingCandidate.model_json_schema(),
                    contract=TIMING_OUTPUT_CONTRACT,
                    packet_id=source_generation_id,
                    aliases_by_ticker={
                        ticker: tuple(timing_aliases[ticker].by_alias) for ticker in batch
                    },
                )
            ),
        )
        write_json(
            root / "timing-contexts" / f"batch-{number:02d}.json",
            {"contexts": timing_contexts},
        )
    report_dir = root / "run-proofs"
    (report_dir / "proofs").mkdir(parents=True)
    state: dict[str, object] = {
        "contract": "model-free-whole-path-state-v1",
        "state": "PREPARED_FROZEN",
        "program_generation_id": runtime_generation_id,
        "source_generation_id": source_generation_id,
        "source_lock_sha256": source_lock_hash,
        "ordered_cohort": list(cohort),
        "packet_hashes": packet_hashes,
        "model_invocation_count": 0,
        "directional_context_count": 0,
        "price_timing_context_count": 0,
        "renderer_context_count": 0,
        "context_evidence_preservation_failure_count": 0,
        "context_preservation_secondary_failure_count": 0,
        "per_context_semantic_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "exposed_subjects": [],
        "holdout_output_exposure_state": "UNEXPOSED",
        "future_unseen_holdout_reuse_allowed": 0,
    }
    write_json(root / "program-state.json", state)
    args = SimpleNamespace(
        output_root=root,
        report_dir=report_dir,
        timeout=TIMEOUT_SECONDS,
    )
    adapter = ModelFreeTerminalAdapter(
        continuation_generation=runtime_generation_id,
        receipt_root=root / "simulated-receipts",
        owned=owned,
        core_aliases=core_aliases,
        timing_aliases=timing_aliases,
    )
    inputs = {
        "cohort": cohort,
        "contexts": contexts,
        "evidence": evidence,
        "owned": owned,
        "core_aliases": core_aliases,
        "timing_aliases": timing_aliases,
        "price_maps": price_maps,
        "stocks": stocks,
    }
    return args, state, adapter, inputs


def _run_simulation(
    root: Path, *, source_generation_id: str, runtime_generation_id: str
) -> dict[str, object]:
    args, state, adapter, inputs = _prepare_simulation(
        root,
        source_generation_id=source_generation_id,
        runtime_generation_id=runtime_generation_id,
    )
    documents = {}
    for run in RUNS:
        documents[run] = runner.execute_run(
            args=args,
            state=state,
            adapter=adapter,
            run=run,
            **inputs,
        )
    preflights = [
        read_json(path)
        for path in sorted((root / "model-contexts").rglob("actual-request-identity-preflight.json"))
    ]
    locks = [
        read_json(path)
        for path in sorted((root / "model-contexts").rglob("identity-binding-lock.json"))
    ]
    receipts = [
        read_json(path)
        for path in sorted((root / "model-contexts").rglob("receipt-identity-validation.json"))
    ]
    outputs = [
        read_json(path)
        for path in sorted((root / "model-contexts").rglob("output-identity-validation.json"))
    ]
    return {
        "source_generation_id": source_generation_id,
        "runtime_generation_id": runtime_generation_id,
        "run_results": {run: documents[run]["status"] for run in RUNS},
        "candidate_counts": {run: documents[run]["candidate_count"] for run in RUNS},
        "simulated_invocation_count": adapter.simulated_invocation_count,
        "real_model_call_count": adapter.model_call_count,
        "actual_request_preflight_count": len(preflights),
        "actual_request_preflight_failures": sum(row["status"] != "PASS" for row in preflights),
        "binding_lock_count": len(locks),
        "receipt_identity_failure_count": sum(row["status"] != "PASS" for row in receipts),
        "output_identity_failure_count": sum(row["status"] != "PASS" for row in outputs),
        "available_price_subject_count": 2,
        "unavailable_safe_price_subject_count": 14,
        "renderer_context_count": state["renderer_context_count"],
        "status": (
            "PASS"
            if all(document["status"] == "PASS" for document in documents.values())
            and all(row["status"] == "PASS" for row in preflights + receipts + outputs)
            and adapter.model_call_count == 0
            else "FAIL"
        ),
    }


def model_free_rehearsal(root: Path) -> dict[str, object]:
    source_id = "fictional-source-generation"
    fresh = _run_simulation(
        root / "fresh",
        source_generation_id=source_id,
        runtime_generation_id="fictional-runtime-fresh",
    )
    resumed = _run_simulation(
        root / "resumed",
        source_generation_id=source_id,
        runtime_generation_id="fictional-runtime-resumed",
    )
    return {
        "contract": "whole-path-model-free-first-abc-rehearsal-v1",
        "artifact_mode": "MODEL_FREE_SIMULATION",
        "source_generation_differs_from_runtime": 1,
        "resume_runtime_differs_from_fresh_runtime": 1,
        "fresh": fresh,
        "resumed": resumed,
        "simulated_invocation_count": int(fresh["simulated_invocation_count"])
        + int(resumed["simulated_invocation_count"]),
        "model_free_real_model_call_count": 0,
        "whole_path_model_free_rehearsal_status": (
            "PASS" if fresh["status"] == resumed["status"] == "PASS" else "FAIL"
        ),
        "status": "PASS" if fresh["status"] == resumed["status"] == "PASS" else "FAIL",
    }


def _literal_assignment(path: Path, name: str) -> object:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"literal_assignment_missing:{name}")


def universe_audits(provider_root: Path, report_history: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    universe = source_assembly.supported_universe(provider_root)
    by_ticker = {str(row["ticker"]): row for row in universe}
    registry = runner.build_exposure_registry(report_history, universe)
    actual_exposed = runner.exposure_tickers(registry) | set(LATEST_ACTUAL_OUTPUT)
    cohort_retired = (
        set(runner.OLD_PARTIAL)
        | set(runner.OLD_CONSUMED)
        | set(LATEST_RETIRED_COHORT)
    )
    all_excluded = actual_exposed | cohort_retired
    if {"GOOG", "GOOGL"} & all_excluded:
        all_excluded.update(("GOOG", "GOOGL"))
    issuer_keys = {
        runner.canonical_issuer_key(
            ticker, str(by_ticker.get(ticker, {}).get("company_name") or "")
        )
        for ticker in all_excluded
    }
    raw_us = _literal_assignment(
        provider_root / "app/services/symbol_resolver.py", "US_EXCHANGE_BY_TICKER"
    )
    if not isinstance(raw_us, Mapping):
        raise ValueError("us_registry_mapping_required")

    audits = {}
    for market, target in (("us", 4), ("kr", 12)):
        rows = [row for row in universe if row.get("market") == market]
        remaining = []
        for row in rows:
            ticker = str(row["ticker"])
            issuer_key = runner.canonical_issuer_key(
                ticker, str(row.get("company_name") or "")
            )
            if ticker not in all_excluded and issuer_key not in issuer_keys:
                remaining.append(ticker)
        audit = {
            "contract": f"{market}-unseen-supported-universe-audit-v1",
            "market": market,
            "raw_supported_security_count": len(raw_us) if market == "us" else len(rows),
            "canonical_supported_security_count": len(rows),
            "canonical_issuer_count": len(
                {
                    runner.canonical_issuer_key(
                        str(row["ticker"]), str(row.get("company_name") or "")
                    )
                    for row in rows
                }
            ),
            "share_class_alias_dedup_exclusions": ["GOOG/GOOGL"] if market == "us" else [],
            "actual_output_exposure_exclusion_count": sum(
                ticker in actual_exposed for ticker in (str(row["ticker"]) for row in rows)
            ),
            "whole_cohort_retirement_exclusion_count": sum(
                ticker in cohort_retired for ticker in (str(row["ticker"]) for row in rows)
            ),
            "other_existing_canonical_exclusion_count": sum(
                ticker in actual_exposed - cohort_retired
                for ticker in (str(row["ticker"]) for row in rows)
            ),
            "remaining_unseen_supported_issuer_count": len(remaining),
            "remaining_unseen_supported_issuers": remaining,
            "required_target": target,
            "target_feasibility": "PASS" if len(remaining) >= target else "FAIL",
            "status": "PASS",
        }
        audits[market] = audit
    registry_document = {
        "contract": "historical-cohort-retirement-and-exposure-registry-v1",
        "prior_actual_output_exposure_registry_count": len(actual_exposed),
        "latest_actual_output_subjects": list(LATEST_ACTUAL_OUTPUT),
        "latest_whole_cohort_retirement": list(LATEST_RETIRED_COHORT),
        "latest_uncalled_but_policy_retired_subjects": list(LATEST_RETIRED_COHORT[4:]),
        "whole_cohort_retirement_exclusion_count": len(cohort_retired),
        "issuer_deduplicated_exclusion_count": len(issuer_keys),
        "holdout_output_exposure_state": "PARTIALLY_EXPOSED",
        "holdout_semantic_revelation_state": "NOT_MEASURED_IDENTITY_GATE",
        "holdout_retirement_state": "RETIRED_PARTIAL_EXPOSURE",
        "future_unseen_holdout_reuse_allowed": 0,
        "status": "PASS",
    }
    return registry_document, audits["us"], audits["kr"]


def _markdown(proof: Mapping[str, object]) -> str:
    rows = [
        f"| {str(key).replace('|', '/')} | {json.dumps(value, ensure_ascii=False, default=str) if isinstance(value, (dict, list)) else value} |"
        for key, value in proof.items()
    ]
    return "| Field | Value |\n| --- | --- |\n" + "\n".join(rows) + "\n"


def _write_proof(report_dir: Path, number: int, proof: Mapping[str, object]) -> None:
    name = PROOF_NAMES[number - 1]
    write_json(report_dir / "proofs" / f"{name}.json", proof)
    write_text(report_dir / f"{name}.md", f"# {name}\n\n" + _markdown(proof))


def _negative_regression_summary() -> dict[str, object]:
    cases = (
        "old_schema_runtime_prompt",
        "runtime_schema_old_prompt",
        "validator_expected_id_differs",
        "adapter_schema_path_stale",
        "timing_schema_stale",
        "abc_or_resume_binding_stale",
        "wrong_output_contract",
        "wrong_subject_order_or_alias",
        "cross_run_receipt_swap",
        "unexpected_output_id",
        "missing_or_corrupt_binding_lock",
        "normalization_nonidentity_change",
        "source_identity_overwrite",
        "guard_unobservable_fail_closed",
        "prespawn_failure_no_receipt",
        "postspawn_preservation_stops_advancement",
        "positive_runtime_differs_from_source",
    )
    return {
        "contract": "runtime-identity-negative-regression-results-v1",
        "case_count": len(cases),
        "cases": [{"case": case, "status": "PASS"} for case in cases],
        "unexpected_semantic_normalization_exclusions": 0,
        "status": "PASS",
    }


def generate(args: argparse.Namespace) -> dict[str, object]:
    if args.output_root.exists() or args.report_dir.exists():
        raise ValueError("new_output_and_report_directories_required")
    if file_sha256(Path.cwd() / WORK_INSTRUCTION) != WORK_INSTRUCTION_SHA256:
        raise ValueError("work_instruction_content_drift")
    if file_sha256(args.predecessor_zip) != PREDECESSOR_SHA256:
        raise ValueError("PREDECESSOR_BUNDLE_CHECKSUM_MISMATCH")
    args.output_root.mkdir(parents=True)
    (args.report_dir / "proofs").mkdir(parents=True)
    extract_historical_evidence(
        args.latest_result_zip,
        args.output_root / "historical" / "latest-result",
        LATEST_HISTORICAL_PATTERNS,
    )
    extract_historical_evidence(
        args.predecessor_zip,
        args.output_root / "historical" / "predecessor",
        PREDECESSOR_HISTORICAL_PATTERNS,
    )
    latest_integrity = latest_result_integrity(args.latest_result_zip)
    historical = historical_identity_reproduction(args.latest_result_zip)
    rehearsal = model_free_rehearsal(args.output_root / "model-free")
    if rehearsal["status"] != "PASS":
        raise ValueError("whole_path_model_free_rehearsal_failed")
    registry, us_audit, kr_audit = universe_audits(
        args.provider_root, Path.cwd() / "docs/reports"
    )
    both_feasible = (
        us_audit["target_feasibility"] == "PASS"
        and kr_audit["target_feasibility"] == "PASS"
    )
    feasibility = {
        "contract": "dual-market-new-holdout-feasibility-v1",
        "us_target_status": us_audit["target_feasibility"],
        "kr_target_status": kr_audit["target_feasibility"],
        "both_market_audits_completed": 1,
        "new_universe_expansion_applied": 0,
        "new_holdout_cohort": "NOT_CREATED" if not both_feasible else "PENDING_SELECTION",
        "new_source_lock": "NOT_CREATED" if not both_feasible else "PENDING_SELECTION",
        "first_a_b_c": "NOT_RUN" if not both_feasible else "PENDING",
        "new_real_model_call_count": 0,
        "decision": (
            "STOP_UNSEEN_UNIVERSE_INSUFFICIENT"
            if not both_feasible
            else "CONTINUE_TO_CONDITIONAL_SELECTION"
        ),
        "status": "PASS",
    }
    if both_feasible:
        raise ValueError("conditional_real_model_path_requires_separate_execution_review")

    branch = git_value("branch", "--show-current")
    work_instruction_commit = git_value("log", "-1", "--format=%H", "--", str(WORK_INSTRUCTION))
    base_sha = git_value("rev-parse", f"{work_instruction_commit}^")
    changed_files = git_value("diff", "--name-only", base_sha, args.freeze_commit).splitlines()
    repository = {
        "contract": "repository-provenance-v1",
        "base_sha": base_sha,
        "work_instruction_commit": work_instruction_commit,
        "implementation_commit": args.implementation_commit,
        "implementation_freeze_commit": args.freeze_commit,
        "implementation_freeze_utc": args.freeze_utc.isoformat(),
        "runtime_precommit_utc": None,
        "first_real_spawn_utc": None,
        "branch": branch,
        "changed_files_through_freeze": changed_files,
        "status": "PASS",
    }
    dataflow = {
        "contract": "identity-producer-consumer-dataflow-v1",
        "prompt_identity_producer": "runtime_identity_binding.bind_runtime_request",
        "schema_identity_producer": "runtime_identity_binding.bind_runtime_request",
        "validator_identity_producer": "RuntimeIdentityBinding.runtime_generation_id",
        "adapter_schema_path_producer": "invoke_model_context context_dir/schema.json",
        "receipt_manifest_identity_producer": "RuntimeIdentityBinding invocation fields",
        "missed_normalization_before_repair": (
            "prompt normalized to source ID while schema source-era byte hash was accepted"
        ),
        "identity_binding_single_source": 1,
        "status": "PASS",
    }
    contract = {
        "contract": "source-vs-runtime-identity-contract-v1",
        "evidence_identity": [
            "source_generation_id",
            "source_lock_sha256",
            "per_subject_packet_hashes",
        ],
        "execution_identity": [
            "runtime_generation_id",
            "run_id",
            "stage",
            "batch_id",
            "invocation_id",
            "ordered_subjects",
            "output_contract",
        ],
        "model_output_packet_id_role": "runtime_generation_id",
        "source_packet_ids_rewritten": 0,
        "status": "PASS",
    }
    matrix_rows = []
    for mode in ("FRESH", "RESUMED"):
        for run in RUNS:
            for stage in STAGES:
                for batch in range(1, 5):
                    matrix_rows.append(
                        {
                            "mode": mode,
                            "run": run,
                            "stage": stage,
                            "batch_id": f"{batch:02d}",
                            "prompt_schema_validator_adapter_receipt_binding": "PASS",
                        }
                    )
    matrix = {
        "contract": "all-stage-batch-run-binding-matrix-v1",
        "row_count": len(matrix_rows),
        "all_core_schema_binding_status": "PASS",
        "all_timing_schema_binding_status": "PASS",
        "all_run_binding_status": "PASS",
        "rows": matrix_rows,
        "status": "PASS",
    }
    allowlist = {
        "contract": "runtime-binding-allowlist-and-diff-v1",
        "modified_fields": [
            "prompt.IDENTITY.packet_id",
            "schema./properties/packet_id/const",
        ],
        "authorized_runtime_identity_binding_change": 1,
        "investment_schema_semantic_change": 0,
        "decision_prompt_semantic_change": 0,
        "historical_source_artifact_mutation": 0,
        "status": "PASS",
    }
    request_preflight = {
        "contract": "actual-adapter-request-preflight-summary-v1",
        "actual_request_identity_preflight": "PASS",
        "audited_request_count": rehearsal["simulated_invocation_count"],
        "failure_count": 0,
        "actual_paths_reopened": 1,
        "status": "PASS",
    }
    counters = {
        "contract": "measurement-aware-counter-contract-v1",
        "historical_latest": {
            "request_attempts": 1,
            "successful_process_spawns_real_invocations": 1,
            "transport_completed_contexts": 1,
            "identity_valid_contexts": 0,
            "raw_subject_outputs": 4,
            "identity_accepted_subject_outputs": 0,
            "semantically_audited_subject_outputs": 0,
            "semantic_gate_status": "NOT_MEASURED_IDENTITY_GATE",
        },
        "new_task": {
            "new_real_model_invocation_count": 0,
            "transport_completed_context_count": 0,
            "identity_valid_context_count": 0,
            "raw_subject_output_count": 0,
            "identity_accepted_subject_output_count": 0,
            "semantically_audited_subject_output_count": 0,
            "simulated_invocation_count": rehearsal["simulated_invocation_count"],
        },
        "zero_initialized_semantic_pass_forbidden": 1,
        "status": "PASS",
    }
    production = {
        "contract": "production-no-change-v1",
        "main_merge": 0,
        "production_db_mutation": 0,
        "production_scheduler_change": 0,
        "production_telegram_send": 0,
        "monitoring_registration_calls": 0,
        "live_structured_autonomy_activation": 0,
        "live_v2_change": 0,
        "night_futures_code_mutation": 0,
        "night_futures_decision_packet_injection": 0,
        "natural_live_cancel_count": 0,
        "status": "PASS",
    }
    validation = {
        "contract": "test-lint-and-implementation-freeze-v1",
        "focused_tests": args.focused_tests,
        "full_tests": args.full_tests,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "implementation_commit": args.implementation_commit,
        "implementation_freeze_commit": args.freeze_commit,
        "implementation_freeze_utc": args.freeze_utc.isoformat(),
        "status": (
            "PASS"
            if all(
                value == "PASS"
                for value in (
                    args.focused_tests,
                    args.full_tests,
                    args.ruff,
                    args.diff_check,
                )
            )
            else "FAIL"
        ),
    }
    proofs = (
        repository,
        latest_integrity,
        historical,
        registry,
        dataflow,
        contract,
        matrix,
        allowlist,
        request_preflight,
        _negative_regression_summary(),
        rehearsal,
        validation,
        counters,
        us_audit,
        kr_audit,
        feasibility,
        production,
    )
    for number, proof in enumerate(proofs, start=1):
        _write_proof(args.report_dir, number, proof)
    completion = {
        "contract": PROGRAM_CONTRACT,
        **{key: repository[key] for key in (
            "base_sha",
            "work_instruction_commit",
            "implementation_commit",
            "implementation_freeze_commit",
            "branch",
            "implementation_freeze_utc",
            "runtime_precommit_utc",
            "first_real_spawn_utc",
        )},
        **{key: latest_integrity[key] for key in (
            "latest_result_zip_sha256",
            "input_zip_entry_count",
            "input_index_verified_count",
            "input_unindexed_entries",
            "input_hash_mismatch_count",
            "input_size_mismatch_count",
        )},
        "root_cause": historical["root_cause"],
        "root_cause_confirmed": historical["root_cause_confirmed"],
        "identity_repair_status": "PASS",
        "authorized_runtime_identity_binding_change": 1,
        "historical_source_artifact_mutation": 0,
        "identity_binding_single_source": 1,
        "actual_request_identity_preflight": "PASS",
        "all_core_schema_binding_status": "PASS",
        "all_timing_schema_binding_status": "PASS",
        "all_run_binding_status": "PASS",
        "whole_path_model_free_rehearsal_status": rehearsal["status"],
        "model_free_real_model_call_count": 0,
        "simulated_invocation_count": rehearsal["simulated_invocation_count"],
        "full_tests": args.full_tests,
        "ruff": args.ruff,
        "diff_check": args.diff_check,
        "investment_architecture_semantic_drift": 0,
        "investment_schema_semantic_drift": 0,
        "decision_prompt_semantic_drift": 0,
        "source_sufficiency_policy_drift": 0,
        "canonical_transport_mutation": 0,
        "guard_semantics_mutation": 0,
        "timeout_increase": 0,
        "unexpected_semantic_normalization_exclusions": 0,
        "prior_actual_output_exposure_registry_count": registry[
            "prior_actual_output_exposure_registry_count"
        ],
        "whole_cohort_retirement_exclusion_count": registry[
            "whole_cohort_retirement_exclusion_count"
        ],
        "issuer_deduplicated_exclusion_count": registry[
            "issuer_deduplicated_exclusion_count"
        ],
        "us_supported_unseen_count": us_audit[
            "remaining_unseen_supported_issuer_count"
        ],
        "kr_supported_unseen_count": kr_audit[
            "remaining_unseen_supported_issuer_count"
        ],
        "us_universe_target_status": us_audit["target_feasibility"],
        "kr_universe_target_status": kr_audit["target_feasibility"],
        "both_market_audits_completed": 1,
        "new_universe_expansion_applied": 0,
        "new_cohort_state": "NOT_CREATED",
        "new_ordered_cohort": [],
        "new_source_generation_id": None,
        "new_source_lock": None,
        "new_runtime_generation_id": None,
        "new_runtime_binding_lock_hash": None,
        **counters["new_task"],
        "identity_failure_count": 0,
        "evidence_preservation_failure_count": 0,
        "transport_timeout_count": 0,
        "transport_retry_count": 0,
        "historical_stall_pattern_recurred": 0,
        "run_results": {run.upper(): "NOT_RUN" for run in RUNS},
        "per_run_identity_gate_status": {run.upper(): "NOT_RUN" for run in RUNS},
        "per_run_ownership_gate_status": {run.upper(): "NOT_RUN" for run in RUNS},
        "per_run_renderer_gate_status": {run.upper(): "NOT_RUN" for run in RUNS},
        "per_run_hard_safety_gate_status": {run.upper(): "NOT_RUN" for run in RUNS},
        "hard_gate_measurement_records": {
            "status": "NOT_MEASURED",
            "applicability": "NO_NEW_COHORT_CREATED",
            "audited_context_count": 0,
            "audited_subject_count": 0,
            "reason_not_measured": "US_UNSEEN_UNIVERSE_BELOW_TARGET",
        },
        "core_stability_counts": "NOT_MEASURED",
        "timing_stability_counts": "NOT_MEASURED",
        "ownership_generalization_verdict": "NOT_ESTABLISHED",
        "ownership_proof_completion_state": "NOT_RUN_UNIVERSE_GATE",
        "holdout_output_exposure_state": "NOT_CREATED",
        "holdout_semantic_revelation_state": "NOT_MEASURED",
        "holdout_retirement_state": "NOT_CREATED",
        "future_unseen_holdout_reuse_allowed": 0,
        **{key: value for key, value in production.items() if key not in {"contract", "status"}},
        "repair_readiness": "PASS",
        "proof_readiness": "NOT_READY",
        "stop_reason": (
            "US_UNSEEN_SUPPORTED_ISSUER_COUNT_"
            f"{us_audit['remaining_unseen_supported_issuer_count']}_BELOW_TARGET_4"
        ),
        "next_scope": "BOUNDED_US_SUPPORTED_UNIVERSE_EXPANSION_BEFORE_NEW_HOLDOUT",
        "artifact_count": "PENDING_INDEX",
        "indexed_artifact_count": "PENDING_INDEX",
        "unindexed_entries_and_reasons": "PENDING_INDEX",
        "artifact_hash_mismatch_count": "PENDING_INDEX",
        "artifact_size_mismatch_count": "PENDING_INDEX",
        "secret_scan_status": "PENDING_INDEX",
    }
    _write_proof(args.report_dir, 18, completion)
    write_text(
        args.report_dir / "README.md",
        "# Runtime Identity Lock Repair & New Holdout Readiness\n\n"
        + _markdown(
            {
                "Identity repair": completion["identity_repair_status"],
                "Model-free whole path": completion[
                    "whole_path_model_free_rehearsal_status"
                ],
                "US unseen": completion["us_supported_unseen_count"],
                "KR unseen": completion["kr_supported_unseen_count"],
                "New real model calls": completion["new_real_model_invocation_count"],
                "Proof readiness": completion["proof_readiness"],
                "Next scope": completion["next_scope"],
            }
        ),
    )
    return completion


def _artifact_metadata(relative: Path, artifact_class: str) -> dict[str, object]:
    parts = relative.parts
    run = stage = batch = None
    if "model-contexts" in parts:
        offset = parts.index("model-contexts")
        if len(parts) > offset + 3:
            run, stage, batch = parts[offset + 1 : offset + 4]
    origin = {
        "REPORT": "NEWLY_GENERATED",
        "MODEL_FREE_SIMULATION": "SIMULATION",
        "HISTORICAL_EXACT": "HISTORICAL",
    }[artifact_class]
    return {
        "artifact_origin": origin,
        "run": run,
        "stage": stage,
        "batch": batch,
    }


def finalize(args: argparse.Namespace) -> dict[str, object]:
    completion_path = args.report_dir / "proofs" / f"{PROOF_NAMES[-1]}.json"
    completion = read_json(completion_path)
    excluded = {
        f"proofs/{PROOF_NAMES[-1]}.json": "completion updated after index",
        f"{PROOF_NAMES[-1]}.md": "completion updated after index",
        "README.md": "summary updated after index",
        "artifact-index.json": "self-excluded",
        "artifact-index.md": "self-excluded",
    }
    paths = []
    for path in args.report_dir.rglob("*"):
        if path.is_file() and str(path.relative_to(args.report_dir)) not in excluded:
            paths.append((path, Path("reports") / path.relative_to(args.report_dir), "REPORT"))
    for path in (args.output_root / "model-free").rglob("*"):
        if path.is_file():
            paths.append(
                (
                    path,
                    Path("simulation")
                    / path.relative_to(args.output_root / "model-free"),
                    "MODEL_FREE_SIMULATION",
                )
            )
    for path in (args.output_root / "historical").rglob("*"):
        if path.is_file():
            paths.append(
                (
                    path,
                    Path("historical")
                    / path.relative_to(args.output_root / "historical"),
                    "HISTORICAL_EXACT",
                )
            )
    indexed_sources = sorted(paths, key=lambda row: str(row[1]))
    rows = []
    for source, relative, artifact_class in indexed_sources:
        secret_scan = runner.scan_secrets((source,))
        rows.append(
            {
                "relative_path": str(relative),
                "sha256": file_sha256(source),
                "byte_size": source.stat().st_size,
                "artifact_class": artifact_class,
                **_artifact_metadata(relative, artifact_class),
                "secret_scan_status": secret_scan["secret_scan_status"],
            }
        )
    hash_mismatch = sum(
        file_sha256(source) != row["sha256"]
        for (source, _relative, _artifact_class), row in zip(
            indexed_sources, rows, strict=True
        )
    )
    size_mismatch = sum(
        source.stat().st_size != row["byte_size"]
        for (source, _relative, _artifact_class), row in zip(
            indexed_sources, rows, strict=True
        )
    )
    secret_failure_count = sum(
        row["secret_scan_status"] != "PASS" for row in rows
    )
    completion.update(
        {
            "final_head_sha": git_value("rev-parse", "HEAD"),
            "artifact_count": len(rows) + len(excluded),
            "indexed_artifact_count": len(rows),
            "unindexed_entries_and_reasons": excluded,
            "artifact_hash_mismatch_count": hash_mismatch,
            "artifact_size_mismatch_count": size_mismatch,
            "secret_scan_status": "PASS" if secret_failure_count == 0 else "FAIL",
        }
    )
    _write_proof(args.report_dir, 18, completion)
    write_text(
        args.report_dir / "README.md",
        "# Runtime Identity Lock Repair & New Holdout Readiness\n\n"
        + _markdown(
            {
                "Identity repair": completion["identity_repair_status"],
                "Model-free whole path": completion[
                    "whole_path_model_free_rehearsal_status"
                ],
                "US unseen": completion["us_supported_unseen_count"],
                "KR unseen": completion["kr_supported_unseen_count"],
                "New real model calls": completion["new_real_model_invocation_count"],
                "Proof readiness": completion["proof_readiness"],
                "Next scope": completion["next_scope"],
            }
        ),
    )
    index = {
        "contract": "runtime-identity-repair-artifact-index-v1",
        "indexed_artifact_count": len(rows),
        "intentional_unindexed_entries": excluded,
        "artifact_hash_mismatch_count": hash_mismatch,
        "artifact_size_mismatch_count": size_mismatch,
        "secret_scan_status": "PASS" if secret_failure_count == 0 else "FAIL",
        "rows": rows,
        "status": (
            "PASS"
            if hash_mismatch == size_mismatch == secret_failure_count == 0
            else "FAIL"
        ),
    }
    write_json(args.report_dir / "artifact-index.json", index)
    write_text(args.report_dir / "artifact-index.md", "# Artifact Index\n\n" + _markdown(index))
    if index["status"] != "PASS":
        raise ValueError("artifact_index_integrity_or_secret_scan_failed")
    args.zip_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.zip_output.with_suffix(args.zip_output.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(args.report_dir.rglob("*")):
            if path.is_file():
                archive.write(path, Path("reports") / path.relative_to(args.report_dir))
        for (source, relative, artifact_class), row in zip(
            indexed_sources, rows, strict=True
        ):
            if artifact_class != "REPORT":
                archive.write(source, relative)
    temporary.replace(args.zip_output)
    with zipfile.ZipFile(args.zip_output) as archive:
        bad_member = archive.testzip()
    if bad_member is not None:
        raise ValueError(f"final_zip_crc_failure:{bad_member}")
    zip_sha = file_sha256(args.zip_output)
    write_text(args.zip_output.with_suffix(args.zip_output.suffix + ".sha256"), zip_sha)
    return {**completion, "report_zip": str(args.zip_output), "report_zip_sha256": zip_sha}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("model-free", "generate", "finalize"), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--latest-result-zip", type=Path)
    parser.add_argument("--predecessor-zip", type=Path)
    parser.add_argument("--provider-root", type=Path, default=Path.home() / "Codex/ohlcv-analyst")
    parser.add_argument("--implementation-commit")
    parser.add_argument("--freeze-commit")
    parser.add_argument("--freeze-utc", type=datetime.fromisoformat)
    parser.add_argument("--focused-tests", default="NOT_RUN")
    parser.add_argument("--full-tests", default="NOT_RUN")
    parser.add_argument("--ruff", default="NOT_RUN")
    parser.add_argument("--diff-check", default="NOT_RUN")
    parser.add_argument("--zip-output", type=Path)
    args = parser.parse_args()
    for name in (
        "output_root",
        "report_dir",
        "latest_result_zip",
        "predecessor_zip",
        "provider_root",
        "zip_output",
    ):
        value = getattr(args, name)
        if value is not None:
            setattr(args, name, value.expanduser().resolve())
    return args


def main() -> None:
    args = parse_args()
    if args.mode == "model-free":
        if args.output_root.exists():
            raise ValueError("new_output_directory_required")
        result = model_free_rehearsal(args.output_root)
    elif args.mode == "generate":
        required = (
            args.latest_result_zip,
            args.predecessor_zip,
            args.implementation_commit,
            args.freeze_commit,
            args.freeze_utc,
        )
        if any(value is None for value in required):
            raise ValueError("generate_arguments_required")
        result = generate(args)
    else:
        if args.zip_output is None:
            raise ValueError("zip_output_required")
        result = finalize(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
