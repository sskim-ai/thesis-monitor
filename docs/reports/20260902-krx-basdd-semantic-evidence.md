# KRX BAS_DD Semantic Evidence

Repository mapping is explicit: `BAS_DD` is the date field, `MKT_NM` is the session discriminator, and only `MKT_NM=야간` is a NIGHT row. [NIGHT_FUTURES_SESSION_BASIS.md](../architecture/NIGHT_FUTURES_SESSION_BASIS.md) retains an official KRX link and states that the 18:00-06:00 night session is assigned by its 06:00 end. [NIGHT_FUTURES_SESSION_DATE_CONTRACT.md](../architecture/NIGHT_FUTURES_SESSION_DATE_CONTRACT.md) separates the provider end date from a UI start date.

Support is `PARTIAL`, not `PROVEN`, for this investigation. The repository contains the official rules citation and a tested internal contract, but it does not archive an official KRX field dictionary that independently defines API field `BAS_DD`. More importantly, the exact 09/02 row required to join that semantic rule to the user’s candle is absent.

`PROVIDER_SEMANTICS_DOC_SUPPORT = PARTIAL`

This report does not weaken the existing production contract; it only limits what the current row proof can establish.
