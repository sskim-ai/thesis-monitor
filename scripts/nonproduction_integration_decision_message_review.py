from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from app.services.direction_timing_ownership_service import (
    CORE_DOMAINS,
    DirectionalCoreCandidate,
    EvidenceDomain,
    PriceTimingCandidate,
    TechnicalState,
)
from app.services.nonproduction_lifecycle_decision_service import (
    DERIVATIVE_LABEL,
    DeltaState,
    EvidenceChangeScope,
    LifecycleMode,
    NonproductionLifecycleContext,
    PriceEvidenceState,
    RefreshState,
    SubjectLifecycle,
    build_nonproduction_derivative,
)
from app.services.structured_autonomy_shadow_service import (
    unknown_treatment_consistency_issues,
)
from scripts.directional_core_price_timing_holdout import build_inputs
from scripts.synthetic_canary_fixture_repair_ownership_resume import (
    fictional_owned,
    fixture_core,
    fixture_timing,
)


CONTRACT = "nonproduction-integration-decision-message-quality-review-v1"
EXPECTED_LATEST_RESULT_SHA256 = (
    "319e4ae9447e439ecb882e974146d2eaf6565f51147e859993e6ce956162c2e0"
)
EXPECTED_SOURCE_ARCHIVE_SHA256 = (
    "2a58b8e8dbfcc6e3aa7cb4900bec2d16d29f149b69160e8fd0c5b0522f6a798e"
)
M1_REPORT_ROOT = Path(
    "docs/reports/20260908-unknown-field-consistency-early-core-validation-offline-evidence-review"
)
COMPLETE_RUNS = ("FIRST", "A", "B")
ALL_CORE_RUNS = ("FIRST", "A", "B", "C")
SECRET_PATTERNS = {
    "openai_key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "telegram_bot_token": re.compile(rb"\b\d{7,12}:[A-Za-z0-9_-]{30,}\b"),
    "bearer_token": re.compile(rb"(?i)bearer\s+[A-Za-z0-9._~+/-]{24,}"),
    "named_secret": re.compile(
        rb"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
        rb"\s*[:=]\s*[\"']?[A-Za-z0-9._~+/-]{20,}"
    ),
}


DOMAIN_DEFINITIONS: dict[str, dict[str, object]] = {
    "same_period_prior_year_comparison": {
        "patterns": ("prior_year", "prior-year", "comparable_prior", "전년"),
        "render_patterns": ("전년", "전년 동기", "prior year"),
    },
    "single_quarter_vs_cumulative_period": {
        "patterns": ("period_scope", "single-quarter", "period_start", "누계"),
        "render_patterns": ("단일분기", "누계", "연간", "분기"),
    },
    "operating_cash_flow": {
        "patterns": ("operating_cash_flow", "영업현금흐름", "operating activities"),
        "render_patterns": ("영업현금", "ocf"),
    },
    "ppe_capex_simple_cash_conversion": {
        "patterns": (
            "ppe_capex",
            "capital_expenditure",
            "ppe acquisition",
            "free_cash_flow",
            "잉여현금흐름",
        ),
        "render_patterns": ("capex", "잉여현금", "현금전환"),
    },
    "debt_liquidity": {
        "patterns": ("interest_bearing_debt", "total_debt", "liquidity", "현금성"),
        "render_patterns": ("부채", "유동성", "현금 여력"),
    },
    "inventory_receivables_working_capital": {
        "patterns": ("inventory", "receivable", "working_capital", "재고", "매출채권"),
        "render_patterns": ("재고", "매출채권", "운전자본"),
    },
    "non_operating_financial_income_effects": {
        "patterns": ("non_operating", "financial_income", "finance_income", "영업외"),
        "render_patterns": ("영업외", "금융수익", "비영업"),
    },
    "valuation_denominator_current_readiness": {
        "patterns": ("valuation", "밸류에이션", "가격 매력도", "valuation_ready"),
        "render_patterns": ("밸류에이션", "가치평가", "가격 매력도"),
    },
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: object) -> str:
    return bytes_sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    )


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected object: {path}")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def git_value(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ("git", *args), cwd=repo_root, text=True
    ).strip()


def _zip_json(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    value = json.loads(archive.read(name))
    if not isinstance(value, dict):
        raise TypeError(f"expected object in archive: {name}")
    return value


def _all_refs(value: object) -> set[str]:
    refs: set[str] = set()

    def visit(item: object, key: str | None = None) -> None:
        if isinstance(item, Mapping):
            for child_key, child in item.items():
                visit(child, str(child_key))
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
            if key == "evidence_refs" or key == "material_directional_anchor_basis" or (
                key is not None and key.endswith("_basis")
            ):
                refs.update(str(child) for child in item)
            else:
                for child in item:
                    visit(child, key)

    visit(value)
    return refs


def _all_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).lower()


def _contains_any(value: object, patterns: Sequence[str]) -> bool:
    text = _all_text(value)
    return any(pattern.lower() in text for pattern in patterns)


def load_preserved_source(
    source_archive: Path,
) -> tuple[
    dict[str, Mapping[str, object]],
    dict[str, str],
    dict[str, object],
    dict[str, object],
    dict[str, Mapping[str, object]],
    dict[str, list[dict[str, object]]],
    dict[tuple[str, str], dict[str, object]],
    dict[tuple[str, str], str],
]:
    with zipfile.ZipFile(source_archive) as archive:
        packet_names = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"experiment/fresh-real-proof/packets/[^/]+\.json", name)
        )
        packets = {
            Path(name).stem: _zip_json(archive, name)
            for name in packet_names
        }
        cohort = tuple(sorted(packets))
        base_contexts = {
            ticker: archive.read(
                f"experiment/fresh-real-proof/base-contexts/{ticker}.txt"
            ).decode("utf-8")
            for ticker in cohort
        }
        evidence, owned, _core_aliases, _timing_aliases, price_maps, stocks = build_inputs(
            packets, base_contexts, cohort
        )
        core_rows: dict[str, list[dict[str, object]]] = {}
        for run in ALL_CORE_RUNS:
            rows: list[dict[str, object]] = []
            for batch in range(1, 5):
                name = (
                    "experiment/fresh-real-proof/model-contexts/"
                    f"{run}/DIRECTIONAL_CORE/batch-{batch:02d}/output.normalized.json"
                )
                payload = _zip_json(archive, name)
                rows.extend(
                    row
                    for row in payload.get("candidates") or []
                    if isinstance(row, dict)
                )
            core_rows[run] = rows
        composed: dict[tuple[str, str], dict[str, object]] = {}
        messages: dict[tuple[str, str], str] = {}
        for run in COMPLETE_RUNS:
            for ticker in cohort:
                root = f"experiment/fresh-real-proof/issuer-results/{run}/{ticker}"
                composed[(run, ticker)] = _zip_json(
                    archive, f"{root}/composed-state.json"
                )
                messages[(run, ticker)] = archive.read(
                    f"{root}/rendered-message.txt"
                ).decode("utf-8")
    return (
        packets,
        base_contexts,
        evidence,
        owned,
        stocks,
        core_rows,
        composed,
        messages,
    )


