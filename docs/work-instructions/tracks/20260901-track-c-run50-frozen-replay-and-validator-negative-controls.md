# Track C — Run-50 Frozen Replay + Validator Negative Controls

Use immutable copies of both KR run-50 natural packets.

Replay the actual production path:
claim paths → natural `_paths()` → schema → CLI → candidate → validation → adjudication → accepted → renderer.

Target:
- context 8/8
- model call reached
- candidate 8/8 unless a new independently proven subject error appears
- explicit V2 block for accepted-ready subjects

Keep 000660 valuation-quality and 005930 unsupported R/R as genuine negative controls.
Do not weaken guards.

No production resend or delivery intent.
