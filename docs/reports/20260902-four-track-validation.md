# Four-Track Validation

## Scope

Base `89d3dc7ea350564c2b55b36b0c9ef9406330b3f9` contains the approved runtime-state, CLI-path,
identifier-provenance, daily-review, technical-recovery, previous-XKRX-date, and KRX NIGHT history
repairs. The four tracks remain independently reviewable.

## Focused Gates

| Track | Commit | Result |
|---|---|---|
| A: natural Codex transport | `20c80b6d968b5770947a6621fa4867d51967dbe0` | 28 focused tests PASS; signed-in safe model smoke PASS |
| B: daily-review semantics | `70d60e4ba100ad140b9aef6e26cfda0acf4f1a8f` | 331 focused tests PASS; both frozen run-52 candidates PASS |
| C: US market renderer | `4407cd11a78579e11681b503b2d4e72ee3c3d60f` | 61 focused and 255 broader tests PASS |
| D: renderer/consistency | `ee4e4688816d35f7a5ade7630eac07e6edd215eb` | 47 focused tests PASS |

## Integration

- KR signed-in `gpt-5.6-sol / xhigh`: context/candidate/accepted/explicit `8/8/8/8`, fallback `0`.
- US signed-in `gpt-5.6-sol / xhigh`: context/candidate/accepted/explicit `14/14/14/14`, fallback `0`.
- Dedicated non-production recipient: `22/22 exact`; duplicate/orphan `0/0`.
- Production recipient send/intent and all production replay-state mutations: `0`.
- Common disclaimer after repair: `0`.
- Unexplained accepted-decision drift: `0`.

## Full Validation

- full pytest: `2119 passed`, one pre-existing Starlette/httpx deprecation warning;
- Ruff: PASS;
- `git diff --check`: PASS;
- Investment Knowledge checksum/parity: PASS;
- Chart Knowledge checksum/parity: PASS;
- Public Action: `0.4.5`, operation IDs `20/20` unique;
- integration commit `c0a4d66616eb775415b602e58ddf2c8198cf4962`: Actions Test/Lint PASS,
  run `33627236776`;
- API health before promotion: PASS;
- scheduler timing and ownership diff: `0/0`.

The report-containing commit must also pass Actions before promotion. No validator threshold was
relaxed.
