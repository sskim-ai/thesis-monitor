# V2 Natural Path Permutation Controls

| Schema | cwd | I/O | Result |
| --- | --- | --- | --- |
| absolute | absolute | absolute | PASS |
| relative | relative | absolute | PASS |
| relative | absolute | absolute | PASS |
| relative | relative | relative | PASS |
| missing | relative | relative | PRE-CALL REJECT |

The exact run-50 persisted claim shape calls production `_paths()` and the same invocation helper. Duplicated claim segments: 0.
