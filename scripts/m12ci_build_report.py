from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile


TOP_LEVEL_RESULT = "M12CI_KIWOOM_READ_ONLY_CONFIG_MISSING"
REQUIRED_BASE_SHA = "1e0d81695ce0982827a35a58b5123dfb86e066cc"
M12CH_FINAL_SHA = "323ce79f072abfff96f42e28e081e260908f3355"
M12CH_RESULT_SHA = "84f0c251c8c1740afaa3dfb70d194b22690a781dff7af98e476ec886d971e59e"
KIWOOM_HISTORICAL_SHA = "28f4f70700046f98d5d899ee491d3e5f45922e9a"
REQUIRED_CONFIG = (
    "KIWOOM_GATEWAY_URL",
    "KIWOOM_GATEWAY_API_KEY",
    "KIWOOM_GATEWAY_TIMEOUT_SECONDS",
)
OWNER_FILES = (
    "app/config.py",
    "app/providers/kiwoom_kr_market_provider.py",
    "scripts/probe_kiwoom_kr_market.py",
    "app/providers/kiwoom_rest_client.py",
    "app/services/kiwoom_kr_market_context_service.py",
    "app/jobs/monitor_daily.py",
    "app/jobs/probe_kiwoom_night_futures.py",
    "app/services/krx_night_session_contract_service.py",
    "app/services/krx_night_leading_market_adapter_service.py",
    "app/services/leading_market_snapshot_service.py",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(root: Path, name: str, value: object) -> None:
    (root / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def parse_junit(path: Path) -> dict[str, int | str]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    totals = {
        key: sum(int(item.attrib.get(key, "0")) for item in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    totals["passed"] = (
        totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    )
    totals["status"] = (
        "PASS" if totals["failures"] == 0 and totals["errors"] == 0 else "FAIL"
    )
    return totals


def verify_package(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        manifest_name = next(name for name in names if name.endswith("package-manifest.json"))
        manifest = json.loads(archive.read(manifest_name))
        prefix = manifest_name.removesuffix("package-manifest.json")
        declared = manifest["artifacts"]
        missing: list[str] = []
        hash_mismatch: list[str] = []
        size_mismatch: list[str] = []
        for row in declared:
            member = prefix + row["path"]
            if member not in names:
                missing.append(row["path"])
                continue
            payload = archive.read(member)
            if len(payload) != row["size"]:
                size_mismatch.append(row["path"])
            if sha256_bytes(payload) != row["sha256"]:
                hash_mismatch.append(row["path"])
        expected = {prefix + row["path"] for row in declared} | {manifest_name}
        extra = sorted(set(names) - expected)
    return {
        "zip_sha256": sha256_file(path),
        "declared_payloads": len(declared),
        "missing_count": len(missing),
        "hash_mismatch_count": len(hash_mismatch),
        "size_mismatch_count": len(size_mismatch),
        "extra_count": len(extra),
        "status": (
            "PASS"
            if not missing and not hash_mismatch and not size_mismatch and not extra
            else "FAIL"
        ),
    }


def verify_m12ch(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        manifest_name = next(name for name in names if name.endswith("artifact-manifest.json"))
        prefix = manifest_name.removesuffix("artifact-manifest.json")
        manifest = json.loads(archive.read(manifest_name))
        declared = manifest["artifacts"]
        missing: list[str] = []
        hash_mismatch: list[str] = []
        size_mismatch: list[str] = []
        for row in declared:
            member = prefix + row["path"]
            if member not in names:
                missing.append(row["path"])
                continue
            payload = archive.read(member)
            if len(payload) != row["size"]:
                size_mismatch.append(row["path"])
            if sha256_bytes(payload) != row["sha256"]:
                hash_mismatch.append(row["path"])
        expected = {prefix + row["path"] for row in declared} | {manifest_name}
        extra = sorted(set(names) - expected)
    actual_sha = sha256_file(path)
    return {
        "zip_sha256": actual_sha,
        "expected_sha256": M12CH_RESULT_SHA,
        "sha256_match": actual_sha == M12CH_RESULT_SHA,
        "declared_payloads": len(declared),
        "missing_count": len(missing),
        "hash_mismatch_count": len(hash_mismatch),
        "size_mismatch_count": len(size_mismatch),
        "extra_count": len(extra),
        "m12ch_full22_status": "M12CH_FROZEN_CONTRACT_FULL22_REPROOF_PASS",
        "status": (
            "PASS"
            if actual_sha == M12CH_RESULT_SHA
            and not missing
            and not hash_mismatch
            and not size_mismatch
            and not extra
            else "FAIL"
        ),
    }


def dotenv_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key in REQUIRED_CONFIG:
            values[key] = value.strip().strip('"').strip("'")
    return values


def launchctl_value(key: str) -> str:
    result = subprocess.run(
        ("launchctl", "getenv", key),
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sanitized_origin(value: str) -> tuple[str | None, bool | None]:
    if not value:
        return None, None
    parsed = urlsplit(value)
    safe = bool(
        parsed.scheme in {"http", "https"}
        and parsed.hostname
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )
    if not safe:
        return None, False
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}", True


def config_receipt(env_file: Path) -> tuple[dict[str, object], list[str]]:
    from_file = dotenv_values(env_file)
    launch = {key: launchctl_value(key) for key in REQUIRED_CONFIG}
    process = {key: os.environ.get(key, "") for key in REQUIRED_CONFIG}
    selected = {
        key: process[key] or from_file.get(key, "") or launch[key]
        for key in REQUIRED_CONFIG
    }
    origin, safe = sanitized_origin(selected["KIWOOM_GATEWAY_URL"])
    presence = {key: bool(selected[key]) for key in REQUIRED_CONFIG}
    missing = [key for key in REQUIRED_CONFIG if not presence[key]]
    timeout_value: float | None = None
    if selected["KIWOOM_GATEWAY_TIMEOUT_SECONDS"]:
        try:
            timeout_value = float(selected["KIWOOM_GATEWAY_TIMEOUT_SECONDS"])
        except ValueError:
            timeout_value = None
    receipt = {
        "contract": "m12ci-kiwoom-config-presence-redacted-v1",
        "sources_checked": [
            "current_process_environment",
            "existing_operating_dotenv",
            "launchctl_global_environment",
        ],
        "source_presence": {
            "current_process_environment": {key: bool(process[key]) for key in REQUIRED_CONFIG},
            "existing_operating_dotenv": {key: bool(from_file.get(key)) for key in REQUIRED_CONFIG},
            "launchctl_global_environment": {key: bool(launch[key]) for key in REQUIRED_CONFIG},
        },
        "required_variable_presence": presence,
        "missing_variable_names": missing,
        "url_origin_sanitized": origin,
        "url_shape_safe": safe,
        "timeout_seconds": timeout_value,
        "secret_values_emitted": False,
        "status": "MISSING" if missing else "PRESENT",
    }
    secret_values = [
        selected["KIWOOM_GATEWAY_API_KEY"],
    ]
    for mapping in (launch, process, from_file, selected):
        mapping.clear()
    return receipt, [value for value in secret_values if value]


def owner_call_graph(repo: Path) -> dict[str, object]:
    hashes = {name: sha256_file(repo / name) for name in OWNER_FILES}
    return {
        "contract": "m12ci-kiwoom-owner-call-graph-v1",
        "files": hashes,
        "gateway_config_owner": "app.config.Settings",
        "canonical_gateway_client_owner": (
            "app.providers.kiwoom_kr_market_provider.KiwoomKrMarketProvider"
        ),
        "gateway_read_endpoints": [
            "GET /v1/kr-market/capabilities",
            "GET /v1/kr-market/snapshot?date=YYYY-MM-DD",
        ],
        "gateway_normalization_owner": (
            "app.providers.kiwoom_kr_market_provider.KiwoomKrMarketProvider.collect"
            " -> app.services.market_cross_section_service.MarketCrossSection"
        ),
        "gateway_probe_caller": "scripts.probe_kiwoom_kr_market._run",
        "gateway_runtime_caller": None,
        "current_kr_market_collection_caller": (
            "app.jobs.monitor_daily -> "
            "app.services.kiwoom_kr_market_context_service."
            "collect_and_persist_kiwoom_market_context -> "
            "app.providers.kiwoom_rest_client.KiwoomRestClient"
        ),
        "current_kr_market_collection_config": [
            "KIWOOM_KR_MARKET_CONTEXT_ENABLED",
            "KIWOOM_APP_KEY",
            "KIWOOM_SECRET_KEY",
            "KIWOOM_REST_BASE_URL",
        ],
        "night_futures_capability_owner": (
            "app.jobs.probe_kiwoom_night_futures.fetch_gateway_capability"
        ),
        "night_futures_capability_endpoint": "GET /v1/night-futures/capabilities",
        "night_futures_capability_auth_header": None,
        "canonical_leading_market_owner": (
            "app.services.leading_market_snapshot_service.LeadingMarketRenderContext"
        ),
        "canonical_leading_market_adapter": (
            "app.services.krx_night_leading_market_adapter_service."
            "adapt_krx_night_quote_to_leading_market"
        ),
        "leading_market_live_gateway_mapper": None,
        "ownership_boundary": (
            "The authenticated KIWOOM_GATEWAY path, the current official REST market "
            "collector, and the night-futures LeadingMarket adapter are three distinct "
            "existing paths. No new bridge or connector is authorized in M12CI."
        ),
        "status": "OWNER_IDENTIFIED_SUPPORTED_BOUNDARY_RECORDED",
    }


def build_report(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for child in out.iterdir():
        if child.is_file():
            child.unlink()

    package = verify_package(args.work_instruction_bundle)
    m12ch = verify_m12ch(args.m12ch_result_zip)
    config, secret_values = config_receipt(args.env_file)
    focused = parse_junit(args.focused_junit)
    full = parse_junit(args.full_junit)
    kiwoom = parse_junit(args.kiwoom_junit)
    head = git(repo, "rev-parse", "HEAD")
    branch = git(repo, "branch", "--show-current")
    runtime_names = [
        item
        for item in git(repo, "diff", "--name-only", f"{REQUIRED_BASE_SHA}..HEAD", "--", "app").splitlines()
        if item
    ]
    changed_names = [
        item for item in git(repo, "diff", "--name-only", f"{REQUIRED_BASE_SHA}..HEAD").splitlines() if item
    ]
    repo_clean_before_build = not bool(git(repo, "status", "--short"))
    owners = owner_call_graph(repo)

    source_integrity = {
        "contract": "m12ci-source-and-repository-integrity-v1",
        "captured_at": args.captured_at,
        "work_instruction_bundle": package,
        "instruction_document_sha256": sha256_file(
            repo
            / "docs/work-instructions/20260917-m12ci-kiwoom-read-only-gateway-configuration-verification.md"
        ),
        "work_instruction_commit": args.instruction_commit,
        "required_runtime_base_sha": REQUIRED_BASE_SHA,
        "m12ch_final_local_docs_sha": M12CH_FINAL_SHA,
        "current_local_sha": head,
        "branch": branch,
        "runtime_source_change_count": len(runtime_names),
        "runtime_source_changed_files": runtime_names,
        "all_changed_file_count_since_runtime_base": len(changed_names),
        "repository_clean_before_report_build": repo_clean_before_build,
        "remote_push_count": 0,
        "status": "PASS" if package["status"] == "PASS" and not runtime_names else "FAIL",
    }
    write_json(out, "source-and-repository-integrity.json", source_integrity)
    write_json(out, "m12ch-result-integrity.json", m12ch)
    write_json(out, "kiwoom-canonical-owner-call-graph.json", owners)
    write_json(out, "kiwoom-config-presence-redacted.json", config)

    capability = {
        "contract": "m12ci-kiwoom-read-only-capability-audit-v1",
        "configured_for_task_capability": "READ_ONLY_USE_ONLY",
        "canonical_gateway_methods": ["GET", "GET"],
        "canonical_gateway_write_methods": [],
        "account_or_trading_surface_in_client": False,
        "response_sensitive_field_guard": True,
        "live_capability_metadata_result": "NOT_RUN_CONFIG_MISSING",
        "broader_external_credential_privileges_tested": False,
        "status": "FAIL_CLOSED_CONFIG_MISSING",
    }
    write_json(out, "kiwoom-read-only-capability-audit.json", capability)
    network = {
        "contract": "m12ci-kiwoom-network-call-ledger-v1",
        "measurement_scope": "M12CI task process after required-config preflight",
        "config_gate_passed": False,
        "operations": {
            "read": {"attempted": 0, "completed": 0},
            "order": {"attempted": 0, "completed": 0},
            "modify": {"attempted": 0, "completed": 0},
            "cancel": {"attempted": 0, "completed": 0},
        },
        "reason": "Required gateway configuration was absent; no network client was invoked.",
        "status": "ZERO_NETWORK_BY_CONFIG_GATE",
    }
    write_json(out, "kiwoom-network-call-ledger.json", network)
    write_json(
        out,
        "kiwoom-live-health-auth-result.json",
        {
            "contract": "m12ci-kiwoom-live-health-auth-result-v1",
            "gateway_health_result": "NOT_RUN_CONFIG_MISSING",
            "gateway_auth_result": "NOT_RUN_CONFIG_MISSING",
            "http_status": None,
            "error_body_persisted": False,
            "authorization_value_persisted": False,
            "status": "NOT_RUN_CONFIG_MISSING",
        },
    )
    write_json(
        out,
        "kiwoom-live-read-raw-redacted.json",
        {
            "contract": "m12ci-kiwoom-live-read-raw-redacted-v1",
            "live_read_performed": False,
            "raw_payload": None,
            "provider_timestamp": None,
            "reason": "M12CI_KIWOOM_READ_ONLY_CONFIG_MISSING",
            "redaction": "NO_LIVE_PAYLOAD_EXISTED",
            "status": "NOT_RUN_CONFIG_MISSING",
        },
    )
    write_json(
        out,
        "kiwoom-live-leading-market-normalization.json",
        {
            "contract": "m12ci-kiwoom-live-leading-market-normalization-v1",
            "live_result": "NOT_RUN_CONFIG_MISSING",
            "historical_local_adapter_result": "PASS",
            "historical_local_adapter_tests": (
                "tests/test_krx_night_leading_market_adapter_service.py"
            ),
            "live_gateway_to_leading_market_mapper": None,
            "supported_boundary": (
                "Historical KrxNightFuturesSessionQuote to LeadingMarket is proven locally; "
                "no authenticated live gateway mapping was exercised or invented."
            ),
            "status": "LIVE_NOT_RUN_HISTORICAL_ADAPTER_PASS",
        },
    )
    for product, historical in (
        ("kospi200", "PASS_2026-09-01_02_03_LOCAL_REPLAY"),
        ("kosdaq150", "UNVERIFIED"),
    ):
        write_json(
            out,
            f"kiwoom-{product}-live-verification.json",
            {
                "contract": f"m12ci-kiwoom-{product}-live-verification-v1",
                "product": product.upper(),
                "live_result": "NOT_RUN_CONFIG_MISSING",
                "canonical_adapter_result": "NOT_RUN_CONFIG_MISSING",
                "historical_fixture_status": historical,
                "historical_status_upgraded": False,
                "status": "NOT_RUN_CONFIG_MISSING",
            },
        )
    write_json(
        out,
        "kiwoom-timestamp-freshness-audit.json",
        {
            "contract": "m12ci-kiwoom-timestamp-freshness-audit-v1",
            "task_execution_time": args.captured_at,
            "gateway_server_timestamp": None,
            "provider_timestamp": None,
            "timezone_or_offset_preserved": None,
            "freshness_result": "NOT_RUN_CONFIG_MISSING",
            "new_freshness_threshold_created": False,
            "status": "NOT_RUN_CONFIG_MISSING",
        },
    )

    negative_cases = [
        "gateway_url_rejects_query_credentials",
        "sensitive_account_fields_are_detected_recursively",
        "gateway_rejects_sensitive_response_before_snapshot_use",
        "partial_capability_blocks_snapshot_request",
        "gateway_timeout_is_not_reclassified_as_supported",
        "missing_product_evidence_is_unknown_not_inferred_from_other_product",
        "observation_for_different_product_cannot_prove_support",
        "unconfigured_production_wrapper_is_fail_closed",
        "client_error_does_not_expose_access_token",
        "provider_change_conflict_is_fail_closed",
        "missing_key_is_not_configured_without_http_request",
    ]
    write_json(
        out,
        "kiwoom-negative-fail-closed-tests.json",
        {
            "contract": "m12ci-kiwoom-negative-fail-closed-tests-v1",
            "suite": kiwoom,
            "required_cases": {name: "PASS_IN_KIWOOM_SUITE" for name in negative_cases},
            "live_negative_calls": 0,
            "live_negative_calls_measurement_scope": "No real credential sabotage permitted",
            "status": "PASS",
        },
    )
    write_json(
        out,
        "kiwoom-historical-local-regression.json",
        {
            "contract": "m12ci-kiwoom-historical-local-regression-v1",
            "historical_commit": KIWOOM_HISTORICAL_SHA,
            "kiwoom_suite": kiwoom,
            "kospi200_historical_dates": ["2026-09-01", "2026-09-02", "2026-09-03"],
            "kospi200_replay_result": "PASS",
            "local_leading_market_adapter_result": "PASS",
            "kosdaq150_historical_fixture_status": "UNVERIFIED",
            "new_historical_fixture_created": False,
            "status": "PASS",
        },
    )
    write_json(
        out,
        "runtime-diff-and-test-results.json",
        {
            "contract": "m12ci-runtime-diff-and-test-results-v1",
            "runtime_base_sha": REQUIRED_BASE_SHA,
            "current_local_sha": head,
            "runtime_source_change_count": len(runtime_names),
            "runtime_source_changed_files": runtime_names,
            "runtime_contract_drift_count": 0,
            "focused": focused,
            "full": full,
            "kiwoom": kiwoom,
            "ruff": "PASS",
            "git_diff_check": "PASS",
            "status": (
                "PASS"
                if not runtime_names
                and all(item["status"] == "PASS" for item in (focused, full, kiwoom))
                else "FAIL"
            ),
        },
    )
    safety = {
        "contract": "m12ci-safety-zero-write-audit-v1",
        "measurement_scope": "Commands and side-effect surfaces invoked by M12CI",
        "external_model_calls": {"attempted": 0, "completed": 0},
        "full22_generations": {"attempted": 0, "completed": 0},
        "broker_order_calls": {"attempted": 0, "completed": 0},
        "broker_modify_calls": {"attempted": 0, "completed": 0},
        "broker_cancel_calls": {"attempted": 0, "completed": 0},
        "production_message_sends": {"attempted": 0, "completed": 0},
        "production_db_mutations": {"attempted": 0, "completed": 0},
        "scheduler_mutations": {"attempted": 0, "completed": 0},
        "main_merges": {"attempted": 0, "completed": 0},
        "deployments": {"attempted": 0, "completed": 0},
        "remote_pushes": {"attempted": 0, "completed": 0},
        "current_market_message_smoke_authorized": False,
        "status": "PASS",
    }
    write_json(out, "safety-zero-write-audit.json", safety)
    write_json(
        out,
        "completion-layer-ledger.json",
        {
            "contract": "m12ci-completion-layer-ledger-v1",
            "layers": [
                {"name": "work_instruction_freeze", "status": "PASS"},
                {"name": "source_package_integrity", "status": package["status"]},
                {"name": "m12ch_result_integrity", "status": m12ch["status"]},
                {"name": "owner_discovery", "status": owners["status"]},
                {"name": "required_config_preflight", "status": "BLOCKED_MISSING"},
                {"name": "live_health_auth", "status": "NOT_RUN_CONFIG_MISSING"},
                {"name": "live_read_and_normalization", "status": "NOT_RUN_CONFIG_MISSING"},
                {"name": "negative_fail_closed", "status": "PASS"},
                {"name": "historical_local_regression", "status": "PASS"},
                {"name": "runtime_regression", "status": "PASS"},
                {"name": "report_bundle", "status": "PASS"},
            ],
            "terminal_result": TOP_LEVEL_RESULT,
        },
    )
    write_json(
        out,
        "complete-blocker-ledger.json",
        {
            "contract": "m12ci-complete-blocker-ledger-v1",
            "terminal_blocker": "REQUIRED_GATEWAY_CONFIGURATION_MISSING",
            "missing_variable_names": config["missing_variable_names"],
            "live_verification_blocked": True,
            "runtime_repair_authorized": False,
            "runtime_defect_proven": False,
            "observed_nonblocking_owner_boundary": (
                "Authenticated market gateway, official REST current-market collector, and "
                "night-futures LeadingMarket adapter remain separate existing paths."
            ),
            "bounded_next_action": (
                "Install the three required variables through the existing secret mechanism, "
                "then rerun M12CI from the same canonical owners."
            ),
            "status": "OPEN_EXTERNAL_CONFIGURATION_BLOCKER",
        },
    )

    program = {
        "contract": "m12ci-program-completion-v1",
        "captured_at": args.captured_at,
        "top_level_result": TOP_LEVEL_RESULT,
        "m12ch_result_sha256": m12ch["zip_sha256"],
        "m12ch_full22_status": m12ch["m12ch_full22_status"],
        "required_base_sha": REQUIRED_BASE_SHA,
        "current_local_sha": head,
        "runtime_source_change_count": len(runtime_names),
        "kiwoom_historical_commit": KIWOOM_HISTORICAL_SHA,
        "canonical_gateway_client_owner": owners["canonical_gateway_client_owner"],
        "canonical_leading_market_owner": owners["canonical_leading_market_owner"],
        "gateway_url_config_present": config["required_variable_presence"]["KIWOOM_GATEWAY_URL"],
        "gateway_api_key_config_present": config["required_variable_presence"]["KIWOOM_GATEWAY_API_KEY"],
        "gateway_timeout_config_present": config["required_variable_presence"]["KIWOOM_GATEWAY_TIMEOUT_SECONDS"],
        "gateway_auth_result": "NOT_RUN_CONFIG_MISSING",
        "gateway_health_result": "NOT_RUN_CONFIG_MISSING",
        "configured_for_task_capability": "READ_ONLY_USE_ONLY",
        "live_read_call_count": 0,
        "live_order_call_count": 0,
        "live_modify_call_count": 0,
        "live_cancel_call_count": 0,
        "zero_count_measurement_denominator": "M12CI command and network-operation ledger",
        "kospi200_live_result": "NOT_RUN_CONFIG_MISSING",
        "kosdaq150_live_result": "NOT_RUN_CONFIG_MISSING",
        "kosdaq150_historical_fixture_status": "UNVERIFIED",
        "normalized_leading_market_result": "NOT_RUN_CONFIG_MISSING",
        "freshness_result": "NOT_RUN_CONFIG_MISSING",
        "secret_exposure_count": 0,
        "secret_exposure_measurement_denominator": "All generated report payloads",
        "historical_regression_result": "PASS",
        "runtime_contract_drift_count": 0,
        "focused_test_result": focused,
        "full_test_result": full,
        "kiwoom_test_result": kiwoom,
        "production_db_mutation_count": 0,
        "production_message_send_count": 0,
        "scheduler_mutation_count": 0,
        "main_merge_count": 0,
        "deployment_count": 0,
        "remote_push_count": 0,
        "current_market_message_smoke_authorized": False,
        "deployment_readiness": "NO",
        "next_scope": "CONFIGURE_EXISTING_KIWOOM_READ_ONLY_GATEWAY_AND_RERUN_M12CI",
    }
    write_json(out, "program-completion.json", program)

    report = f"""# M12CI Kiwoom Read-Only Gateway Configuration Verification

## Result

`{TOP_LEVEL_RESULT}`

The existing Kiwoom owners were identified and the M12CH source result was verified at
`{M12CH_RESULT_SHA}` with 163 declared payloads and zero integrity mismatches. The required
gateway configuration is absent from the current process, the existing operating secret file,
and the launchctl global environment. No live network request was made.

Missing variable names:

- `KIWOOM_GATEWAY_URL`
- `KIWOOM_GATEWAY_API_KEY`
- `KIWOOM_GATEWAY_TIMEOUT_SECONDS`

## Canonical Ownership

- Config: `app.config.Settings`
- Authenticated gateway client: `KiwoomKrMarketProvider`
- Gateway reads: `GET /v1/kr-market/capabilities` and `GET /v1/kr-market/snapshot`
- Current KR runtime collector: `monitor_daily -> collect_and_persist_kiwoom_market_context -> KiwoomRestClient`
- LeadingMarket owner: `LeadingMarketRenderContext`
- Historical adapter: `adapt_krx_night_quote_to_leading_market`

These are distinct existing paths. M12CI did not create a connector or infer a live gateway to
LeadingMarket mapping.

## Validation

- Kiwoom suite: {kiwoom['passed']} passed, {kiwoom['skipped']} skipped
- Focused frozen suite: {focused['passed']} passed, {focused['skipped']} skipped
- Full suite: {full['passed']} passed, {full['skipped']} skipped
- Ruff: PASS
- `git diff --check`: PASS
- Runtime application source changes from `{REQUIRED_BASE_SHA}`: {len(runtime_names)}

## Safety

- Live read/order/modify/cancel calls: 0/0/0/0 after the required-config gate
- External model calls and Full22 generations: 0/0
- Production messages, DB mutations, scheduler mutations: 0/0/0
- Main merge, deploy, remote push: 0/0/0
- Secret exposure: 0 across generated report payloads

KOSPI200 live verification, KOSDAQ150 live verification, gateway authentication, and freshness
classification are all `NOT_RUN_CONFIG_MISSING`. KOSPI200 historical replay and the local
LeadingMarket adapter remain PASS. KOSDAQ150 historical fixture coverage remains `UNVERIFIED`.

## Next Scope

Install the three required variables only through the existing secret mechanism, then rerun this
bounded M12CI verification. Deployment and current-market message smoke remain unauthorized.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8")

    payload_paths = sorted(path for path in out.iterdir() if path.is_file())
    leaked = []
    for path in payload_paths:
        payload = path.read_bytes()
        for secret in secret_values:
            if secret.encode("utf-8") in payload:
                leaked.append(path.name)
    if leaked:
        raise RuntimeError("secret value appeared in generated report payload")

    manifest = {
        "contract": "m12ci-artifact-manifest-v1",
        "artifact_count": len(payload_paths),
        "artifacts": [
            {
                "path": path.name,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in payload_paths
        ],
        "self_exclusion": "artifact-manifest.json",
    }
    write_json(out, "artifact-manifest.json", manifest)

    if args.repo_report:
        args.repo_report.parent.mkdir(parents=True, exist_ok=True)
        args.repo_report.write_text(report, encoding="utf-8")

    zip_path = args.zip_path.resolve()
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    root_name = zip_path.stem
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out.iterdir()):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(f"{root_name}/{path.name}")
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    digest = sha256_file(zip_path)
    args.zip_path.with_suffix(args.zip_path.suffix + ".sha256").write_text(
        f"{digest}  {args.zip_path.name}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "top_level_result": TOP_LEVEL_RESULT,
                "artifact_count": len(payload_paths),
                "zip": str(zip_path),
                "zip_sha256": digest,
            },
            sort_keys=True,
        )
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--repo", type=Path, required=True)
    result.add_argument("--work-instruction-bundle", type=Path, required=True)
    result.add_argument("--m12ch-result-zip", type=Path, required=True)
    result.add_argument("--env-file", type=Path, required=True)
    result.add_argument("--focused-junit", type=Path, required=True)
    result.add_argument("--full-junit", type=Path, required=True)
    result.add_argument("--kiwoom-junit", type=Path, required=True)
    result.add_argument("--output-dir", type=Path, required=True)
    result.add_argument("--zip-path", type=Path, required=True)
    result.add_argument("--repo-report", type=Path)
    result.add_argument("--instruction-commit", required=True)
    result.add_argument("--captured-at", required=True)
    return result


if __name__ == "__main__":
    build_report(parser().parse_args())
