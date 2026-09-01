# Product-Identifier Provenance Root Cause

The legacy numeric lexer treated the suffix digits in canonical model identifiers `KF-21` and `FA-50` as standalone claims. The repair recognizes a complete alphanumeric identifier only when its exact span is owned by canonical evidence or a structured registry. No ticker or model allowlist was introduced.
