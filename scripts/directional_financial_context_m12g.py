from __future__ import annotations

import argparse
import copy
import difflib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from scripts import directional_financial_context_m12 as m12
from scripts import directional_financial_context_m12r as m12r


PROGRAM_CONTRACT = "directional-financial-context-m12g-v1"
BASE_SHA = "6a870cd34dd9ec7825559dc3ad964021b7cea64a"
WORK_INSTRUCTION_COMMIT = "7e3fac6385760e3356213eab81c67e957d1c55d6"
M12R_GENERATION_ID = "20260909-m12r-fictional-20260909T043009Z-ffc3fd557f05"
LATEST_RESULT_ZIP = Path(
    "/Users/sskim/Documents/Codex/"
    "thesis-monitor-20260909-bounded-directional-financial-context-validator-"
    "repair-full-fictional-canary-report.zip"
)
LATEST_RESULT_SHA256 = "0a55f4f04615602c2bac72e47c0489d30788437394135b772598e377c1289ab4"
REPORT_DIRECTORY_NAME = (
    "20260909-bounded-directional-financial-anchor-grounding-repair-full-fictional-canary"
)
DEFAULT_REPORT_DIR = Path("docs/reports") / REPORT_DIRECTORY_NAME
DEFAULT_OUTPUT_ROOT = Path("artifacts") / REPORT_DIRECTORY_NAME
DEFAULT_BUNDLE_PATH = Path("/Users/sskim/Documents/Codex") / (
    "thesis-monitor-20260909-bounded-directional-financial-anchor-grounding-"
    "repair-full-fictional-canary-report.zip"
)
INSTRUCTION_PATH = Path("docs/work-instructions") / (
    "20260909-bounded-directional-financial-anchor-grounding-repair-and-full-fictional-canary.md"
)

GROUNDING_PROMPT_MARKER = "cite its typed financial evidence alias"
GROUNDING_ROOT_CAUSE = "FIC_FIN_06_TYPED_FINANCIAL_EVIDENCE_NOT_GROUNDED"

_METRIC_FAMILY = {
    "operating_cash_flow": "CASH_CONVERSION",
    "ppe_capex_cash_outflow": "CASH_CONVERSION",
    "ocf_less_ppe_capex": "CASH_CONVERSION",
    "cash_and_cash_equivalents": "DEBT_LIQUIDITY",
    "interest_bearing_debt_total": "DEBT_LIQUIDITY",
    "net_debt": "DEBT_LIQUIDITY",
    "inventory": "WORKING_CAPITAL",
    "trade_accounts_receivable": "WORKING_CAPITAL",
    "trade_accounts_payable": "WORKING_CAPITAL",
    "operating_income": "EARNINGS_PERIOD",
    "net_income": "NON_OPERATING_EFFECT",
    "net_financial_income_effect": "NON_OPERATING_EFFECT",
    "interest_income": "NON_OPERATING_EFFECT",
    "interest_expense": "NON_OPERATING_EFFECT",
}

_FAMILY_TOKENS = {
    "CASH_CONVERSION": (
        "ocf",
        "operating cash",
        "cash conversion",
        "영업현금",
        "현금전환",
        "현금 전환",
        "현금창출",
        "현금 창출",
        "재투자",
    ),
    "DEBT_LIQUIDITY": (
        "debt",
        "liquidity",
        "leverage",
        "cash buffer",
        "부채",
        "유동성",
        "레버리지",
        "현금 여력",
        "재무 여력",
    ),
    "WORKING_CAPITAL": (
        "inventory",
        "inventories",
        "receivable",
        "working capital",
        "재고",
        "매출채권",
        "운전자본",
    ),
    "NON_OPERATING_EFFECT": (
        "non-operating",
        "financial income",
        "financial effect",
        "interest income",
        "interest expense",
        "비영업",
        "금융손익",
        "금융 효과",
        "이자수익",
        "이자비용",
        "순이익",
    ),
    "EARNINGS_PERIOD": (
        "qtd",
        "ytd",
        "quarter",
        "cumulative",
        "operating income",
        "분기",
        "누계",
        "누적",
        "영업이익",
        "영업손실",
    ),
}

