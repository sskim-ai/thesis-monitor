# Price Structure v3 Legacy Detector False-Positive Root Cause

- Instruction commit: `97b65fc1d258339563b54961a83acd997867e11e`
- Implementation: `3685aa991589ca0e7cc560104d4ebf8289e3f91d`
- Test run: `v3-legacy-detector-run:9e082343e51115738580`
- Dataset: `v3-current-dataset:252d923f98173a1f2638`
- Render: `v3-legacy-detector-render:a1b39f8917bfcc17ee81`
- Source run: `v3-current-run:ff97be1d62a9810dc315`
- Target sessions: KR `2026-08-26`, US `2026-08-25`.

The previous renderer applied an unbounded, case-insensitive indicator regex to every line. The ordinary-word span `rsi` at `(6, 9)` inside `Recursion` was classified as RSI. Because the header had no date, the whole line became stale legacy technical prose and was suppressed. The repaired path protects the company header before lexical matching and requires complete token boundaries.
