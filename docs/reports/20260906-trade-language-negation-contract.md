# Trade Language Negation Contract

거래 표현은 `ACTIONABLE`, `NEGATED`, `DESCRIPTIVE`, `NONE`으로 분류한다. Bounded suffix negation은 안전한 부정으로 처리하지만 같은 문장 뒤의 별도 actionable directive는 계속 차단한다. 특정 ticker나 SNDK/TSLA 문장 whitelist는 없다.

Fresh FIRST에서 `즉시 매수 신호가 아니며`가 `mandatory_trade_language`로 거절됐다. 이는 actionable instruction이 아닌 nominal negation이지만 현재 bounded suffix가 `신호` 같은 일반 명사구를 소유하지 못한 새 false positive다. 같은 generation의 hotfix는 금지되어 있으므로 validator는 변경하지 않았고 후속 bounded repair로 이관한다.