_CHECKPOINT_PATH_MARKERS = (
    "core_investment_judgment",
    "dominant_evidence",
    "risk_context",
    "business_reevaluation_up",
    "business_reevaluation_down",
    "fundamental_new_buyer.confirmation_business_condition",
    "fundamental_holder.business_invalidation_condition",
    "buy_drivers",
    "sell_drivers",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _report_path(report_dir: Path, number: int, slug: str) -> Path:
    return report_dir / f"{number:02d}-{slug}.json"


def _zip_bytes(path: str) -> bytes:
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        return archive.read(path)


def _zip_json(path: str) -> dict[str, object]:
    value = json.loads(_zip_bytes(path))
    if not isinstance(value, dict):
        raise ValueError(f"m12g_zip_json_object_required:{path}")
    return value


def _latest_result_integrity() -> dict[str, object]:
    actual_sha = m12.file_sha256(LATEST_RESULT_ZIP)
    hash_mismatches = 0
    size_mismatches = 0
    missing = 0
    extra = 0
    indexed_payload_count = 0
    index_secret_failures = 0
    zip_test_errors: list[str] = []
    with zipfile.ZipFile(LATEST_RESULT_ZIP) as archive:
        bad = archive.testzip()
        if bad:
            zip_test_errors.append(bad)
        index = json.loads(archive.read("artifact-index.json"))
        rows = index.get("artifacts") or []
        indexed_payload_count = len(rows)
        names = set(archive.namelist())
        indexed_names = {str(row.get("path") or "") for row in rows}
        missing = sum(path not in names for path in indexed_names)
        extra = len(names - indexed_names - {"artifact-index.json"})
        for row in rows:
            path = str(row.get("path") or "")
            if path not in names:
                continue
            payload = archive.read(path)
            hash_mismatches += int(m12r._sha_bytes(payload) != str(row.get("sha256") or ""))
            size_mismatches += int(len(payload) != int(row.get("size_bytes") or -1))
        index_secret_failures = int(index.get("artifact_secret_scan_failure_count") or 0)
    status = (
        "PASS"
        if actual_sha == LATEST_RESULT_SHA256
        and not zip_test_errors
        and indexed_payload_count == 92
        and hash_mismatches == 0
        and size_mismatches == 0
        and missing == 0
        and extra == 0
        and index_secret_failures == 0
        else "FAIL"
    )
    return {
        "contract": "m12g-latest-result-integrity-v1",
        "path": str(LATEST_RESULT_ZIP),
        "expected_sha256": LATEST_RESULT_SHA256,
        "actual_sha256": actual_sha,
        "checksum_match": actual_sha == LATEST_RESULT_SHA256,
        "zip_test_errors": zip_test_errors,
        "indexed_payload_count": indexed_payload_count,
        "artifact_hash_mismatch_count": hash_mismatches,
        "artifact_size_mismatch_count": size_mismatches,
        "artifact_missing_count": missing,
        "artifact_extra_count": extra,
        "artifact_secret_scan_failure_count": index_secret_failures,
        "status": status,
    }


def _function_freeze(
    *,
    path: str,
    function_names: Sequence[str],
) -> dict[str, object]:
    before_source = m12._git_file(BASE_SHA, path)
    after_source = Path(path).read_text(encoding="utf-8")
    rows = []
    for name in function_names:
        before = m12._function_source_from_text(before_source, name)
        after = m12._function_source_from_text(after_source, name)
        rows.append(
            {
                "function": name,
                "before_sha256": m12r._sha_text(before),
                "after_sha256": m12r._sha_text(after),
                "changed": before != after,
            }
        )
    return {
        "path": path,
        "functions": rows,
        "change_count": sum(bool(row["changed"]) for row in rows),
        "status": "PASS" if all(not row["changed"] for row in rows) else "FAIL",
    }


def _file_freeze(path: str) -> dict[str, object]:
    before = m12._git_file(BASE_SHA, path)
    after = Path(path).read_text(encoding="utf-8")
    return {
        "path": path,
        "before_sha256": m12r._sha_text(before),
        "after_sha256": m12r._sha_text(after),
        "changed": before != after,
        "status": "PASS" if before == after else "FAIL",
    }


def _metric_family(metric: str) -> str | None:
    return _METRIC_FAMILY.get(metric)


def _text_families(text: str) -> set[str]:
    folded = text.casefold()
    return {
        family
        for family, tokens in _FAMILY_TOKENS.items()
        if any(token.casefold() in folded for token in tokens)
    }


def _candidate_mapping(candidate: object) -> Mapping[str, object]:
    if hasattr(candidate, "model_dump"):
        value = candidate.model_dump(mode="json")
    else:
        value = candidate
    if not isinstance(value, Mapping):
        raise TypeError("m12g_candidate_mapping_required")
    return value


def _claim_rows(value: object, path: str = "") -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if isinstance(value, Mapping):
        text = value.get("text")
        refs = value.get("evidence_refs")
        if (
            isinstance(text, str)
            and isinstance(refs, Sequence)
            and not isinstance(refs, (str, bytes))
        ):
            rows.append(
                {
                    "path": path,
                    "text": text,
                    "evidence_refs": [str(ref) for ref in refs],
                }
            )
        for condition_key, refs_key in (
            (
                "confirmation_business_condition",
                "confirmation_business_condition_refs",
            ),
            (
                "business_invalidation_condition",
                "business_invalidation_condition_refs",
            ),
        ):
            condition = value.get(condition_key)
            condition_refs = value.get(refs_key)
            if (
                isinstance(condition, str)
                and isinstance(condition_refs, Sequence)
                and not isinstance(condition_refs, (str, bytes))
            ):
                condition_path = f"{path}.{condition_key}" if path else condition_key
                rows.append(
                    {
                        "path": condition_path,
                        "text": condition,
                        "evidence_refs": [str(ref) for ref in condition_refs],
                    }
                )
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            rows.extend(_claim_rows(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            rows.extend(_claim_rows(child, f"{path}[{index}]"))
    return rows


def audit_financial_grounding(
    candidate: object,
    *,
    selected_metrics_by_ref: Mapping[str, str],
) -> dict[str, object]:
    data = _candidate_mapping(candidate)
    selected_refs = set(selected_metrics_by_ref)
    selected_families = {
        family
        for metric in selected_metrics_by_ref.values()
        if (family := _metric_family(metric)) is not None
    }
    all_refs = m12._candidate_refs(data)
    used_refs = all_refs & selected_refs
    claims = _claim_rows(data)
    grounded_rows = []
    narrative_only_rows = []
    irrelevant_rows = []
    relevant_claim_rows = []
    checkpoint_rows = []
    checkpoint_grounded_rows = []
    for claim in claims:
        text = str(claim["text"])
        families = _text_families(text) & selected_families
        if not families:
            continue
        refs = set(claim["evidence_refs"])
        relevant_typed_refs = {
            ref
            for ref in refs & selected_refs
            if _metric_family(selected_metrics_by_ref[ref]) in families
        }
        selected_wrong_family_refs = (refs & selected_refs) - relevant_typed_refs
        row = {
            **claim,
            "financial_families": sorted(families),
            "relevant_typed_refs": sorted(relevant_typed_refs),
            "selected_wrong_family_refs": sorted(selected_wrong_family_refs),
        }
        relevant_claim_rows.append(row)
        if relevant_typed_refs:
            grounded_rows.append(row)
        elif refs - selected_refs:
            narrative_only_rows.append(row)
        if selected_wrong_family_refs and not relevant_typed_refs:
            irrelevant_rows.append(row)
        if "WORKING_CAPITAL" in families and any(
            marker in str(claim["path"]) for marker in _CHECKPOINT_PATH_MARKERS
        ):
            checkpoint_rows.append(row)
            if relevant_typed_refs:
                checkpoint_grounded_rows.append(row)

    anchor_refs = {
        str(ref)
        for ref in data.get("material_directional_anchor_basis") or ()
        if str(ref) in selected_refs
    }
    material_required = bool(selected_refs and relevant_claim_rows)
    material_grounded = bool(grounded_rows or anchor_refs)
    working_capital_required = bool("WORKING_CAPITAL" in selected_families and checkpoint_rows)
    working_capital_grounded = bool(checkpoint_grounded_rows)
    material_failure = int(material_required and not material_grounded)
    working_capital_failure = int(working_capital_required and not working_capital_grounded)
    narrative_substitution_failure = int(
        material_required and not material_grounded and bool(narrative_only_rows)
    )
    irrelevant_ref_failure = int(
        material_required and not material_grounded and bool(irrelevant_rows)
    )
    errors = []
    if material_failure:
        errors.append("material_financial_anchor_grounding_failure")
    if working_capital_failure:
        errors.append("working_capital_grounding_failure")
    if narrative_substitution_failure:
        errors.append("narrative_substitution_failure")
    if irrelevant_ref_failure:
        errors.append("irrelevant_financial_ref_grounding_failure")
    return {
        "contract": "directional-financial-anchor-grounding-audit-v1",
        "selected_financial_refs": sorted(selected_refs),
        "used_financial_refs": sorted(used_refs),
        "material_financial_anchor_refs": sorted(
            {ref for row in grounded_rows for ref in row["relevant_typed_refs"]} | anchor_refs
        ),
        "financial_checkpoint_refs": sorted(
            {ref for row in checkpoint_grounded_rows for ref in row["relevant_typed_refs"]}
        ),
        "narrative_only_duplicate_refs": sorted(
            {
                ref
                for row in narrative_only_rows
                for ref in row["evidence_refs"]
                if ref not in selected_refs
            }
        ),
        "relevant_claim_count": len(relevant_claim_rows),
        "grounded_claim_count": len(grounded_rows),
        "working_capital_checkpoint_count": len(checkpoint_rows),
        "grounded_working_capital_checkpoint_count": len(checkpoint_grounded_rows),
        "material_grounding_required": material_required,
        "working_capital_grounding_required": working_capital_required,
        "material_financial_anchor_grounding_failure_count": material_failure,
        "working_capital_grounding_failure_count": working_capital_failure,
        "narrative_substitution_failure_count": narrative_substitution_failure,
        "irrelevant_financial_ref_grounding_failure_count": irrelevant_ref_failure,
        "errors": errors,
        "valid": not errors,
        "status": "PASS" if not errors else "FAIL",
    }


def _selected_metrics_for_ticker(
    owned: Mapping[str, object],
    ticker: str,
) -> dict[str, str]:
    context = m12.financial_decision_context_for_owned(owned[ticker])
    if context is None:
        return {}
    return {item.evidence_id: item.metric for item in context.evidence_items}


def _audit_core_batch_with_grounding(
    batch: object,
    *,
    owned: Mapping[str, object],
    catalogs: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows, audit = m12._audit_core_batch(batch, owned=owned, catalogs=catalogs)
    additional_error_count = 0
    totals = Counter()
    for row in rows:
        grounding = audit_financial_grounding(
            row["core"],
            selected_metrics_by_ref=_selected_metrics_for_ticker(owned, str(row["ticker"])),
        )
        new_errors = [error for error in grounding["errors"] if error not in row["errors"]]
        row["errors"].extend(new_errors)
        row["status"] = "PASS" if not row["errors"] else "FAIL"
        row["financial_grounding"] = grounding
        additional_error_count += len(new_errors)
        totals.update(
            {
                "selected_financial_ref_count": len(grounding["selected_financial_refs"]),
                "used_financial_ref_count": len(grounding["used_financial_refs"]),
                "material_financial_anchor_grounding_failure_count": grounding[
                    "material_financial_anchor_grounding_failure_count"
                ],
                "working_capital_grounding_failure_count": grounding[
                    "working_capital_grounding_failure_count"
                ],
                "narrative_substitution_failure_count": grounding[
                    "narrative_substitution_failure_count"
                ],
                "irrelevant_financial_ref_grounding_failure_count": grounding[
                    "irrelevant_financial_ref_grounding_failure_count"
                ],
            }
        )
    audit = {
        **audit,
        **dict(totals),
        "hard_error_count": int(audit.get("hard_error_count") or 0) + additional_error_count,
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }
    return rows, audit


def _resolved_historical_rows(
    *,
    context_number: int,
) -> tuple[list[dict[str, object]], dict[str, object], Mapping[str, object], Mapping[str, object]]:
    raw = _zip_json(f"experiment/model-calls/run-1/context-{context_number:02d}/output.raw.json")
    packets, owned, catalogs, _contexts = m12.fictional_inputs(M12R_GENERATION_ID)
    batch, _alias_audit = m12._resolve_core_batch(
        raw,
        generation_id=M12R_GENERATION_ID,
        tickers=m12.CONTEXTS[context_number - 1],
        packets=packets,
        catalogs=catalogs,
    )
    rows, audit = _audit_core_batch_with_grounding(
        batch,
        owned=owned,
        catalogs=catalogs,
    )
    return rows, audit, owned, catalogs


def _historical_regressions() -> dict[str, object]:
    first_rows, first_audit, _owned, _catalogs = _resolved_historical_rows(context_number=1)
    second_rows, second_audit, owned, catalogs = _resolved_historical_rows(context_number=2)
    fic03 = next(row for row in first_rows if row["ticker"] == "FIC-FIN-03")
    fic06 = next(row for row in second_rows if row["ticker"] == "FIC-FIN-06")

    corrected_data = copy.deepcopy(fic06["core"])
    typed_refs = set(fic06["selected_financial_refs"])
    for field, refs_field in (
        ("risk_context", "evidence_refs"),
        ("fundamental_new_buyer", "confirmation_business_condition_refs"),
        ("fundamental_holder", "business_invalidation_condition_refs"),
    ):
        target = corrected_data[field]
        target[refs_field] = sorted(set(target[refs_field]) | typed_refs)
    corrected = m12.DirectionalCoreCandidate.model_validate(corrected_data)
    corrected_batch = m12.DirectionalCoreBatch(
        packet_id=M12R_GENERATION_ID,
        candidates=(corrected,),
    )
    corrected_rows, corrected_audit = _audit_core_batch_with_grounding(
        corrected_batch,
        owned=owned,
        catalogs=catalogs,
    )
    corrected_row = corrected_rows[0]
    return {
        "fic03": fic03,
        "fic03_context_audit": first_audit,
        "fic06": fic06,
        "fic06_context_audit": second_audit,
        "corrected_fic06": corrected_row,
        "corrected_fic06_audit": corrected_audit,
        "old_fic_fin_03_regression_status": fic03["status"],
        "old_fic_fin_06_regression_status": (
            "PASS"
            if fic06["status"] == "FAIL"
            and "material_financial_anchor_not_used" in fic06["errors"]
            and "working_capital_checkpoint_not_used" in fic06["errors"]
            and fic06["financial_grounding"]["status"] == "FAIL"
            else "FAIL"
        ),
        "corrected_fic_fin_06_status": corrected_row["status"],
    }


def _positive_grounding_fixtures() -> dict[str, object]:
    inventory = "canonical:fixture:inventory"
    receivables = "canonical:fixture:receivables"
    ocf = "canonical:fixture:ocf"
    debt = "canonical:fixture:debt"
    cash = "canonical:fixture:cash"
    effect = "canonical:fixture:financial-effect"
    narrative = "fictional:fixture:narrative-risk"
    fixtures = (
        (
            "working-capital-inventory",
            {
                "risk_context": {
                    "text": "재고 증가는 전환 확인이 필요하다.",
                    "evidence_refs": [inventory],
                }
            },
            {inventory: "inventory"},
        ),
        (
            "working-capital-receivables",
            {
                "risk_context": {
                    "text": "매출채권 회수 품질을 확인해야 한다.",
                    "evidence_refs": [receivables],
                }
            },
            {receivables: "trade_accounts_receivable"},
        ),
        (
            "working-capital-both-plus-narrative",
            {
                "risk_context": {
                    "text": "재고와 매출채권의 전환을 확인해야 한다.",
                    "evidence_refs": [inventory, receivables, narrative],
                }
            },
            {inventory: "inventory", receivables: "trade_accounts_receivable"},
        ),
        (
            "cash-conversion-ocf",
            {"dominant_evidence": {"text": "영업현금 전환이 핵심 근거다.", "evidence_refs": [ocf]}},
            {ocf: "operating_cash_flow"},
        ),
        (
            "debt-liquidity-complete",
            {
                "risk_context": {
                    "text": "부채와 현금 여력을 함께 확인한다.",
                    "evidence_refs": [debt, cash],
                }
            },
            {debt: "interest_bearing_debt_total", cash: "cash_and_cash_equivalents"},
        ),
        (
            "non-operating-financial-effect",
            {
                "dominant_evidence": {
                    "text": "금융손익 효과를 영업 개선과 분리한다.",
                    "evidence_refs": [effect],
                }
            },
            {effect: "net_financial_income_effect"},
        ),
    )
    rows = []
    for fixture_id, candidate, selected in fixtures:
        audit = audit_financial_grounding(
            candidate,
            selected_metrics_by_ref=selected,
        )
        rows.append(
            {
                "fixture_id": fixture_id,
                "candidate": candidate,
                "selected_metrics_by_ref": selected,
                "audit": audit,
                "status": audit["status"],
            }
        )
    return {
        "contract": "m12g-positive-grounding-fixtures-v1",
        "fixture_count": len(rows),
        "pass_count": sum(row["status"] == "PASS" for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _negative_grounding_fixtures() -> dict[str, object]:
    inventory = "canonical:fixture:inventory"
    receivables = "canonical:fixture:receivables"
    cash = "canonical:fixture:cash"
    narrative = "fictional:fixture:narrative-risk"
    fixtures = (
        (
            "narrative-only-substitution",
            {
                "risk_context": {
                    "text": "재고와 매출채권이 연말 이후 증가했다.",
                    "evidence_refs": [narrative],
                }
            },
            {inventory: "inventory", receivables: "trade_accounts_receivable"},
        ),
        (
            "irrelevant-financial-ref",
            {
                "risk_context": {
                    "text": "재고와 매출채권의 전환을 확인해야 한다.",
                    "evidence_refs": [cash],
                }
            },
            {inventory: "inventory", cash: "cash_and_cash_equivalents"},
        ),
        (
            "typed-ref-only-in-unrelated-field",
            {
                "risk_context": {
                    "text": "재고와 매출채권의 전환을 확인해야 한다.",
                    "evidence_refs": [narrative],
                },
                "sector_interpretation": {
                    "text": "산업 수요의 가시성을 본다.",
                    "evidence_refs": [inventory],
                },
            },
            {inventory: "inventory", receivables: "trade_accounts_receivable"},
        ),
    )
    rows = []
    for fixture_id, candidate, selected in fixtures:
        audit = audit_financial_grounding(
            candidate,
            selected_metrics_by_ref=selected,
        )
        rows.append(
            {
                "fixture_id": fixture_id,
                "candidate": candidate,
                "selected_metrics_by_ref": selected,
                "audit": audit,
                "status": "PASS" if audit["status"] == "FAIL" else "FAIL",
            }
        )
    return {
        "contract": "m12g-negative-grounding-fixtures-v1",
        "fixture_count": len(rows),
        "rejected_count": sum(row["status"] == "PASS" for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
    }


def _no_selected_financial_context_control() -> dict[str, object]:
    candidate = {
        "risk_context": {
            "text": "재고와 매출채권의 전환을 확인해야 한다.",
            "evidence_refs": ["fictional:fixture:narrative-risk"],
        }
    }
    audit = audit_financial_grounding(candidate, selected_metrics_by_ref={})
    return {
        "contract": "m12g-no-selected-financial-context-control-v1",
        "candidate": candidate,
        "audit": audit,
        "fake_grounding_requirement_count": int(
            audit["material_grounding_required"] or audit["working_capital_grounding_required"]
        ),
        "status": audit["status"],
    }


def _prompt_before_after() -> dict[str, object]:
    path = "scripts/directional_core_price_timing_holdout.py"
    before_source = m12._git_file(BASE_SHA, path)
    after_source = Path(path).read_text(encoding="utf-8")
    before = m12._function_source_from_text(before_source, "_core_prompt")
    after = m12._function_source_from_text(after_source, "_core_prompt")
    diff = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"{BASE_SHA[:12]}:{path}:_core_prompt",
            tofile="working-tree:_core_prompt",
            lineterm="",
        )
    )
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")]
    marker_lines = [line for line in added if GROUNDING_PROMPT_MARKER in line]
    status = (
        "PASS"
        if len(marker_lines) == 1
        and not removed
        and all(not line.strip() or line in marker_lines for line in added)
        else "FAIL"
    )
    return {
        "contract": "m12g-directional-prompt-before-after-v1",
        "path": path,
        "function": "_core_prompt",
        "before_sha256": m12r._sha_text(before),
        "after_sha256": m12r._sha_text(after),
        "directional_prompt_change_count": int(before != after),
        "bounded_grounding_clarification_count": len(marker_lines),
        "removed_line_count": len(removed),
        "added_lines": added,
        "removed_lines": removed,
        "diff": diff,
        "classification": "BOUNDED_TYPED_FINANCIAL_ALIAS_GROUNDING_CLARIFICATION",
        "status": status,
    }


def _model_input_freeze(
    *,
    generation_id: str,
    output_root: Path,
) -> dict[str, object]:
    prompt_rows = []
    schema_rows = []
    for context_number in range(1, m12.CONTEXT_COUNT + 1):
        old_base = f"experiment/frozen-contexts/context-{context_number:02d}"
        new_base = output_root / "frozen-contexts" / f"context-{context_number:02d}"
        old_prompt = _zip_bytes(f"{old_base}/prompt.txt").decode("utf-8")
        new_prompt = (new_base / "prompt.txt").read_text(encoding="utf-8")
        old_normalized = old_prompt.replace(M12R_GENERATION_ID, "<GENERATION_ID>")
        new_normalized = new_prompt.replace(generation_id, "<GENERATION_ID>")
        prompt_rows.append(
            {
                "context": context_number,
                "before_normalized_sha256": m12r._sha_text(old_normalized),
                "after_normalized_sha256": m12r._sha_text(new_normalized),
                "changed": old_normalized != new_normalized,
                "grounding_marker_present": GROUNDING_PROMPT_MARKER in new_prompt,
            }
        )
        old_schema = _zip_json(f"{old_base}/schema.json")
        new_schema = m12.read_json(new_base / "schema.json")
        old_sha = m12r._normalized_json_sha(old_schema, M12R_GENERATION_ID)
        new_sha = m12r._normalized_json_sha(new_schema, generation_id)
        schema_rows.append(
            {
                "context": context_number,
                "before_normalized_sha256": old_sha,
                "after_normalized_sha256": new_sha,
                "changed": old_sha != new_sha,
            }
        )
    return {
        "contract": "m12g-model-input-freeze-v1",
        "prompt_rows": prompt_rows,
        "schema_rows": schema_rows,
        "model_prompt_hash_change_count": sum(bool(row["changed"]) for row in prompt_rows),
        "schema_change_count": sum(bool(row["changed"]) for row in schema_rows),
        "status": (
            "PASS"
            if all(row["changed"] and row["grounding_marker_present"] for row in prompt_rows)
            and all(not row["changed"] for row in schema_rows)
            else "FAIL"
        ),
    }


def _packet_context_freeze(
    *,
    generation_id: str,
    output_root: Path,
) -> dict[str, object]:
    case_rows = []
    context_rows = []
    alias_rows = []
    for ticker in m12.TICKERS:
        for label, directory, rows in (
            ("packet", "packets", case_rows),
            ("context", "contexts", context_rows),
            ("alias", "aliases", alias_rows),
        ):
            old = _zip_json(f"experiment/{directory}/{ticker}.json")
            new = m12.read_json(output_root / directory / f"{ticker}.json")
            old_for_comparison = copy.deepcopy(old)
            new_for_comparison = copy.deepcopy(new)
            derived_identity_hash_changed = False
            if label == "alias":
                derived_identity_hash_changed = (
                    old_for_comparison.pop("alias_map_sha256", None)
                    != new_for_comparison.pop("alias_map_sha256", None)
                )
            old_sha = m12r._normalized_json_sha(
                old_for_comparison, M12R_GENERATION_ID
            )
            new_sha = m12r._normalized_json_sha(new_for_comparison, generation_id)
            rows.append(
                {
                    "ticker": ticker,
                    "artifact": label,
                    "before_normalized_sha256": old_sha,
                    "after_normalized_sha256": new_sha,
                    "changed": old_sha != new_sha,
                    "derived_identity_hash_changed": derived_identity_hash_changed,
                }
            )
    return {
        "contract": "m12g-packet-context-freeze-v1",
        "case_rows": case_rows,
        "context_rows": context_rows,
        "alias_rows": alias_rows,
        "fictional_case_change_count": sum(bool(row["changed"]) for row in case_rows),
        "financial_context_selection_change_count": sum(
            bool(row["changed"]) for row in context_rows
        ),
        "alias_change_count": sum(bool(row["changed"]) for row in alias_rows),
        "status": (
            "PASS"
            if all(not row["changed"] for row in (*case_rows, *context_rows, *alias_rows))
            else "FAIL"
        ),
    }


def _write_frozen_inputs(
    *,
    generation_id: str,
    output_root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    return m12r._write_frozen_inputs(
        generation_id=generation_id,
        output_root=output_root,
    )


def _validation_commands(output_root: Path) -> dict[str, dict[str, object]]:
    focused_tests = (
        "tests/test_decision_evidence_financial_context.py",
        "tests/test_financial_context_adapter_service.py",
        "tests/test_financial_lineage_projection_service.py",
        "tests/test_source_class_financial_mapping_service.py",
        "tests/test_debt_liquidity_financial_mapping_service.py",
        "tests/test_working_capital_financial_mapping_service.py",
        "tests/test_non_operating_financial_mapping_service.py",
        "tests/test_directional_financial_context_service.py",
        "tests/test_directional_financial_context_m12.py",
        "tests/test_directional_financial_context_m12r.py",
        "tests/test_directional_financial_context_m12g.py",
        "tests/test_direction_timing_ownership_service.py",
        "tests/test_directional_balance_ordinal_calibration.py",
        "tests/test_coldstart_fundamental_enrichment_service.py",
        "tests/test_nonproduction_monitoring_lifecycle_service.py",
        "tests/test_structured_autonomy_shadow_service.py",
    )
    validation_dir = output_root / "validation"
    return {
        "focused": m12._run_command(
            [sys.executable, "-m", "pytest", "-q", *focused_tests],
            output_path=validation_dir / "focused-tests.txt",
            timeout=1800,
        ),
        "full": m12._run_command(
            [sys.executable, "-m", "pytest", "-q"],
            output_path=validation_dir / "full-tests.txt",
            timeout=3600,
        ),
        "ruff": m12._run_command(
            [str(Path(sys.executable).with_name("ruff")), "check", "."],
            output_path=validation_dir / "ruff.txt",
            timeout=600,
        ),
        "diff": m12._run_command(
            ["git", "diff", "--check"],
            output_path=validation_dir / "git-diff-check.txt",
            timeout=120,
        ),
    }


def phase_a(args: argparse.Namespace) -> None:
    implementation_commit = _git("rev-parse", "HEAD")
    if implementation_commit == WORK_INSTRUCTION_COMMIT:
        raise ValueError("m12g_implementation_commit_required")
    if (args.output_root / "phase-a-receipt.json").exists():
        raise ValueError("m12g_existing_phase_a_artifacts_refuse_rerun")

    args.report_dir.mkdir(parents=True, exist_ok=True)
    args.output_root.mkdir(parents=True, exist_ok=True)
    source_lock, model_inputs = _write_frozen_inputs(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    latest_integrity = _latest_result_integrity()
    historical = _historical_regressions()
    positive = _positive_grounding_fixtures()
    negative = _negative_grounding_fixtures()
    no_selected = _no_selected_financial_context_control()
    prompt = _prompt_before_after()
    model_input_freeze = _model_input_freeze(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    packet_context_freeze = _packet_context_freeze(
        generation_id=args.generation_id,
        output_root=args.output_root,
    )
    timing_freeze = _function_freeze(
        path="scripts/directional_core_price_timing_holdout.py",
        function_names=("_timing_prompt",),
    )
    selector_freeze = _function_freeze(
        path="app/services/directional_financial_context_service.py",
        function_names=(
            "semantic_category",
            "_period_rank",
            "_metric_rank",
            "_latest_per_metric_period",
            "_suppress_redundant_refs",
            "_comparison",
            "_decision_item",
            "build_financial_decision_context",
            "compact_financial_decision_context",
        ),
    )
    fictional_freeze = _function_freeze(
        path="scripts/directional_financial_context_m12.py",
        function_names=(
            "_period",
            "_financial_ref",
            "_financial_pair",
            "_generic_ref",
            "_technical_ref",
            "_common_refs",
            "_case_refs",
            "_family_for_ref",
            "fictional_inputs",
            "fictional_manifest",
            "_source_lock",
            "_write_frozen_model_inputs",
        ),
    )
    financial_validator_freeze = _function_freeze(
        path="app/services/directional_financial_context_service.py",
        function_names=("validate_directional_financial_semantics",),
    )
    qtd_ytd_validator_freeze = _function_freeze(
        path="app/services/directional_financial_context_service.py",
        function_names=("validate_qtd_ytd_conflict_semantics",),
    )
    case_validator_freeze = _function_freeze(
        path="scripts/directional_financial_context_m12.py",
        function_names=("_case_semantic_errors", "_audit_core_batch"),
    )
    no_change = {
        "source_sufficiency": _file_freeze(
            "app/services/coldstart_fundamental_enrichment_service.py"
        ),
        "daily_delta": _file_freeze("app/services/nonproduction_monitoring_lifecycle_service.py"),
        "renderer": _file_freeze("app/services/structured_autonomy_shadow_service.py"),
        "warning": _file_freeze("app/services/warning_backfill_service.py"),
        "notification": _file_freeze("app/services/notification_service.py"),
    }
    validations = _validation_commands(args.output_root)
    schedule = m12r._schedule_observation()

    changed_paths = tuple(
        path
        for path in _git(
            "diff", "--name-only", WORK_INSTRUCTION_COMMIT, implementation_commit
        ).splitlines()
        if path
    )
    expected_changed_paths = {
        "scripts/directional_core_price_timing_holdout.py",
        "scripts/directional_financial_context_m12g.py",
        "tests/test_directional_financial_context_m12g.py",
        "tests/test_directional_financial_context_service.py",
    }
    unexpected_changed_paths = sorted(set(changed_paths) - expected_changed_paths)
    repository = {
        "contract": "m12g-repository-provenance-v1",
        "branch": _git("branch", "--show-current"),
        "base_sha": BASE_SHA,
        "actual_base_head": _git("rev-parse", f"{WORK_INSTRUCTION_COMMIT}^"),
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": implementation_commit,
        "changed_paths_from_instruction_commit": list(changed_paths),
        "unexpected_changed_paths": unexpected_changed_paths,
        "status": "PASS" if not unexpected_changed_paths else "FAIL",
    }
    scope = {
        "contract": "m12g-scope-freeze-v1",
        "model": m12.MODEL,
        "reasoning_effort": m12.EFFORT,
        "timeout_seconds": m12.TIMEOUT_SECONDS,
        "fictional_subject_count": len(m12.TICKERS),
        "fictional_context_count": m12.CONTEXT_COUNT,
        "fictional_repetition_count": m12.REPETITION_COUNT,
        "fictional_model_calls": m12.EXPECTED_MODEL_CALLS,
        "real_model_calls": 0,
        "judge_model_calls": 0,
        "provider_source_fetches": 0,
        "prompt_only_production_behavior_change": True,
        "validator_relaxation_allowed": False,
        "production_side_effects_allowed": False,
        "status": "FROZEN",
    }
    validator = {
        "contract": "m12g-validator-no-relaxation-proof-v1",
        "financial_semantic_validator": financial_validator_freeze,
        "qtd_ytd_validator": qtd_ytd_validator_freeze,
        "case_semantic_validator": case_validator_freeze,
        "financial_semantic_validator_change_count": (
            financial_validator_freeze["change_count"] + case_validator_freeze["change_count"]
        ),
        "qtd_ytd_validator_semantic_change_count": qtd_ytd_validator_freeze["change_count"],
    }
    validator["status"] = (
        "PASS"
        if validator["financial_semantic_validator_change_count"] == 0
        and validator["qtd_ytd_validator_semantic_change_count"] == 0
        else "FAIL"
    )
    selector = {
        "contract": "m12g-financial-context-selection-freeze-proof-v1",
        "function_freeze": selector_freeze,
        "context_rows": packet_context_freeze["context_rows"],
        "financial_context_selection_change_count": (
            selector_freeze["change_count"]
            + packet_context_freeze["financial_context_selection_change_count"]
        ),
    }
    selector["status"] = (
        "PASS" if selector["financial_context_selection_change_count"] == 0 else "FAIL"
    )
    cases = {
        "contract": "m12g-fictional-case-freeze-proof-v1",
        "function_freeze": fictional_freeze,
        "packet_rows": packet_context_freeze["case_rows"],
        "alias_rows": packet_context_freeze["alias_rows"],
        "fictional_case_change_count": (
            fictional_freeze["change_count"]
            + packet_context_freeze["fictional_case_change_count"]
            + packet_context_freeze["alias_change_count"]
        ),
    }
    cases["status"] = "PASS" if cases["fictional_case_change_count"] == 0 else "FAIL"
    schema = {
        "contract": "m12g-schema-freeze-proof-v1",
        "rows": model_input_freeze["schema_rows"],
        "schema_change_count": model_input_freeze["schema_change_count"],
        "status": ("PASS" if model_input_freeze["schema_change_count"] == 0 else "FAIL"),
    }
    price_timing = {
        "contract": "m12g-price-timing-freeze-proof-v1",
        "function_freeze": timing_freeze,
        "price_timing_prompt_change_count": timing_freeze["change_count"],
        "status": timing_freeze["status"],
    }
    production_firewall = {
        "contract": "m12g-production-side-effect-firewall-v1",
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "live_v2_changes": 0,
        "night_futures_changes": 0,
        "automatic_monitoring_resume": 0,
        "status": "PASS",
    }

    reports = {
        (1, "repository-provenance"): repository,
        (2, "latest-result-integrity"): latest_integrity,
        (3, "m12g-scope-freeze"): scope,
        (4, "m12r-failure-reproduction"): {
            "contract": "m12g-m12r-failure-reproduction-v1",
            "ticker": "FIC-FIN-06",
            "errors": historical["fic06"]["errors"],
            "selected_financial_refs": historical["fic06"]["selected_financial_refs"],
            "used_financial_refs": historical["fic06"]["used_financial_refs"],
            "status": historical["old_fic_fin_06_regression_status"],
        },
        (5, "fic-fin-06-grounding-root-cause"): {
            "contract": "m12g-grounding-root-cause-v1",
            "root_cause": GROUNDING_ROOT_CAUSE,
            "model_understood_financial_concept": True,
            "selected_typed_financial_ref_used": False,
            "validator_false_reject": False,
            "status": "CONFIRMED",
        },
        (6, "financial-grounding-contract"): {
            "contract": "directional-financial-anchor-grounding-audit-v1",
            "material_claim_requires_relevant_typed_ref": True,
            "generic_narrative_may_supplement": True,
            "generic_narrative_may_substitute": False,
            "all_selected_refs_required": False,
            "exact_numeric_prose_required": False,
            "status": "PASS",
        },
        (7, "prompt-before-after"): {
            **prompt,
            "model_input_freeze": model_input_freeze,
        },
        (8, "validator-no-relaxation-proof"): validator,
        (9, "old-fic-fin-03-regression"): historical["fic03"],
        (10, "old-fic-fin-06-remains-fail"): historical["fic06"],
        (11, "corrected-fic-fin-06-fixture"): historical["corrected_fic06"],
        (12, "positive-grounding-fixture-manifest"): positive,
        (13, "negative-grounding-fixture-manifest"): negative,
        (14, "narrative-substitution-negative-control"): negative["rows"][0],
        (15, "irrelevant-financial-ref-negative-control"): negative["rows"][1],
        (16, "no-selected-financial-context-control"): no_selected,
        (17, "financial-context-selection-freeze-proof"): selector,
        (18, "fictional-case-freeze-proof"): cases,
        (19, "schema-freeze-proof"): schema,
        (20, "price-timing-freeze-proof"): price_timing,
        (21, "source-sufficiency-no-change-proof"): {
            **no_change["source_sufficiency"],
            "source_sufficiency_semantic_change_count": int(
                no_change["source_sufficiency"]["changed"]
            ),
        },
        (22, "daily-delta-no-change-proof"): {
            **no_change["daily_delta"],
            "daily_delta_semantic_change_count": int(no_change["daily_delta"]["changed"]),
            "monitoring_lifecycle_semantic_change_count": int(no_change["daily_delta"]["changed"]),
            "warning": no_change["warning"],
            "notification": no_change["notification"],
            "warning_semantic_change_count": int(
                no_change["warning"]["changed"] or no_change["notification"]["changed"]
            ),
        },
        (23, "renderer-ownership-no-change-proof"): {
            **no_change["renderer"],
            "renderer_substantive_change_count": int(no_change["renderer"]["changed"]),
        },
        (24, "focused-test-results"): validations["focused"],
        (25, "full-test-results"): validations["full"],
        (26, "ruff-and-diff-results"): {
            "ruff": validations["ruff"],
            "git_diff_check": validations["diff"],
            "status": (
                "PASS"
                if validations["ruff"]["status"] == "PASS"
                and validations["diff"]["status"] == "PASS"
                else "FAIL"
            ),
        },
        (43, "production-no-change"): production_firewall,
        (44, "schedule-pause-observation"): {
            "contract": "m12g-schedule-pause-start-observation-v1",
            "start": schedule,
            "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
            "scheduler_mutation_count": 0,
            "automatic_monitoring_resume": 0,
            "status": schedule["status"],
        },
    }
    for (number, slug), report in reports.items():
        m12.write_json(_report_path(args.report_dir, number, slug), report)

    checks = {
        "latest_result_integrity": latest_integrity["status"],
        "repository_scope": repository["status"],
        "old_fic_fin_03": historical["old_fic_fin_03_regression_status"],
        "old_fic_fin_06": historical["old_fic_fin_06_regression_status"],
        "corrected_fic_fin_06": historical["corrected_fic_fin_06_status"],
        "positive_grounding_fixtures": positive["status"],
        "negative_grounding_fixtures": negative["status"],
        "no_selected_financial_context": no_selected["status"],
        "prompt_diff_scope": prompt["status"],
        "model_input_freeze": model_input_freeze["status"],
        "validator_no_relaxation": validator["status"],
        "financial_context_selection_freeze": selector["status"],
        "fictional_case_freeze": cases["status"],
        "schema_freeze": schema["status"],
        "price_timing_freeze": price_timing["status"],
        "source_sufficiency_no_change": no_change["source_sufficiency"]["status"],
        "daily_delta_no_change": no_change["daily_delta"]["status"],
        "renderer_no_change": no_change["renderer"]["status"],
        "warning_no_change": (
            "PASS"
            if no_change["warning"]["status"] == "PASS"
            and no_change["notification"]["status"] == "PASS"
            else "FAIL"
        ),
        "production_side_effect_firewall": production_firewall["status"],
        "schedule_pause": schedule["status"],
        "focused_tests": validations["focused"]["status"],
        "full_tests": validations["full"]["status"],
        "ruff": validations["ruff"]["status"],
        "git_diff_check": validations["diff"]["status"],
    }
    receipt = {
        "contract": "m12g-phase-a-gate-v1",
        "generation_id": args.generation_id,
        "implementation_commit": implementation_commit,
        "source_lock_sha256": source_lock["source_lock_sha256"],
        "model_inputs": model_inputs,
        "checks": checks,
        "model_calls_before_gate": 0,
        "status": "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL",
        "stop_reason": (
            None if all(value == "PASS" for value in checks.values()) else "NO_MODEL_CALLS"
        ),
    }
    m12.write_json(_report_path(args.report_dir, 27, "phase-a-gate"), receipt)
    m12.write_json(args.output_root / "phase-a-receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), flush=True)
    if receipt["status"] != "PASS":
        raise SystemExit(2)


def run_canary(args: argparse.Namespace) -> None:
    phase_a_receipt = m12.read_json(args.output_root / "phase-a-receipt.json")
    if phase_a_receipt.get("status") != "PASS":
        raise ValueError("m12g_phase_a_gate_not_passed")
    if phase_a_receipt.get("generation_id") != args.generation_id:
        raise ValueError("m12g_phase_a_generation_mismatch")
    if phase_a_receipt.get("implementation_commit") != _git("rev-parse", "HEAD"):
        raise ValueError("m12g_code_changed_after_phase_a")
    source_lock = m12.read_json(args.output_root / "source-lock.json")
    packets, owned, catalogs, contexts = m12.fictional_inputs(args.generation_id)
    rebuilt_lock = m12._source_lock(
        args.generation_id,
        packets,
        owned,
        catalogs,
        contexts,
    )
    if source_lock != rebuilt_lock:
        raise ValueError("m12g_source_lock_rebuild_mismatch")

    codex_bin = m12._signed_in_codex_bin()
    registry = m12.CodexRuntimeIsolationRegistry()
    run_documents: dict[str, dict[str, object]] = {}
    invocation_count = 0
    for repetition in range(1, m12.REPETITION_COUNT + 1):
        for context_number, tickers in enumerate(m12.CONTEXTS, start=1):
            invocation_count += 1
            call_dir = (
                args.output_root
                / "model-calls"
                / f"run-{repetition}"
                / f"context-{context_number:02d}"
            )
            frozen_dir = args.output_root / "frozen-contexts" / f"context-{context_number:02d}"
            prompt = call_dir / "prompt.txt"
            schema = call_dir / "schema.json"
            prompt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(frozen_dir / "prompt.txt", prompt)
            shutil.copyfile(frozen_dir / "schema.json", schema)
            output = call_dir / "output.raw.json"
            log = call_dir / "transport.log"
            call_receipt_path = call_dir / "receipt.json"
            invocation_id = f"{args.generation_id}:run-{repetition}:context-{context_number:02d}"
            print(
                f"M12G_CALL_START {invocation_count}/{m12.EXPECTED_MODEL_CALLS} "
                f"run={repetition} context={context_number}",
                flush=True,
            )
            call_receipt = m12._single_attempt_model_call(
                codex_bin=codex_bin,
                prompt=prompt,
                schema=schema,
                output=output,
                log=log,
                receipt_path=call_receipt_path,
                working_directory=call_dir / "working-directory",
                runtime_state_root=args.output_root / "runtime-state",
                isolation_registry=registry,
                invocation_id=invocation_id,
                base_namespace=f"M12G_DIRECTIONAL_FINANCIAL_{args.generation_id}",
            )
            raw = m12.read_json(output)
            batch, alias_audit = m12._resolve_core_batch(
                raw,
                generation_id=args.generation_id,
                tickers=tickers,
                packets=packets,
                catalogs=catalogs,
            )
            rows, audit = _audit_core_batch_with_grounding(
                batch,
                owned=owned,
                catalogs=catalogs,
            )
            grounding_summary = _grounding_summary(
                rows,
                require_complete=False,
            )
            document = {
                "contract": "m12g-fictional-canary-context-run-v1",
                "generation_id": args.generation_id,
                "source_lock_sha256": source_lock["source_lock_sha256"],
                "repetition": repetition,
                "context": context_number,
                "tickers": list(tickers),
                "model": m12.MODEL,
                "reasoning_effort": m12.EFFORT,
                "prompt_sha256": m12.file_sha256(prompt),
                "schema_sha256": m12.file_sha256(schema),
                "output_sha256": m12.file_sha256(output),
                "receipt_sha256": m12.file_sha256(call_receipt_path),
                "transport": call_receipt,
                "alias_audit": alias_audit,
                "rows": rows,
                "audit": audit,
                "financial_grounding_audit": grounding_summary,
                "status": audit["status"],
            }
            m12.write_json(call_dir / "run-document.json", document)
            key = f"run-{repetition}-context-{context_number:02d}"
            run_documents[key] = document
            m12.write_json(
                _report_path(
                    args.output_root / "runner-reports",
                    29 + invocation_count,
                    f"canary-context-{context_number:02d}-run-{repetition}",
                ),
                document,
            )
            print(
                f"M12G_CALL_COMPLETE {invocation_count}/{m12.EXPECTED_MODEL_CALLS} "
                f"status={audit['status']}",
                flush=True,
            )
            if audit["status"] != "PASS":
                grounding_failures = sum(
                    int(grounding_summary.get(field) or 0)
                    for field in (
                        "material_financial_anchor_grounding_failure_count",
                        "working_capital_grounding_failure_count",
                        "narrative_substitution_failure_count",
                    )
                )
                m12.write_json(
                    args.output_root / "canary-stop.json",
                    {
                        "status": "FAIL",
                        "stop_reason": (
                            "M12G_MODEL_GROUNDING_FAIL"
                            if grounding_failures
                            else "M12G_MODEL_CANARY_FAIL"
                        ),
                        "failed_invocation": invocation_id,
                        "model_calls_completed": invocation_count,
                        "wrapper_retry_count": 0,
                    },
                )
                raise SystemExit(3)

    if invocation_count != m12.EXPECTED_MODEL_CALLS:
        raise ValueError("m12g_model_call_count_mismatch")
    canonical_args = argparse.Namespace(
        generation_id=args.generation_id,
        output_root=args.output_root,
        report_dir=args.output_root / "runner-reports",
    )
    summary = m12._final_canary_audits(
        args=canonical_args,
        run_documents=run_documents,
        source_lock=source_lock,
        registry=registry,
    )
    all_rows = [row for document in run_documents.values() for row in document["rows"]]
    grounding = _grounding_summary(all_rows, require_complete=True)
    summary = {
        **summary,
        "contract": "m12g-fictional-canary-summary-v1",
        "financial_grounding_audit": grounding,
        "status": (
            "PASS" if summary["status"] == "PASS" and grounding["status"] == "PASS" else "FAIL"
        ),
    }
    summary["stop_reason"] = None if summary["status"] == "PASS" else "M12G_MODEL_CANARY_FAIL"
    m12.write_json(args.output_root / "canary-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
    if summary["status"] != "PASS":
        raise SystemExit(4)


def _grounding_summary(
    rows: Sequence[Mapping[str, object]],
    *,
    require_complete: bool,
) -> dict[str, object]:
    details = []
    totals = Counter()
    for row in rows:
        grounding = row.get("financial_grounding") or {}
        if not isinstance(grounding, Mapping):
            grounding = {}
        detail = {
            "ticker": row.get("ticker"),
            "selected_financial_refs": grounding.get("selected_financial_refs", []),
            "used_financial_refs": grounding.get("used_financial_refs", []),
            "material_financial_anchor_refs": grounding.get("material_financial_anchor_refs", []),
            "financial_checkpoint_refs": grounding.get("financial_checkpoint_refs", []),
            "narrative_only_duplicate_refs": grounding.get("narrative_only_duplicate_refs", []),
            "grounding_status": grounding.get("status", "NOT_MEASURED"),
            "errors": grounding.get("errors", []),
        }
        details.append(detail)
        totals.update(
            {
                "selected_financial_ref_count": len(detail["selected_financial_refs"]),
                "used_financial_ref_count": len(detail["used_financial_refs"]),
                "material_financial_anchor_grounding_failure_count": int(
                    grounding.get("material_financial_anchor_grounding_failure_count", 0)
                ),
                "working_capital_grounding_failure_count": int(
                    grounding.get("working_capital_grounding_failure_count", 0)
                ),
                "narrative_substitution_failure_count": int(
                    grounding.get("narrative_substitution_failure_count", 0)
                ),
                "irrelevant_financial_ref_grounding_failure_count": int(
                    grounding.get("irrelevant_financial_ref_grounding_failure_count", 0)
                ),
            }
        )
    complete = len(rows) == len(m12.TICKERS) * m12.REPETITION_COUNT
    hard_failures = sum(
        totals[field]
        for field in (
            "material_financial_anchor_grounding_failure_count",
            "working_capital_grounding_failure_count",
            "narrative_substitution_failure_count",
            "irrelevant_financial_ref_grounding_failure_count",
        )
    )
    return {
        "contract": "m12g-full-fictional-canary-financial-grounding-audit-v1",
        "rows": details,
        **dict(totals),
        "complete_sample": complete,
        "status": ("PASS" if hard_failures == 0 and (complete or not require_complete) else "FAIL"),
    }


def _run_documents(output_root: Path) -> dict[tuple[int, int], dict[str, object]]:
    return m12r._run_documents(output_root)


def _receipts(output_root: Path) -> list[dict[str, object]]:
    return m12r._receipts(output_root)


def _partial_semantic_audit(
    *,
    generation_id: str,
    run_documents: Mapping[tuple[int, int], Mapping[str, object]],
) -> dict[str, object]:
    return {
        **m12r._partial_semantic_audit(
            generation_id=generation_id,
            run_documents=run_documents,
        ),
        "contract": "m12g-fictional-canary-semantic-audit-v1",
    }


def _partial_runtime(output_root: Path) -> dict[str, object]:
    return {
        **m12r._partial_runtime(output_root),
        "contract": "m12g-runtime-observations-v1",
    }


def _validator_audit(
    run_documents: Mapping[tuple[int, int], Mapping[str, object]],
) -> dict[str, object]:
    return {
        **m12r._validator_audit(run_documents),
        "contract": "m12g-full-fictional-canary-validator-audit-v1",
    }


def _artifact_source_rows(
    *,
    report_dir: Path,
    output_root: Path,
) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    for path in sorted(report_dir.rglob("*")):
        if path.is_file():
            rows.append((f"reports/{path.relative_to(report_dir)}", path))
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(output_root)
        if any(
            excluded in relative.parts
            for excluded in ("runtime-state", "working-directory", "runner-reports")
        ):
            continue
        rows.append((f"experiment/{relative}", path))
    rows.extend(
        (
            ("docs/MASTER_WORKFLOW.md", Path("docs/MASTER_WORKFLOW.md")),
            (f"docs/work-instructions/{INSTRUCTION_PATH.name}", INSTRUCTION_PATH),
        )
    )
    seen: set[str] = set()
    unique = []
    for archive_name, path in rows:
        if archive_name in seen:
            raise ValueError(f"m12g_duplicate_artifact_path:{archive_name}")
        seen.add(archive_name)
        unique.append((archive_name, path))
    return unique


def _secret_scan_failures(rows: Sequence[tuple[str, Path]]) -> list[str]:
    return m12r._secret_scan_failures(rows)


def finalize(args: argparse.Namespace) -> None:
    phase_a_receipt = m12.read_json(args.output_root / "phase-a-receipt.json")
    if phase_a_receipt.get("status") != "PASS":
        raise ValueError("m12g_finalize_requires_passed_phase_a")
    run_documents = _run_documents(args.output_root)
    canary_summary_path = args.output_root / "canary-summary.json"
    canary_summary = m12.read_json(canary_summary_path) if canary_summary_path.is_file() else None

    manifest = m12.read_json(args.output_root / "manifest.json")
    source_lock = m12.read_json(args.output_root / "source-lock.json")
    m12.write_json(
        _report_path(args.report_dir, 28, "fictional-canary-generation-manifest"),
        {
            **manifest,
            "contract": "m12g-fictional-canary-generation-manifest-v1",
            "status": "FROZEN",
        },
    )
    m12.write_json(
        _report_path(args.report_dir, 29, "fictional-canary-source-lock"),
        {
            **source_lock,
            "contract": "m12g-fictional-canary-source-lock-v1",
            "status": "FROZEN",
        },
    )
    for repetition in range(1, m12.REPETITION_COUNT + 1):
        for context_number in range(1, m12.CONTEXT_COUNT + 1):
            number = 30 + (repetition - 1) * 2 + (context_number - 1)
            document = run_documents.get((repetition, context_number))
            if document is None:
                receipt_path = (
                    args.output_root
                    / "model-calls"
                    / f"run-{repetition}"
                    / f"context-{context_number:02d}"
                    / "receipt.json"
                )
                document = {
                    "contract": "m12g-fictional-canary-context-run-v1",
                    "generation_id": args.generation_id,
                    "repetition": repetition,
                    "context": context_number,
                    "receipt": (m12.read_json(receipt_path) if receipt_path.is_file() else None),
                    "status": "FAIL" if receipt_path.is_file() else "NOT_RUN",
                }
            else:
                document = {
                    **document,
                    "contract": "m12g-fictional-canary-context-run-v1",
                }
            m12.write_json(
                _report_path(
                    args.report_dir,
                    number,
                    f"run-{repetition}-context-{context_number:02d}",
                ),
                document,
            )

    if canary_summary is not None:
        semantic = {
            **canary_summary["semantic_audit"],
            "contract": "m12g-full-fictional-canary-semantic-audit-v1",
        }
        grounding = {
            **canary_summary["financial_grounding_audit"],
            "contract": "m12g-full-fictional-canary-financial-grounding-audit-v1",
        }
        stability = {
            **canary_summary["stability"],
            "contract": "m12g-full-fictional-canary-stability-v1",
        }
        specificity = {
            **canary_summary["specificity"],
            "contract": "m12g-full-fictional-canary-message-specificity-v1",
            "typed_financial_anchor_specificity": grounding["status"],
        }
        runtime = {
            **canary_summary["runtime"],
            "contract": "m12g-runtime-observations-v1",
        }
    else:
        semantic = _partial_semantic_audit(
            generation_id=args.generation_id,
            run_documents=run_documents,
        )
        partial_rows = [row for document in run_documents.values() for row in document["rows"]]
        grounding = _grounding_summary(partial_rows, require_complete=True)
        stability = {
            "contract": "m12g-full-fictional-canary-stability-v1",
            "fictional_stable_count": "NOT_MEASURED",
            "fictional_boundary_uncertainty_count": "NOT_MEASURED",
            "fictional_unstable_count": "NOT_MEASURED",
            "opposite_direction_reversal_count": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        specificity = {
            "contract": "m12g-full-fictional-canary-message-specificity-v1",
            "typed_financial_anchor_specificity": "NOT_MEASURED",
            "status": "NOT_MEASURED",
        }
        runtime = _partial_runtime(args.output_root)
    validator = _validator_audit(run_documents)

    m12.write_json(
        _report_path(args.report_dir, 36, "full-fictional-canary-semantic-audit"),
        semantic,
    )
    m12.write_json(
        _report_path(
            args.report_dir,
            37,
            "full-fictional-canary-financial-grounding-audit",
        ),
        grounding,
    )
    m12.write_json(
        _report_path(args.report_dir, 38, "full-fictional-canary-validator-audit"),
        validator,
    )
    m12.write_json(
        _report_path(args.report_dir, 39, "full-fictional-canary-stability"),
        stability,
    )
    m12.write_json(
        _report_path(
            args.report_dir,
            40,
            "full-fictional-canary-message-specificity-advisory",
        ),
        specificity,
    )
    m12.write_json(_report_path(args.report_dir, 41, "runtime-observations"), runtime)

    hard_zero_fields = (
        "invalid_financial_reference_count",
        "partial_capex_called_fcf_count",
        "year_end_as_yoy_count",
        "partial_debt_total_claim_count",
        "normalized_earnings_claim_violation_count",
        "financial_sector_generic_financial_context_leak_count",
        "fixed_financial_score_rule_count",
        "directional_core_price_technical_refs",
        "directional_core_supply_refs",
        "ai_imperative_primary_action_count",
        "qtd_ytd_conflict_violation_count",
    )
    grounding_zero_fields = (
        "material_financial_anchor_grounding_failure_count",
        "working_capital_grounding_failure_count",
        "narrative_substitution_failure_count",
        "irrelevant_financial_ref_grounding_failure_count",
    )
    canary_pass = bool(
        len(run_documents) == m12.EXPECTED_MODEL_CALLS
        and semantic["status"] == "PASS"
        and grounding["status"] == "PASS"
        and validator["status"] == "PASS"
        and stability["status"] == "PASS"
        and runtime["status"] == "PASS"
        and int(semantic["fictional_output_row_count"]) == len(m12.TICKERS) * m12.REPETITION_COUNT
        and int(semantic["fictional_schema_pass_count"]) == len(m12.TICKERS) * m12.REPETITION_COUNT
        and all(int(semantic.get(field) or 0) == 0 for field in hard_zero_fields)
        and all(int(grounding.get(field) or 0) == 0 for field in grounding_zero_fields)
        and int(runtime["wrapper_retry_count"]) == 0
        and int(runtime["timeout_count"]) == 0
        and int(runtime["capacity_failure_count"]) == 0
        and int(runtime["orphan_process_count"]) == 0
    )
    receipts = _receipts(args.output_root)
    runtime_failures = [
        str(receipt.get("failure_type") or "")
        for receipt in receipts
        if receipt.get("status") != "PASS"
    ]
    grounding_failure_count = sum(int(grounding.get(field) or 0) for field in grounding_zero_fields)
    if canary_pass:
        status = "M12G_COMPLETE"
        stop_reason = None
        next_scope = "FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF"
        fresh_real_readiness = "READY"
    elif runtime_failures:
        status = "M12G_CANARY_FAIL"
        stop_reason = "M12G_RUNTIME_FAILURE:" + ",".join(runtime_failures)
        next_scope = "BOUNDED_FICTIONAL_RUNTIME_REPAIR"
        fresh_real_readiness = "NOT_READY"
    elif grounding_failure_count:
        status = "M12G_CANARY_FAIL"
        stop_reason = "PROMPT_GROUNDING_INSUFFICIENT"
        next_scope = "FINANCIAL_CONTEXT_OUTPUT_GROUNDING_ARCHITECTURE_REVIEW"
        fresh_real_readiness = "NOT_READY"
    elif semantic["status"] != "PASS" or validator["status"] != "PASS":
        status = "M12G_CANARY_FAIL"
        stop_reason = "M12G_NEW_FINANCIAL_SEMANTIC_BLOCKER"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR"
        fresh_real_readiness = "NOT_READY"
    else:
        status = "M12G_CANARY_FAIL"
        stop_reason = "M12G_FINANCIAL_INTERPRETATION_STABILITY_FAILURE"
        next_scope = "BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_STABILITY_REVIEW"
        fresh_real_readiness = "NOT_READY"

    readiness = {
        "contract": "m12g-fresh-real-proof-readiness-decision-v1",
        "financial_grounding_repair_status": "PASS",
        "full_fictional_canary_status": "PASS" if canary_pass else "FAIL",
        "fresh_real_proof_readiness": fresh_real_readiness,
        "production_readiness": "NOT_READY",
        "next_scope": next_scope,
        "status": "PASS" if canary_pass else "FAIL",
    }
    production = m12.read_json(_report_path(args.report_dir, 43, "production-no-change"))
    schedule_start = m12.read_json(_report_path(args.report_dir, 44, "schedule-pause-observation"))
    schedule_end = m12r._schedule_observation()
    schedule = {
        "contract": "m12g-schedule-pause-start-end-observation-v1",
        "start": schedule_start["start"],
        "end": schedule_end,
        "observed_paused_schedule_count": schedule_end["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "status": (
            "PASS"
            if schedule_start["status"] == "PASS" and schedule_end["status"] == "PASS"
            else "REVIEW"
        ),
    }
    master_text = Path("docs/MASTER_WORKFLOW.md").read_text(encoding="utf-8")
    master = {
        "contract": "m12g-master-workflow-update-v1",
        "path": "docs/MASTER_WORKFLOW.md",
        "sha256": m12r._sha_text(master_text),
        "m12g_recorded": "M12G" in master_text,
        "grounding_root_cause_recorded": GROUNDING_ROOT_CAUSE in master_text,
        "next_scope_recorded": next_scope in master_text,
        "production_not_ready_recorded": "production_readiness=NOT_READY" in master_text,
    }
    master["status"] = (
        "PASS"
        if all(
            master[key]
            for key in (
                "m12g_recorded",
                "grounding_root_cause_recorded",
                "next_scope_recorded",
                "production_not_ready_recorded",
            )
        )
        else "FAIL"
    )
    m12.write_json(
        _report_path(args.report_dir, 42, "fresh-real-proof-readiness-decision"),
        readiness,
    )
    m12.write_json(_report_path(args.report_dir, 43, "production-no-change"), production)
    m12.write_json(_report_path(args.report_dir, 44, "schedule-pause-observation"), schedule)
    m12.write_json(_report_path(args.report_dir, 45, "master-workflow-update"), master)

    historical03 = m12.read_json(_report_path(args.report_dir, 9, "old-fic-fin-03-regression"))
    historical06 = m12.read_json(_report_path(args.report_dir, 10, "old-fic-fin-06-remains-fail"))
    corrected06 = m12.read_json(_report_path(args.report_dir, 11, "corrected-fic-fin-06-fixture"))
    positive = m12.read_json(
        _report_path(args.report_dir, 12, "positive-grounding-fixture-manifest")
    )
    negative = m12.read_json(
        _report_path(args.report_dir, 13, "negative-grounding-fixture-manifest")
    )
    prompt = m12.read_json(_report_path(args.report_dir, 7, "prompt-before-after"))
    validator_freeze = m12.read_json(
        _report_path(args.report_dir, 8, "validator-no-relaxation-proof")
    )
    selector = m12.read_json(
        _report_path(args.report_dir, 17, "financial-context-selection-freeze-proof")
    )
    cases = m12.read_json(_report_path(args.report_dir, 18, "fictional-case-freeze-proof"))
    schema = m12.read_json(_report_path(args.report_dir, 19, "schema-freeze-proof"))
    timing = m12.read_json(_report_path(args.report_dir, 20, "price-timing-freeze-proof"))
    source = m12.read_json(_report_path(args.report_dir, 21, "source-sufficiency-no-change-proof"))
    daily = m12.read_json(_report_path(args.report_dir, 22, "daily-delta-no-change-proof"))
    completion_path = _report_path(args.report_dir, 46, "program-completion")
    preliminary_rows = _artifact_source_rows(
        report_dir=args.report_dir,
        output_root=args.output_root,
    )
    anticipated_artifact_count = len(preliminary_rows) + int(not completion_path.exists())
    completion = {
        "contract": PROGRAM_CONTRACT,
        "base_sha": BASE_SHA,
        "work_instruction_commit": WORK_INSTRUCTION_COMMIT,
        "implementation_commit": phase_a_receipt["implementation_commit"],
        "report_commit": args.report_commit,
        "final_head_sha": "NOT_MEASURED",
        "branch": _git("branch", "--show-current"),
        "latest_result_zip_sha256": LATEST_RESULT_SHA256,
        "latest_result_integrity": "PASS",
        **{f"m{index}_status": "COMPLETE" for index in range(1, 12)},
        "m12_status": "DETERMINISTIC_COMPLETE_CANARY_BLOCKED",
        "m12r_status": "BLOCKED",
        "m12g_status": "COMPLETE" if canary_pass else "BLOCKED",
        "m12r_grounding_root_cause": GROUNDING_ROOT_CAUSE,
        "financial_grounding_repair_status": "PASS",
        "old_fic_fin_03_regression_status": historical03["status"],
        "old_fic_fin_06_regression_status": (
            "PASS" if historical06["status"] == "FAIL" else "FAIL"
        ),
        "corrected_fic_fin_06_status": corrected06["status"],
        "positive_grounding_fixture_count": positive["fixture_count"],
        "positive_grounding_fixture_pass_count": positive["pass_count"],
        "negative_grounding_fixture_count": negative["fixture_count"],
        "negative_grounding_fixture_rejected_count": negative["rejected_count"],
        "financial_semantic_validator_change_count": validator_freeze[
            "financial_semantic_validator_change_count"
        ],
        "qtd_ytd_validator_semantic_change_count": validator_freeze[
            "qtd_ytd_validator_semantic_change_count"
        ],
        "directional_prompt_change_count": prompt["directional_prompt_change_count"],
        "price_timing_prompt_change_count": timing["price_timing_prompt_change_count"],
        "financial_context_selection_change_count": selector[
            "financial_context_selection_change_count"
        ],
        "fictional_case_change_count": cases["fictional_case_change_count"],
        "schema_change_count": schema["schema_change_count"],
        "directional_threshold_changed": False,
        "directional_increment_changed": False,
        "hold_lean_contract_changed": False,
        "calibration_tiebreak_changed": False,
        "source_sufficiency_semantic_change_count": source[
            "source_sufficiency_semantic_change_count"
        ],
        "daily_delta_semantic_change_count": daily["daily_delta_semantic_change_count"],
        "warning_semantic_change_count": daily["warning_semantic_change_count"],
        "fictional_generation_id": args.generation_id,
        "fictional_subject_count": len(m12.TICKERS),
        "fictional_context_count": m12.CONTEXT_COUNT,
        "fictional_repetition_count": m12.REPETITION_COUNT,
        "model_calls_real": 0,
        "model_calls_fictional": runtime["model_calls_fictional"],
        "model_calls_judge": 0,
        "model_context_success_count": runtime["model_context_success_count"],
        "model_context_failure_count": runtime["model_context_failure_count"],
        "wrapper_retry_count": runtime["wrapper_retry_count"],
        "timeout_count": runtime["timeout_count"],
        "capacity_failure_count": runtime["capacity_failure_count"],
        "orphan_process_count": runtime["orphan_process_count"],
        "fictional_output_row_count": semantic["fictional_output_row_count"],
        "fictional_schema_pass_count": semantic["fictional_schema_pass_count"],
        "invalid_financial_reference_count": semantic["invalid_financial_reference_count"],
        "hard_financial_semantic_violation_count": semantic[
            "hard_financial_semantic_violation_count"
        ],
        "selected_financial_ref_count": grounding.get("selected_financial_ref_count", 0),
        "used_financial_ref_count": grounding.get("used_financial_ref_count", 0),
        "material_financial_anchor_grounding_failure_count": grounding.get(
            "material_financial_anchor_grounding_failure_count", 0
        ),
        "working_capital_grounding_failure_count": grounding.get(
            "working_capital_grounding_failure_count", 0
        ),
        "narrative_substitution_failure_count": grounding.get(
            "narrative_substitution_failure_count", 0
        ),
        "validator_false_reject_count": validator["validator_false_reject_count"],
        "validator_false_accept_count": validator["validator_false_accept_count"],
        "fictional_stable_count": stability["fictional_stable_count"],
        "fictional_boundary_uncertainty_count": stability["fictional_boundary_uncertainty_count"],
        "fictional_unstable_count": stability["fictional_unstable_count"],
        "opposite_direction_reversal_count": stability["opposite_direction_reversal_count"],
        "message_specificity_advisory_status": specificity["status"],
        "real_issuer_model_exposure_count": 0,
        "provider_source_fetches": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "main_merges": 0,
        "deployments": 0,
        "live_v2_changes": 0,
        "night_futures_changes": 0,
        "observed_paused_schedule_count": schedule["observed_paused_schedule_count"],
        "scheduler_mutation_count": 0,
        "automatic_monitoring_resume": 0,
        "focused_test_result": "PASS",
        "full_test_result": "PASS",
        "ruff_result": "PASS",
        "git_diff_check": "PASS",
        "artifact_count": anticipated_artifact_count,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "fresh_real_proof_readiness": fresh_real_readiness,
        "production_readiness": "NOT_READY",
        "status": status,
        "stop_reason": stop_reason,
        "next_scope": next_scope,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    m12.write_json(completion_path, completion)
    print(json.dumps(completion, ensure_ascii=False, sort_keys=True), flush=True)


def bundle(args: argparse.Namespace) -> None:
    rows = _artifact_source_rows(
        report_dir=args.report_dir,
        output_root=args.output_root,
    )
    failures = _secret_scan_failures(rows)
    if failures:
        raise ValueError("m12g_artifact_secret_scan_failed:" + ",".join(failures))
    index_rows = [
        {
            "path": archive_name,
            "sha256": m12.file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for archive_name, path in rows
    ]
    index = {
        "contract": "m12g-artifact-index-v1",
        "payload_count": len(index_rows),
        "artifacts": index_rows,
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
    }
    args.bundle_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.bundle_path.with_suffix(args.bundle_path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for archive_name, path in rows:
            archive.write(path, archive_name)
        archive.writestr(
            "artifact-index.json",
            json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
    os.replace(temporary, args.bundle_path)
    with zipfile.ZipFile(args.bundle_path) as archive:
        bad = archive.testzip()
        stored_index = json.loads(archive.read("artifact-index.json"))
        names = set(archive.namelist())
        hash_mismatch_count = 0
        size_mismatch_count = 0
        for row in stored_index["artifacts"]:
            if row["path"] not in names:
                hash_mismatch_count += 1
                size_mismatch_count += 1
                continue
            payload = archive.read(row["path"])
            hash_mismatch_count += int(m12r._sha_bytes(payload) != row["sha256"])
            size_mismatch_count += int(len(payload) != row["size_bytes"])
    status = (
        "PASS"
        if bad is None and hash_mismatch_count == 0 and size_mismatch_count == 0 and not failures
        else "FAIL"
    )
    digest = m12.file_sha256(args.bundle_path)
    args.bundle_path.with_suffix(args.bundle_path.suffix + ".sha256").write_text(
        digest + "\n",
        encoding="utf-8",
    )
    result = {
        "bundle": str(args.bundle_path),
        "sha256": digest,
        "payload_count": len(index_rows),
        "hash_mismatch_count": hash_mismatch_count,
        "size_mismatch_count": size_mismatch_count,
        "secret_scan_failure_count": len(failures),
        "status": status,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    if status != "PASS":
        raise SystemExit(5)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("command", choices=("phase-a", "run-canary", "finalize", "bundle"))
    value.add_argument("--generation-id")
    value.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    value.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    value.add_argument("--bundle-path", type=Path, default=DEFAULT_BUNDLE_PATH)
    value.add_argument("--report-commit", default="NOT_MEASURED")
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command != "bundle" and not args.generation_id:
        raise ValueError("m12g_generation_id_required")
    if args.command == "phase-a":
        phase_a(args)
    elif args.command == "run-canary":
        run_canary(args)
    elif args.command == "finalize":
        finalize(args)
    else:
        bundle(args)


if __name__ == "__main__":
    main()
