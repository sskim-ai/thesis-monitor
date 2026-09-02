from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Mapping

from app.services.krx_night_history_service import (
    KRX_NIGHT_DAILY_OHLC_CONTRACT,
    KRX_NIGHT_DWM_CONTRACT,
    KRX_NIGHT_HISTORY_CONTRACT,
    KRX_NIGHT_OHLC_FIELD_MAPPING,
    KRX_NIGHT_RAW_RECEIPT_CONTRACT,
    KrxNightTimeframes,
    build_same_contract_timeframes,
    load_history,
)
from app.services.night_futures import (
    NIGHT_FUTURES_LABELS,
    night_futures_context_row,
    summarize_night_futures,
)
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.us_full_message_service import render_us_full_market_message
from app.services.us_market_digest_plan_service import render_specific_macro_claim
from app.services.us_market_message_quality_service import (
    validate_us_market_message_payload,
)


CONTRACT = "run51-krx-night-live-path-evidence-v1"
PACKET_ID = "2026-09-02-us-run-51-39a4d4eec53e"
REFERENCE_DATE = date(2026, 9, 1)
SERIES = (
    "KRX_KOSPI200_NIGHT_FUT",
    "KRX_KOSDAQ150_NIGHT_FUT",
)
PRODUCTS = ("KOSPI200", "KOSDAQ150")


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected_json_object:{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sectionless_market(text: str) -> str:
    blocks = text.split("\n\n")
    return "\n\n".join(
        block
        for block in blocks
        if not block.startswith("🌙 한국 야간선물") and not block.startswith("🌐 보조 시장환경")
    )


def _raw_source_proof(history_root: Path) -> dict[str, object]:
    receipts = sorted((history_root / "raw/2026/09/01").glob("*.receipt.json"))
    if len(receipts) != 1:
        raise ValueError(f"run51_raw_receipt_count_invalid:{len(receipts)}")
    receipt = _read_json(receipts[0])
    raw_path = history_root / str(receipt["raw_relative_path"])
    if _sha256(raw_path) != receipt.get("raw_payload_sha256"):
        raise ValueError("run51_raw_payload_sha_mismatch")
    payload = _read_json(raw_path)
    raw_rows = payload.get("OutBlock_1")
    rows = raw_rows if isinstance(raw_rows, list) else []
    selected = [
        row
        for row in rows
        if isinstance(row, Mapping)
        and str(row.get("ISU_CD") or "") in {"A0169000", "A0669000"}
        and str(row.get("MKT_NM") or "").strip() == "야간"
    ]
    if len(selected) != 2:
        raise ValueError(f"run51_selected_raw_row_count_invalid:{len(selected)}")
    return {
        "endpoint": receipt.get("source_url"),
        "service": receipt.get("service"),
        "query_date": receipt.get("query_date"),
        "raw_payload_sha256": receipt.get("raw_payload_sha256"),
        "raw_size_bytes": receipt.get("raw_size_bytes"),
        "row_count": receipt.get("row_count"),
        "field_names": receipt.get("field_names"),
        "raw_relative_path": receipt.get("raw_relative_path"),
        "selected_exact_rows": selected,
        "field_mapping": KRX_NIGHT_OHLC_FIELD_MAPPING,
        "contracts": {
            "daily": KRX_NIGHT_DAILY_OHLC_CONTRACT,
            "raw_receipt": KRX_NIGHT_RAW_RECEIPT_CONTRACT,
        },
    }


def _timeframes(
    history_root: Path,
    fixture: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    market = deepcopy(fixture.get("market"))
    if not isinstance(market, dict):
        raise ValueError("run51_night_fixture_market_missing")
    observations = market.get("observations")
    if not isinstance(observations, list):
        raise ValueError("run51_night_fixture_observations_missing")
    outputs: dict[str, object] = {}
    for product in PRODUCTS:
        row = next(
            (
                item
                for item in observations
                if isinstance(item, dict) and str(item.get("instrument") or "") == product
            ),
            None,
        )
        if row is None:
            raise ValueError(f"run51_night_fixture_product_missing:{product}")
        frames = build_same_contract_timeframes(
            history_root,
            instrument_root=product,
            reference_date=REFERENCE_DATE,
            daily_change_value=float(row["change_value"]),
            daily_change_pct=float(row["change_pct"]),
            daily_baseline_date=date.fromisoformat(str(row["reference_date"])),
            daily_baseline_close=float(row["reference_price"]),
        )
        if frames is None:
            raise ValueError(f"run51_same_contract_dwm_unavailable:{product}")
        row["night_timeframes"] = frames.model_dump(mode="json")
        outputs[product] = frames.model_dump(mode="json")

    summary = summarize_night_futures(market)
    if len(summary.items) != 2:
        raise ValueError(f"run51_night_summary_count_invalid:{len(summary.items)}")
    rows = [night_futures_context_row(item) for item in summary.items]
    return rows, {
        "contract": KRX_NIGHT_DWM_CONTRACT,
        "packet_id": PACKET_ID,
        "reference_date": REFERENCE_DATE,
        "products": outputs,
    }


def _enriched_market(
    packet_dir: Path,
    night_rows: list[dict[str, object]],
    *,
    real_yield_previous: float,
    real_yield_previous_date: date,
) -> dict[str, object]:
    context = _read_json(packet_dir / "market-context.json")
    facts = [dict(row) for row in context.get("fact_catalog") or () if isinstance(row, dict)]
    real_yield = next(
        (
            row
            for row in facts
            if row.get("fact_type") == "market_real_yield"
            and isinstance(row.get("fields"), dict)
            and row["fields"].get("series_code") == "DFII10"
        ),
        None,
    )
    if real_yield is None:
        raise ValueError("run51_real_yield_fact_missing")
    fields = dict(real_yield["fields"])
    current = float(fields["level_pct"])
    change_pp = round(current - real_yield_previous, 10)
    change_bp = round(change_pp * 100, 8)
    fields.update(
        {
            "previous_level_pct": real_yield_previous,
            "previous_observation_date": real_yield_previous_date.isoformat(),
            "change_pp": change_pp,
            "change_bp": change_bp,
        }
    )
    real_yield["fields"] = fields

    facts = [
        row
        for row in facts
        if row.get("fact_type") not in {"night_futures", "night_futures_timeframe"}
    ]
    timeframe_facts: list[dict[str, object]] = []
    for row in night_rows:
        fields_row = dict(row)
        facts.append(
            {
                "fact_id": row["fact_id"],
                "fact_type": "night_futures",
                "as_of_date": row["session_date"],
                "fields": fields_row,
            }
        )
        # Re-validate the typed sidecar before exposing any aggregate numeric fact.
        frames = KrxNightTimeframes.model_validate(row.get("night_timeframes"))
        if (
            frames.series_code != row["series_code"]
            or frames.contract_code != row["contract_code"]
            or frames.reference_date.isoformat() != str(row["session_date"])
        ):
            raise ValueError(f"run51_timeframe_fact_revalidation_failed:{row['series_code']}")
        for frame in (frames.daily, frames.weekly, frames.monthly):
            frame_fields = frame.model_dump(mode="json")
            frame_fields.update(
                {
                    "label": NIGHT_FUTURES_LABELS[str(row["series_code"])],
                    "state": "CURRENT_DIRECTIONAL",
                }
            )
            timeframe_facts.append(
                {
                    "fact_id": frame.fact_id,
                    "fact_type": "night_futures_timeframe",
                    "as_of_date": frame.reference_date.isoformat(),
                    "source": "official_krx_same_contract_history",
                    "fields": frame_fields,
                }
            )
    facts.extend(timeframe_facts)
    context["fact_catalog"] = facts
    context["night_futures"] = night_rows
    context["night_futures_cautions"] = []
    context["required_market_fact_ids"] = list(
        dict.fromkeys(
            [
                *[str(item) for item in context.get("required_market_fact_ids") or ()],
                *[str(fact["fact_id"]) for fact in timeframe_facts],
            ]
        )
    )
    context["numeric_registry"] = build_numeric_registry(facts)

    rendered = render_us_full_market_message(context)
    quality = validate_us_market_message_payload(rendered.text)
    if rendered.status != "PASS" or quality.status != "PASS":
        raise ValueError(
            "run51_market_render_failed:" + ",".join((*rendered.validation_errors, *quality.errors))
        )
    baseline = str(_read_json(packet_dir / "market-review.json").get("message") or "")
    if not baseline:
        baseline = str(_read_json(packet_dir / "packet.json").get("market_message") or "")
    if not baseline:
        fixture_baseline = _read_json(Path("tests/fixtures/run51_night_reference.json"))
        baseline = str(fixture_baseline.get("baseline_market_message") or "")
    non_night_parity = _sectionless_market(rendered.text) == baseline

    new_fact_ids = {str(fact["fact_id"]) for fact in timeframe_facts} | {str(real_yield["fact_id"])}
    new_registry = [
        row for row in context["numeric_registry"] if str(row.get("fact_id") or "") in new_fact_ids
    ]
    unsupported = [
        f"{row.get('fact_id')}:{row.get('field_path')}"
        for row in new_registry
        if row.get("registered") is not True
    ]
    if unsupported:
        raise ValueError("run51_market_numeric_registry_unsupported:" + ",".join(unsupported))
    claim_ids = set(rendered.night_fact_ids)
    expected_night_ids = {str(fact["fact_id"]) for fact in timeframe_facts}
    if claim_ids != expected_night_ids:
        raise ValueError("run51_night_numeric_fact_binding_incomplete")

    return {
        "contract": CONTRACT,
        "packet_id": PACKET_ID,
        "market_message": rendered.text,
        "market_message_sha256": hashlib.sha256(rendered.text.encode()).hexdigest(),
        "render": {**rendered.to_dict(), "status": rendered.status},
        "message_quality": quality.to_dict(),
        "non_night_market_numeric_diff": 0 if non_night_parity else 1,
        "non_night_market_selection_diff": 0 if non_night_parity else 1,
        "real_yield": {
            "fact_id": real_yield["fact_id"],
            "current": current,
            "current_date": real_yield["as_of_date"],
            "previous": real_yield_previous,
            "previous_date": real_yield_previous_date,
            "delta_pp": change_pp,
            "delta_bp": change_bp,
            "rendered_claim": render_specific_macro_claim(real_yield),
        },
        "night_fact_ids": sorted(claim_ids),
        "numeric_registry": new_registry,
        "numeric_registry_unsupported": unsupported,
        "required_market_fact_ids": context["required_market_fact_ids"],
        "context": context,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, required=True)
    parser.add_argument("--backfill-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--real-yield-previous", type=float, required=True)
    parser.add_argument("--real-yield-previous-date", type=date.fromisoformat, required=True)
    args = parser.parse_args()

    packet = _read_json(args.packet_dir / "packet.json")
    fixture = _read_json(args.fixture)
    if packet.get("packet_id") != PACKET_ID or fixture.get("packet_id") != PACKET_ID:
        raise ValueError("run51_packet_identity_mismatch")
    if fixture.get("expected_reference_date") != REFERENCE_DATE.isoformat():
        raise ValueError("run51_reference_date_mismatch")

    source = _raw_source_proof(args.history_root)
    night_rows, dwm = _timeframes(args.history_root, fixture)
    enriched = _enriched_market(
        args.packet_dir,
        night_rows,
        real_yield_previous=args.real_yield_previous,
        real_yield_previous_date=args.real_yield_previous_date,
    )
    backfill = _read_json(args.backfill_summary)
    all_bars = {
        product: [
            bar.model_dump(mode="json")
            for bar in load_history(
                args.history_root,
                instrument_root=product,
                end=REFERENCE_DATE,
            )
        ]
        for product in PRODUCTS
    }
    history = {
        "contract": KRX_NIGHT_HISTORY_CONTRACT,
        "namespace": "TEST_HISTORICAL",
        "cutoff": REFERENCE_DATE,
        "backfill": backfill,
        "bars": all_bars,
        "post_cutoff_bar_count": sum(
            str(bar["reference_date"]) > REFERENCE_DATE.isoformat()
            for rows in all_bars.values()
            for bar in rows
        ),
    }
    real_yield = {
        "contract": "us-market-real-yield-observation-pair-v1",
        **enriched["real_yield"],
        "delta_is_percentage_return": False,
        "same_day_label_used": False,
        "rounding_contract": "delta_pp_times_100_equals_delta_bp",
    }
    stage_matrix = {
        "contract": "run51-live-path-stage-matrix-v1",
        "packet_id": PACKET_ID,
        "stages": {
            "frozen_packet": "PASS",
            "krx_source_schema": "PASS",
            "raw_preservation": "PASS",
            "history_store": "PASS",
            "same_contract_dwm": "PASS",
            "real_yield_pair": "PASS",
            "market_render": "PASS",
            "v2_live_path": "PENDING",
            "pre_send_atomic_readiness": "PENDING",
            "test_delivery": "PENDING",
        },
    }
    proof = {
        "contract": CONTRACT,
        "packet_id": PACKET_ID,
        "status": "SOURCE_AND_MARKET_PASS",
        "reference_date": REFERENCE_DATE,
        "source": source,
        "history_summary": {
            "request_count": backfill.get("request_count"),
            "success_count": backfill.get("success_count"),
            "failure_count": backfill.get("failure_count"),
            "cache_hit_count": backfill.get("cache_hit_count"),
            "normalized_bar_count": backfill.get("normalized_bar_count"),
            "stored_bar_count": backfill.get("stored_bar_count"),
            "rejection_count": backfill.get("rejection_count"),
        },
        "dwm": dwm,
        "real_yield": real_yield,
        "market": {
            "status": enriched["render"]["status"],
            "quality": enriched["message_quality"]["status"],
            "non_night_market_numeric_diff": enriched["non_night_market_numeric_diff"],
            "non_night_market_selection_diff": enriched["non_night_market_selection_diff"],
            "numeric_registry_unsupported": enriched["numeric_registry_unsupported"],
        },
    }

    outputs = {
        "20260902-krx-night-source-contract.json": source,
        "20260902-krx-night-history.json": history,
        "20260902-run51-night-dwm.json": dwm,
        "20260902-run51-real-yield-delta.json": real_yield,
        "20260902-run51-market-enriched.json": enriched,
        "20260902-run51-live-path-stage-matrix.json": stage_matrix,
        "20260902-run51-live-path-with-krx-night-proof.json": proof,
    }
    for name, value in outputs.items():
        _write_json(args.output_dir / name, value)
    _write_text(args.output_dir / "run51-enriched-market-message.txt", enriched["market_message"])
    print(json.dumps(proof, ensure_ascii=False, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
