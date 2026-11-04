"""Cooperative same-host account pacing; not evidence of exclusive provider use.

Every participating process must use the same private directory and account key.
Uninstrumented services and a VM clock/filesystem require separate admission.
Persistent stops are deliberately not reset by constructing a new instance.
"""
import asyncio
import ctypes
from contextlib import asynccontextmanager
import fcntl
import json
import math
import os
from pathlib import Path
import re
import stat
import time

from app.services.unified_live_source_transport import SourceSafetyStop

CONTRACT = 'kiwoom-account-paced-query-v2'


def host_boot_identity():
    """macOS host clock domain. Unsupported hosts must not silently reset state."""
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        query = libc.sysctlbyname
    except AttributeError as exc:
        raise SourceSafetyStop('account_pacing_boot_identity_unavailable') from exc
    query.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
    query.restype = ctypes.c_int
    size = ctypes.c_size_t(128)
    value = ctypes.create_string_buffer(size.value)
    if query(b'kern.bootsessionuuid', value, ctypes.byref(size), None, 0) != 0:
        raise SourceSafetyStop('account_pacing_boot_identity_unavailable')
    identity = value.value.decode('ascii').lower()
    if not re.fullmatch(r'[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}', identity):
        raise SourceSafetyStop('account_pacing_boot_identity_invalid')
    return identity


class AccountQueryPacer:
    def __init__(self, *, directory, account_key, environment, interval=1.5,
                 clock=time.monotonic, sleep=asyncio.sleep, boot_identity=host_boot_identity):
        root = Path(directory).absolute()
        if (environment not in {'real', 'demo'} or not re.fullmatch(r'[a-f0-9]{64}', account_key)
                or not math.isfinite(interval) or interval < 1.5):
            raise ValueError('account_pacing_configuration_denied')
        if (any(p.is_symlink() for p in (root, *root.parents)) or not root.is_dir()
                or root.stat().st_uid != os.getuid() or stat.S_IMODE(root.stat().st_mode) & 0o077):
            raise ValueError('account_pacing_private_plain_directory_required')
        self.path = root / (environment + '-' + account_key + '.pace')
        self.interval, self.clock, self.sleep = interval, clock, sleep
        self.environment = environment
        self.boot_identity = boot_identity

    def _open(self):
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        st = os.fstat(fd)
        if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid()
                or stat.S_IMODE(st.st_mode) & 0o077):
            os.close(fd)
            raise SourceSafetyStop('account_pacing_unsafe_state')
        return fd

    async def _lock(self, fd):
        start = self.clock()
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                now = self.clock()
                if now < start or now - start > 30:
                    raise SourceSafetyStop('account_pacing_lock_unavailable')
                await self.sleep(0.01)

    def _load(self, fd):
        os.lseek(fd, 0, os.SEEK_SET)
        raw = os.read(fd, 4097)
        if not raw:
            return dict(last_boundary=None, halted=False, in_flight=False, boot_identity=self.boot_identity())
        try:
            value = json.loads(raw)
            last = value['last_boundary']
            if (set(value) != {'last_boundary', 'halted', 'in_flight', 'boot_identity'}
                    or not isinstance(value['boot_identity'], str) or not value['boot_identity']
                    or type(value['halted']) is not bool or type(value['in_flight']) is not bool
                    or (last is not None and (type(last) not in {int, float}
                        or not math.isfinite(last) or last < 0))):
                raise ValueError
            return value
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceSafetyStop('account_pacing_state_corrupt') from exc

    @staticmethod
    def _save(fd, value):
        raw = json.dumps(value, sort_keys=True, allow_nan=False).encode()
        os.lseek(fd, 0, os.SEEK_SET)
        # A crash/torn write is fail-closed on the next parse, not a reset.
        if os.write(fd, raw) != len(raw):
            raise SourceSafetyStop('account_pacing_state_write_incomplete')
        os.ftruncate(fd, len(raw))
        os.fsync(fd)

    @asynccontextmanager
    async def slot(self):
        fd = self._open()
        try:
            await self._lock(fd)
            value = self._load(fd)
            if value['boot_identity'] != self.boot_identity():
                value['halted'] = True
                self._save(fd, value)
                raise SourceSafetyStop('account_pacing_boot_domain_changed')
            if value['halted'] or value['in_flight']:
                raise SourceSafetyStop('account_pacing_stop_latched')
            now = self.clock()
            last = value['last_boundary']
            if not math.isfinite(now) or now < 0 or (last is not None and now < last):
                value['halted'] = True
                self._save(fd, value)
                raise SourceSafetyStop('account_pacing_clock_reversed')
            if last is not None and now - last < self.interval:
                await self.sleep(self.interval - (now - last))
            now = self.clock()
            if not math.isfinite(now) or (last is not None and now - last < self.interval):
                value['halted'] = True
                self._save(fd, value)
                raise SourceSafetyStop('account_pacing_interval_unproven')
            value.update(last_boundary=now, in_flight=True)
            self._save(fd, value)
            receipt = dict(contract=CONTRACT, environment=self.environment,
                started_monotonic=now, minimum_interval_seconds=self.interval,
                previous_boundary_distance=None if last is None else now-last,
                lock='SAME_HOST_FLOCK_HELD', stopped=False)
            try:
                yield receipt
            except BaseException:
                receipt['stopped'] = True
                raise
            finally:
                end = self.clock()
                # Space the next I/O after completion as well as start. This
                # covers pre-I/O disk delays; a crashed in-flight lease denies.
                value.update(last_boundary=end if math.isfinite(end) and end >= now else now,
                    in_flight=False, halted=receipt['stopped'] or not math.isfinite(end) or end < now)
                self._save(fd, value)
        finally:
            os.close(fd)

    async def halt(self):
        fd = self._open()
        try:
            await self._lock(fd)
            value = self._load(fd)
            value['halted'] = True
            self._save(fd, value)
        finally:
            os.close(fd)
