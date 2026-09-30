"""Opt-in, fail-closed qualification of an official shadow execution host.

The legacy launch guard remains the default. A parent probe is not evidence
that an opaque native child performs no writes to its official state store.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat

from scripts import m12ds_launch_context as legacy

CONTRACT = "qualified-official-model-launch-context-v1"
PREFIX = "R2B_R9_REV31_C1_"
ALLOWED_TRANSITION = frozenset({"CODEX_SANDBOX"})


class LaunchQualificationError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise LaunchQualificationError(PREFIX + code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def environment(names):
    return {key: {"present": key in os.environ,
                  "sha256": legacy.digest(os.environ[key]) if key in os.environ else None}
            for key in sorted(names)}


def inventory_names():
    policy = json.loads((legacy.INSTRUCTION / "m12ds-launch-context-parity-contract.json").read_bytes())
    return sorted(set(policy["safe_env_inventory"] + list(legacy.SAFE_MARKERS) + [
        "http_proxy", "https_proxy", "all_proxy", "no_proxy",
        "GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", "NIX_SSL_CERT_FILE"]))


@dataclass(frozen=True)
class LaunchIdentity:
    implementation_sha: str
    source_generation_id: str
    whole_source_sha256: str
    source_only_zip_sha256: str
    request_freeze_sha256: str
    prompt_schema_sha256: str
    executable_sha256: str
    launcher_sha256: str
    qualification_sha256: str
    cwd_sha256: str
    model: str = "gpt-5.6-sol"
    effort: str = "xhigh"
    timeout_seconds: int = 1200
    max_calls: int = 26
    retries: int = 0


@dataclass(frozen=True)
class StateWriteEvidence:
    scope: str
    write_calls: int | None
    permission_mutations: int
    proof_sha256: str | None
    executable_sha256: str
    launcher_sha256: str


def capture_context(names):
    """Read zero state bytes via O_RDONLY; never SQLite-open or change modes."""
    home = Path(os.environ["HOME"])
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
    state = codex_home / "state_5.sqlite"
    before = state.stat()
    readable = False
    access_errno = None
    try:
        fd = os.open(state, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            opened = os.fstat(fd)
            readable = (opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino)
        finally:
            os.close(fd)
    except OSError as exc:
        access_errno = exc.errno
    after = state.stat()
    def attrs(st):
        return (st.st_uid, st.st_gid, stat.S_IMODE(st.st_mode))
    return dict(contract=CONTRACT, at=datetime.now(timezone.utc).isoformat(),
        pid=os.getpid(), uid=os.geteuid(), gid=os.getegid(),
        cwd_sha256=legacy.digest(str(Path.cwd().resolve())),
        home_sha256=legacy.digest(str(home)), codex_home_sha256=legacy.digest(str(codex_home)),
        codex_home_env=environment(["CODEX_HOME"])["CODEX_HOME"],
        state_path_sha256=legacy.digest(str(state.resolve())),
        state_owner_mode=list(attrs(after)), state_read_ready=readable,
        state_access_errno=access_errno, state_probe_open_flags="O_RDONLY|O_NOFOLLOW",
        state_probe_write_calls=0, state_permissions_modified=attrs(before) != attrs(after),
        safe_environment=environment(names))


def stable_context(context):
    return {key: value for key, value in context.items() if key not in {"at", "state_access_errno"}}


def validate_transition(preparation, actual, *, preparation_sha256, actual_preparation_sha256):
    require(preparation_sha256 == actual_preparation_sha256, "LAUNCH_CONTEXT_TRANSITION_GAP")
    require((preparation["uid"], preparation["gid"]) == (actual["uid"], actual["gid"]),
            "LAUNCH_CONTEXT_TRANSITION_GAP")
    state = preparation["state_access"]
    require([state["uid"], state["gid"], int(state["mode"], 8)] == actual["state_owner_mode"],
            "LAUNCH_CONTEXT_TRANSITION_GAP")
    require(state["path_sha256"] == actual["state_path_sha256"], "LAUNCH_CONTEXT_TRANSITION_GAP")
    require(preparation["home_access"]["path_sha256"] == actual["home_sha256"]
            and preparation["codex_home_access"]["path_sha256"] == actual["codex_home_sha256"],
            "LAUNCH_CONTEXT_TRANSITION_GAP")
    before, after = preparation["safe_environment"], actual["safe_environment"]
    require(set(before) == set(after), "LAUNCH_CONTEXT_TRANSITION_GAP")
    differences = sorted(key for key in before if before[key] != after[key])
    require(set(differences) <= ALLOWED_TRANSITION, "LAUNCH_CONTEXT_TRANSITION_GAP")
    return differences


@dataclass(frozen=True)
class QualifiedOfficialModelLaunchContext:
    identity: LaunchIdentity
    # JSON strings make nested receipt contents immutable after construction.
    context_json: str
    state_evidence_json: str
    preparation_sha256: str
    transition_differences: tuple[str, ...]

    def receipt(self):
        return dict(contract=CONTRACT, status="PASS", identity=asdict(self.identity),
            context=json.loads(self.context_json), state_evidence=json.loads(self.state_evidence_json),
            preparation_sha256=self.preparation_sha256,
            transition_differences=list(self.transition_differences))

    @property
    def sha256(self):
        return digest(self.receipt())

    @classmethod
    def qualify(cls, *, identity, expected_identity, preparation, preparation_sha256,
                actual_preparation_sha256, context, entry_environment, state_evidence,
                binding_verified, provider_calls, secret_scan_passed):
        require(identity == expected_identity, "REQUEST_FREEZE_IDENTITY_GAP")
        require(identity.model == "gpt-5.6-sol" and identity.effort == "xhigh"
                and identity.timeout_seconds == 1200 and identity.max_calls == 26
                and identity.retries == 0, "REQUEST_FREEZE_IDENTITY_GAP")
        require(context["cwd_sha256"] == identity.cwd_sha256, "OFFICIAL_HOST_QUALIFICATION_GAP")
        require(binding_verified and provider_calls == 0 and secret_scan_passed,
                "OFFICIAL_HOST_QUALIFICATION_GAP")
        require(context["safe_environment"] == entry_environment, "OFFICIAL_HOST_QUALIFICATION_GAP")
        require(context["state_read_ready"], "STATE_ACCESS_GAP")
        require(context["state_probe_write_calls"] == 0 and not context["state_permissions_modified"],
                "OFFICIAL_HOST_QUALIFICATION_GAP")
        # The parent probe's literal zero must never certify native child writes.
        require(state_evidence.scope == "PARENT_AND_OFFICIAL_CHILD"
                and state_evidence.write_calls == 0 and state_evidence.permission_mutations == 0
                and bool(state_evidence.proof_sha256)
                and state_evidence.executable_sha256 == identity.executable_sha256
                and state_evidence.launcher_sha256 == identity.launcher_sha256,
                "OFFICIAL_HOST_QUALIFICATION_GAP")
        differences = validate_transition(preparation, context, preparation_sha256=preparation_sha256,
                                          actual_preparation_sha256=actual_preparation_sha256)
        return cls(identity, json.dumps(context, sort_keys=True), json.dumps(asdict(state_evidence), sort_keys=True),
                   preparation_sha256, tuple(differences))

    def verify(self, *, context, identity, preparation_sha256, freeze_sha256):
        require(self.sha256 == freeze_sha256 and identity == self.identity
                and preparation_sha256 == self.preparation_sha256
                and stable_context(context) == stable_context(json.loads(self.context_json)),
                "POST_FREEZE_CONTEXT_DRIFT")
        return dict(contract=CONTRACT, status="PASS", freeze_sha256=freeze_sha256,
                    at=context["at"], immediate_context_sha256=digest(context))
