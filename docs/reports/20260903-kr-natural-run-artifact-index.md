# 2026-09-03 KR Natural Run Artifact Index

## Scope

This index records the immutable evidence used for the read-only extraction. Paths point to the operating archive; no source artifact was copied back into production or rewritten. SHA-256 values were captured during this review.

## Operating And Run Evidence

| Artifact | SHA-256 | Role |
|---|---|---|
| `logs/kr-close.out.log` | `b0a0adb6c561bb13fff09399be409ed500917512b251045b0625815da3a4fe1f` | Primary, backup, and late-backup lifecycle evidence |
| `logs/kr-close.err.log` | `1e82dd3ee33d4d15280a7e72d1f4f6fff37984782f611173bc939b08e7b50430` | Scheduler stderr evidence |
| `data/runs/2026-09-03.json` | `06976b13cd0790bcff3b04d9e9c314f88e79be477cdadd31a5c9882a64a2e888` | Authoritative run ledger |
| `data/market-context/structured/kr/2026-09-03.json` | `36a288b2d74c180c7f4dbd117bd337472590049f4d1c7adda9a9321fefc6066b` | Current KR market context |
| `data/telemetry/krx/publication-readiness/2026-09-03.jsonl` | `2d7988fc4e735daee8851e8763528c05f76939011a07764999e778e4ab214bfb` | KRX 16:05 publication telemetry |

## Primary Packet And AI Evidence

Packet: `2026-09-03-kr-run-54-f19bb379daa7`

| Artifact | SHA-256 | Role |
|---|---|---|
| `data/ai_review/inbox/2026-09-03-kr-run-54-f19bb379daa7.json` | `ad0ce85e77f6918ff455e5d2c1cf90e9b91de6e3ea2ce331020a28fa6154ecbb` | Immutable review input |
| `pilot/history/.../packet.json` | `4838f72e1e8e91219c7247ac517883962cb88332adabff8200861c1bc8e400b8` | Archived packet |
| `pilot/history/.../validation-result.json` | `bd0e2258d916d228461ffab1e8ee2789226d71b900333e0101e77d5760e3e99b` | Accepted corrected-candidate validation |
| `pilot/history/.../message-quality-receipt.json` | `5c7f4c9e54f3eb9536974cd8ed6a2111d038e5b7e1ad303fcde9e9d62397f41d` | Runtime quality receipt |
| `pilot/history/.../ai-assisted-messages.json` | `669172fa02bec354ae2ed04b17bc3f75b6c2c7ff308a6978d9232134c7741562` | Accepted AI-assisted preview |
| `pilot/history/.../delivery-result.json` | `0a9be789ba9109a6e555674c2e1a0fb0954a0a11b3ed685a02810f66c455a2ef` | Primary candidate remained pending |
| `history/...daily-review-v3.10...json` | `b09f5a47e92469eb0e761b4a8f5b3fb1defe7aae676a8a5e147367ae2aa22d41` | Accepted corrected candidate |
| `rejected/...1788420528.validation.json` | `15daede0f474e17b99f5198e6749eb6bd4c833bd48868892766cfba452292a50` | Initial rejection details |

The abbreviated `pilot/history/...` paths above resolve under `data/ai_review/pilot/history/2026/09/2026-09-03-kr-run-54-f19bb379daa7/`. The abbreviated `history` and `rejected` paths resolve under `data/ai_review/`.

## Delivered Fallback Evidence

Packet: `2026-09-03-kr-run-54-78ed269de3df`

| Artifact | SHA-256 | Role |
|---|---|---|
| `pilot/history/.../fallback-messages.json` | `ac224979ec2b263e3ba99cd2e847765b8a75c89e25ac7b32340f18851c3b4176` | Exact one-market plus KR8 payload |
| `pilot/history/.../delivery-result.json` | `a31ec69943487d49735ff60cfbe9e16dda4f16a705ac9923178e29ac5d95227e` | Sent receipt, nine of nine |
| `pilot/history/.../validation-result.json` | `278b937ad2798676ce5fa9dc24ee9fc4de39289000b51c46804f38eddc34ee7d` | Post-dispatch anomalous validation artifact |
| `logs/ai-review-fallback.out.log` | `74bc11771cdea5c4cf557424c9736ef9aa4415fb9bef439b252f7656940b19bd` | Fallback scheduler lifecycle |
| `logs/ai-review-delivery-retry.out.log` | `0efd0754def0de7f5c704cd0ca5eabf009df570c408211ac810c6170bf82c30b` | Retry reported no pending AI delivery |

The abbreviated fallback paths resolve under `data/ai_review/pilot/history/2026/09/2026-09-03-kr-run-54-78ed269de3df/`.

## Bundle Boundary

The downloadable bundle contains reports, machine-readable extraction JSON, the work instruction, and exact delivered message text files only. It excludes production logs, database files, API credentials, Telegram recipient identifiers, and raw provider payloads.
