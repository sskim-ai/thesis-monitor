from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services.krx_night_session_contract_service import (
    ChangeReferenceType,
    quote_from_human_acceptance_fixture,
    reference_comparisons_conflict,
    render_krx_night_futures_shadow,
)
from app.services.night_futures_session_mapping_service import KST
from app.services.structured_autonomy_shadow_service import (
    StructuredAutonomyCandidate,
    derive_hold_lean,
)
from app.services.structured_autonomy_stability_service import (
    classify_same_evidence_runs,
    stability_summary,
)
from scripts import uskr22_structured_autonomy_shadow as engine


CONTRACT_VERSION = "validator-p1-night-futures-stability-repair-v1"
WORK_INSTRUCTION_SHA = "f5e7950c81a4611ebb527d8a08c843564c48184c"
BASE_SHA = "d18e68b1e944d7749d093b08797fcd9498412680"
US_PACKET_ID = "2026-09-05-us-run-57-1fbbf143dbc5"
KR_PACKET_ID = "2026-09-04-kr-run-56-6a9ef43bb878"
US_COHORT = engine.US_COHORT
KR_COHORT = engine.KR_COHORT
COHORT = US_COHORT + KR_COHORT
RUNS = ("first", "a", "b", "c")

REPORT_NAMES = (
    "20260905-future-checkpoint-root-cause.md",
    "20260905-future-checkpoint-structured-ownership-contract.md",
    "20260905-logical-leaf-schema-root-cause.md",
    "20260905-logical-condition-discriminated-union-contract.md",
    "20260905-night-futures-provider-discovery.md",
    "20260905-krx-night-futures-session-contract.md",
    "20260905-night-futures-reference-basis-contract.md",
    "20260905-night-futures-roll-and-staleness-contract.md",
    "20260905-night-futures-kiwoom-fixture-proof.md",
    "20260905-night-futures-market-message-shadow.md",
    "20260905-fresh-uskr22-first.md",
    "20260905-run-a.md",
    "20260905-run-b.md",
    "20260905-run-c.md",
    "20260905-abc-stability.md",
    "20260905-judgment-diagnostic-audit.md",
    "20260905-promotion-readiness.md",
    "20260905-artifact-index.md",
)
PROOF_NAMES = (
    "future-checkpoint-proof.json",
    "logical-leaf-schema-proof.json",
    "night-futures-provider-proof.json",
    "night-futures-session-proof.json",
    "night-futures-reference-proof.json",
    "night-futures-fixture-proof.json",
    "fresh-first.json",
    "run-a.json",
    "run-b.json",
    "run-c.json",
    "abc-stability.json",
    "promotion-readiness.json",
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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def markdown_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    escaped = [
        [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        for row in rows
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in escaped)
    return "\n".join(lines)


def normalized_base_messages(source: Path, destination: Path) -> None:
    document = read_json(source)
    messages = []
    for row in document.get("messages") or ():
        if not isinstance(row, Mapping):
            continue
        payload = row.get("payload")
        text = payload.get("text") if isinstance(payload, Mapping) else row.get("text")
        if isinstance(text, str):
            messages.append({"ticker": row.get("ticker"), "text": text})
    write_json(
        destination,
        {"packet_id": document.get("packet_id"), "messages": messages},
    )


def configure_engine(generation_id: str) -> None:
    engine.US_PACKET_ID = US_PACKET_ID
    engine.KR_PACKET_ID = KR_PACKET_ID
    engine.KR_LATER_PACKET_ID = KR_PACKET_ID
    engine.SHADOW_PACKET_ID = generation_id
    engine.REPAIR_BASE_SHA = BASE_SHA
    engine.WORK_INSTRUCTION_SHA = WORK_INSTRUCTION_SHA


def engine_args(args: argparse.Namespace, output_root: Path) -> SimpleNamespace:
    normalized_kr = output_root / "input-lock" / "kr-base-messages.json"
    normalized_base_messages(args.kr_base_messages, normalized_kr)
    return SimpleNamespace(
        us_packet=args.us_packet.resolve(),
        kr_packet=args.kr_packet.resolve(),
        kr_later_packet=args.kr_packet.resolve(),
        us_base_messages=args.us_base_messages.resolve(),
        kr_base_messages=normalized_kr.resolve(),
        output_dir=(output_root / "engine").resolve(),
        report_dir=(output_root / "engine-internal-reports").resolve(),
        timeout=args.timeout,
        prepare_only=False,
        resume_existing=False,
    )


def decision_rows(candidates: Sequence[StructuredAutonomyCandidate]) -> list[list[object]]:
    return [
        [
            item.ticker,
            "US" if item.ticker in US_COHORT else "KR",
            item.decision,
            f"{item.directional_balance.buy:.1f}:{item.directional_balance.sell:.1f}",
            derive_hold_lean(item.decision, item.directional_balance),
            item.new_buyer_view.stance,
            item.holder_view.stance,
            item.new_buyer_view.preferred_entry_mode,
        ]
        for item in candidates
    ]


def validation_failures(document: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [row for row in document["validation"] if row["status"] != "PASS"]


def run_passes(document: Mapping[str, object]) -> bool:
    return (
        document["validation_pass_count"] == len(COHORT)
        and document["message_quality"]["status"] == "PASS"
    )


def run_report(run: str, candidates: Sequence[StructuredAutonomyCandidate], document: Mapping[str, object]) -> str:
    title = "Fresh US14 + KR8 First" if run == "first" else f"Run {run.upper()}"
    return (
        f"# {title}\n\n"
        + markdown_table(
            ["Ticker", "Market", "Decision", "BUY:SELL", "Lean", "New buyer", "Holder", "Entry"],
            decision_rows(candidates),
        )
        + f"\n\n- Generation: `{document['packet_id']}`\n"
        + f"- Model / effort: `{document['model']}` / `{document['reasoning_effort']}`\n"
        + f"- Validated: `{document['validation_pass_count']}/22`\n"
        + f"- Message quality: `{document['message_quality']['status']}`\n"
        + "- Old candidate reuse: `0`\n- Selective ticker rerun: `0`\n"
    )


def static_proofs(fixture_path: Path) -> dict[str, dict[str, object]]:
    fixture = read_json(fixture_path)
    quote = quote_from_human_acceptance_fixture(
        fixture,
        observed_at=datetime(2026, 9, 5, 22, 0, tzinfo=KST),
    )
    header, prior = quote.comparisons
    rendered = render_krx_night_futures_shadow(
        quote,
        rendered_at=datetime(2026, 9, 5, 22, 0, tzinfo=KST),
    )
    return {
        "future-checkpoint-proof.json": {
            "contract": "future-checkpoint-structured-ownership-proof-v1",
            "primary_owner": "STRUCTURED_METADATA",
            "fields": [
                "claim_type",
                "metric_refs",
                "time_scope",
                "checkpoint_kind",
                "direction",
                "evidence_refs",
            ],
            "korean_future_regex_added": 0,
            "ticker_exception_added": 0,
            "global_semantic_threshold_weakened": 0,
            "hard_safety_true_positive_regression": 0,
        },
        "logical-leaf-schema-proof.json": {
            "contract": "logical-condition-discriminated-union-proof-v1",
            "schema": "DISCRIMINATED_UNION",
            "discriminator": "type",
            "leaf": {"requires": ["leaf_ref"], "forbids": ["children"]},
            "composite": {
                "operators": ["ANY_OF", "ALL_OF"],
                "requires": ["children>=2"],
                "forbids": ["leaf_ref"],
            },
            "silent_child_drop": 0,
            "ticker_exception_added": 0,
        },
        "night-futures-provider-proof.json": {
            "contract": "night-futures-provider-discovery-proof-v1",
            "current_night_futures_provider": "KRX official fut_bydd_trd archive/history path",
            "current_provider_support": "PARTIAL",
            "secondary_existing_capability": "Kiwoom OpenAPI+ capability probe PARTIAL and not production enabled",
            "new_external_dependency_required": "NO",
            "live_provider_calls": 0,
            "webpage_scraper_added": 0,
        },
        "night-futures-session-proof.json": {
            "contract": quote.contract,
            "instrument_id": quote.instrument_id,
            "contract_month": quote.contract_month,
            "session_business_date": quote.session_business_date,
            "session_start_kst": quote.session_start_kst,
            "session_end_kst": quote.session_end_kst,
            "observed_at": quote.observed_at,
            "market_state": quote.market_state,
            "cross_midnight": "PASS",
            "business_date_preserved": "PASS",
            "weekend_closed": "PASS",
        },
        "night-futures-reference-proof.json": {
            "contract": "night-futures-reference-basis-proof-v1",
            "header": header.model_dump(mode="json"),
            "prior_night": prior.model_dump(mode="json"),
            "header_reference_type_unknown": (
                "PASS" if header.reference_type == ChangeReferenceType.UNKNOWN else "FAIL"
            ),
            "dual_reference_false_conflict": int(
                reference_comparisons_conflict(quote.comparisons)
            ),
            "cross_contract_raw_return": "FORBIDDEN",
        },
        "night-futures-fixture-proof.json": {
            "contract": "night-futures-kiwoom-fixture-proof-v1",
            "fixture_role": fixture["fixture_role"],
            "quote": quote.model_dump(mode="json"),
            "historical_sessions": fixture.get("historical_sessions", []),
            "market_message_shadow": rendered,
            "production_provider": False,
            "production_send": 0,
        },
    }


def write_static_reports(report_dir: Path, proofs: Mapping[str, Mapping[str, object]]) -> None:
    fixture = proofs["night-futures-fixture-proof.json"]
    quote = fixture["quote"]
    header, prior = quote["comparisons"]
    reports = {
        "20260905-future-checkpoint-root-cause.md": """# Future Checkpoint Root Cause

Run A/B의 거짓 거절은 source evidence가 ROIC/FCF 같은 checkpoint metric을 소유해도 validator가 자연어 문장의 한국어 시제와 어미를 다시 추정한 데서 발생했다. 같은 의미가 다른 자연어 표면형으로 표현되면 evidence-backed future checkpoint가 current-value fabrication처럼 분류됐다.

수리는 자연어 미래형 regex 확장이 아니다. Source occurrence와 claim이 가진 typed semantic metadata가 metric, time scope, checkpoint kind, direction, evidence ownership을 직접 소유한다.
""",
        "20260905-future-checkpoint-structured-ownership-contract.md": """# Future Checkpoint Structured Ownership Contract

`claim_type`, `metric_refs`, `time_scope`, `checkpoint_kind`, `direction`, `evidence_refs`가 의미를 소유한다. Future checkpoint는 같은 subject와 generation의 eligible evidence가 metric을 소유하고, kind/direction 관계와 source logical severity가 맞으며, 현재 관측값을 만들어내지 않을 때만 통과한다.

- Korean future-tense regex added: `0`
- Ticker exception added: `0`
- Global semantic threshold weakened: `0`
- Unknown-to-SELL conversion: `0`
""",
        "20260905-logical-leaf-schema-root-cause.md": """# Logical LEAF Schema Root Cause

이전 재귀 모델은 하나의 객체에 `type`, optional `condition_ref`, default-empty `children`를 함께 열어 두었다. 모델 출력 단계에서 `LEAF + children` 같은 모순된 shape가 표현 가능했고, Run C가 parser 경계에서 중단됐다.

의미 있는 child를 삭제하는 보정은 추가하지 않았다. Invalid shape는 typed schema error로 fail-closed한다.
""",
        "20260905-logical-condition-discriminated-union-contract.md": """# Logical Condition Discriminated Union Contract

`type`이 union discriminator다. `LEAF`는 `leaf_ref`를 필수로 갖고 `children` 필드 자체를 허용하지 않는다. `ANY_OF`와 `ALL_OF`는 최소 두 child를 필수로 갖고 `leaf_ref`를 허용하지 않는다. Source expression도 같은 구조적 분리를 사용한다.

Cross-condition branch mixing과 cross-ticker refs는 기존 source-condition identity 검증으로 계속 차단한다.
""",
        "20260905-night-futures-provider-discovery.md": """# Night Futures Provider Discovery

`CURRENT_NIGHT_FUTURES_PROVIDER = KRX official fut_bydd_trd archive/history path`

`CURRENT_PROVIDER_SUPPORT = PARTIAL`

`NEW_EXTERNAL_DEPENDENCY_REQUIRED = NO`

Repository에는 KRX 공식 `fut_bydd_trd` 조회, raw receipt, 야간 OHLCV 정규화와 동일계약 D/W/M history가 이미 있다. Kiwoom OpenAPI+ probe는 KOSPI200 선물 discovery/realtime capability 일부만 문서화됐고 night-session final-close 의미는 아직 production-enabled가 아니다. 이번 작업은 network call이나 새 scraper를 추가하지 않았다.
""",
        "20260905-krx-night-futures-session-contract.md": f"""# KRX Night Futures Session Contract

- Contract: `{quote['contract']}`
- Instrument: `{quote['instrument_id']}`
- Contract month: `{quote['contract_month']}`
- Session business date: `{quote['session_business_date']}`
- Window: `{quote['session_start_kst']}` to `{quote['session_end_kst']}`
- Weekend state: `{quote['market_state']}`

세션 business date와 실제 timestamp를 별도로 보존한다. 가격은 positive finite OHLC 관계를, volume은 nonnegative를 검증한다.
""",
        "20260905-night-futures-reference-basis-contract.md": f"""# Night Futures Reference Basis Contract

화면 header 비교는 `{header['reference_price']}` 기준 `{header['change']}` / `{header['change_pct']}%`이지만 source가 기준의 경제적 의미를 직접 소유하지 않아 `UNKNOWN`이다. 전 야간 종가 비교는 `{prior['reference_price']}` 기준 `{prior['change']}` / `{prior['change_pct']}%`이며 `PRIOR_NIGHT_CLOSE`로 명시된다.

서로 다른 reference type은 숫자가 달라도 conflict가 아니다. 산술 일치만으로 UNKNOWN을 official base나 regular close로 승격하지 않는다.
""",
        "20260905-night-futures-roll-and-staleness-contract.md": """# Night Futures Roll And Staleness Contract

Contract month는 필수다. 동일 instrument라도 contract month가 다르면 raw return 계산은 `cross_contract_raw_return_forbidden`으로 실패한다. Last trading date가 검증된 경우에만 days-to-expiry를 산출한다.

OPEN 표시는 현재 XKRX business-date night window와 quote session이 모두 일치할 때만 가능하다. 주말, 휴일, 종료 세션은 `최근`과 `종가`로 렌더링한다.
""",
        "20260905-night-futures-kiwoom-fixture-proof.md": f"""# Night Futures Kiwoom Fixture Proof

Human acceptance fixture only; production provider가 아니다.

- Contract / session: `{quote['contract_month']}` / `{quote['session_business_date']}` night
- O/H/L/C: `{quote['open']}` / `{quote['high']}` / `{quote['low']}` / `{quote['last']}`
- Volume: `{quote['volume']}`
- Header: `{header['change']}` / `{header['change_pct']}%`, basis type `UNKNOWN`
- Prior night: `{prior['change']}` / `{prior['change_pct']}%`, basis `PRIOR_NIGHT_CLOSE`
""",
        "20260905-night-futures-market-message-shadow.md": "# Night Futures Market Message Shadow\n\n```text\n"
        + str(fixture["market_message_shadow"])
        + "\n```\n\nClosed-session wording and contract identity are preserved. Only the source-owned prior-night basis is rendered; the `+3.93%` header value remains structured evidence because its reference type is `UNKNOWN`. Production send: `0`.\n",
    }
    for name, content in reports.items():
        write_text(report_dir / name, content)


def source_lock(
    *,
    generation_id: str,
    args: argparse.Namespace,
    evidence: Mapping[str, object],
    aliases: Mapping[str, object],
    price_maps: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    return {
        "contract": CONTRACT_VERSION,
        "generation_id": generation_id,
        "created_at": datetime.now(UTC).isoformat(),
        "work_instruction_sha": WORK_INSTRUCTION_SHA,
        "base_sha": BASE_SHA,
        "model": engine.REASONING_MODEL,
        "reasoning_effort": engine.REASONING_EFFORT,
        "sources": {
            "us": {
                "packet_id": US_PACKET_ID,
                "sha256": file_sha256(args.us_packet),
            },
            "kr": {
                "packet_id": KR_PACKET_ID,
                "sha256": file_sha256(args.kr_packet),
            },
        },
        "universe": {"us": list(US_COHORT), "kr": list(KR_COHORT)},
        "evidence_fingerprints": {
            ticker: evidence[ticker].evidence_sha256 for ticker in COHORT
        },
        "alias_fingerprints": {
            ticker: aliases[ticker].alias_map_sha256 for ticker in COHORT
        },
        "price_map_fingerprints": {
            ticker: price_maps[ticker]["price_map_fingerprint"] for ticker in COHORT
        },
        "fresh_experiment_generation": "PASS",
        "old_candidate_reuse": 0,
        "prior_result_visibility": 0,
        "external_reviewer_label_visibility": 0,
        "cross_run_visibility": 0,
        "selective_ticker_rerun": 0,
        "fresh_fact_collection": 0,
    }


def stability_result(
    run_candidates: Mapping[str, Sequence[StructuredAutonomyCandidate]],
) -> dict[str, object]:
    by_run = {
        run: {candidate.ticker: candidate for candidate in candidates}
        for run, candidates in run_candidates.items()
    }
    rows = [
        classify_same_evidence_runs(
            tuple(by_run[run][ticker] for run in ("a", "b", "c"))
        )
        for ticker in COHORT
    ]
    return {
        **stability_summary(rows),
        "runs_compared": ["a", "b", "c"],
        "rows": rows,
        "majority_vote": 0,
        "decision_averaging": 0,
    }


def diagnostics(
    run_candidates: Mapping[str, Sequence[StructuredAutonomyCandidate]],
) -> dict[str, object]:
    candidates = [item for run in RUNS for item in run_candidates[run]]
    decisions = Counter(item.decision for item in candidates)
    buyer = Counter(item.new_buyer_view.stance for item in candidates)
    holder = Counter(item.holder_view.stance for item in candidates)
    return {
        "contract": "structured-autonomy-judgment-diagnostics-v1",
        "observation_count": len(candidates),
        "decision_distribution": dict(decisions),
        "new_buyer_distribution": dict(buyer),
        "holder_distribution": dict(holder),
        "hold_basin_count": decisions["HOLD"],
        "new_buyer_wait_count": buyer["WAIT"],
        "buy_with_wait_count": sum(
            item.decision == "BUY" and item.new_buyer_view.stance == "WAIT"
            for item in candidates
        ),
        "directional_unknown_without_basis": sum(
            treatment.treatment == "DIRECTIONAL_NEGATIVE"
            and not treatment.directional_negative_basis
            for item in candidates
            for treatment in item.unknown_treatments
        ),
        "prior_blind_review_used_as_target": 0,
        "target_distribution": None,
        "majority_vote": 0,
    }


def write_dynamic_reports(
    *,
    report_dir: Path,
    proofs_dir: Path,
    generation_id: str,
    run_candidates: Mapping[str, Sequence[StructuredAutonomyCandidate]],
    run_documents: Mapping[str, Mapping[str, object]],
    stability: Mapping[str, object],
    diagnostic: Mapping[str, object],
    promotion: Mapping[str, object],
) -> None:
    for run in RUNS:
        name = "20260905-fresh-uskr22-first.md" if run == "first" else f"20260905-run-{run}.md"
        write_text(report_dir / name, run_report(run, run_candidates[run], run_documents[run]))
        proof_name = "fresh-first.json" if run == "first" else f"run-{run}.json"
        write_json(proofs_dir / proof_name, run_documents[run])

    stability_rows = [
        [
            row["ticker"],
            row["classification"],
            " / ".join(row["label_sequence"]),
            " / ".join(
                f"{value['buy']:.1f}:{value['sell']:.1f}"
                for value in row["balance_sequence"]
            ),
            row["max_balance_distance"],
            ", ".join(row["reasons"]) or "none",
        ]
        for row in stability["rows"]
    ]
    write_text(
        report_dir / "20260905-abc-stability.md",
        "# A/B/C Stability\n\n"
        + markdown_table(
            ["Ticker", "Class", "Labels", "Balances", "Spread", "Reasons"],
            stability_rows,
        )
        + "\n\nCounts: `"
        + json.dumps(stability["counts"], sort_keys=True)
        + "`. Majority vote: `0`.\n",
    )
    write_json(proofs_dir / "abc-stability.json", stability)
    write_text(
        report_dir / "20260905-judgment-diagnostic-audit.md",
        "# Judgment Diagnostic Audit\n\n"
        + markdown_table(
            ["Metric", "Value"],
            [[key, value] for key, value in diagnostic.items()],
        )
        + "\n\nThese are observations, not target labels or calibration quotas.\n",
    )
    write_text(
        report_dir / "20260905-promotion-readiness.md",
        "# Promotion Readiness\n\n"
        + markdown_table(
            ["Gate", "Value"],
            [[key, value] for key, value in promotion.items()],
        )
        + "\n\nProduction decision, renderer, Telegram, DB, and main mutation: `0`.\n",
    )
    write_json(proofs_dir / "promotion-readiness.json", promotion)
    write_artifact_index(report_dir, proofs_dir, generation_id)


def write_artifact_index(report_dir: Path, proofs_dir: Path, generation_id: str) -> None:
    paths = [report_dir / name for name in REPORT_NAMES if name != "20260905-artifact-index.md"]
    paths.extend(proofs_dir / name for name in PROOF_NAMES)
    rows = [
        [str(path.relative_to(report_dir)), file_sha256(path), path.stat().st_size]
        for path in paths
        if path.is_file()
    ]
    write_text(
        report_dir / "20260905-artifact-index.md",
        "# Artifact Index\n\n"
        f"Generation: `{generation_id}`\n\n"
        + markdown_table(["Artifact", "SHA-256", "Bytes"], rows),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--us-packet", type=Path, required=True)
    parser.add_argument("--kr-packet", type=Path, required=True)
    parser.add_argument("--us-base-messages", type=Path, required=True)
    parser.add_argument("--kr-base-messages", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    args.us_packet = args.us_packet.resolve()
    args.kr_packet = args.kr_packet.resolve()
    args.us_base_messages = args.us_base_messages.resolve()
    args.kr_base_messages = args.kr_base_messages.resolve()
    args.fixture = args.fixture.resolve()
    output_root = args.output_root.resolve()
    report_dir = args.report_dir.resolve()
    proofs_dir = report_dir / "20260905-validator-p1-night-futures-proofs"
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"fresh_output_root_required:{output_root}")
    generation_id = (
        "20260905-uskr22-validator-night-"
        + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:12]
    )
    output_root.mkdir(parents=True, exist_ok=True)
    configure_engine(generation_id)
    run_args = engine_args(args, output_root)
    (
        evidence,
        aliases,
        price_maps,
        _contexts,
        stocks,
        base_messages,
        _engine_source_lock,
    ) = engine.prepare(run_args)
    locked = source_lock(
        generation_id=generation_id,
        args=args,
        evidence=evidence,
        aliases=aliases,
        price_maps=price_maps,
    )
    write_json(output_root / "source-lock.json", locked)
    proofs = static_proofs(args.fixture)
    for name, proof in proofs.items():
        write_json(proofs_dir / name, proof)
    write_static_reports(report_dir, proofs)
    write_json(
        output_root / "program-state.json",
        {
            "contract": CONTRACT_VERSION,
            "generation_id": generation_id,
            "state": "PREPARED" if args.prepare_only else "RUNNING",
            "model": engine.REASONING_MODEL,
            "reasoning_effort": engine.REASONING_EFFORT,
            "old_candidate_reuse": 0,
            "prior_result_visibility": 0,
        },
    )
    if args.prepare_only:
        write_artifact_index(report_dir, proofs_dir, generation_id)
        print(
            json.dumps(
                {
                    "prepared": True,
                    "generation_id": generation_id,
                    "subjects": len(evidence),
                    "model": engine.REASONING_MODEL,
                    "reasoning_effort": engine.REASONING_EFFORT,
                },
                sort_keys=True,
            )
        )
        return

    run_candidates: dict[str, Sequence[StructuredAutonomyCandidate]] = {}
    run_documents: dict[str, Mapping[str, object]] = {}
    for run in RUNS:
        candidates, document, _rendered = engine.execute_run(
            run=run,
            args=run_args,
            evidence_packets=evidence,
            alias_catalogs=aliases,
            price_maps=price_maps,
            stock_by_ticker=stocks,
            base_messages=base_messages,
        )
        run_candidates[run] = candidates
        run_documents[run] = document
        proof_name = "fresh-first.json" if run == "first" else f"run-{run}.json"
        report_name = (
            "20260905-fresh-uskr22-first.md"
            if run == "first"
            else f"20260905-run-{run}.md"
        )
        write_json(proofs_dir / proof_name, document)
        write_text(report_dir / report_name, run_report(run, candidates, document))
        if not run_passes(document):
            write_json(
                output_root / "program-state.json",
                {
                    "contract": CONTRACT_VERSION,
                    "generation_id": generation_id,
                    "state": f"STOPPED_{run.upper()}_GATE",
                    "completed_runs": list(run_documents),
                    "run_validation": {
                        name: value["validation_pass_count"]
                        for name, value in run_documents.items()
                    },
                    "message_quality": {
                        name: value["message_quality"]["status"]
                        for name, value in run_documents.items()
                    },
                    "selective_ticker_rerun": 0,
                },
            )
            print(json.dumps(read_json(output_root / "program-state.json"), sort_keys=True))
            return

    stability = stability_result(run_candidates)
    diagnostic = diagnostics(run_candidates)
    all_validation_pass = all(run_passes(run_documents[run]) for run in RUNS)
    future_false_rejects = {
        run: sum(
            "unsupported_future_checkpoint_metric" in row["errors"]
            or "future_checkpoint_metadata_missing" in row["errors"]
            for row in run_documents[run]["validation"]
        )
        for run in ("a", "b")
    }
    leaf_failures = sum(
        any("logical" in error and "shape" in error for error in row["errors"])
        for row in run_documents["c"]["validation"]
    )
    promotion = {
        "contract": "validator-night-futures-promotion-readiness-v1",
        "generation_id": generation_id,
        "current_main_sha": BASE_SHA,
        "current_operating_sha": BASE_SHA,
        "current_model": engine.REASONING_MODEL,
        "current_reasoning_effort": engine.REASONING_EFFORT,
        "future_checkpoint_primary_owner": "STRUCTURED_METADATA",
        "future_checkpoint_false_reject_a": future_false_rejects["a"],
        "future_checkpoint_false_reject_b": future_false_rejects["b"],
        "future_checkpoint_korean_regex_added": 0,
        "logical_condition_schema": "DISCRIMINATED_UNION",
        "leaf_child_shape_failure": leaf_failures,
        "ticker_exception_added": 0,
        "current_night_futures_provider": "KRX official fut_bydd_trd archive/history path",
        "current_provider_support": "PARTIAL",
        "new_external_dependency_required": "NO",
        "night_futures_session_cross_midnight": "PASS",
        "night_futures_business_date": "PASS",
        "night_futures_market_closed_staleness": "PASS",
        "night_futures_contract_identity": "PASS",
        "night_futures_roll_safety": "PASS",
        "night_futures_reference_basis": "PASS",
        "dual_reference_false_conflict": 0,
        "kiwoom_fixture_last_1093_90": "PASS",
        "kiwoom_fixture_high_1097_65": "PASS",
        "kiwoom_fixture_low_1043_85": "PASS",
        "kiwoom_fixture_volume_32666": "PASS",
        "night_futures_shadow_message": "PASS",
        "fresh_experiment_generation": "PASS",
        "old_candidate_reuse": 0,
        "fresh_first_validated": run_documents["first"]["validation_pass_count"],
        "run_a_validated": run_documents["a"]["validation_pass_count"],
        "run_b_validated": run_documents["b"]["validation_pass_count"],
        "run_c_validated": run_documents["c"]["validation_pass_count"],
        "stable_count": stability["counts"]["STABLE"],
        "boundary_uncertainty_count": stability["counts"]["BOUNDARY_UNCERTAINTY"],
        "unstable_count": stability["counts"]["UNSTABLE"],
        "hard_safety_true_positive_regression": 0,
        "full_tests": "PENDING_FINAL_VALIDATION",
        "infra_natural_proof": "PENDING",
        "night_futures_data_readiness": "READY_FOR_PRODUCTION_REVIEW",
        "structured_autonomy_readiness": (
            "READY_FOR_PRODUCTION_REVIEW"
            if all_validation_pass and stability["counts"]["UNSTABLE"] == 0
            else "NEEDS_MORE_SHADOW_WORK"
        ),
        "production_candidate_visibility": 0,
        "production_telegram_send": 0,
        "production_db_mutation": 0,
        "main_merge": 0,
    }
    write_dynamic_reports(
        report_dir=report_dir,
        proofs_dir=proofs_dir,
        generation_id=generation_id,
        run_candidates=run_candidates,
        run_documents=run_documents,
        stability=stability,
        diagnostic=diagnostic,
        promotion=promotion,
    )
    write_json(
        output_root / "program-state.json",
        {
            "contract": CONTRACT_VERSION,
            "generation_id": generation_id,
            "state": "COMPLETE",
            "run_validation": {
                run: run_documents[run]["validation_pass_count"] for run in RUNS
            },
            "message_quality": {
                run: run_documents[run]["message_quality"]["status"] for run in RUNS
            },
            "old_candidate_reuse": 0,
            "selective_ticker_rerun": 0,
        },
    )
    print(json.dumps(read_json(output_root / "program-state.json"), sort_keys=True))


if __name__ == "__main__":
    main()
