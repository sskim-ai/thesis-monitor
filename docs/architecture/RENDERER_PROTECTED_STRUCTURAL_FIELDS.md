# Renderer Protected Structural Fields

## Protected Fields

Company headers, company names, tickers, status lines, and section headings are
`PROTECTED_STRUCTURAL_FIELD`. The legacy technical suppressor never evaluates or removes them,
even when their text contains an indicator token or an indicator-like character sequence.

Current v3 price structure, stored monitoring rules, valuation, business/earnings, risk, and
next-check bodies retain their own semantic owners. Only a sentence in an explicitly eligible
legacy-technical candidate field can reach freshness suppression.

## Clause Rule

Eligible paragraphs are split at sentence boundaries. A stale technical sentence may be removed,
while adjacent business prose remains. The policy never removes an entire rendered message block
from a global keyword hit.

## Invariant

All active-universe headers, names, tickers, and canonical headings must survive byte-equivalent.
Any protected-field loss is a material renderer failure.