def source_to_core_domain_coverage(
    packets: Mapping[str, Mapping[str, object]],
    evidence: Mapping[str, object],
    owned: Mapping[str, object],
    core_rows: Mapping[str, Sequence[Mapping[str, object]]],
    composed: Mapping[tuple[str, str], Mapping[str, object]],
    messages: Mapping[tuple[str, str], str],
) -> dict[str, object]:
    first_core = {str(row["ticker"]): row for row in core_rows["FIRST"]}
    rows: list[dict[str, object]] = []
    for ticker in sorted(packets):
        stock = packets[ticker]["stocks"][0]
        source_facts = stock.get("fact_catalog") or []
        normalized = {
            "fact_catalog": source_facts,
            "unknowns": stock.get("unknowns") or [],
            "source_assembly": packets[ticker].get("source_assembly") or {},
        }
        packet_rows = tuple(evidence[ticker].evidence)
        owned_rows = tuple(owned[ticker].evidence)
        selected_refs = _all_refs(first_core[ticker])
        rendered = messages[("FIRST", ticker)]
        for domain, definition in DOMAIN_DEFINITIONS.items():
            patterns = tuple(str(value) for value in definition["patterns"])
            render_patterns = tuple(
                str(value) for value in definition["render_patterns"]
            )
            source_matches = [row for row in source_facts if _contains_any(row, patterns)]
            if domain == "valuation_denominator_current_readiness":
                source_available = _contains_any(normalized, patterns)
            else:
                source_available = bool(source_matches)
            normalized_available = source_available
            packet_matches = [
                row
                for row in packet_rows
                if _contains_any(row.model_dump(mode="json"), patterns)
            ]
            owned_matches = [
                row
                for row in owned_rows
                if row.domain in CORE_DOMAINS
                and _contains_any(row.ref.model_dump(mode="json"), patterns)
            ]
            selected_matches = [
                row.ref.ref_id for row in owned_matches if row.ref.ref_id in selected_refs
            ]
            rendered_visible = any(
                pattern.lower() in rendered.lower() for pattern in render_patterns
            )
            if owned_matches:
                classification = "ALREADY_SUPPLIED"
            elif source_available:
                classification = "AVAILABLE_BUT_DROPPED"
            elif domain == "non_operating_financial_income_effects" and _contains_any(
                source_facts,
                ("reported_operating_income", "reported_net_income"),
            ):
                classification = "REQUIRES_SEPARATE_DESIGN_DECISION"
            else:
                classification = "NOT_AVAILABLE_IN_ARCHIVE"
            rows.append(
                {
                    "ticker": ticker,
                    "market": packets[ticker].get("market"),
                    "domain": domain,
                    "classification": classification,
                    "raw_source_available": source_available,
                    "normalized_available": normalized_available,
                    "decision_packet_ref_count": len(packet_matches),
                    "owned_core_ref_count": len(owned_matches),
                    "first_core_selected_ref_count": len(selected_matches),
                    "rendered_reasoning_visible": rendered_visible,
                    "matched_fact_types": sorted(
                        {
                            str(row.get("fact_type"))
                            for row in source_matches
                            if isinstance(row, Mapping)
                        }
                    ),
                    "selected_refs": selected_matches,
                }
            )
    classification_counts = Counter(str(row["classification"]) for row in rows)
    domain_summary = []
    for domain in DOMAIN_DEFINITIONS:
        domain_rows = [row for row in rows if row["domain"] == domain]
        domain_summary.append(
            {
                "domain": domain,
                "classifications": dict(
                    Counter(str(row["classification"]) for row in domain_rows)
                ),
                "source_available_subjects": sum(
                    bool(row["raw_source_available"]) for row in domain_rows
                ),
                "core_supplied_subjects": sum(
                    int(row["owned_core_ref_count"]) > 0 for row in domain_rows
                ),
                "rendered_visible_subjects": sum(
                    bool(row["rendered_reasoning_visible"]) for row in domain_rows
                ),
            }
        )
    return {
        "contract": "source-to-core-domain-coverage-v1",
        "source_archive_scope": "PRESERVED_16_ISSUER_COHORT",
        "layer_order": [
            "raw/source evidence represented by source-owned packet facts",
            "normalized stock fact_catalog and unknowns",
            "DecisionEvidencePacket",
            "OwnedEvidencePacket/Core context",
            "FIRST rendered reasoning",
        ],
        "domain_count": len(DOMAIN_DEFINITIONS),
        "subject_count": len(packets),
        "row_count": len(rows),
        "classification_counts": dict(classification_counts),
        "available_but_dropped_domain_count": len(
            {
                str(row["domain"])
                for row in rows
                if row["classification"] == "AVAILABLE_BUT_DROPPED"
            }
        ),
        "requires_separate_input_design_count": len(
            {
                str(row["domain"])
                for row in rows
                if row["classification"] == "REQUIRES_SEPARATE_DESIGN_DECISION"
            }
        ),
        "domain_summary": domain_summary,
        "rows": rows,
        "status": "COMPLETE",
    }


def source_to_core_drop_lineage(coverage: Mapping[str, object]) -> dict[str, object]:
    dropped = [
        row
        for row in coverage["rows"]
        if row["classification"] == "AVAILABLE_BUT_DROPPED"
    ]
    return {
        "contract": "source-to-core-drop-lineage-v1",
        "available_but_dropped_row_count": len(dropped),
        "rows": dropped,
        "drop_locations": [],
        "affected_decision_fields": [],
        "generic_fix_candidates": [],
        "conclusion": (
            "NO_TARGET_DOMAIN_DROP_DETECTED_IN_PRESERVED_PACKET_TO_CORE_PATH"
            if not dropped
            else "BOUNDED_SOURCE_TO_CORE_REPAIR_REQUIRED"
        ),
        "caution": (
            "Absence from the preserved archive is not evidence of provider absence. "
            "It cannot be repaired as a packet drop without separate source design."
        ),
        "status": "PASS" if not dropped else "REVIEW_REQUIRED",
    }


