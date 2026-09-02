# KR Disclaimer Cleanup Inventory

Exact pending line: `※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다.`

- occurrence count in the nine sent KR fallback messages: 0
- production accepted-renderer owner: `app/services/accepted_decision_v2_service.py`
- shadow canary owner: `app/services/decision_canary_service.py`
- KR/US shared production component: yes, `accepted_decision_v2_service`
- expected occurrence if eight KR V2 decisions had rendered: one per stock message

No cleanup was implemented in this review.
