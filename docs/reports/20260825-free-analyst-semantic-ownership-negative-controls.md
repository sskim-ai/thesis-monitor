# Free Analyst Semantic Ownership Negative Controls

Focused suite: `75 passed`.

| Control | Expected | Result |
| --- | --- | --- |
| memory HBM/ASP/product mix with current memory refs | ACCEPT | PASS |
| defense backlog/delivery/margin with current defense refs | ACCEPT | PASS |
| defense product mix explicitly present in current source | ACCEPT | PASS |
| memory HBM claim on defense refs | REJECT | PASS |
| very-high wording on current high expectation ref | REJECT | PASS |
| insurance underwriting claim on semiconductor refs | REJECT | PASS |
| defense backlog/delivery claim on logistics refs | REJECT | PASS |
| cross-ticker thesis-driver atom owner | REJECT | PASS |
| second renderer call reusing first message concepts | REJECT/ABSENT | PASS |
| unsupported ownership candidate | per-message fallback | PASS |

These controls prove semantic provenance rather than a Hanwha-specific patch. Renderer calls are stateless and consume only the current validated immutable analysis object.