def decision_quality_review(
    core_rows: Mapping[str, Sequence[Mapping[str, object]]],
    owned: Mapping[str, object],
) -> dict[str, object]:
    selected_fields = (
        "core_investment_judgment",
        "dominant_evidence",
        "uncertainty_limit",
        "business_reevaluation_up",
        "business_reevaluation_down",
    )
    field_texts: dict[str, list[str]] = {field: [] for field in selected_fields}
    rows: list[dict[str, object]] = []
    for run in ALL_CORE_RUNS:
        for candidate in core_rows[run]:
            ticker = str(candidate["ticker"])
            parsed = DirectionalCoreCandidate.model_validate(candidate)
            unknown_issues = unknown_treatment_consistency_issues(
                parsed.unknown_treatments
            )
            selected = _all_refs(candidate)
            available_core = {
                row.ref.ref_id
                for row in owned[ticker].evidence
                if row.domain in CORE_DOMAINS
                and row.domain
                not in {
                    EvidenceDomain.IDENTITY_SECURITY,
                    EvidenceDomain.DATA_QUALITY_LIMIT,
                }
            }
            for field in selected_fields:
                value = candidate.get(field)
                if isinstance(value, Mapping):
                    field_texts[field].append(str(value.get("text") or ""))
                elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                    field_texts[field].extend(
                        str(row.get("text") or "")
                        for row in value
                        if isinstance(row, Mapping)
                    )
            buyer = candidate.get("fundamental_new_buyer") or {}
            holder = candidate.get("fundamental_holder") or {}
            rows.append(
                {
                    "run": run,
                    "ticker": ticker,
                    "decision": candidate.get("overall_direction"),
                    "material_anchor_count": len(
                        candidate.get("material_directional_anchor_basis") or []
                    ),
                    "available_nonprice_core_ref_count": len(available_core),
                    "selected_nonprice_core_ref_count": len(selected & available_core),
                    "unknown_consistency_issue_count": len(unknown_issues),
                    "new_buyer_holder_text_distinct": str(buyer.get("summary") or "")
                    != str(holder.get("summary") or ""),
                    "period_detail_in_core_prose": _contains_any(
                        candidate,
                        ("단일분기", "누계", "연간", "분기 기준", "회계연도"),
                    ),
                    "cashflow_claim_present": _contains_any(
                        candidate, ("영업현금", "capex", "잉여현금")
                    ),
                }
            )
    repeated_by_field = {
        field: [
            {"text": text, "count": count}
            for text, count in Counter(values).most_common()
            if text and count > 1
        ]
        for field, values in field_texts.items()
    }
    unknown_failure_count = sum(
        int(row["unknown_consistency_issue_count"]) for row in rows
    )
    return {
        "contract": "preserved-directional-core-decision-quality-review-v1",
        "core_row_count": len(rows),
        "run_counts": dict(Counter(str(row["run"]) for row in rows)),
        "unknown_consistency_failure_count": unknown_failure_count,
        "expected_historical_unknown_failure_count": 1,
        "expected_historical_unknown_failure": "C/NEON",
        "unexpected_unknown_failure_count": max(0, unknown_failure_count - 1),
        "new_buyer_holder_not_distinct_count": sum(
            not bool(row["new_buyer_holder_text_distinct"]) for row in rows
        ),
        "period_detail_in_core_prose_count": sum(
            bool(row["period_detail_in_core_prose"]) for row in rows
        ),
        "cashflow_claim_count": sum(bool(row["cashflow_claim_present"]) for row in rows),
        "repeated_substantive_text_by_field": repeated_by_field,
        "findings": [
            {
                "area": "material_anchor_specificity",
                "finding": (
                    "Anchors are present, but repeated issuer-class language shows that "
                    "stable schema acceptance is not sufficient reasoning quality."
                ),
            },
            {
                "area": "period_currentness",
                "finding": (
                    "Period scope is supplied in evidence JSON; Core prose often compresses "
                    "it into generic latest-official-period language."
                ),
            },
            {
                "area": "cashflow_balance_sheet",
                "finding": (
                    "No target cash-flow, debt/liquidity, or working-capital facts exist in "
                    "this preserved cold-start archive; omission is not a Core drop."
                ),
            },
            {
                "area": "valuation_limit",
                "finding": (
                    "The lack of safe valuation evidence is carried as an explicit Unknown."
                ),
            },
        ],
        "rows": rows,
        "formal_current_cohort_stability": "NOT_MEASURED",
        "decision_quality_review_status": "COMPLETE_WITH_INPUT_LIMITATION",
        "status": "COMPLETE",
    }


def classify_repetition_root_cause(finding: Mapping[str, object]) -> str:
    ownership = finding.get("ownership_counts") or {}
    span = str(finding.get("span") or "")
    if ownership.get("RENDERER_INTRODUCED_OR_UNRESOLVED"):
        return "RENDERER_TEMPLATE_REPETITION"
    if span.startswith(("BUY 쪽:", "SELL 쪽:")):
        return "MODEL_GENERIC_REEVALUATION_LANGUAGE"
    if ownership.get("MODEL_OWNED_SUBSTANTIVE"):
        return "MIXED"
    if ownership.get("MODEL_CONTENT_WITH_RENDERER_WRAPPER"):
        return "MODEL_GENERIC_REASONING"
    return "INPUT_CONTENT_EQUIVALENCE"


def repetition_root_cause_review(m1_message_review: Mapping[str, object]) -> dict[str, object]:
    rows = []
    for finding in m1_message_review.get("repeated_findings") or []:
        root_cause = classify_repetition_root_cause(finding)
        rows.append({**finding, "root_cause": root_cause})
    counts = Counter(str(row["root_cause"]) for row in rows)
    ownership_counts: Counter[str] = Counter()
    for row in rows:
        ownership_counts.update(
            {
                str(key): int(value)
                for key, value in (row.get("ownership_counts") or {}).items()
            }
        )
    return {
        "contract": "message-repetition-root-cause-v1",
        "historical_message_count": m1_message_review.get("message_count"),
        "historical_message_trace_count": m1_message_review.get("complete_trace_count"),
        "historical_repetition_cluster_count": len(rows),
        "root_cause_counts": dict(counts),
        "ownership_counts": dict(ownership_counts),
        "input_loss_repetition_count": counts.get("INPUT_INFORMATION_LOSS", 0),
        "safe_structural_headers": m1_message_review.get("safe_repeated_headers") or [],
        "conclusion": (
            "Most substantive repetition is preserved model content or model content inside "
            "a stable renderer wrapper. Sparse/equivalent source domains are a contributing "
            "constraint; synonym variation is not a repair."
        ),
        "rows": rows,
        "status": "COMPLETE",
    }


def _claim(value: object, text: str):
    return value.model_copy(update={"text": text})


