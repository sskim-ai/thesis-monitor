# Track A — Non-Mandatory Trade-Language Semantic Ownership

Fix false positives such as:
"자동 매도보다 실적 재평가가 우선".

Do not reject raw "자동 매도" substring when the sentence is explicitly non-directive.

Prefer renderer-owned non-mandatory semantics.

Must block true directives:
반드시 매도, 즉시 매도, 자동 매도한다, 무조건 축소, 손절해야 한다.

No AI classifier. Deterministic semantic validator only.
