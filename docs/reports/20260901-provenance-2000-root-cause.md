# Provenance `2000` Root Cause

The archived raw candidate's `market_context.text` contained no literal `2000`. Ownership
normalization later inserted a canonical market-internals sentence containing
`Russell 2000이었습니다`. The former structural-label pattern ended in `\b`; because the following
Korean particle is a Unicode word character, that boundary failed and the numeric lexer emitted a
standalone `2000` claim.

The diagnostic path then displayed the earlier raw candidate instead of the exact normalized text
that had been bound and rejected. This made the receipt appear impossible.

Repair:

- structural index labels use ASCII-aware lookarounds around numeric labels;
- provenance still runs on market context;
- correction diagnostics inspect `binding.output`, the exact final validated candidate;
- diagnostics include literal, parsed value, span, path, rule, and binding attempts.

Run-49 exact replay now retains `Russell 2000이었습니다` with zero phantom errors.

`PROVENANCE_2000_ALLOWLIST_HACK = 0`

`PROVENANCE_VALIDATES_DIFFERENT_TEXT_THAN_RENDERER = 0`

`PHANTOM_2000_FALSE_POSITIVE = 0`
