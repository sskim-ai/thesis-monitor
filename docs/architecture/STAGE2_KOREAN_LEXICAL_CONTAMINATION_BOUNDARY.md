# Stage-2 Korean Lexical Contamination Boundary

Contract: `stage2-language-contamination-v2`

Stage 2 keeps evidence-domain ownership as the primary safety check. A separate
language matcher scans only the four stance-owned prose fields for uncited
price, technical, or market-flow language.

## Matching rules

- `주가` starts only at a valid non-Hangul, non-alphanumeric left boundary.
  Korean particles and compounds after the lexeme remain allowed, so `주가가`
  and `주가하락` match while `수주가` and `발주가` do not.
- `기술적` requires an intended timing phrase. Fundamental uses such as
  `기술적 경쟁력` and `기술적 진입장벽` remain clean.
- `수급` requires market actors or nearby position/timing language. Operational
  supply context does not become market-flow contamination by the lexeme alone.
- Other existing Korean and Latin lexemes use explicit left or token boundaries.

Every match records the scanned field, matched span, canonical lexeme, start and
end offsets, rule identifier, and lexical risk class. Evidence-reference and
language contamination counts remain separate.

The contract does not alter prompts, schemas, business-delta semantics,
financial semantics, Directional thresholds, Stage-1 Core, Stage-2 stance
ownership, final composition, Price-Timing, or renderer behavior.
