"""Explicit local-test authority; never an issuer of production source rights."""

from copy import deepcopy
from dataclasses import dataclass
import asyncio
import os
from pathlib import Path
import time
import weakref

import httpx

from app.services.sealed_source_transport import SealedSourceTransport
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_snapshot_contract import digest
from app.services.unified_stock_acquisition import StockPlan


CONTRACT = "test-only-native-runtime-v1"
_ISSUED = weakref.WeakKeyDictionary()
_KEY = object()


class _CapabilityTransport(httpx.AsyncBaseTransport):
    """Check each original dispatcher attempt, including bounded retries."""

    def __init__(self, capability, inner):
        self.capability, self.inner = capability, inner

    async def handle_async_request(self, request):
        timeout = self.capability.remaining_seconds()
        response = None
        try:
            response = await asyncio.wait_for(self.inner.handle_async_request(request), timeout)
            timeout = self.capability.remaining_seconds()
            await asyncio.wait_for(response.aread(), timeout)
            self.capability._state()
        except TimeoutError:
            self.capability.revoke()
            if response is not None:
                try:
                    await asyncio.wait_for(response.aclose(), 1)
                except Exception:
                    pass
            raise SourceSafetyStop("native_test_transport_deadline") from None
        except SourceSafetyStop:
            if response is not None:
                try:
                    await asyncio.wait_for(response.aclose(), 1)
                except Exception:
                    pass
            raise
        return response

    async def aclose(self):
        await self.inner.aclose()


def is_test_scope(frozen, *, plan_generation=None):
    owner = frozen.get("native_owner", {})
    if not isinstance(owner, dict):
        raise NativeEnvelopeError(("invalid:native_owner",))
    stock = frozen.get("stock_plan", {})
    if not isinstance(stock, dict):
        raise NativeEnvelopeError(("invalid:stock_plan",))
    generations = (
        frozen.get("generation_id"),
        stock.get("run_id"),
        owner.get("generation_id"),
        plan_generation,
    )
    return (
        frozen.get("execution_scope") == "TEST_ONLY"
        or frozen.get("non_promotable") is True
        or any(str(g).startswith("TEST_ONLY_SYNTHETIC-") for g in generations)
        or owner.get("execution_scope") == "TEST_ONLY"
        or owner.get("non_promotable") is True
    )


class NativeEnvelopeError(SourceSafetyStop):
    def __init__(self, problems):
        self.problems = tuple(problems)
        super().__init__("test_native_envelope_invalid:" + ",".join(self.problems))


