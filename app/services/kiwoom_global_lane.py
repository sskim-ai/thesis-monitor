"""Opt-in host-global physical Kiwoom lane. No automatic activation/reset.

One byte-identical protocol is installed in each participant; the lock inode,
activation generation and state directory, not Python module names, are shared.
Activation requires a separately qualified quiet-window cutover. Legacy callers
remain unchanged until KIWOOM_GLOBAL_LANE_REQUIRED=1 is configured at startup.
"""
import asyncio
from contextlib import contextmanager, asynccontextmanager
import ctypes
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time
import uuid

PROTOCOL = 'kiwoom-host-global-lane-v1'
DEFAULT_ROOT = Path.home() / 'Library/Application Support/ThesisMonitor/KiwoomGlobalLane'
_loaded_lane = None


class GlobalLaneStop(RuntimeError):
    pass


def boot_identity():
    libc = ctypes.CDLL(None, use_errno=True)
    size = ctypes.c_size_t(128)
    value = ctypes.create_string_buffer(size.value)
    if not hasattr(libc, 'sysctlbyname') or libc.sysctlbyname(
            b'kern.bootsessionuuid', value, ctypes.byref(size), None, 0) != 0:
        raise GlobalLaneStop('global_lane_boot_identity_unavailable')
    return str(uuid.UUID(value.value.decode('ascii')))


def _private(path, directory=False):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise GlobalLaneStop('global_lane_symlink_denied')
    st = path.stat()
    if (st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) & 0o077
            or not (stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode))
            or (not directory and st.st_nlink != 1)):
        raise GlobalLaneStop('global_lane_private_custody_required')
    return st


