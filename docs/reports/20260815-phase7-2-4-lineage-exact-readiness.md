# Phase 7.2.4 Lineage-Exact Financial Eligibility Readiness

## Repository State

- Repository: `sskim-ai/thesis-monitor`
- Experimental branch: `codex/phase-7-2-relational-reasoning`
- Required base: `09d7e42432478666c17b2d896e5cccbfb87f37ff`
- Core lineage implementation: `aa00b47173e86db6a8bc920365d0c3633d104c53`
- Persisted fallback-lineage implementation: `7b9dbf75b610faa20935fe120313dbbbfd0ce225`
- Validated implementation/documentation commit: `afd1ae7fdd2e705af7156ebe5301efa4ada65d74`
- GitHub Actions validating that content: [run 31880750341](https://github.com/sskim-ai/thesis-monitor/actions/runs/31880750341), Test/Lint PASS
- Production main and operating checkout: `7d9f59fa1b5bc6034ea5cc9620482b39e4a96f07` (unchanged)
- Experimental/production policy: `daily-review-v3.10` / `daily-review-v3.9`
- Pilot at experiment start: KR `1/5`, US `1/5`
- Current operating Pilot after the independent natural v3.9 KR session: KR `2/5`, US `1/5`
- Production Assist: disabled

This is isolated experimental evidence. It has not been merged, deployed, scheduled, or sent to Telegram.

## Root Cause Reproduction

Phase 7.2.3 used `ttm_contains_preliminary` and a combined PE taint flag as proxies. Three failure modes were reproduced and closed:

1. A critical full statement inside the actual TTM quarter set could leave TTM EPS, trailing PER, and historical PE eligible when `ttm_contains_preliminary=false`.
2. A critical modeled-forward input could deny a clean historical trailing PE because both were merged into one PE state.
3. A mixed `valuation:current` Fact could carry denied PER and allowed PBR, allowing a number-free denied-PER conclusion to pass.

After v2, full/preliminary source type is descriptive; exact dependency periods and basis decide eligibility. Historical PE follows only trailing PER, and mixed aggregate valuation is not interpretation eligible.

## Lineage Design

`financial-quality-taint-v2` records independent lineage for direct earnings, trailing, modeled forward, consensus forward, current book, modeled forward book, historical PE, and historical PB. Each field carries source period/type/provider, dependency periods, denominator period, basis status, quality reasons, eligibility, and verification state.

Unknown lineage remains unavailable. Clean book-value fields and verified independent consensus remain available when earnings lineage is denied. New valuation snapshots persist the exact source metadata in the existing assessment JSON so deterministic fallback applies the same boundary without a DB migration.

## Interpretation Fence

Numeric registry rows continue to use `valuation:current`, but qualitative reasoning cites lineage-homogeneous Facts. The validator rejects:

- `valuation:current` when its fields have mixed eligibility;
- denied or unknown trailing/modeled/consensus/book interpretation Facts;
- raw or placeholder use of a non-eligible numeric row.

An allowed `valuation:book` interpretation and a number-free `financial_quality:<period>` explanation pass. This uses Fact identity and lineage metadata, not keyword filtering.

## KR Retrospective

- Session/run/state: `2026-08-14`, run `17`, `after_hours/final`
- Source DB SHA-256: `23451ab3ac99b08b203c6dd736f31aac1ced1f1603be2a387d2ce2a0d22018a1`
- Phase 7.2.3 packet: `2026-08-14-kr-run-17-cbfc8bd24224`
- Phase 7.2.4 packet: `2026-08-14-kr-run-17-9c9ba4a5dd73`
- Packet file SHA-256: `f1f51aaf578990ae6fdce9f97ffa0f0ee2d42c99dd58159158ab4d8f7bd4179d`
- Active/packet/output/rendered stocks: `7/7/7/7`
- Tickers: `000660`, `003690`, `005490`, `005930`, `010120`, `012450`, `086280`
- Logical messages: market `1` + stocks `7`
- Automatic bindings: `141`; manual bindings: `0`
- Formatter errors/unresolved placeholders: `0/0`
- Validator: `PASS`, errors `0`
- Denied numeric/qualitative leakage: `0/0`
- Observer/holder distinct: `7/7`
- Substantive sentence repetitions across 3+ stocks: `0`

SK hynix direct earnings, exact four-quarter TTM EPS/trailing PER, modeled forward EPS/fPER, and trailing historical PE remain denied. Current PBR/BVPS uses the verified `2026-03-31` book denominator. Modeled fPBR uses eight clean full-statement periods ending `2026-03-31`. Historical PB remains available.

The Phase 7.2.4 Telegram payload is byte-identical to the approved Phase 7.2.3 corrected payload. Both payload sets have SHA-256 `140e1ee5ee911275f799d7f5ea84ff4c4d05fd1abbdf84ad468968019d417405`; changed message indexes are empty.

## US Revalidation

- Original corrected packet: `2026-08-15-us-run-18-dca26c59bb82`
- Revalidation packet: `2026-08-15-us-run-18-39f4b8810c45`
- Revalidation packet SHA-256: `aa3f6bb0fff7da93fda6c0b21d1d2665eabcc3289be56a09194e570d416239fd`
- Logical messages: market `1` + stocks `13`
- Automatic bindings: `162`; manual bindings: `0`
- Binder/validator: `PASS/PASS`; errors `0/0`
- Label/source/instrument mismatch: `0/0/0`
- Denied numeric/qualitative leakage: `0/0`
- TSM: issuer financials `TWD`, ADR price `USD`; no conversion
- TSLA/WRD unsafe monetary revenue remains absent

The stricter lineage contract intentionally changes messages `3`, `9`, `10`, `12`, and `13`: CRCL, SKHY, SNDK, TSM, and WRD. Their old provider PER/PBR values lacked an exact denominator period or ADR/share basis. The corrected messages retain independently verified consensus, TWD issuer earnings, price, chart, volume, and book facts where eligible, and replace unsupported multiple interpretation with a specific hold.

Old payload SHA-256: `7498f859abd69ad2adff1ae5d8242e0e7b23fa96b65417b3dc0879f4ccf4e7c5`.

Corrected payload SHA-256: `0b42e8f293bdc7456c4bf841b1d9299b5fbf3b3fe2de59a4505baefcb4e2a0dd`.

The byte difference is safety-required, not a message-style rewrite.

## Deterministic Fallback

The isolated matrix verifies:

| Case | Trailing PE | Forward PE | PBR | Historical PE |
| --- | --- | --- | --- | --- |
| Critical preliminary in TTM | hidden | hidden | retained | hidden |
| Critical full statement in TTM | hidden | hidden | retained | hidden |
| Older critical quarter in TTM | hidden | hidden | retained | hidden |
| Modeled-forward-only taint | retained | hidden | retained | retained |
| Trailing taint + independent consensus | hidden | retained | retained | hidden |

Persisted-payload retry and single-delivery contracts are unchanged. Fallback does not recollect data, rerun AI, or rerender during network retry.

## Isolation

- Telegram sends: `0`
- Operating DB/archive/assessment writes: `0/0/0`
- Pilot mutations: `0`
- Scheduled Task changes: `0`
- Main branch or operating checkout changes: `0`
- Production Assist changes: `0`

The experiment used a SQLite-consistent copy and a separate `/tmp` data directory. New packet and Preview artifacts are experimental only.

The zeroes above describe this experiment. While it was running, the existing production v3.9 KR Scheduled Task independently completed packet `2026-08-15-kr-run-19-919a670464b4` at about 16:30 KST. That natural session sent its own production payload and moved the operating KR counter from `1/5` to `2/5`; it was not triggered, edited, or replayed by this work. US remains `1/5`. The production project-state document still says KR `1/5`, which is now a separate documentation-staleness gap and is not changed on this experimental branch.

## Contracts

- DB migration: none
- Public Action: `0.4.5`; operationId `20/20` unique
- Output schema: `4`
- OHLCV / Pilot / Renderer: `v2 / v3 / v3`
- Investment Knowledge v3 SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge v1 SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`

## Validation

- Focused lineage, interpretation-fence, and fallback tests: PASS
- Full pytest: `727 passed`, one third-party deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- GitHub Actions for `afd1ae7fdd2e705af7156ebe5301efa4ada65d74`: Test/Lint PASS ([run 31880750341](https://github.com/sskim-ai/thesis-monitor/actions/runs/31880750341))

## Artifacts

- [Architecture contract](../architecture/FINANCIAL_QUALITY_TAINT_PROPAGATION.md)
- [Lineage dependency matrix](20260815-phase7-2-4-financial-lineage-dependency-matrix.json)
- [Qualitative validator matrix](20260815-phase7-2-4-qualitative-interpretation-validator-matrix.json)
- [Fallback validation](20260815-phase7-2-4-fallback-validation.json)
- [KR full Preview](20260814-kr-v310-lineage-exact-corrected-preview.md)
- [KR binding](20260814-kr-v310-lineage-exact-binding.json)
- [KR validator](20260814-kr-v310-lineage-exact-validation.json)
- [KR quality audit](20260814-kr-v310-lineage-exact-quality-audit.json)
- [KR eligibility matrix](20260814-kr-financial-lineage-v2-eligibility-matrix.json)
- [KR Phase 7.2.3 payload comparison](20260814-kr-phase7-2-3-vs-7-2-4-payload-comparison.json)
- [US full Preview](20260815-us-v310-lineage-exact-corrected-preview.md)
- [US binding](20260815-us-v310-lineage-exact-binding.json)
- [US validator](20260815-us-v310-lineage-exact-validation.json)
- [US quality audit](20260815-us-v310-lineage-exact-quality-audit.json)
- [US revalidation and exact diffs](20260815-us-v310-lineage-exact-revalidation.json)

## Remaining Gaps

- CRCL, SKHY, SNDK, TSM, and WRD need provider denominator-period or ADR/share-basis metadata before the withheld provider multiples can be restored.
- SKHY is currently classified as non-depositary by SecurityMaster while its profile and user-facing name identify an ADR. This is a separate `DATA / SECURITY_IDENTITY` gap; the corrected Preview does not calculate a premium or convert the security.
- Human review of both full Previews is still required before main merge or deployment.
- No live v3.10 run is authorized. Production remains v3.9; this experiment did not change the Pilot counter.
- The current runtime Pilot state is KR `2/5`, US `1/5` after the independent natural v3.9 KR session. Production documentation still says KR `1/5`; correcting that production source-of-truth document requires a separate main update and is outside this experimental-only task.
