# Track D — Common Renderer Cleanup + Integration / Live Guard

Remove from all KR/US V2 BUY/HOLD/SELL stock messages:
`※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다.`

Preserve accepted_decision_plan as sole downstream authority.

Add integration decision-consistency diagnostics:
evidence fingerprint → candidate → adjudication → accepted.

Accepted decision changes require:
material evidence delta or valid adjudication.

Then run:
- US14 production-equivalent
- KR8 production-equivalent
- real TEST-recipient delivery
- full pytest/Ruff/CI
- exact payload/duplicate checks

No production recipient.
No production state mutation.
No scheduler timing/ownership change.

Final natural US/KR live proof still required after deployment.
