# US Shadow vs Natural TLS Runtime

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Classification

`NATURAL_US_TLS_STATUS = UNKNOWN_ISSUER_OBSERVED`  
`SHADOW_US_INTERFERENCE = NONE_CONFIRMED`

| Runtime | Window KST | CLI | Model/effort | Workdir | Result |
| --- | --- | --- | --- | --- | --- |
| Pre-window shadow | `07:03:52..07:16:09` | `0.148.0-alpha.15` | `gpt-5.6-sol / xhigh` | isolated `/private/tmp/.../run-first` | `UnknownIssuer`, no output |
| Natural primary V2 canary | `08:30:09..08:35:15` | same | same | claim directory | `UnknownIssuer`, no output |
| Natural backup V2 canary | `08:33:37..08:37:08` | same | same | claim directory | `UnknownIssuer`, no output |

All three used signed-in CLI authentication through isolated runtime state and the same account/network boundary. The shadow was stopped more than an hour before natural primary and made zero protected-window model calls. It did not share packet claim files or production delivery state. The repeated TLS symptom is common-runtime evidence, not evidence that shadow caused the natural failure.