@dataclass(frozen=True)
class TestOnlyNativeOwnerEnvelope:
    """A validated projection, not itself an executable capability."""

    frozen_sha256: str
    plan_sha256: str
    generation_id: str
    native_input: dict

    @classmethod
    def validate(cls, *, frozen, dispatcher, settings, owner_configuration):
        required = (
            "native_owner",
            "native_owner_root",
            "stock_plan",
            "plan",
            "generation_id",
            "execution_purpose",
            "execution_scope",
            "non_promotable",
            "us_market_symbols",
            "us_market_reads",
            "sessions",
            "config_identities",
            "settings_sha256",
            "query_kst_date",
            "kr_local_cap",
        )
        problems = ["missing:" + k for k in required if k not in frozen]
        if problems:
            raise NativeEnvelopeError(problems)
        generation = frozen["generation_id"]
        if (
            frozen["execution_scope"] != "TEST_ONLY"
            or frozen["non_promotable"] is not True
            or not str(generation).startswith("TEST_ONLY_SYNTHETIC-")
        ):
            problems.append("test_scope")
        if frozen["execution_purpose"] != "MANUAL_SHADOW_UNSENT":
            problems.append("purpose")
        owner = frozen["native_owner"]
        if not isinstance(owner, dict):
            raise NativeEnvelopeError(("invalid:native_owner",))
        if (
            owner != owner_configuration
            or owner.get("execution_scope") != "TEST_ONLY"
            or owner.get("non_promotable") is not True
            or owner.get("generation_id") != generation
            or owner.get("live_provider") is not False
            or owner.get("credentials") != "SYNTHETIC_PLACEHOLDERS_ONLY"
        ):
            problems.append("independently_issued_owner_configuration")
        if frozen["settings_sha256"] != digest(settings.model_dump(mode="json")):
            problems.append("settings_identity")
        try:
            stock = StockPlan.model_validate(frozen["stock_plan"])
        except ValueError:
            problems.append("stock_plan")
        else:
            for field in (
                "owner_head",
                "owner_files",
                "settings_sha256",
                "request_environment_sha256",
            ):
                if getattr(stock, field) != owner.get(field):
                    problems.append("stock_owner:" + field)
            if stock.run_id != generation:
                problems.append("stock_generation")
        if dispatcher.plan.generation_id != generation or frozen[
            "plan"
        ] != dispatcher.plan.model_dump(mode="json"):
            problems.append("compiled_plan")
        configs = frozen["config_identities"]
        if not isinstance(configs, dict) or any(
            configs.get(d.provider) != d.config_identity_sha256 for d in dispatcher.plan.descriptors
        ):
            problems.append("config_identities")
        from app.macro.providers.market import MARKET_SYMBOLS
        from app.services.unified_source_observer import OhlcvRead

        symbols = frozen["us_market_symbols"]
        reads = frozen["us_market_reads"]
        if (
            symbols != list(MARKET_SYMBOLS)
            or not isinstance(reads, list)
            or not isinstance(frozen["sessions"], dict)
            or any(not isinstance(r, dict) for r in reads)
        ):
            problems.append("market_reads")
        else:
            try:
                typed_reads = [OhlcvRead.model_validate(r) for r in reads]
            except ValueError:
                problems.append("market_reads_schema")
            else:
                if [r.symbol for r in typed_reads] != symbols or any(
                    r.session_date.isoformat() != frozen["sessions"].get("us") for r in typed_reads
                ):
                    problems.append("market_reads_identity")
        if not isinstance(frozen["kr_local_cap"], int) or frozen["kr_local_cap"] <= 0:
            problems.append("kr_local_cap")
        if problems:
            raise NativeEnvelopeError(problems)
        native = {
            k: deepcopy(frozen[k])
            for k in (
                "native_owner",
                "stock_plan",
                "us_market_symbols",
                "generation_id",
                "execution_purpose",
                "execution_scope",
                "non_promotable",
            )
        }
        native.update(
            latest_completed_us_session=frozen["sessions"].get("us"),
            canonical_plan_sha256=dispatcher.plan.plan_sha256,
            runtime_contract=CONTRACT,
        )
        return cls(digest(frozen), dispatcher.plan.plan_sha256, generation, native)


