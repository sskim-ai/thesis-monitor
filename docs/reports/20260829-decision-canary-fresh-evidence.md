# Decision Canary Fresh Evidence

Fresh canonical decision evidence was rebuilt from the latest immutable production packets:

- KR: `2026-08-28-kr-run-44-e4cf532e619b`
- US: `2026-08-29-us-run-45-0e9c491532df`
- Model: signed-in Codex CLI `gpt-5.6-sol`
- Reasoning effort: `xhigh`

| Ticker | Evidence SHA-256 | Result |
|---|---|---|
| `003690` | `510a7b157d4247a9c611e38dfd96dd34851434323907b1bc10955299d8c92b6b` | PASS |
| `000660` | `899971b974ad32c206398254e726d48c7c92079bd6ce96af5274d95ce7e9fb41` | PASS |
| `GOOGL` | `ca42efbaae98cd548a4e1b82e5bfb141b4c768eb78ca7342539900eae6b98b66` | PASS |
| `RXRX` | `841dc9cd32476470ede419acd6600f68f83b88c0f559144539ede0d6680307d5` | PASS |

The exact evidence bytes and model-evidence hashes matched the previous canonical calibration
packets for all four subjects. Local OHLCV acquisition made `8` bounded requests: `4` succeeded
and `4` transient HTTP 502 attempts were retried. SEC, OpenDART, paid-provider, and broad research
calls were `0`.

Machine artifact SHA-256: `058e66198c2d4d915baca5c166658ca4b38317348e04e697659fd4d6e8db6aad`.