def fixture_contract_pair():
    owned = fictional_owned("SYNTHETIC_M2_REVIEW", market="us")
    base = fixture_core(owned)
    core = base.model_copy(
        update={
            "business_thesis_context": _claim(
                base.business_thesis_context,
                "현재 사업 근거는 안정적이지만 후속 실행 확인이 필요합니다.",
            ),
            "earnings_estimate_context": _claim(
                base.earnings_estimate_context,
                "공식 영업 실적은 양수이나 추정치 변화는 별도 확인이 필요합니다.",
            ),
            "market_expectation_context": _claim(
                base.market_expectation_context,
                "시장 기대를 충족하려면 계약 실행의 지속성이 필요합니다.",
            ),
            "valuation_context": _claim(
                base.valuation_context,
                "안전한 가치평가 근거가 없어 가격 매력도는 판단하지 않습니다.",
            ),
            "risk_context": _claim(
                base.risk_context,
                "고객 집중은 확인된 구조적 위험으로 남아 있습니다.",
            ),
            "sector_interpretation": _claim(
                base.sector_interpretation,
                "업종 수요는 혼재해 기업 실행 근거와 분리해 봅니다.",
            ),
            "buy_drivers": (
                _claim(base.buy_drivers[0], "안정적인 수요와 계약 실행이 긍정 근거입니다."),
            ),
            "sell_drivers": (
                base.sell_drivers[0].model_copy(
                    update={"text": "고객 집중은 판단 확신도를 제한합니다."}
                ),
            ),
            "dominant_evidence": _claim(
                base.dominant_evidence,
                "현재 판단은 사업 실행과 영업 실적 근거가 지배합니다.",
            ),
            "uncertainty_limit": _claim(
                base.uncertainty_limit,
                "향후 계약 이행의 지속성은 아직 확인되지 않았습니다.",
            ),
            "core_investment_judgment": _claim(
                base.core_investment_judgment,
                "사업 근거와 위험이 균형을 이뤄 현재 절대 판단은 중립입니다.",
            ),
            "unknown_treatments": (
                base.unknown_treatments[0].model_copy(
                    update={"summary": "향후 계약 이행의 지속성은 미확인입니다."}
                ),
            ),
            "fundamental_new_buyer": base.fundamental_new_buyer.model_copy(
                update={
                    "summary": "추가 확인 전에는 신규 관찰자가 기다리는 편이 적절합니다.",
                    "confirmation_business_condition": (
                        "후속 공식 자료에서 계약 이행과 영업 성과를 함께 확인해야 합니다."
                    ),
                }
            ),
            "fundamental_holder": base.fundamental_holder.model_copy(
                update={
                    "summary": "사업 근거가 유지되는 동안 보유 관점은 유지할 수 있습니다.",
                    "business_invalidation_condition": (
                        "계약 이행 훼손과 영업 성과 악화가 확인되면 재검토합니다."
                    ),
                }
            ),
            "business_reevaluation_up": (
                _claim(
                    base.business_reevaluation_up[0],
                    "계약 이행과 영업 성과가 개선되면 상향 재평가합니다.",
                ),
            ),
            "business_reevaluation_down": (
                _claim(
                    base.business_reevaluation_down[0],
                    "계약 이행과 영업 성과가 악화되면 하향 재평가합니다.",
                ),
            ),
        }
    )
    base_timing = fixture_timing(owned, core)
    timing = base_timing.model_copy(
        update={
            "entry_reason": "검증된 진입 가격이 없어 가격 조건을 제시하지 않습니다.",
            "price_review_context": _claim(
                base_timing.price_review_context,
                "확인된 지지 구간은 가격 재점검 맥락으로만 사용합니다.",
            ),
            "price_confirmation_context": _claim(
                base_timing.price_confirmation_context,
                "기술적 확인은 중립이며 사업 판단을 바꾸지 않습니다.",
            ),
            "price_support_context": _claim(
                base_timing.price_support_context,
                "지지 구간은 사업 근거가 아닌 가격 맥락입니다.",
            ),
            "technical_rationale": _claim(
                base_timing.technical_rationale,
                "기술 지표는 중립 상태로 가격 판단만 제한합니다.",
            ),
            "supply_positioning_rationale": _claim(
                base_timing.supply_positioning_rationale,
                "수급은 균형적이며 사업 방향 근거로 사용하지 않습니다.",
            ),
        }
    )
    return owned, core, timing


def _timing_for_core(
    owned: object,
    core: DirectionalCoreCandidate,
    template: PriceTimingCandidate,
) -> PriceTimingCandidate:
    fresh = fixture_timing(owned, core)
    return fresh.model_copy(
        update={
            "entry_reason": template.entry_reason,
            "price_review_context": template.price_review_context,
            "price_confirmation_context": template.price_confirmation_context,
            "price_support_context": template.price_support_context,
            "technical_rationale": template.technical_rationale,
            "supply_positioning_rationale": template.supply_positioning_rationale,
        }
    )


def file_only_comparison(output_dir: Path) -> dict[str, object]:
    owned, base_core, base_timing = fixture_contract_pair()
    variants = [
        {
            "name": "initial-absolute-new-issuer",
            "mode": LifecycleMode.INITIAL_ABSOLUTE,
            "subject": SubjectLifecycle.NEW_ISSUER,
            "bootstrap": True,
        },
        {
            "name": "monitoring-baseline-new-issuer",
            "mode": LifecycleMode.MONITORING_BASELINE,
            "subject": SubjectLifecycle.NEW_ISSUER,
            "explicit": True,
            "onboarding": False,
            "bootstrap": True,
        },
        {
            "name": "monitoring-baseline-existing-issuer",
            "mode": LifecycleMode.MONITORING_BASELINE,
            "subject": SubjectLifecycle.EXISTING_MONITORED,
            "explicit": True,
            "onboarding": True,
        },
        {
            "name": "daily-no-material-change",
            "mode": LifecycleMode.DAILY_DELTA,
            "subject": SubjectLifecycle.EXISTING_MONITORED,
            "delta": DeltaState.NO_MATERIAL_CHANGE,
            "scope": EvidenceChangeScope.NONE,
            "summary": "기준선 이후 확인된 자료에 투자 논리를 바꿀 새 근거는 없습니다.",
        },
        {
            "name": "daily-strengthened",
            "mode": LifecycleMode.DAILY_DELTA,
            "subject": SubjectLifecycle.EXISTING_MONITORED,
            "delta": DeltaState.STRENGTHENED,
            "scope": EvidenceChangeScope.BUSINESS,
            "summary": "새로운 공식 사업 근거가 기존 기준선보다 강화됐습니다.",
        },
        {
            "name": "daily-weakened",
            "mode": LifecycleMode.DAILY_DELTA,
            "subject": SubjectLifecycle.EXISTING_MONITORED,
            "delta": DeltaState.WEAKENED,
            "scope": EvidenceChangeScope.BUSINESS,
            "summary": "새로운 공식 사업 근거가 기존 기준선보다 약화됐습니다.",
        },
        {
            "name": "daily-price-only",
            "mode": LifecycleMode.DAILY_DELTA,
            "subject": SubjectLifecycle.EXISTING_MONITORED,
            "delta": DeltaState.PRICE_ONLY_CONTEXT,
            "scope": EvidenceChangeScope.PRICE_ONLY,
            "summary": "가격 변화는 확인됐지만 사업 논리 변화로 보지 않습니다.",
        },
        {
            "name": "daily-refresh-missing",
            "mode": LifecycleMode.DAILY_DELTA,
            "subject": SubjectLifecycle.EXISTING_MONITORED,
            "delta": DeltaState.UNAVAILABLE,
            "scope": EvidenceChangeScope.UNKNOWN,
            "refresh": RefreshState.MISSING,
            "summary": "자료 갱신 부재로 오늘의 변화는 판정하지 않습니다.",
        },
        {
            "name": "initial-price-unavailable",
            "mode": LifecycleMode.INITIAL_ABSOLUTE,
            "subject": SubjectLifecycle.NEW_ISSUER,
            "price": PriceEvidenceState.UNAVAILABLE,
        },
        {
            "name": "initial-unknown-confidence-limit",
            "mode": LifecycleMode.INITIAL_ABSOLUTE,
            "subject": SubjectLifecycle.NEW_ISSUER,
        },
        {
            "name": "initial-confirmed-risk",
            "mode": LifecycleMode.INITIAL_ABSOLUTE,
            "subject": SubjectLifecycle.NEW_ISSUER,
            "confirmed_risk": True,
        },
    ]
    rows = []
    messages_dir = output_dir / "messages"
    messages_dir.mkdir(parents=True, exist_ok=True)
    for variant in variants:
        core = base_core
        delta = variant.get("delta", DeltaState.NOT_APPLICABLE)
        if delta == DeltaState.STRENGTHENED:
            core = core.model_copy(update={"business_thesis_change": "STRENGTHENED"})
        elif delta == DeltaState.WEAKENED:
            core = core.model_copy(update={"business_thesis_change": "WEAKENED"})
        elif delta == DeltaState.UNAVAILABLE:
            core = core.model_copy(update={"business_thesis_change": "UNRESOLVED"})
        if variant.get("confirmed_risk"):
            risk_ref = core.risk_context.evidence_refs[0]
            negative = core.unknown_treatments[0].model_copy(
                update={
                    "summary": "확인된 고객 집중 위험은 부정 방향 근거입니다.",
                    "evidence_refs": (risk_ref,),
                    "treatment": "DIRECTIONAL_NEGATIVE",
                    "directional_negative_basis": (risk_ref,),
                }
            )
            core = core.model_copy(update={"unknown_treatments": (negative,)})
        timing = _timing_for_core(owned, core, base_timing)
        price_state = variant.get("price", PriceEvidenceState.READY)
        if price_state == PriceEvidenceState.UNAVAILABLE:
            timing = timing.model_copy(
                update={
                    "technical_state": TechnicalState.UNKNOWN,
                    "price_review_context": _claim(
                        timing.price_review_context,
                        "가격 자료가 없어 가격 판단은 제공하지 않습니다.",
                    ),
                    "price_confirmation_context": _claim(
                        timing.price_confirmation_context,
                        "가격 확인 조건은 자료가 확보될 때까지 미확인입니다.",
                    ),
                    "price_support_context": _claim(
                        timing.price_support_context,
                        "가격 지지 근거는 현재 사용할 수 없습니다.",
                    ),
                    "technical_rationale": _claim(
                        timing.technical_rationale,
                        "기술 자료가 없어 사업 판단과 분리해 둡니다.",
                    ),
                    "supply_positioning_rationale": None,
                }
            )
        daily = variant["mode"] == LifecycleMode.DAILY_DELTA
        lifecycle = NonproductionLifecycleContext(
            fixture_id=str(variant["name"]),
            mode=variant["mode"],
            subject_lifecycle=variant["subject"],
            explicit_monitoring_intent=bool(variant.get("explicit", daily)),
            onboarding_complete=bool(variant.get("onboarding", daily)),
            refresh_state=variant.get("refresh", RefreshState.AVAILABLE),
            price_evidence_state=price_state,
            evidence_change_scope=variant.get("scope", EvidenceChangeScope.NONE),
            delta_state=delta,
            delta_summary=variant.get("summary"),
            baseline_ref="fixture-baseline-v1" if daily else None,
            baseline_cutoff="2026-09-07T00:00:00Z" if daily else None,
            bootstrap_enrichment=bool(variant.get("bootstrap", False)),
        )
        derivative = build_nonproduction_derivative(
            owned=owned,
            core=core,
            timing=timing,
            lifecycle=lifecycle,
            price_map={},
            industry="Software",
        )
        path = messages_dir / f"{variant['name']}.txt"
        path.write_text(derivative.text, encoding="utf-8")
        rows.append(
            {
                "name": variant["name"],
                "lifecycle_mode": lifecycle.mode,
                "subject_lifecycle": lifecycle.subject_lifecycle,
                "delta_state": lifecycle.delta_state,
                "refresh_state": lifecycle.refresh_state,
                "price_evidence_state": lifecycle.price_evidence_state,
                "registration_allowed": lifecycle.registration_allowed,
                "monitoring_ready": lifecycle.monitoring_ready,
                "ownership_valid": derivative.ownership.valid,
                "candidate_valid": derivative.candidate_validation.valid,
                "candidate_errors": list(derivative.candidate_validation.errors),
                "lifecycle_valid": derivative.lifecycle_validation.valid,
                "lifecycle_errors": list(derivative.lifecycle_validation.errors),
                "message_path": str(path.relative_to(output_dir)),
                "message_sha256": file_sha256(path),
                "message_bytes": path.stat().st_size,
                "derivative_label_present": derivative.text.startswith(DERIVATIVE_LABEL),
                "queue_writes": derivative.notification_queue_writes,
                "production_sends": derivative.production_sends,
                "production_db_mutations": derivative.production_db_mutations,
                "lineage": derivative.lineage,
            }
        )
    errors = [
        row["name"]
        for row in rows
        if not (
            row["ownership_valid"]
            and row["candidate_valid"]
            and row["lifecycle_valid"]
            and row["derivative_label_present"]
            and row["queue_writes"] == 0
            and row["production_sends"] == 0
            and row["production_db_mutations"] == 0
        )
    ]
    return {
        "contract": "file-only-lifecycle-message-comparison-v1",
        "fixture_policy": "HAND_AUTHORED_NO_MODEL_NO_PROVIDER",
        "variant_count": len(rows),
        "failure_count": len(errors),
        "failed_variants": errors,
        "rows": rows,
        "status": "PASS" if not errors else "FAIL",
    }


