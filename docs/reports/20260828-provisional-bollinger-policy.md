# Provisional Bollinger Policy

The authoritative hierarchy remains unchanged: historical near/major S/R owns confirmed price
structure, completed-bar Bollinger owns dynamic context, and valid in-progress D/W/M bars may own
only `PROVISIONAL_BOLLINGER_SUPPORT/RESISTANCE`.

- Standalone / overlap / suppressed: `17 / 2 / 1`.
- Per-stock provisional display maximum: `1`.
- Provisional-to-near/major/stored/Fib/wave leakage: `0/0/0/0/0`.
- AI calculation/promotion: `0/0`.
- Distinct ranges render once; overlap becomes one `잠정 <TF> 볼린저 중첩` annotation.
- A provisional line is explicitly `잠정`, `진행중`, and `봉 마감 전 변동 가능`.
