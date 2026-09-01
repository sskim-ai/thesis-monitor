# OHLC Provider Field Mapping

Kiwoom US field contract: `dt -> date`, `open_pric -> open`, `high_pric -> high`, `low_pric -> low`, `cur_prc -> close`, `acc_trde_qty -> volume`, and `acc_trde_prica -> value`. Daily, weekly, and monthly use provider-native APIs `usa06012`, `usa06013`, and `usa06014`. The adapter strips provider sign notation but does not swap, clip, or manufacture OHLC values. `OHLC_FIELD_MAPPING_CONTRACT = PASS`.
