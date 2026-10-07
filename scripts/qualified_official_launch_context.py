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
import sys

from app.services.official_codex_shadow_transport_service import (
    OfficialShadowError,
    OfficialShadowExecutionPolicy,
)
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


MUTATION_TARGET_CONTRACT = 'manual-mutation-target-identity-v1'
_MUTATION_EVENTS = frozenset({'open', 'os.remove', 'os.rmdir', 'os.mkdir', 'os.chmod',
    'os.chown', 'os.truncate', 'os.rename', 'os.link', 'os.symlink', 'sqlite3.connect'})


def _file_identity(value):
    return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode))


def _descriptor_path(fd):
    if sys.platform == 'darwin':
        import fcntl
        # F_GETPATH is 50 in the Darwin SDK (sys/fcntl.h).
        raw = fcntl.fcntl(fd, getattr(fcntl, 'F_GETPATH', 50), b'\0' * 1024)
        return Path(os.fsdecode(raw.split(b'\0', 1)[0]))
    if sys.platform.startswith('linux'):
        return Path(os.readlink(f'/proc/self/fd/{fd}'))
    raise ValueError('FD_PATH_PLATFORM_UNSUPPORTED')


def _darwin_fd_type(fd):
    import ctypes

    class FDInfo(ctypes.Structure):
        _fields_ = [('fd', ctypes.c_int32), ('kind', ctypes.c_uint32)]

    query = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True).proc_pidinfo
    query.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int]
    query.restype = ctypes.c_int
    # PROC_PIDLISTFDS=1; proc_fdinfo is defined by Darwin sys/proc_info.h.
    required = query(os.getpid(), 1, 0, None, 0)
    if required <= 0:
        raise ValueError('PIPE_KERNEL_TYPE_UNAVAILABLE')
    rows = (FDInfo * (required // ctypes.sizeof(FDInfo) + 32))()
    copied = query(os.getpid(), 1, 0, rows, ctypes.sizeof(rows))
    if copied <= 0 or copied >= ctypes.sizeof(rows) or copied % ctypes.sizeof(FDInfo):
        raise ValueError('PIPE_KERNEL_TYPE_INCOMPLETE')
    matches = [row.kind for row in rows[:copied // ctypes.sizeof(FDInfo)] if row.fd == fd]
    if len(matches) != 1:
        raise ValueError('PIPE_KERNEL_TYPE_UNRESOLVED')
    return matches[0]


def _anonymous_pipe_authority(fd):
    info = os.fstat(fd)
    if not stat.S_ISFIFO(info.st_mode):
        raise ValueError('FD_NOT_ANONYMOUS_PIPE')
    if sys.platform == 'darwin':
        if info.st_nlink == 0 and _darwin_fd_type(fd) == 6:  # PROX_FDTYPE_PIPE
            return 'DARWIN_KERNEL_PIPE_TYPE'
    elif sys.platform.startswith('linux'):
        # Linux anonymous pipes normally have one link. Their positive authority
        # is the procfs pipe identity, not a filesystem unlink count.
        proc = f'/proc/self/fd/{fd}'
        if (os.readlink(proc) == f'pipe:[{info.st_ino}]'
                and _file_identity(os.stat(proc)) == _file_identity(info)
                and _file_identity(os.fstat(fd)) == _file_identity(info)):
            return 'LINUX_PROC_ANONYMOUS_PIPE_IDENTITY'
    raise ValueError('ANONYMOUS_PIPE_AUTHORITY_UNRESOLVED')


def _canonical_entry(path, seen=None):
    try:
        parent = path.parent.resolve(strict=True)
    except FileNotFoundError:
        # Path.mkdir(parents=True) first tries the complete path. Resolve missing
        # components from a verified ancestor, without suppressing other errors.
        _, parent = _canonical_entry(path.parent, seen)
    try:
        parent_info = parent.stat()
    except FileNotFoundError:
        pass
    else:
        if not stat.S_ISDIR(parent_info.st_mode):
            raise ValueError('PARENT_NOT_DIRECTORY')
    entry = Path(os.path.normpath(parent / path.name))
    try:
        info = entry.lstat()
    except FileNotFoundError:
        return entry, entry
    if not stat.S_ISLNK(info.st_mode):
        return entry, entry.resolve(strict=True)
    seen = set() if seen is None else seen
    identity = _file_identity(info)
    if identity in seen:
        raise ValueError('SYMLINK_CYCLE')
    seen.add(identity)
    target = Path(os.readlink(entry))
    # Unlinking a dangling symlink is valid. Its known parent still owns the
    # target path; do not treat arbitrary unresolved parent directories as safe.
    _, canonical = _canonical_entry(target if target.is_absolute() else parent / target, seen)
    return entry, canonical


class _MutationTargets:
    """Resolve one event while pinning descriptors; never cache a numeric fd."""

    def __init__(self):
        self.pins = []
        self.pipe_pins = {}

    def descriptor(self, fd, *, directory, allow_pipe=False):
        if type(fd) is not int or fd < 0:
            raise ValueError('FD_INVALID')
        before = _file_identity(os.fstat(fd))
        pinned = os.dup(fd)
        self.pins.append((fd, pinned, before))
        if before != _file_identity(os.fstat(pinned)):
            raise ValueError('FD_REUSE_MISMATCH')
        if directory and before[2] != stat.S_IFDIR:
            raise ValueError('DIR_FD_NOT_DIRECTORY')
        if allow_pipe and not directory and before[2] == stat.S_IFIFO:
            authority = _anonymous_pipe_authority(pinned)
            self.pipe_pins[pinned] = authority
            return None, dict(fd=fd, directory_required=False, identity=list(before),
                authority=authority)
        if before[2] not in (stat.S_IFDIR, stat.S_IFREG):
            raise ValueError('FD_NOT_FILESYSTEM_TARGET')
        path = _descriptor_path(pinned)
        if not path.is_absolute():
            raise ValueError('FD_PATH_NOT_ABSOLUTE')
        path = path.resolve(strict=True)
        if _file_identity(path.stat()) != before:
            raise ValueError('FD_PATH_IDENTITY_MISMATCH')
        return path, dict(fd=fd, directory_required=directory,
            identity=list(before), canonical_directory_or_file=str(path))

    def resolve(self, raw, fd=-1, *, role='target', base=None, allow_pipe=False):
        record = dict(role=role, raw_path=os.fsdecode(raw) if isinstance(raw, (str, bytes, os.PathLike))
            else raw if type(raw) is int else None, dir_fd=fd, fd_identity=None)
        if type(raw) is int:
            if fd not in (None, -1) or base is not None:
                raise ValueError('AMBIGUOUS_FILE_FD')
            path, record['fd_identity'] = self.descriptor(raw, directory=False, allow_pipe=allow_pipe)
            if path is None:
                record.update(path_kind='ANONYMOUS_PIPE_DESCRIPTOR',
                    resolution_confidence='VERIFIED_ANONYMOUS_IPC_IDENTITY', protected_roots=[],
                    protected_relation_basis='KERNEL_NON_FILESYSTEM_PIPE')
                return record
            record['path_kind'] = 'FILE_DESCRIPTOR'
        else:
            if not isinstance(raw, (str, bytes, os.PathLike)):
                raise ValueError('UNKNOWN_PATH_TYPE')
            value = os.fsdecode(raw)
            if not value or '\0' in value:
                raise ValueError('EMPTY_OR_NUL_PATH')
            path = Path(value)
            record['path_kind'] = 'ABSOLUTE' if path.is_absolute() else 'RELATIVE'
            if not path.is_absolute():
                if base is not None:
                    anchor = base
                elif fd not in (None, -1):
                    anchor, record['fd_identity'] = self.descriptor(fd, directory=True)
                else:
                    anchor = Path.cwd().resolve(strict=True)
                record['anchor'] = str(anchor)
                path = anchor / path
            else:
                record['absolute_path_ignores_dir_fd'] = True
        lexical = Path(os.path.abspath(path))
        entry, canonical = _canonical_entry(path)
        ancestor = canonical
        while True:
            try:
                ancestor_info = ancestor.stat()
                break
            except FileNotFoundError:
                if ancestor.parent == ancestor:
                    raise ValueError('EXISTING_ANCESTOR_UNRESOLVED')
                ancestor = ancestor.parent
        record.update(lexical_absolute_target=str(lexical), canonical_entry=str(entry),
            canonical_target=str(canonical), symlink_or_traversal_normalized=path != canonical,
            existing_ancestor=dict(path=str(ancestor), identity=list(_file_identity(ancestor_info))),
            resolution_confidence='VERIFIED_FILESYSTEM_IDENTITY' if ancestor == canonical else
                'VERIFIED_ANCESTOR_TARGET_PROJECTION')
        return record

    def verify(self):
        for original, pinned, identity in self.pins:
            if (_file_identity(os.fstat(original)) != identity
                    or _file_identity(os.fstat(pinned)) != identity):
                raise ValueError('FD_REUSE_MISMATCH')
            if pinned in self.pipe_pins:
                if any(_anonymous_pipe_authority(fd) != self.pipe_pins[pinned]
                        for fd in (original, pinned)):
                    raise ValueError('PIPE_AUTHORITY_CHANGED')
                continue
            path = _descriptor_path(pinned)
            if not path.is_absolute() or _file_identity(path.resolve(strict=True).stat()) != identity:
                raise ValueError('FD_PATH_IDENTITY_MISMATCH')

    def close(self):
        for _, pinned, _ in self.pins:
            os.close(pinned)


class ManualMutationGuard:
    """Parent-only ownership checks, not an OS sandbox or a native-child monitor."""

    def __init__(self, roots):
        self.roots = tuple(Path(path).resolve() for path in roots)
        self.root_identities = {}
        for root in self.roots:
            try:
                self.root_identities[root] = _file_identity(root.stat())
            except FileNotFoundError:
                self.root_identities[root] = None
        self.blocked_attempts = 0
        self.receipts = []

    def __call__(self, event, args):
        if event not in _MUTATION_EVENTS:
            return
        receipt = dict(contract=MUTATION_TARGET_CONTRACT, operation=event, targets=[],
            raw_arguments=[os.fsdecode(arg) if isinstance(arg, (str, bytes, os.PathLike))
                else arg if arg is None or type(arg) in (int, bool) else type(arg).__name__ for arg in args],
            decision='DENY', resolution_confidence='UNRESOLVED', reason=None)
        resolver = _MutationTargets()
        try:
            targets = receipt['targets']
            if event == 'open':
                path, mode, flags = args
                if not (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
                        or isinstance(mode, str) and any(c in mode for c in 'wax+')):
                    return
                # os.open's audit event omits dir_fd. A relative raw OS open
                # cannot be distinguished from one based on a protected fd.
                if mode is None and not isinstance(path, int) and not Path(os.fsdecode(path)).is_absolute():
                    raise ValueError('OPEN_DIR_FD_NOT_OBSERVABLE')
                targets.append(resolver.resolve(path, allow_pipe=True))
            elif event in {'os.rename', 'os.link'}:
                src, dst, src_fd, dst_fd = args
                targets.append(resolver.resolve(src, src_fd, role='source'))
                targets.append(resolver.resolve(dst, dst_fd, role='destination'))
            elif event == 'os.symlink':
                src, dst, fd = args
                destination = resolver.resolve(dst, fd, role='destination')
                targets.append(destination)
                targets.append(resolver.resolve(src, role='symlink_referent',
                    base=Path(destination['canonical_entry']).parent))
            elif event in {'os.remove', 'os.rmdir'}:
                path, fd = args
                targets.append(resolver.resolve(path, fd))
            elif event in {'os.mkdir', 'os.chmod'}:
                path, _, fd = args
                targets.append(resolver.resolve(path, fd))
            elif event == 'os.chown':
                path, _, _, fd = args
                targets.append(resolver.resolve(path, fd))
            elif event == 'os.truncate':
                path, _ = args
                targets.append(resolver.resolve(path))
            else:
                (path,) = args
                if not isinstance(path, (str, bytes, os.PathLike)) or os.fsdecode(path).startswith(('file:', ':')):
                    raise ValueError('SQLITE_TARGET_NOT_PLAIN_PATH')
                targets.append(resolver.resolve(path))
            resolver.verify()
            for target in targets:
                if target['path_kind'] == 'ANONYMOUS_PIPE_DESCRIPTOR':
                    continue
                paths = [Path(target[key]) for key in
                    ('lexical_absolute_target', 'canonical_entry', 'canonical_target')]
                ancestor_identities = set()
                for path in {p for value in paths for p in (value, *value.parents)}:
                    try:
                        ancestor_identities.add(_file_identity(path.stat()))
                    except FileNotFoundError:
                        continue
                target['protected_roots'] = [str(root) for root in self.roots
                    if any(path == root or root in path.parents for path in paths)
                    or self.root_identities[root] in ancestor_identities]
                target['protected_relation_basis'] = 'PATH_CONTAINMENT_AND_FILESYSTEM_ANCESTOR_IDENTITY'
            pipe_open = event == 'open' and targets[0]['path_kind'] == 'ANONYMOUS_PIPE_DESCRIPTOR'
            receipt['resolution_confidence'] = ('VERIFIED_ANONYMOUS_IPC_IDENTITY' if pipe_open
                else 'VERIFIED_FILESYSTEM_IDENTITY')
            if any(target['protected_roots'] for target in targets):
                receipt['reason'] = 'PROTECTED_ROOT'
            else:
                receipt.update(decision='ALLOW', reason='VERIFIED_ANONYMOUS_PIPE_OPEN' if pipe_open
                    else 'OUTSIDE_PROTECTED_ROOTS')
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            receipt['reason'] = 'TARGET_RESOLUTION_FAILED:' + type(exc).__name__
            receipt['resolution_error'] = str(exc)
        finally:
            resolver.close()
        self.receipts.append(receipt)
        if receipt['decision'] == 'DENY':
            self.blocked_attempts += 1
            raise LaunchQualificationError(PREFIX + 'MANUAL_STATE_MUTATION_BLOCKED')


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

    @property
    def execution_policy(self):
        return OfficialShadowExecutionPolicy(self.timeout_seconds, self.max_calls, self.retries)


@dataclass(frozen=True)
class StateWriteEvidence:
    scope: str
    write_calls: int | None
    permission_mutations: int
    proof_sha256: str | None
    executable_sha256: str
    launcher_sha256: str
    official_maintenance_authorization_sha256: str | None = None


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
                binding_verified, provider_calls, secret_scan_passed,
                expected_maintenance_authorization_sha256=None):
        require(identity == expected_identity, "REQUEST_FREEZE_IDENTITY_GAP")
        require(identity.model == "gpt-5.6-sol" and identity.effort == "xhigh",
                "REQUEST_FREEZE_IDENTITY_GAP")
        try:
            identity.execution_policy.validate()
        except OfficialShadowError as exc:
            raise LaunchQualificationError(PREFIX + "REQUEST_FREEZE_IDENTITY_GAP") from exc
        require(context["cwd_sha256"] == identity.cwd_sha256, "OFFICIAL_HOST_QUALIFICATION_GAP")
        require(binding_verified and provider_calls == 0 and secret_scan_passed,
                "OFFICIAL_HOST_QUALIFICATION_GAP")
        require(context["safe_environment"] == entry_environment, "OFFICIAL_HOST_QUALIFICATION_GAP")
        require(context["state_read_ready"], "STATE_ACCESS_GAP")
        require(context["state_probe_write_calls"] == 0 and not context["state_permissions_modified"],
                "OFFICIAL_HOST_QUALIFICATION_GAP")
        # Native housekeeping is only out of scope under explicit frozen authority.
        complete_scope = state_evidence.scope == "PARENT_AND_OFFICIAL_CHILD"
        authorized_scope = (state_evidence.scope == "CONTROLLER_ONLY_OFFICIAL_MAINTENANCE_AUTHORIZED"
            and bool(expected_maintenance_authorization_sha256)
            and state_evidence.official_maintenance_authorization_sha256
                == expected_maintenance_authorization_sha256)
        require((complete_scope or authorized_scope)
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
