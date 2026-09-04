# US Backup Model Runtime

- Target: `US / 2026-09-04 KST`
- Packet: `2026-09-04-us-run-55-54cd536c6e4d`
- Operating revision: `5d5f3363d3a762b62698943b1feb4fa121d0d0f9`
- Evidence mode: read-only; replay/model rerun/resend/mutation all `0`

## Review authoring model

`BACKUP_MODEL_STATE = COMPLETED`. The backup scheduled Codex Desktop automation reused the same immutable packet's primary draft, adapted only the active claim fence, and later made one permitted content correction. Both backup candidates held market 1 + stocks 14 and 125 numeric references.

## Nested V2 decision canary

`BACKUP_V2_CANARY_MODEL_STATE = FAILED_TLS`. The signed-in claim-scoped CLI had the same version/model/xhigh/read-only configuration. It started at `08:33:37.239119`; first `UnknownIssuer` was `08:33:41.594080`; it yielded no model result and was interrupted at `08:37:08.504`, exit `130`.

First candidate SHA: `fa1499059847e3a1bd3283fef2e266385960e4e1e18550f9f41e9cd0d9f24d11`. Corrected candidate SHA: `29dd96d0b9c1efec9d23a6c22fab1b02b3b92f65a28af71f01abf8b119757a7b`. Neither became accepted.