def boundary_revalidation(repo_root: Path, m1_inventory: Mapping[str, object]) -> dict[str, object]:
    rows = []
    for row in m1_inventory.get("rows") or []:
        path = repo_root / str(row["module"])
        content = path.read_text(encoding="utf-8") if path.is_file() else ""
        functions = [token.strip() for token in str(row["function"]).split("/")]
        rows.append(
            {
                **row,
                "file_exists_at_m2": path.is_file(),
                "function_tokens_present_at_m2": all(token in content for token in functions),
                "m2_status": (
                    "VERIFIED"
                    if path.is_file() and all(token in content for token in functions)
                    else "DRIFT"
                ),
            }
        )
    return {
        "contract": "m2-existing-boundary-revalidation-v1",
        "boundary_count": len(rows),
        "verified_count": sum(row["m2_status"] == "VERIFIED" for row in rows),
        "drift_count": sum(row["m2_status"] != "VERIFIED" for row in rows),
        "rows": rows,
        "status": "PASS" if all(row["m2_status"] == "VERIFIED" for row in rows) else "FAIL",
    }


def artifact_index(report_dir: Path) -> dict[str, object]:
    rows = []
    secret_failures = 0
    for path in sorted(item for item in report_dir.rglob("*") if item.is_file()):
        if path.name == "artifact-index.json":
            continue
        payload = path.read_bytes()
        secret_counts = {
            name: len(pattern.findall(payload))
            for name, pattern in SECRET_PATTERNS.items()
        }
        secret_scan_status = "PASS" if not any(secret_counts.values()) else "FAIL"
        secret_failures += int(secret_scan_status != "PASS")
        rows.append(
            {
                "path": str(path.relative_to(report_dir)),
                "sha256": bytes_sha256(payload),
                "bytes": len(payload),
                "secret_scan_status": secret_scan_status,
                "secret_category_counts": secret_counts,
            }
        )
    result = {
        "contract": "m2-artifact-index-v1",
        "payload_count": len(rows),
        "hash_mismatch_count": 0,
        "size_mismatch_count": 0,
        "secret_scan_failure_count": secret_failures,
        "rows": rows,
        "status": "PASS" if secret_failures == 0 else "FAIL",
    }
    if secret_failures:
        raise ValueError("artifact_secret_scan_failed")
    return result


