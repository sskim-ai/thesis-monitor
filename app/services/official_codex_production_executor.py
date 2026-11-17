"""Production executor preserving the byte-frozen historical shadow transport.

The historical module stays immutable. Body parity is independently tested;
production authorization remains outside the model-visible input.
"""
import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from time import monotonic

from app.services.official_codex_shadow_transport_service import (
    command_prefix, OfficialShadowError, _require,
    file_sha256, classify_input_events,
)
from app.services.codex_runtime_binding import validate_binding, invocation_environment


def model_failure_diagnosis(raw):
    """Read protocol error objects, not model prose or provider error text."""
    rows=[]
    for line in raw.splitlines():
        try:
            value = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if not isinstance(value, dict):
            continue
        candidates=[(value.get('error'),value)]
        if value.get('type') in {'error','turn.failed'}:
            nested=value.get('error')
            message=value.get('message') or (nested.get('message') if isinstance(nested,dict) else None)
            if isinstance(message,str):
                try:
                    decoded=json.loads(message)
                except (ValueError,UnicodeError):
                    pass
                else:
                    if isinstance(decoded,dict):candidates.append((decoded.get('error'),decoded))
        for error,envelope in candidates:
            if not isinstance(error,dict):continue
            row={key:error[key] for key in ('code','type') if isinstance(error.get(key),str)
                and 0<len(error[key])<=80 and all(c.isalnum() or c=='_' for c in error[key])}
            for key in ('status','status_code'):
                if type(error.get(key)) is int and 100<=error[key]<=599:row['status']=error[key]
            if 'status' not in row and type(envelope.get('status')) is int and 100<=envelope['status']<=599:
                row['status']=envelope['status']
            # Only explicit machine reset fields; never infer a reset from prose.
            for key in ('retry_after_seconds','reset_at'):
                v=error.get(key)
                if type(v) in (int,float) and v>=0:row[key]=v
            if row and row not in rows:rows.append(row)
    codes={r.get(k) for r in rows for k in ('code','type')}
    statuses={r.get('status') for r in rows}
    if codes&{'model_not_found','model_not_available'}:kind='MODEL_CLIENT_ACCOUNT_COMBINATION_UNSUPPORTED'
    elif codes&{'workspace_mismatch','organization_mismatch','workspace_not_found'}:kind='AUTH_WORKSPACE_MISMATCH'
    elif codes&{'invalid_api_key','authentication_error','unauthorized','token_expired'} or 401 in statuses:kind='AUTHENTICATION_FAILURE'
    elif codes&{'usage_limit_reached','quota_exceeded','insufficient_quota','rate_limit_exceeded'} or 429 in statuses:kind='QUOTA_OR_RATE_LIMIT'
    else:kind='PROCESS_ERROR_UNCLASSIFIED'
    return dict(classification=kind,server_errors=rows,provider_text_exported=False,
        reset_information='OBSERVED' if any('retry_after_seconds' in r or 'reset_at' in r for r in rows) else 'UNOBSERVED')


def _availability_failure(raw):
    kind=model_failure_diagnosis(raw)['classification']
    return {'MODEL_CLIENT_ACCOUNT_COMBINATION_UNSUPPORTED':'MODEL_ENTITLEMENT_OR_QUOTA_UNAVAILABLE',
        'QUOTA_OR_RATE_LIMIT':'MODEL_ENTITLEMENT_OR_QUOTA_UNAVAILABLE',
        'AUTHENTICATION_FAILURE':'MODEL_AUTHENTICATION_FAILED',
        'AUTH_WORKSPACE_MISMATCH':'MODEL_WORKSPACE_MISMATCH'}.get(kind,'PROCESS_NONZERO')


