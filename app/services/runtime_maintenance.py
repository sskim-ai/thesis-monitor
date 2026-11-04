"""Explicit startup-only maintenance hold; no public administration endpoint."""
from contextlib import contextmanager
import hashlib
import inspect
import json
import marshal
import os
from pathlib import Path
import threading
import time
import types

_MODE = os.environ.get("KIWOOM_MAINTENANCE_STARTUP", "0")


class MaintenanceDenied(RuntimeError):
    pass


def maintenance_enabled():
    current = os.environ.get("KIWOOM_MAINTENANCE_STARTUP", "0")
    if current != _MODE or _MODE not in ("0", "1"):
        raise MaintenanceDenied("maintenance_startup_mode_changed")
    return _MODE == "1"


def assert_operation_allowed():
    if maintenance_enabled():
        raise MaintenanceDenied("maintenance_hold_no_new_job_or_provider_call")


class RequestDrain:
    def __init__(self):
        self._condition = threading.Condition()
        self._active = 0
        self._accepting = True

    @contextmanager
    def operation(self):
        with self._condition:
            if not self._accepting:
                raise MaintenanceDenied("request_admission_closed")
            self._active += 1
        try:
            yield
        finally:
            with self._condition:
                self._active -= 1
                self._condition.notify_all()

    def drain(self, timeout=5):
        if not 0 < timeout <= 30:
            raise ValueError("bounded_drain_timeout_required")
        deadline = time.monotonic() + timeout
        with self._condition:
            self._accepting = False
            while self._active:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise MaintenanceDenied("inflight_drain_timeout_admission_stays_closed")
                self._condition.wait(remaining)
            return self.snapshot()

    def snapshot(self):
        with self._condition:
            return dict(pid=os.getpid(), accepting=self._accepting, active=self._active,
                        scope="THIS_LOADED_HTTP_PROCESS_NOT_SCHEDULED_OR_REMOTE")


class MaintenanceMiddleware:
    def __init__(self, app, control):
        self.app, self.control = app, control

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        try:
            with self.control.operation():
                if maintenance_enabled() and not (
                        scope["type"] == "http" and scope.get("method") == "GET"
                        and scope.get("path") in ("/", "/health")):
                    raise MaintenanceDenied("maintenance_health_only")
                return await self.app(scope, receive, send)
        except MaintenanceDenied:
            if scope["type"] == "websocket":
                await send(dict(type="websocket.close", code=1013))
            else:
                body=b'{"detail":"maintenance_admission_closed"}'
                await send(dict(type="http.response.start", status=503,
                                headers=[(b"content-type",b"application/json")]))
                await send(dict(type="http.response.body", body=body))


def loaded_identity(module):
    """Match loaded definitions to compiled on-disk definitions, not cwd/health alone."""
    path = Path(module.__file__).absolute()
    raw = path.read_bytes()
    expected = {}
    def walk(code):
        expected[(code.co_qualname, code.co_firstlineno)] = code
        for c in code.co_consts:
            if isinstance(c, types.CodeType):
                walk(c)
    walk(compile(raw, str(path), "exec", dont_inherit=True, optimize=0))
    actual = {}
    excluded = []
    for obj in vars(module).values():
        functions = [obj]
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            functions += [v.__func__ if isinstance(v,(classmethod,staticmethod)) else v for v in vars(obj).values()]
        for fn in functions:
            if inspect.isfunction(fn) and fn.__module__ == module.__name__:
                import dataclasses
                generated = getattr(fn, "__wrapped__", fn)
                if (inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__")
                        and generated.__code__.co_filename == "<string>"
                        and fn.__code__.co_filename in ("<string>", dataclasses.__file__)):
                    excluded.append(fn.__qualname__ + ":dataclass_generated")
                    continue
                # contextlib decorators retain the underlying source definition.
                if hasattr(fn, "__wrapped__"):
                    import contextlib
                    wrapper = contextlib.asynccontextmanager if inspect.isasyncgenfunction(fn.__wrapped__) else contextlib.contextmanager
                    if fn.__code__ != wrapper(fn.__wrapped__).__code__:
                        raise MaintenanceDenied("unreviewed_definition_wrapper:" + module.__name__ + ":" + fn.__qualname__)
                    fn = fn.__wrapped__
                if fn.__code__.co_filename == "<string>" and inspect.isclass(obj) and hasattr(obj, "__dataclass_fields__"):
                    excluded.append(fn.__qualname__ + ":dataclass_generated")
                    continue
                key = (fn.__code__.co_qualname, fn.__code__.co_firstlineno)
                value = hashlib.sha256(marshal.dumps(fn.__code__)).hexdigest()
                if fn.__code__.co_filename != str(path) or expected.get(key) != fn.__code__:
                    raise MaintenanceDenied("loaded_source_definition_mismatch")
                actual[str(key)] = value
    if not actual:
        raise MaintenanceDenied("no_loaded_definitions_to_attest")
    return dict(path=str(path), source_sha256=hashlib.sha256(raw).hexdigest(),
                loaded_definitions_sha256=hashlib.sha256(json.dumps(actual,sort_keys=True).encode()).hexdigest(),
                definitions=len(actual), excluded_generated=excluded,
                boundary="Source-defined functions, not a universal mutable-global-state attestation")


def startup_attestation(modules, control, lane=None, schema=None):
    if not maintenance_enabled():
        return None
    if lane is None:
        raise MaintenanceDenied("maintenance_requires_qualified_global_lane")
    return dict(protocol="maintenance-startup-attestation-v1", pid=os.getpid(),
                modules=[loaded_identity(m) for m in modules], drain=control.snapshot(),
                schema=schema, lock_identity=list(lane.lock_identity),
                activation=dict(lane.activation), provider_calls_allowed=False,
                source="ACTUAL_LOADED_PYTHON_DEFINITIONS",
                limitations=["No claim about old processes, other jobs, VM or remote account activity"])
