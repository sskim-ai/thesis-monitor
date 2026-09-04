# 2026-09-04 Signed-in CLI TLS Preflight

The minimal preflight used the production-equivalent signed-in binary, ephemeral runtime namespace, read-only sandbox, `gpt-5.6-sol`, `xhigh`, the actual model endpoint, and one constrained JSON result. It used no production packet.

| Gate | Result |
|---|---|
| CLI | `/Applications/ChatGPT.app/Contents/Resources/codex` (`0.148.0-alpha.15`) |
| Model result count | `1` |
| CLI exit code | `0` |
| `UnknownIssuer` count | `0` |
| certificate verify error count | `0` |
| transport attempts | `1` |
| trust source | `ROOT_OWNED_SYSTEM_CA_BUNDLE` |
| production packet used | `0` |
| Telegram sends | `0` |
| scheduler mutations | `0` |
| database mutations | `0` |

This gate passed before the 15-part E2E was attempted.
