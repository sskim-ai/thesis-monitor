# Manual Mutation Target Identity

REV59G repairs the parent-only `ManualMutationGuard` in
`scripts/qualified_official_launch_context.py`. The roots supplied by callers,
official CLI maintenance policy, guarded event set and economic contracts do not
change. This is not an OS sandbox and does not monitor a native CLI child.

## Target Contract

`manual-mutation-target-identity-v1` records each guarded operation, raw arguments,
target role, path kind, directory FD, resolved FD identity, lexical location,
canonical directory entry, symlink referent, verified existing ancestor,
protected-root relation, confidence and ALLOW/DENY decision.

Relative paths use the actual supplied directory descriptor; absent descriptors
use cwd. Absolute paths keep OS absolute-path semantics. Descriptor resolution
duplicates the descriptor and compares device/inode/type before, during and after
resolution. macOS uses Darwin `F_GETPATH`; Linux uses `/proc/self/fd`. Both paths
must match `fstat`. Unsupported platforms, closed descriptors, non-directory
directory descriptors, deleted directories and observed reuse mismatches deny.
Descriptor numbers are never cached as authority across operations.

Missing path components are projected from a verified existing ancestor, so
`mkdir(parents=True)` can make its ordinary initial attempt. Only absence is
projected; permission errors, cycles and unresolved identities deny. Both a
symlink entry and its referent remain subject to protection, including dangling
links. Lexical containment cannot escape a protected root through a symlink.
Existing protected-root device/inode/type is also matched against target
ancestors, so case-insensitive filesystem aliases do not gain new authority.

## Operation Matrix

| CPython event | Binding |
|---|---|
| `os.remove`, `os.rmdir` | path and directory FD |
| `os.mkdir`, `os.chmod`, `os.chown` | path and operation-specific directory FD position |
| `os.rename`, `os.link` | independent source/destination FD and path checks |
| `os.symlink` | destination FD; relative referent relative to link parent |
| `os.truncate` | plain path or verified file descriptor |
| `open` write | absolute path, builtin cwd-relative path, or verified file FD |
| `sqlite3.connect` | plain filesystem path only; URI/special targets deny |

`unlink` aliases `os.remove`; `replace` aliases `os.rename` at this audit surface.
Raw `os.open` omits its directory FD from the audit event. Relative raw-OS write
opens therefore deny explicitly rather than guessing their base; absolute write
opens and builtin cwd-relative writes remain resolvable. SQLite URI/special
targets are likewise not inferred. No `/tmp` exception or allowlist is added.

Event signatures were checked against the official
[Python audit table](https://docs.python.org/3.11/library/audit_events.html) and
[filesystem API semantics](https://docs.python.org/3.11/library/os.html#dir-fd).
Darwin's local SDK `sys/fcntl.h` defines `F_GETPATH` as 50.

## Proof Boundaries

Generic tests exercise real nested cleanup and rename/replace/link/symlink
operations in a child with the actual audit hook installed, including protected
source and destination controls. Portable US/KR native Market builder tests
compare exact payload bytes before and after guard installation and verify every
cleanup target stays inside the actual created temporary root.

The task-local full 70-request offline proof uses sealed source-only fixtures,
new synthetic responses, real native validators/builders and the installed guard.
It does not read prior AI outputs or call providers/models. Its complete guard
receipts are local proof artifacts, not production telemetry.

These checks detect identity changes observed during resolution; they do not
claim atomic exclusion of adversarial concurrent filesystem mutations after the
Python audit callback returns. Such isolation would require a separate OS-level
design. No protection is disabled to accommodate that limitation.