class NativeWorkerTestCapability:
    """Trusted Python parent lifetime; public JSON never rehydrates this object.

    The authorized test controller must first obtain configuration from the
    original isolated Owner bootstrap. This factory does not grant file access.
    """

    def __init__(self, key):
        if key is not _KEY:
            raise SourceSafetyStop("native_test_capability_not_issued")

    @classmethod
    def issue(cls, *, frozen, dispatcher, inner, settings, root, worker, ttl_seconds=300):
        if type(inner) is not httpx.MockTransport or not 0 < ttl_seconds <= 900:
            raise SourceSafetyStop("native_test_mock_and_bounded_lifetime_required")
        if Path(root) / "dispatch" != dispatcher.root:
            raise SourceSafetyStop("native_test_source_root_mismatch")
        # The backend worker supplies its independently verified configuration;
        # caller-provided frozen metadata alone is not issuance authority.
        configuration = worker.authorize_runtime(
            frozen=frozen, dispatcher=dispatcher, inner=inner, root=Path(root)
        )
        envelope = TestOnlyNativeOwnerEnvelope.validate(
            frozen=frozen,
            dispatcher=dispatcher,
            settings=settings,
            owner_configuration=configuration,
        )
        value = cls(_KEY)
        _ISSUED[value] = dict(
            pid=os.getpid(),
            expires=time.monotonic() + ttl_seconds,
            root=Path(root),
            dispatcher=dispatcher,
            inner=inner,
            worker=worker,
            envelope=envelope,
            settings_sha=digest(settings.model_dump(mode="json")),
            revoked=False,
            bound=False,
            launched=False,
            validated_input=None,
            owner_root=Path(frozen["native_owner_root"]),
        )
        return value

    def _state(self):
        state = _ISSUED.get(self)
        if (
            state is None
            or state["revoked"]
            or state["pid"] != os.getpid()
            or time.monotonic() >= state["expires"]
        ):
            raise SourceSafetyStop("native_test_capability_inactive")
        if state["dispatcher"].plan.plan_sha256 != state["envelope"].plan_sha256:
            raise SourceSafetyStop("native_test_plan_drift")
        if state["bound"] and (
            state["transport"].inner is not state["guarded_inner"]
            or state["guarded_inner"].inner is not state["inner"]
            or state["transport"].dispatcher is not state["dispatcher"]
        ):
            raise SourceSafetyStop("native_test_transport_drift")
        return state

    def bind_acquisition(self, *, root, frozen, settings, transport):
        state = self._state()
        if (
            state["bound"]
            or Path(root) != state["root"]
            or type(transport) is not SealedSourceTransport
            or transport.inner is not state["inner"]
            or transport.dispatcher is not state["dispatcher"]
            or digest(frozen) != state["envelope"].frozen_sha256
            or digest(settings.model_dump(mode="json")) != state["settings_sha"]
        ):
            raise SourceSafetyStop("native_test_acquisition_binding_mismatch")
        state["bound"] = True
        state["transport"] = transport
        state["guarded_inner"] = _CapabilityTransport(self, state["inner"])
        transport.inner = state["guarded_inner"]
        return deepcopy(state["envelope"].native_input)

    def validate_bridge(self, *, transport, input_path, input_sha256):
        from app.services.unified_run_artifacts import sha256_bytes
        import json

        state = self._state()
        if (
            not state["bound"]
            or transport is not state["transport"]
            or Path(input_path) != state["root"] / "native-input.json"
        ):
            raise SourceSafetyStop("native_test_bridge_binding_mismatch")
        raw = Path(input_path).read_bytes()
        if sha256_bytes(raw) != input_sha256 or json.loads(raw) != state["envelope"].native_input:
            raise SourceSafetyStop("native_test_input_binding_mismatch")
        state["worker"].validate_bridge(
            transport=transport, input_path=input_path, input_sha256=input_sha256
        )
        state["validated_input"] = (Path(input_path), input_sha256)

    async def launch(self, **kwargs):
        state = self._state()
        if (
            state["launched"]
            or state["validated_input"] is None
            or state["validated_input"] != (Path(kwargs["input_path"]), kwargs["input_sha256"])
            or Path(kwargs["owner_root"]) != state["owner_root"]
            or Path(kwargs["output"]) != state["root"] / "native"
        ):
            raise SourceSafetyStop("native_test_launch_binding_mismatch")
        self.validate_bridge(
            transport=state["transport"],
            input_path=kwargs["input_path"],
            input_sha256=kwargs["input_sha256"],
        )
        state["launched"] = True
        return await state["worker"].launch(**kwargs)

    def revoke(self):
        state = _ISSUED.get(self)
        if state is not None:
            state["revoked"] = True

    def remaining_seconds(self):
        state = self._state()
        return max(0.0, state["expires"] - time.monotonic())


def native_test_input(*, capability, root, frozen, settings, transport):
    if type(capability) is not NativeWorkerTestCapability:
        raise SourceSafetyStop("native_test_capability_required")
    return capability.bind_acquisition(
        root=root, frozen=frozen, settings=settings, transport=transport
    )