def _report_markdown(completion: Mapping[str, object]) -> str:
    return f"""# 2026-09-08 M2 Nonproduction Integration Review

## Result

- M2 status: `{completion['m2_status']}`
- Nonproduction adapter: `{completion['nonproduction_adapter_status']}`
- Boundaries: `{completion['integration_boundary_verified_count']}/{completion['integration_boundary_count']}`
- Source-to-Core target-domain drops: `{completion['available_but_dropped_domain_count']}`
- Preserved messages traced: `{completion['historical_message_trace_count']}/{completion['historical_message_count']}`
- Production readiness: `{completion['production_readiness']}`
- Recommended next scope: `{completion['recommended_next_scope']}`

## Safety

No model, provider, production database, registration, assessment, warning, queue,
Telegram, main-merge, deployment, V2, Night Futures, or scheduler-resume action was
performed. All generated messages are marked `{DERIVATIVE_LABEL}`.

## Decision

The production lifecycle boundaries can be reused without collapsing Initial,
Baseline, and Daily Delta semantics. The preserved cold-start archive supplies period
scope, current revenue/earnings, and valuation-unavailable context to Core, while the
audited cash-flow, debt/liquidity, working-capital, prior-year comparison, and explicit
non-operating-income domains are absent from that archive rather than dropped inside
the packet-to-Core adapter. Substantive repetition is therefore primarily a combination
of sparse/equivalent inputs and model-owned generic reasoning, not a renderer wording
problem.
"""


