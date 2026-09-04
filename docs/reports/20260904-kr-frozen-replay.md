# 2026-09-04 KR Frozen Replay

The immutable Run-54 packet and candidate were replayed on the integrated KR/US branch without a model call, fresh-fact fetch, database write, or Telegram send.

| Gate | Result |
|---|---|
| Packet | `2026-09-03-kr-run-54-f19bb379daa7` |
| Packet SHA-256 | `ad0ce85e77f6918ff455e5d2c1cf90e9b91de6e3ea2ce331020a28fa6154ecbb` |
| Candidate SHA-256 | `b09f5a47e92469eb0e761b4a8f5b3fb1defe7aae676a8a5e147367ae2aa22d41` |
| Validated scope | `9/9` |
| Rendered | market `1` + stocks `8` |
| Quality receipt | `passed`, verified |
| Validation/binding/typed errors | `0/0/0` |
| Accounting/valuation errors | `0/0` |
| Model/fresh fact/Telegram calls | `0/0/0` |

The integrated US validator exposed six legacy KR valuation interpretations that lacked typed refs. The bounded adapter upgraded only uniquely grounded historical or quality-unknown statements; ambiguous directional valuation language still fails closed. No replay text or threshold was changed.