def _read(path):
    _private(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        raw = os.read(fd, 16385)
        if len(raw) > 16384:
            raise ValueError
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise GlobalLaneStop('global_lane_state_corrupt') from exc
    finally:
        os.close(fd)


def _atomic(path, value):
    # Never replace the lock inode. Only the separately locked state is replaced.
    tmp = path.with_name('.state-' + uuid.uuid4().hex)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        raw = json.dumps(value, sort_keys=True, allow_nan=False).encode()
        if os.write(fd, raw) != len(raw):
            raise GlobalLaneStop('global_lane_short_write')
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class GlobalKiwoomLane:
    def __init__(self, root, *, clock=time.monotonic, sleep=time.sleep,
                 async_sleep=asyncio.sleep, boot=boot_identity, lock_timeout=30):
        self.root = Path(root).absolute()
        _private(self.root, True)
        self.clock, self.sleep, self.async_sleep, self.boot = clock, sleep, async_sleep, boot
        if not 0 < lock_timeout <= 30:
            raise ValueError('global_lane_lock_timeout_invalid')
        self.lock_timeout = lock_timeout
        self.activation = _read(self.root/'activation.json')
        code = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if (set(self.activation) != {'protocol','generation','boot_identity','implementation_sha256'}
                or self.activation['protocol'] != PROTOCOL
                or self.activation['implementation_sha256'] != code
                or not isinstance(self.activation['generation'],str) or not self.activation['generation']
                or self.activation['boot_identity'] != self.boot()):
            raise GlobalLaneStop('global_lane_activation_identity_denied')
        st = _private(self.root/'lane.lock')
        self.lock_identity = (st.st_dev, st.st_ino)

    def _open(self):
        _private(self.root, True)
        fd = os.open(self.root/'lane.lock', os.O_RDWR | os.O_NOFOLLOW)
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino) != self.lock_identity:
            os.close(fd)
            raise GlobalLaneStop('global_lane_lock_replaced')
        try:
            _private(self.root/'lane.lock')
        except BaseException:
            os.close(fd)
            raise
        return fd

    def _try_lock(self, fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False

    def _timeout(self, started):
        now = self.clock()
        if not math.isfinite(now) or now < started or now-started >= self.lock_timeout:
            raise GlobalLaneStop('global_lane_lock_timeout')

    def _state(self):
        if _read(self.root/'activation.json') != self.activation:
            raise GlobalLaneStop('global_lane_activation_changed')
        v = _read(self.root/'state.json')
        required = {'protocol','generation','boot_identity','last_end','in_flight','halted','sequence','pid'}
        if (set(v) != required or v['protocol'] != PROTOCOL
                or v['generation'] != self.activation['generation']
                or type(v['halted']) is not bool or type(v['in_flight']) is not bool
                or type(v['sequence']) is not int or v['sequence'] < 0
                or type(v['pid']) is not int
                or (v['last_end'] is not None and (type(v['last_end']) not in (int,float)
                    or not math.isfinite(v['last_end']) or v['last_end'] < 0))):
            raise GlobalLaneStop('global_lane_state_corrupt')
        if v['boot_identity'] != self.boot():
            self._stop(v, 'global_lane_boot_changed')
        if v['halted'] or v['in_flight']:
            raise GlobalLaneStop('global_lane_persistent_stop')
        return v

    def _stop(self, v, reason):
        v['halted'] = True
        _atomic(self.root/'state.json', v)
        raise GlobalLaneStop(reason)

    def _delay(self, v):
        now = self.clock()
        if not math.isfinite(now) or now < 0 or (v['last_end'] is not None and now < v['last_end']):
            self._stop(v, 'global_lane_clock_reversed')
        return 0 if v['last_end'] is None else max(0, 1.5-(now-v['last_end']))

    def _begin(self, v):
        if self._delay(v) > 0:
            self._stop(v, 'global_lane_spacing_unproven')
        now = self.clock()
        v.update(in_flight=True, pid=os.getpid(), sequence=v['sequence']+1)
        _atomic(self.root/'state.json', v)
        return dict(protocol=PROTOCOL, generation=v['generation'], sequence=v['sequence'],
            pid=os.getpid(), started_monotonic=now, previous_end=v['last_end'], stopped=False)

    def _finish(self, v, receipt):
        now = self.clock()
        v.update(in_flight=False, halted=receipt['stopped'] or not math.isfinite(now)
                 or now < receipt['started_monotonic'],
                 last_end=now if math.isfinite(now) and now >= receipt['started_monotonic'] else receipt['started_monotonic'])
        _atomic(self.root/'state.json', v)

    @contextmanager
    def sync_slot(self):
        from app.services.runtime_maintenance import assert_operation_allowed
        assert_operation_allowed()
        fd = self._open()
        try:
            start = self.clock()
            while not self._try_lock(fd):
                self._timeout(start); self.sleep(.01)
            v = self._state(); self.sleep(self._delay(v)); receipt = self._begin(v)
            try:
                yield receipt
            except BaseException:
                receipt['stopped'] = True
                raise
            finally:
                self._finish(v, receipt)
        finally:
            os.close(fd)

    @asynccontextmanager
    async def slot(self):
        from app.services.runtime_maintenance import assert_operation_allowed
        assert_operation_allowed()
        fd = self._open()
        try:
            start = self.clock()
            while not self._try_lock(fd):
                self._timeout(start); await self.async_sleep(.01)
            v = self._state(); await self.async_sleep(self._delay(v)); receipt = self._begin(v)
            try:
                yield receipt
            except BaseException:
                receipt['stopped'] = True
                raise
            finally:
                self._finish(v, receipt)
        finally:
            os.close(fd)

    async def halt(self):
        async with self.slot() as receipt:
            receipt['stopped'] = True


def configured_lane():
    """Startup opt-in is sticky in-process; missing/corrupt state never resets."""
    global _loaded_lane
    from app.services.runtime_maintenance import maintenance_enabled, MaintenanceDenied
    if maintenance_enabled() and os.environ.get('KIWOOM_GLOBAL_LANE_REQUIRED') != '1':
        raise MaintenanceDenied('maintenance_requires_global_lane_optin')
    if _loaded_lane is not None:
        if os.environ.get('KIWOOM_GLOBAL_LANE_REQUIRED') != '1':
            raise GlobalLaneStop('global_lane_loaded_optin_changed')
        return _loaded_lane
    if os.environ.get('KIWOOM_GLOBAL_LANE_REQUIRED') != '1':
        if (DEFAULT_ROOT/'activation.json').exists():
            raise GlobalLaneStop('global_lane_existing_activation_requires_optin')
        return None
    _loaded_lane = GlobalKiwoomLane(DEFAULT_ROOT)
    return _loaded_lane


def validate_envelope(response):
    """Transport envelope only, never Financial/price/Native use authority."""
    response.raise_for_status()
    payload = response.json()
    if (not isinstance(payload, dict) or str(payload.get('return_code', '0')) not in {'0', ''}
            or (str(response.headers.get('cont-yn', 'N')).upper() == 'Y'
                and not response.headers.get('next-key'))):
        raise GlobalLaneStop('global_lane_provider_envelope_rejected')
    return payload