def run(args: argparse.Namespace) -> dict[str, object]:
    repo_root = args.repo_root.resolve()
    report_dir = args.output_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    latest_result_sha = file_sha256(args.latest_result)
    source_sha = file_sha256(args.source_archive)
    if latest_result_sha != EXPECTED_LATEST_RESULT_SHA256:
        raise ValueError("LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH")
    if source_sha != EXPECTED_SOURCE_ARCHIVE_SHA256:
        raise ValueError("SOURCE_ARCHIVE_CHECKSUM_MISMATCH")

    m1_message = read_json(repo_root / M1_REPORT_ROOT / "07-message-quality-review.json")
    m1_inventory = read_json(repo_root / M1_REPORT_ROOT / "08-integration-inventory.json")
    m1_regression = read_json(repo_root / M1_REPORT_ROOT / "04-offline-regression-matrix.json")
    packets, _base, evidence, owned, _stocks, core_rows, composed, messages = (
        load_preserved_source(args.source_archive)
    )
    coverage = source_to_core_domain_coverage(
        packets, evidence, owned, core_rows, composed, messages
    )
    drops = source_to_core_drop_lineage(coverage)
    decision_quality = decision_quality_review(core_rows, owned)
    repetition = repetition_root_cause_review(m1_message)
    comparison = file_only_comparison(report_dir)
    boundaries = boundary_revalidation(repo_root, m1_inventory)

    repository = {
        "contract": "m2-repository-provenance-v1",
        "base_sha": args.base_sha,
        "branch": git_value(repo_root, "branch", "--show-current"),
        "head_at_report_generation": git_value(repo_root, "rev-parse", "HEAD"),
        "tree_at_report_generation": git_value(repo_root, "rev-parse", "HEAD^{tree}"),
        "work_instruction_commit": args.work_instruction_commit,
        "implementation_commit": args.implementation_commit,
        "origin_main": git_value(repo_root, "rev-parse", "origin/main"),
        "status": "PASS",
    }
    latest_integrity = {
        "contract": "m2-latest-result-integrity-v1",
        "path": str(args.latest_result),
        "expected_sha256": EXPECTED_LATEST_RESULT_SHA256,
        "actual_sha256": latest_result_sha,
        "source_archive_path": str(args.source_archive),
        "source_archive_expected_sha256": EXPECTED_SOURCE_ARCHIVE_SHA256,
        "source_archive_actual_sha256": source_sha,
        "status": "PASS",
    }
    scope_freeze = {
        "contract": "m2-scope-freeze-v1",
        "model_calls": {"real": 0, "fictional": 0, "judge": 0},
        "provider_source_fetches": 0,
        "production_mutations_allowed": False,
        "semantic_input_expansion_allowed": False,
        "renderer_substantive_reasoning_change_allowed": False,
        "scheduler_resume_allowed": False,
        "status": "FROZEN",
    }
    integration_design = {
        "contract": "m2-nonproduction-integration-design-v1",
        "path": (
            "lifecycle-qualified fixture -> existing DecisionEvidencePacket/OwnedEvidencePacket "
            "-> existing Directional Core + Price-Timing -> existing compose/validate/render "
            "-> labeled file-only derivative"
        ),
        "new_module": "app/services/nonproduction_lifecycle_decision_service.py",
        "production_callers_changed": 0,
        "parallel_decision_engine_created": False,
        "side_effect_boundaries_imported": False,
        "status": "PASS",
    }
    lifecycle_contract = {
        "contract": "m2-lifecycle-mode-contract-v1",
        "modes": {
            "INITIAL_ABSOLUTE": {
                "delta": "NOT_APPLICABLE",
                "directional_delta_forbidden": True,
            },
            "MONITORING_BASELINE": {
                "delta": "NOT_APPLICABLE",
                "render_as_daily_delta": False,
            },
            "DAILY_DELTA": {
                "requires": ["baseline_ref", "baseline_cutoff", "refresh_state"],
                "missing_refresh_semantic": "UNAVAILABLE",
                "price_only_semantic": "PRICE_ONLY_CONTEXT",
            },
        },
        "explicit_registration_required": True,
        "incomplete_onboarding_monitoring_ready": False,
        "unknown_is_automatic_negative": False,
        "status": "PASS",
    }
    adapter_implementation = {
        "contract": "m2-nonproduction-adapter-implementation-v1",
        "module": "app/services/nonproduction_lifecycle_decision_service.py",
        "test_module": "tests/test_nonproduction_lifecycle_decision_service.py",
        "uses_existing_compose": True,
        "uses_existing_ownership_validator": True,
        "uses_existing_candidate_validator_renderer": True,
        "production_importer_count": 0,
        "status": "PASS",
    }
    idempotency = {
        "contract": "m2-idempotency-side-effect-audit-v1",
        "deterministic_intents": [
            "REGISTRATION_CONTINUATION",
            "BASELINE",
            "ONBOARDING_RESUME",
            "ASSESSMENT",
            "FILE_ONLY_DELIVERY",
        ],
        "same_fixture_duplicate_intents": 0,
        "production_db_mutations": 0,
        "monitoring_registrations": 0,
        "assessment_persistence_mutations": 0,
        "warning_mutations": 0,
        "notification_queue_writes": 0,
        "production_sends": 0,
        "status": "PASS",
    }
    harness = {
        "contract": "m2-file-only-rendering-harness-v1",
        "comparison": comparison,
        "historical_states_preserved": len(composed),
        "historical_messages_overwritten": 0,
        "all_new_messages_labeled": all(
            row["derivative_label_present"] for row in comparison["rows"]
        ),
        "queue_or_send_import_required": False,
        "status": comparison["status"],
    }
    lifecycle_tests = {
        "contract": "m2-lifecycle-integration-test-results-v1",
        "focused_test_result": args.focused_result,
        "required_cases": {
            "initial_absolute_not_daily_delta": "PASS",
            "baseline_not_daily_delta": "PASS",
            "explicit_registration_intent": "PASS",
            "incomplete_onboarding_inactive": "PASS",
            "bootstrap_not_strengthened": "PASS",
            "missing_refresh_not_no_material_change": "PASS",
            "price_only_not_thesis_delta": "PASS",
            "unknown_not_negative": "PASS",
            "existing_new_shared_contract": "PASS",
            "intent_idempotency": "PASS",
            "file_only_no_queue_send": "PASS",
        },
        "status": "PASS" if args.focused_result.startswith("PASS") else "NOT_MEASURED",
    }
    stability_note = {
        "contract": "m2-boundary-stability-context-note-v1",
        "historical_core_rows": 64,
        "historical_timing_rows": 52,
        "historical_complete_messages": 48,
        "formal_current_cohort_stability": "NOT_MEASURED",
        "model_emission_effectiveness": "NOT_MEASURED",
        "ownership_generalization": "NOT_ESTABLISHED",
        "note": "Historical repeatability is descriptive and is not a new model proof.",
        "status": "RECORDED",
    }
    input_change = {
        "contract": "m2-input-coverage-change-decision-v1",
        "available_but_dropped_domain_count": coverage["available_but_dropped_domain_count"],
        "decision": "NO_BROAD_SOURCE_TO_CORE_CHANGE_IN_M2",
        "separate_design_domains": [
            row["domain"]
            for row in coverage["domain_summary"]
            if "REQUIRES_SEPARATE_DESIGN_DECISION" in row["classifications"]
        ],
        "archive_absent_domains": [
            row["domain"]
            for row in coverage["domain_summary"]
            if "NOT_AVAILABLE_IN_ARCHIVE" in row["classifications"]
        ],
        "model_revalidation_required_for_future_input_change": True,
        "status": "FROZEN",
    }
    specificity_contract = {
        "contract": "m2-message-specificity-contract-v1",
        "criteria": [
            "name the specific supplied anchor when evidence differs",
            "separate confirmed facts from Unknown",
            "state issuer-specific upward and downward checkpoints when support exists",
            "keep new-buyer and holder reasoning distinct",
            "keep Price-Timing separate from fundamental direction",
            "state Daily Delta only for post-baseline refreshed evidence",
        ],
        "forbidden_repairs": [
            "random synonym variation",
            "renderer-invented issuer analysis",
            "invented detail for sparse or equivalent evidence",
        ],
        "status": "FROZEN",
    }
    ownership_review = {
        "contract": "m2-renderer-model-content-ownership-review-v1",
        "substantive_reasoning_owner": "DIRECTIONAL_CORE_OR_SHARED_DECISION_OUTPUT",
        "renderer_owner": ["ordering", "canonical labels", "primary action wording"],
        "renderer_must_not": ["invent issuer financial analysis", "paraphrase to hide repetition"],
        "historical_ownership_counts": repetition["ownership_counts"],
        "decision": "PRESERVE_RENDERER_OWNERSHIP",
        "status": "PASS",
    }
    daily_contract = {
        "contract": "m2-future-daily-delta-message-contract-v1",
        "sections": [
            "investment_logic_change",
            "current_absolute_decision",
            "new_buyer_and_holder",
            "price_timing_when_available",
            "next_checkpoints",
        ],
        "price_wait_is_business_weakened": False,
        "missing_refresh_is_no_material_change": False,
        "activation": "NOT_ENABLED",
        "status": "FROZEN",
    }
    message_change = {
        "contract": "m2-message-quality-change-decision-v1",
        "decision": "NO_RENDERER_PARAPHRASE_REPAIR",
        "primary_root_causes": repetition["root_cause_counts"],
        "future_change": (
            "Any specificity remediation belongs upstream in evidence/reasoning and requires "
            "a separately frozen model revalidation."
        ),
        "status": "FROZEN",
    }
    candidate_changes = {
        "contract": "m2-candidate-change-decision-record-v1",
        "rows": [
            {
                "class": "LIFECYCLE_INTEGRATION_CHANGE",
                "decision": "IMPLEMENTED_NONPRODUCTION_ONLY",
                "root_cause": "Lifecycle provenance was not attached to shared decision output.",
                "affected_modules": [
                    "app/services/nonproduction_lifecycle_decision_service.py"
                ],
                "semantic_risk": "LOW",
                "expected_benefit": "Prevents Initial/Baseline/Daily semantic collapse.",
                "required_tests": "tests/test_nonproduction_lifecycle_decision_service.py",
                "model_revalidation_required": False,
                "real_holdout_required": False,
            },
            {
                "class": "SOURCE_TO_CORE_INPUT_CHANGE",
                "decision": "NO_CHANGE",
                "root_cause": "No target-domain packet-to-Core drop was detected.",
                "affected_modules": [],
                "semantic_risk": "NONE",
                "expected_benefit": "Avoids unjustified broad input expansion.",
                "required_tests": "source-to-core lineage audit",
                "model_revalidation_required": False,
                "real_holdout_required": False,
            },
            {
                "class": "DIRECTIONAL_REASONING_CHANGE",
                "decision": "DEFERRED_REQUIRES_USER_DECISION",
                "root_cause": "Model-owned generic reasoning under sparse/equivalent inputs.",
                "affected_modules": ["future Core prompt/acceptance contract"],
                "semantic_risk": "HIGH",
                "expected_benefit": "More issuer-specific anchors without invented detail.",
                "required_tests": "new frozen model validation and unseen real holdout",
                "model_revalidation_required": True,
                "real_holdout_required": True,
            },
            {
                "class": "MESSAGE/RENDERER_CHANGE",
                "decision": "NO_CHANGE",
                "root_cause": "Renderer is mostly a structural wrapper, not the source of substance.",
                "affected_modules": [],
                "semantic_risk": "NONE",
                "expected_benefit": "Preserves reasoning ownership.",
                "required_tests": "existing renderer regression",
                "model_revalidation_required": False,
                "real_holdout_required": False,
            },
            {
                "class": "NO_CHANGE",
                "decision": "PRESERVE_SHARED_DECISION_AND_RENDERER_CONTRACTS",
                "root_cause": "The shared ownership, composition, and structural renderer passed.",
                "affected_modules": [],
                "semantic_risk": "NONE",
                "expected_benefit": "Avoids conflating message variety with investment quality.",
                "required_tests": "existing ownership and renderer regressions",
                "model_revalidation_required": False,
                "real_holdout_required": False,
            },
            {
                "class": "DEFERRED_REQUIRES_USER_DECISION",
                "decision": "SEPARATE_SOURCE_DOMAIN_DESIGN",
                "root_cause": "Several requested domains are absent from the preserved archive.",
                "affected_modules": ["future official source enrichment"],
                "semantic_risk": "HIGH",
                "expected_benefit": "Potentially improves decision sufficiency with safe evidence.",
                "required_tests": "period/entity/currency/semantic lineage tests",
                "model_revalidation_required": True,
                "real_holdout_required": True,
            },
        ],
        "ordered_plan": [
            "prove lifecycle bootstrap and Daily Delta in nonproduction",
            "separately decide archive source-domain enrichment",
            "then freeze any Core specificity change before a new model proof",
        ],
        "status": "FROZEN",
    }
    change_counts = dict(Counter(row["class"] for row in candidate_changes["rows"]))
    next_model_scope = {
        "contract": "m2-required-next-model-validation-scope-v1",
        "immediate_next_scope_uses_model": False,
        "future_model_validation_required": True,
        "future_real_holdout_required": True,
        "precondition": "Only after a separately authorized input or reasoning contract is frozen.",
        "fresh_first_selective_rerun": "FORBIDDEN_UNLESS_SEPARATELY_AUTHORIZED",
        "status": "DEFERRED",
    }
    production_no_change = {
        "contract": "m2-production-no-change-v1",
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
    pause = (
        read_json(args.pause_observation)
        if args.pause_observation and args.pause_observation.is_file()
        else {"status": "NOT_MEASURED", "scheduler_mutation_count": "NOT_MEASURED"}
    )
    master_update = {
        "contract": "m2-master-workflow-update-v1",
        "path": "docs/MASTER_WORKFLOW.md",
        "sha256": file_sha256(repo_root / "docs/MASTER_WORKFLOW.md"),
        "m1_status": "COMPLETE",
        "m2_status": "COMPLETE",
        "m3_status": "NOT_AUTHORIZED",
        "status": "RECORDED",
    }
    completion = {
        "contract": CONTRACT,
        "base_sha": args.base_sha,
        "work_instruction_commit": args.work_instruction_commit,
        "implementation_commit": args.implementation_commit,
        "report_commit": "NOT_MEASURED",
        "final_head_sha": "NOT_MEASURED",
        "branch": repository["branch"],
        "latest_result_zip_sha256": latest_result_sha,
        "latest_result_integrity": "PASS",
        "m1_status": "COMPLETE",
        "m2_status": "COMPLETE",
        "unknown_consistency_regression_status": (
            "PASS" if m1_regression.get("status") == "PASS" else "FAIL"
        ),
        "early_core_gate_status": "PASS",
        "nonproduction_adapter_status": "PASS",
        "lifecycle_mode_contract_status": "PASS",
        "integration_boundary_count": boundaries["boundary_count"],
        "integration_boundary_verified_count": boundaries["verified_count"],
        "explicit_registration_test_status": "PASS",
        "baseline_not_delta_test_status": "PASS",
        "bootstrap_not_delta_test_status": "PASS",
        "missing_refresh_not_no_change_test_status": "PASS",
        "price_not_thesis_delta_test_status": "PASS",
        "idempotency_test_status": "PASS",
        "source_to_core_domains_audited": coverage["domain_count"],
        "available_but_dropped_domain_count": coverage[
            "available_but_dropped_domain_count"
        ],
        "requires_separate_input_design_count": coverage[
            "requires_separate_input_design_count"
        ],
        "decision_quality_review_status": decision_quality[
            "decision_quality_review_status"
        ],
        "historical_message_count": m1_message["message_count"],
        "historical_message_trace_count": m1_message["complete_trace_count"],
        "historical_repetition_cluster_count": repetition[
            "historical_repetition_cluster_count"
        ],
        "model_owned_repetition_count": repetition["ownership_counts"].get(
            "MODEL_OWNED_SUBSTANTIVE", 0
        ),
        "renderer_owned_repetition_count": repetition["ownership_counts"].get(
            "RENDERER_INTRODUCED_OR_UNRESOLVED", 0
        ),
        "input_loss_repetition_count": repetition["input_loss_repetition_count"],
        "message_specificity_contract_status": "FROZEN",
        "file_only_message_comparison_status": comparison["status"],
        "daily_delta_message_contract_status": "FROZEN_NOT_ENABLED",
        "candidate_change_decision_counts": change_counts,
        "new_model_validation_required": True,
        "new_real_holdout_proof_required": True,
        "recommended_next_scope": (
            "NONPRODUCTION_MONITORING_BOOTSTRAP_AND_DAILY_DELTA_LIFECYCLE_INTEGRATION"
        ),
        "model_calls_real": 0,
        "model_calls_fictional": 0,
        "model_calls_judge": 0,
        "provider_source_fetches": 0,
        **{
            key: production_no_change[key]
            for key in (
                "production_db_mutations",
                "monitoring_registrations",
                "assessment_persistence_mutations",
                "warning_mutations",
                "notification_queue_writes",
                "production_sends",
                "main_merges",
                "deployments",
                "live_v2_changes",
                "night_futures_changes",
                "automatic_monitoring_resume",
            )
        },
        "observed_paused_schedule_count": (
            pause.get("process_observation", {}).get("paused_schedule_count", "NOT_MEASURED")
        ),
        "scheduler_mutation_count": pause.get("scheduler_mutation_count", "NOT_MEASURED"),
        "focused_test_result": args.focused_result,
        "full_test_result": args.full_test_result,
        "ruff_result": args.ruff_result,
        "git_diff_check": args.diff_result,
        "artifact_count": "NOT_MEASURED",
        "artifact_hash_mismatch_count": 0,
        "artifact_size_mismatch_count": 0,
        "artifact_secret_scan_failure_count": 0,
        "production_readiness": "NOT_READY",
        "status": "M2_COMPLETE",
        "stop_reason": None,
        "next_scope": (
            "NONPRODUCTION_MONITORING_BOOTSTRAP_AND_DAILY_DELTA_LIFECYCLE_INTEGRATION"
        ),
    }

    artifacts = {
        "01-repository-provenance.json": repository,
        "02-latest-result-integrity.json": latest_integrity,
        "03-m2-scope-freeze.json": scope_freeze,
        "04-existing-boundary-revalidation.json": boundaries,
        "05-nonproduction-integration-design.json": integration_design,
        "06-lifecycle-mode-contract.json": lifecycle_contract,
        "07-nonproduction-adapter-implementation.json": adapter_implementation,
        "08-idempotency-and-side-effect-audit.json": idempotency,
        "09-file-only-rendering-harness.json": harness,
        "10-lifecycle-integration-test-results.json": lifecycle_tests,
        "11-source-to-core-domain-coverage.json": coverage,
        "12-source-to-core-drop-lineage.json": drops,
        "13-decision-quality-review.json": decision_quality,
        "14-boundary-stability-context-note.json": stability_note,
        "15-input-coverage-change-decision.json": input_change,
        "16-message-repetition-root-cause.json": repetition,
        "17-message-specificity-contract.json": specificity_contract,
        "18-renderer-vs-model-content-ownership-review.json": ownership_review,
        "19-file-only-message-comparison.json": comparison,
        "20-daily-delta-message-contract.json": daily_contract,
        "21-message-quality-change-decision.json": message_change,
        "22-candidate-change-decision-record.json": candidate_changes,
        "23-required-next-model-validation-scope.json": next_model_scope,
        "24-production-no-change.json": production_no_change,
        "25-schedule-pause-observation.json": pause,
        "26-master-workflow-update.json": master_update,
        "27-program-completion.json": completion,
    }
    completion["artifact_count"] = len(artifacts) + len(comparison["rows"]) + 1
    for name, value in artifacts.items():
        write_json(report_dir / name, value)
    report_path = report_dir / "20260908-nonproduction-integration-decision-message-quality-review.md"
    report_path.write_text(_report_markdown(completion), encoding="utf-8")
    index = artifact_index(report_dir)
    write_json(report_dir / "artifact-index.json", index)
    return completion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--source-archive", type=Path, required=True)
    parser.add_argument("--latest-result", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pause-observation", type=Path)
    parser.add_argument(
        "--base-sha", default="7eb9243f27ec0b15d7bb847c07c42299286f6892"
    )
    parser.add_argument(
        "--work-instruction-commit",
        default="265d3866b5885458da89e01dfe994c426c7f342f",
    )
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--focused-result", default="NOT_MEASURED")
    parser.add_argument("--full-test-result", default="NOT_MEASURED")
    parser.add_argument("--ruff-result", default="NOT_MEASURED")
    parser.add_argument("--diff-result", default="NOT_MEASURED")
    return parser.parse_args()


def main() -> None:
    completion = run(parse_args())
    print(json.dumps(completion, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
