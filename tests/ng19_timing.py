"""Content-free timing of original calls; never replaces an owner or validator."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import time


def emit(event, **fields):
    destination = os.environ.get("NG19_TIMING_PATH")
    if not destination:
        return
    path = Path(destination)
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("NG19_TIMING_PATH_must_be_an_absolute_non_symlink")
    row = dict(event=event, monotonic_ns=time.monotonic_ns(), pid=os.getpid(), **fields)
    with path.open("a", encoding="ascii") as stream:
        stream.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


@contextmanager
def span(phase, **labels):
    start = time.monotonic_ns()
    emit("start", phase=phase, **labels)
    try:
        yield
    except BaseException as error:
        emit("end", phase=phase, outcome="RAISED", error_type=type(error).__name__,
             duration_ns=time.monotonic_ns() - start, **labels)
        raise
    else:
        emit("end", phase=phase, outcome="RETURNED", duration_ns=time.monotonic_ns() - start,
             **labels)


_WATCH = {
    ("rev8_source_fixtures.py", "fresh_inputs"): "owner_fixture",
    ("fresh_financial_stock_owner.py", "assemble_fresh_stock"): "owner_fixture",
    ("canonical_monitoring_source.py", "prepare_monitoring_source"): "whole_source",
    ("r9_rev11_replay.py", "replay_twice"): "whole_source_replay",
    ("r9_rev11_market_qualification.py", "qualify_markets"): "market_replay",
    ("canonical_native_source_owner.py", "resolve_subject"): "source_extraction",
    ("canonical_native_source_owner.py", "_record"): "source_owner_revalidation",
    ("direction_timing_ownership_service.py", "verified_owned_packet_view"): "original_packet_validation",
    ("canonical_native_admission.py", "produce_source_inputs"): "producer",
    ("canonical_native_admission.py", "_subject_evidence"): "subject_evidence",
    ("canonical_native_admission.py", "_source_input_bundle"): "per_subject_build",
    ("canonical_native_admission.py", "verify"): "admission_revalidation",
    ("manual_native_owner.py", "issue_manual_native_parents"): "parent",
    ("manual_native_owner.py", "_record"): "parent_revalidation",
    ("manual_shadow_source_session.py", "prepare"): "manual_prepare",
    ("manual_shadow_source_session.py", "admit_native"): "manual_admit_native",
    ("production_monitoring_session.py", "attach_manual_native_parent"): "parent_attach",
    ("production_monitoring_session.py", "native_manual_request"): "original_consumer",
}
_STREAM = {"owner_fixture", "whole_source", "whole_source_replay", "market_replay",
           "producer", "parent", "manual_prepare", "manual_admit_native", "parent_attach",
           "original_consumer"}


@contextmanager
def observe_original_calls(label):
    """Inclusive wall times overlap; counts explain amplification, not CPU attribution.

    Only explicit code names are observed. Existing profiling hooks are chained,
    and all arguments, returns, exceptions and application state are untouched.
    """
    if not os.environ.get("NG19_TIMING_PATH") or os.environ.get("NG19_PROFILE_CALLS") != "1":
        yield
        return
    previous = sys.getprofile()
    codes, active, totals = {}, {}, {}

    def profile(frame, event, arg):
        if previous is not None:
            previous(frame, event, arg)
        if event not in {"call", "return"}:
            return
        code = frame.f_code
        if code not in codes:
            codes[code] = _WATCH.get((code.co_filename.rsplit("/", 1)[-1], code.co_name))
        phase = codes[code]
        if phase is None:
            return
        if event == "call":
            ticker = frame.f_locals.get("ticker")
            ticker = ticker if isinstance(ticker, str) and ticker.isalnum() and len(ticker) <= 32 else None
            active[id(frame)] = time.monotonic_ns(), ticker
            if phase in _STREAM:
                emit("original_call_start", label=label, phase=phase, ticker=ticker,
                     function=code.co_name)
        else:
            started = active.pop(id(frame), None)
            if started is None:
                return
            duration = time.monotonic_ns() - started[0]
            key = (phase, code.co_name, started[1])
            total = totals.setdefault(key, dict(calls=0, inclusive_ns=0, max_ns=0))
            total["calls"] += 1
            total["inclusive_ns"] += duration
            total["max_ns"] = max(total["max_ns"], duration)
            if phase in _STREAM:
                emit("original_call_return", label=label, phase=phase, ticker=started[1],
                     function=code.co_name, duration_ns=duration,
                     note="return_event_is_not_a_test_pass")

    sys.setprofile(profile)
    try:
        yield
    finally:
        sys.setprofile(previous)
        for (phase, name, ticker), values in totals.items():
            emit("original_call_summary", label=label, phase=phase, function=name,
                 ticker=ticker, **values)
