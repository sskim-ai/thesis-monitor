# M12CZ Source Reconciliation Decision

## Terminal

`M12CZ_SOURCE_RECONCILIATION_AND_WAIT_PREVIEW_READY_FOR_CHAT_DECISION`

이 terminal은 투자 정확성, M12CX canonical PASS, production 통합 또는 배포 승인이 아니다. M12CZ는 frozen output을 바꾸지 않은 evidence dossier와 19개 WAIT 문서 preview만 닫았다.

## 결론

1. **Working capital:** MU, 000660, 005490, 005930의 네 canonical relation은 4 reported + 2 derived fact로 Decimal 재현됐다. 005490은 frozen 정의대로 `inventory_vs_revenue`이며 COGS로 바꾸지 않았다. 005930의 `+35.79975884967539121726114215%p`는 재고 증가율과 COGS 증가율의 차이이며 OCF가 아니다.
2. **Entitlement:** source owner의 `working_capital_only_status_or_valuation_change` 제한은 Stage-2 atomic projection에서 전달되지 않고, Pass-B capability는 parent ref를 일반 risk evidence로 승격한다. 005930 Holder는 해당 relation 하나만 선택했다. 따라서 bounded entitlement propagation defect는 확인됐지만, 원래 `REVIEW`는 유지하고 `REVIEW PENDING` 감사 상태만 표시한다.
3. **SK하이닉스:** receipt `20260814003509`의 연결 CIS 단일분기 row와 잠정실적 `20260729800013`이 같은 reported amounts를 보유한다. 76.32824654086185% margin과 net-income > revenue predicate는 정확히 발동한다. 이는 unusual-but-reported reconciliation signal이지 회사 훼손 증거가 아니다. 60% threshold 변경이나 경고 제거 근거는 없다.
4. **Expectations-only Overall:** 000660의 유일한 selected bearish directional claim은 `HBM4 램프업과 높은 메모리 수익성 지속 기대가 이미 매우 높다`이며 parent category는 `expectations`다. 독립 사업/사이클 악화를 입증하지 않으므로 policy acceptance는 `NOT_CLOSED`; 원래 HOLD는 그대로 두고 Chat 판단이 필요하다.
5. **CPNG:** 공식 2026-Q2 Exhibit 99.1은 TTM OCF $1.425b, PPE purchases $1.326b, sale proceeds $6m, management-defined FCF $105m(전년 $784m)을 명시한다. backend PPE-only FCF는 $99m이다. 105m은 거짓이 아니지만 definition이 다르며, frozen legacy thesis path는 accession/definition을 싣지 않았다. `SUPPRESSED`는 module-local canonical display gate이지 모든 독립 FCF의 전역 금지 규칙이 아니다.
6. **WAIT preview:** 19개 WAIT, numeric range 5개, unresolved 14개를 원래 output 그대로 문서화했다. GOOGL primary tag는 `BUSINESS_CONFIRMATION_WAIT`이며 range 위/아래 위치로 새 buy predicate를 만들지 않았다.

## Finding → Source → Rule → Observation → Decision

| Finding | Source locator | Governing rule | Observation | Decision |
|---|---|---|---|---|
| WC arithmetic | `working-capital-operands-and-entitlement.json` | canonical YoY growth-rate difference | 4/4 exact Decimal match | Source facts retained |
| WC status-use restriction | pinned excerpts 01–05 | source prohibition + Stage-2 capability | restriction metadata dropped before capability | repair proposal only |
| SK outliers | DB snapshot 970/events 1119·2999 + excerpts 06–09 | exact versioned predicates | official rows unusual, not arithmetically invalid | anomaly detection kept |
| 000660 expectation support | selected parent `decision-evidence:e69aab50953f46aec513` | thesis/entry separation | expectation reflection only | Chat policy decision |
| CPNG FCF | SEC 8-K `0001834584-26-000070`, 10-Q `0001834584-26-000073` | definition-specific FCF | $105m management FCF vs $99m PPE-only FCF | bind semantics later; no rewrite |

## Remaining uncertainty

- SK하이닉스 profit composition의 반복 가능성과 경제적 지속성은 현재 evidence로 증명되지 않았다.
- 000660 expectations-only Overall 수용 여부는 policy-owner 판단이 남아 있다.
- WC restriction propagation과 CPNG legacy source binding은 code repair 승인을 받지 않았다.

No model call, A/B rerun, current-data refresh, production write/send, runtime code change, merge, push or deploy was performed.
