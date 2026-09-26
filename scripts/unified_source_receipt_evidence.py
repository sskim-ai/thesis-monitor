"""Read-only, no-network artifact evidence for R2A; never qualifies current inputs."""

import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import zipfile

from app.jobs.probe_krx_night_futures import (
    KST, _attach_fetch_telemetry, expected_latest_completed_krx_session,
    parse_krx_futures_payloads,
)
from app.services.unified_run_artifacts import durable_json
from app.services.unified_source_composition import SourceInput, SourceRole
from app.services.unified_source_observer import OhlcvRead


PRIOR_SHA = "afb6ab398e2ad0719690b8b18199a73050e717e7cc6b80d3cc65597e4dd1c199"


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(*, archive: Path, prior_zip: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError("evidence_output_already_exists")
    if file_sha(prior_zip) != PRIOR_SHA:
        raise ValueError("prior_r2_bundle_identity_mismatch")
    with zipfile.ZipFile(prior_zip) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("prior_r2_bundle_corrupt")
        prior_members = len(bundle.namelist())
        manifest = json.loads(bundle.read("bundle-manifest.json"))
        for name, row in manifest.items():
            raw = bundle.read(name)
            if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
                raise ValueError("prior_r2_manifest_mismatch")
    prior = {"sha256": PRIOR_SHA, "members": prior_members,
             "manifest_entries_verified": len(manifest),
             "adopted_final": "59690071f58f0be6ccbabf38999b7a0c5edddb38",
             "adopted_result": "M12DS_R6_R5F_R2_ADAPTER_PARITY_GAP_REMAINS"}
    durable_json(output / "prior-r2-identity.json", prior, exclusive=True)
    instruction = Path("docs/operations/UNIFIED_ACQUISITION_CLASSES.json")
    inventory = json.loads(instruction.read_bytes())
    durable_json(output / "acquisition-class-matrix.json", inventory, exclusive=True)
    durable_json(output / "receipt-schema.json", {
        "ohlcv_read": OhlcvRead.model_json_schema(), "source_input": SourceInput.model_json_schema(),
        "source_role": SourceRole.model_json_schema(),
        "scope": "opt-in unregistered composition; production owner adapters not qualified",
    }, exclusive=True)
    # These are genuine saved provider artifacts, not regenerated OHLC rows.
    probe_path = archive / "source/night-probe.json"
    original = json.loads(probe_path.read_bytes())
    payloads, hashes, bindings = {}, {}, []
    for receipt in original["date_statuses"]:
        day = date.fromisoformat(receipt["query_date"])
        path = archive / "source/krx-raw" / f"{day}.json"
        value = json.loads(path.read_bytes())
        owner_sha = file_sha(path)
        if owner_sha != receipt["raw_payload_sha256"]:
            raise ValueError("historical_owner_artifact_binding_mismatch")
        payloads[day], hashes[day] = value, owner_sha
        bindings.append({"source": str(path), "file_sha256": file_sha(path),
                         "original_owner_payload_sha256": owner_sha,
                         "original_http_status": receipt["http_status"], "query_date": str(day)})
    replay = parse_krx_futures_payloads(payloads,
        fetched_at=datetime.fromisoformat(original["fetched_at"]),
        queried_dates=[date.fromisoformat(d) for d in original["queried_dates"]],
        payload_sha256_by_date=hashes)
    original_time = datetime.fromisoformat(original["fetched_at"])
    replay = _attach_fetch_telemetry(replay, payloads=payloads,
        expected_session=expected_latest_completed_krx_session(original_time.astimezone(KST).date()),
        observation_time=original_time)
    actual = [o.model_dump(mode="json") for o in replay.observations]
    # Owner evolution can legitimately alter eligibility; keep it visible.
    durable_json(output / "genuine-saved-artifact-proof.json", {
        "source_probe_sha256": file_sha(probe_path), "original_fetched_at": original["fetched_at"],
        "artifacts": bindings, "owner": "parse_krx_futures_payloads",
        "replayed_observations": actual, "original_observations": original["observations"],
        "exact_observation_parity": actual == original["observations"],
        "parser_status": replay.parser_status, "night_session_usable": replay.night_session_usable,
        "classification": "HISTORICAL_OWNER_REPLAY_NOT_CURRENT_RUN_CLASS_B",
        "current_acquisition_claimed": False, "provider_calls": 0,
    }, exclusive=True)
    durable_json(output / "source-only-canary-plan.json", {
        "mode": "OFFLINE_ONLY", "planned_external_requests": [], "planned_request_count": 0,
        "reason": "Saved KRX source artifact replay and synthetic OHLCV wire mechanics; other owners remain unqualified.",
        "prohibited_provider_calls": 0, "model_calls": 0, "render_calls": 0,
        "delivery_calls": 0, "full_source_cohort_authorized_by_this_plan": False,
    }, exclusive=True)
    counts = {kind: sum(r["acquisition_class"] == kind for r in inventory["roles"])
              for kind in sorted({r["acquisition_class"] for r in inventory["roles"]})}
    durable_json(output / "inventory-review.json", {"role_count": len(inventory["roles"]),
        "class_counts": counts, "matrix_sha256": file_sha(instruction),
        "unique_roles": len({r["role"] for r in inventory["roles"]}) == len(inventory["roles"]),
        "mandatory_optional": [{"role": r["role"], "mandatory": r["mandatory"]} for r in inventory["roles"]],
        "activation": "OFF"}, exclusive=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--prior-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate(archive=args.archive, prior_zip=args.prior_zip, output=args.output)
    print("Offline evidence written; provider/model/delivery calls: 0")
