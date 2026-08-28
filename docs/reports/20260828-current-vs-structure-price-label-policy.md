# Current vs Structure Price Label Policy

`현재가` is accepted only with source, observation timestamp, market-session state, currency, and
security basis. `가격 구조 기준 종가(정규장)` is the completed regular-session close that owns
authoritative structure and carries its session and adjustment basis.

Equal values collapse to one `현재가(정규장 종가)` line. Different values render both explicit
labels. Current replay produced `20` price lines across `20` subjects, with
ambiguous labels `0`, structure closes without sessions `0`, duplicate identical lines `0`, and
session labels without repository calendar evidence `0`.