def _run_observed_market(command, *, cwd, prompt, stdout, stderr, timeout, options, receipt, request):
    """Persist invocation metadata even when the original CLI never returns output."""
    from app.services.unified_run_artifacts import durable_json

    readback = cwd.parent / "market-cli-dispatch.json"
    exit_path = cwd.parent / "market-cli-exit.json"
    start = datetime.now(UTC)
    tick = monotonic()
    binding = request.binding
    policy = request.execution_policy
    durable_json(readback, dict(argv_sha256=hashlib.sha256(json.dumps(
        command, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
        invocation_identity_sha256=receipt["invocation_identity_sha256"],
        cli_version=binding.version, binary_sha256=binding.executable_sha256,
        auth_method=getattr(binding, "auth_method", None),
        isolated_environment=options.get("env") is not None,
        sandbox=command[command.index("--sandbox")+1],
        model=policy.model, effort=policy.effort, max_calls=policy.max_calls,
        timeout_seconds=timeout, retries=policy.retries, prompt_bytes=len(prompt),
        dispatched_at=start.isoformat()), exclusive=True)
    process = None
    timed_out = False
    try:
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.PIPE, stdout=stdout,
            stderr=stderr, **options)
        with process:
            try:
                process.communicate(prompt, timeout=timeout)
            except BaseException as exc:
                timed_out = isinstance(exc, subprocess.TimeoutExpired)
                if process.poll() is None:
                    process.kill()
                process.wait()
                if timed_out:
                    refusal = OfficialShadowError("TRANSPORT_TIMEOUT", process_started=True)
                    refusal.cli_returncode = process.returncode
                    raise refusal from exc
                raise
        return process
    finally:
        # Event bodies remain private; an absent completion is not a provider error.
        first = last = None
        completion = 0
        truncated = False
        allowed = {"thread.started", "turn.started", "item.started", "item.updated",
            "item.completed", "turn.completed", "turn.failed", "error"}
        with open(stdout.name, "rb") as events:
            for _ in range(4096):
                line = events.readline(128 * 1024 + 1)
                if not line:
                    break
                if len(line) > 128 * 1024:
                    truncated = True
                    break
                try:
                    node = json.loads(line)
                except (UnicodeError, ValueError):
                    continue
                kind = node.get("type") if isinstance(node, dict) else None
                if isinstance(kind, str) and kind in allowed:
                    first = first or kind
                    last = kind
                    completion += kind == "turn.completed"
            else:
                truncated = bool(events.read(1))
        durable_json(exit_path, dict(process_started=process is not None,
            cli_returncode=process.returncode if process is not None else None, timed_out=timed_out,
            first_event=first, last_event=last, completed_turns=completion,
            event_scan_truncated=truncated, elapsed_seconds=round(monotonic()-tick, 3),
            ended_at=datetime.now(UTC).isoformat()), exclusive=True)


def invoke_official_bound(*, codex_bin, prompt, output, log, schema, cwd, timeout,
                          state_namespace, request, receipt_contract):
    """Execute only a separately authorized production request."""
    from app.services.production_model_transport import request_profile
    profile = request_profile(request)
    validate_binding(request.binding, codex_bin, profile=profile)
    request.execution_policy.validate()
    _require(
        type(timeout) is int
        and timeout == request.execution_policy.timeout_seconds
        and state_namespace == request.request_id,
        "REQUEST_ID_OR_TIMEOUT_DRIFT",
    )
    _require(cwd.is_absolute() and cwd.is_dir() and not cwd.is_symlink(), "INPUT_CWD_INVALID")
    _require(
        not any((parent / ".git").exists() for parent in (cwd, *cwd.parents)),
        "INPUT_CWD_INSIDE_REPOSITORY",
    )
    _require(
        prompt == cwd / "prompt.txt" and schema == cwd / "provider-wire-schema.json",
        "REQUEST_INPUT_LAYOUT_INVALID",
    )
    _require(
        set(cwd.iterdir()) == {prompt, schema}
        and all(path.is_file() and not path.is_symlink() for path in (prompt, schema)),
        "UNDECLARED_INPUT_PRESENT",
    )
    prompt_bytes = prompt.read_bytes()
    schema_bytes = schema.read_bytes()
    _require(hashlib.sha256(prompt_bytes).hexdigest() == request.prompt_sha256, "PROMPT_DRIFT")
    _require(hashlib.sha256(schema_bytes).hexdigest() == request.schema_sha256, "SCHEMA_DRIFT")
    try:
        prompt_bytes.decode("utf-8", errors="strict")
        _require(isinstance(json.loads(schema_bytes), dict), "SCHEMA_INVALID")
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OfficialShadowError("INPUT_ENCODING_OR_SCHEMA_INVALID") from exc
    stderr = log.with_name(log.name + ".stderr")
    claim = output.with_name(output.name + ".invocation")
    paths = (output, log, stderr, claim)
    _require(
        len(set(paths)) == 4
        and all(
            path.is_absolute()
            and path.parent == cwd.parent
            and not path.exists()
            and not path.is_symlink()
            for path in paths
        ),
        "OUTPUT_NOT_EXCLUSIVE",
    )
    command = [
        codex_bin,
        *command_prefix(profile),
        "--output-schema",
        str(schema),
        "-o",
        str(output),
        "-",
    ]
    # The exclusive claim survives failure: the same request directory cannot be retried.
    try:
        with claim.open("x", encoding="utf-8") as stream:
            stream.write(request.request_id)
    except FileExistsError as exc:
        raise OfficialShadowError("OUTPUT_NOT_EXCLUSIVE") from exc
    receipt: dict[str, object] = {
        "contract": receipt_contract,
        "request_id": request.request_id,
        "transport_attempts": 1,
        "network_probe_attempts": 0,
        "retry_recovered": False,
        "provider_attempts": "UNOBSERVABLE_CLI_INTERNAL",
        "source_only_inference_certified": False,
        "qualification_sha256": request.binding.qualification_sha256,
        "execution_policy": asdict(request.execution_policy),
        "invocation_identity_sha256": hashlib.sha256(
            json.dumps(
                {
                    "argv": command,
                    "request_id": request.request_id,
                    "prompt_sha256": request.prompt_sha256,
                    "schema_sha256": request.schema_sha256,
                    "executable_sha256": request.binding.executable_sha256,
                    "qualification_sha256": request.binding.qualification_sha256,
                    "timeout": timeout,
                    "execution_policy": asdict(request.execution_policy),
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
    }
    if profile is not None:
        receipt.update(command=command, prompt_sha256=request.prompt_sha256,
                       schema_sha256=request.schema_sha256, model_entitlement='UNKNOWN_UNTIL_APPROVED_CALL')
        if request.model_plan_scope is not None:
            receipt['model_plan_scope'] = request.model_plan_scope
    try:
        with log.open("xb") as events, stderr.open("xb") as errors:
            environment=invocation_environment(request.binding,
                root=cwd.parent/'runtime-state',namespace=request.request_id)
            options={} if environment is None else dict(env=environment)
            if profile is not None and ((request.model_plan_scope or {}).get("stage") == "MARKET"
                                        or getattr(request,"observe_timeout",False)):
                process = _run_observed_market(command, cwd=cwd, prompt=prompt_bytes, stdout=events,
                    stderr=errors, timeout=timeout, options=options, receipt=receipt, request=request)
            else:
                process = subprocess.run(command, cwd=cwd, input=prompt_bytes, stdout=events,
                    stderr=errors, timeout=timeout, check=False, **options)
    except subprocess.TimeoutExpired as exc:
        raise OfficialShadowError("TRANSPORT_TIMEOUT", process_started=True) from exc
    except OSError as exc:
        raise OfficialShadowError("PROCESS_START_FAILED") from exc
    if process.returncode != 0:
        code = _availability_failure(log.read_bytes()) if profile is not None else 'PROCESS_NONZERO'
        error=OfficialShadowError(code,process_started=True)
        error.cli_returncode=process.returncode
        error.diagnosis=model_failure_diagnosis(log.read_bytes())
        raise error
    if file_sha256(prompt) != request.prompt_sha256 or file_sha256(schema) != request.schema_sha256:
        raise OfficialShadowError("INPUT_CHANGED_DURING_INVOCATION", process_started=True)
    if not output.is_file() or output.is_symlink() or not output.stat().st_size:
        raise OfficialShadowError("FINAL_OUTPUT_EMPTY", process_started=True)
    try:
        final = json.loads(output.read_bytes())
        if not isinstance(final, dict):
            raise ValueError
    except (ValueError, UnicodeError) as exc:
        raise OfficialShadowError("FINAL_OUTPUT_MALFORMED", process_started=True) from exc
    receipt["input_boundary"] = classify_input_events(log.read_bytes())
    receipt['cli_returncode']=process.returncode
    if receipt["input_boundary"]["state"] != "DECLARED_INPUT_WITH_DOCUMENTED_RUNTIME_LIMITS":
        raise OfficialShadowError(receipt["input_boundary"]["state"], process_started=True)
    return receipt
