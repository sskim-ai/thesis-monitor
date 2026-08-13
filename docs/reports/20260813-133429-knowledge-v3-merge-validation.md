# Knowledge v3 Merge Validation

## Artifact Chain

| Artifact | Lines | Bytes | SHA-256 |
|---|---:|---:|---|
| Canonical v3 | 704 | 33,624 | `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Custom GPT upload artifact | 704 | 33,624 | `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Codex runtime mirror | 704 | 33,624 | `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |

- Knowledge version: `3.0`
- Analysis policy version: `daily-review-v3`
- Custom GPT Instructions: unchanged
- Public Action schema: unchanged, `0.4.5`, 20 operationIds
- Shadow mode: retained; official assessment and Telegram remain deterministic

Repository byte parity is complete. The actual Custom GPT still uses the pre-v3 Current file until the user replaces it with `docs/custom_gpt_knowledge_ko.md`; remote parity is therefore pending that upload.

## Safety Regression

- Preliminary earnings cannot create missing balance-sheet, FCF, inventory, ROIC, or safe TTM facts.
- Latest-quarter EPS is distinct from TTM EPS; multiplying one quarter by four remains forbidden.
- ADR conversion requires ratio direction, traded-security basis, currency, FX, and denominator compatibility.
- Historical percentile requires comparable price, share, accounting, and currency bases.
- Modeled estimates, consensus, and provider-only multiples remain separate.
- OHLCV indicators are used only when supplied by the Action or packet.
- Supply and positioning remain separate from the fundamental thesis.

## Added Analytical Depth

- FOMC components are interpreted separately; missing Dot Plot, SEP, or expectation data remains Unknown.
- Hyperscaler CAPEX is traced across the value chain without treating budget announcements as supplier orders.
- Price-volume combinations are conditional context, not automatic thesis changes.
- No donor-only industry metric was added: Current already contained the compatible donor coverage and stronger memory, cloud, biotech, and pre-profit safeguards.

## Rejected Donor Semantics

The v3 text contains no fixed score-to-trade mapping, mechanical Reward/Risk threshold, mandatory technical-indicator rule, or basis-free ADR shortcut. It also contains no concrete monitor schedule, retry deadline, LaunchAgent, or claim-lease implementation detail.

## Runtime And Cohort

The Skill index now points to v3 section names, including FOMC and Hyperscaler CAPEX routes. Existing industry routing logic is unchanged. New packets and outputs carry Knowledge `3.0`, the v3 checksum, and policy `daily-review-v3`, while previous Shadow history remains untouched.

## Validation Status At Report Creation

- Baseline before edits: `477 passed`, Ruff passed, diff check passed
- Targeted AI Review and health tests: `31 passed`
- Full pytest: `479 passed`, one pre-existing Starlette/httpx deprecation warning
- Ruff: passed
- Diff check: passed
- Repository Knowledge checksum: passed
- Skill validation: passed
- GitHub Actions: pending at report creation
