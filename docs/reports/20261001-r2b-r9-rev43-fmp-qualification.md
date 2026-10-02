# REV43 FMP Free Basic Qualification

Terminal: `R2B_R9_REV43_FMP_FREE_ENTITLEMENT_GAP`.
Current fPER integration readiness: **NO**. No automatic follow-on execution.

## Actual Account Result

Exactly three requests to the documented annual analyst-estimates endpoint:

| Subject | HTTP | Outcome |
| --- | ---: | --- |
| GOOGL | 200 | Exact-symbol annual rows; positive FY1 EPS qualified |
| MU | 402 | Special-symbol access excluded by current subscription |
| TSM | 200 | Annual rows; listed-ADS currency/share basis unresolved |

GOOGL's success does not override the mandatory GOOGL/MU smoke gate. The other
eleven symbols were never requested, not observed to fail. The 14-row matrix
has one positive qualification, one ADR block and twelve entitlement/gate rows,
of which only MU is an observed entitlement denial. Retries and duplicates: 0.
Estimated daily headroom is at most 247 of the advertised 250; outside account
usage is unknown and no remaining-quota header was supplied.

GOOGL uses the earliest annual forecast after completed FY2025. MU's completed
FY2026 owner was confirmed from the official September 30 release, ending
September 3. No EPS was obtained for MU. TSM, SKHY and WRD depositary ratios
never imply a provider EPS conversion. Forecast date is not estimate-as-of;
accounting basis stays unspecified. No fPER, new price, FX or ADS calculation.

## Validation and Preservation

- REV42 ZIP SHA/sidecar, CRC, 65 members and all 64 payload hashes/sizes: PASS.
- REV42 final `638cec8ed12bd88b0dd864ef3747eccc5c21687a` preserved via the
  instruction's non-force GitHub archival ref, then fetched and verified.
- REV43 instruction `5920e17fd79dbcf99ca774628e03530e68b91c73`.
- Tested implementation: `6f39bb28` (full SHA in result repository identities).
- Pre-acquisition synthetic tests: 62 passed. Post-acquisition focused: 492.
- Full pytest: 7,892 passed, 63 skipped, 3 pre-existing deprecation warnings.
- Ruff, diff, Investment Knowledge and Chart Knowledge: PASS.
- Two socket/DNS-disabled replays match:
  `e1e162c52409fb5a2c4aee7edc3658145086a5ba660f5bdfc08d8708cfc61516`.
- 121 protected files unchanged; operating/main remains
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`.

No REV43 push, main merge, deployment, DB/config/scheduler/notification writes,
model calls, Telegram, Business Quant, Alpha Vantage, new Yahoo or KR APIs.
The commented FMP key was used only in memory; `.env` was not edited.

## Evidence Limits

Official API documentation, pricing and terms were reviewed. Direct public-page
HTTP 403s are distinct from authenticated endpoint results. The linked separate
acceptable-use URL was unavailable; this limitation is recorded. Private
personal evaluation is not a display or redistribution license.

Raw responses are sealed locally, not committed or exported to iCloud. The
report ZIP contains typed projections, hashes, request metadata, changes and
validation receipts; standalone byte replay requires the local raw corpus.
No API key or authenticated URL is included. ZIP and SHA are delivered only to
the user's iCloud Drive `Thesis Monitor` folder with per-file upload checks.

Next choices require a separate decision: leave US fPER unavailable, authorize
a paid estimates source, or use explicitly non-consensus issuer guidance.
No additional free-provider hunting is started by this result.
