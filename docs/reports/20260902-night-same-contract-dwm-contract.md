# Night Same-Contract D/W/M Contract

All Run-51 daily, weekly, and monthly constituent fact IDs carry one exact contract code per product. Tests inject alternate-contract bars and prove they cannot affect O/H/L/C or return. Weekly and monthly baselines require the previous completed same-contract period.

`DWM_SAME_CONTRACT_ONLY = PASS`
`MULTI_CONTRACT_DWM_SPLICING = 0`
