# Kiwoom Market Flow Concentration

`KR_MARKET_FLOW_CONCENTRATION = PASS (KOSDAQ_ONLY)`

| Market | Actor | Direction | Top N | Ratio | Formula |
| --- | --- | --- | --- | --- | --- |
| KOSDAQ | foreign | net_buy | 5 | 21.39% | top_n_same_direction_abs / all_same_direction_abs |
| KOSDAQ | institution | net_buy | 5 | 37.82% | top_n_same_direction_abs / all_same_direction_abs |
| KOSDAQ | retail | net_sell | 5 | 30.73% | top_n_same_direction_abs / all_same_direction_abs |

KOSPI is explicitly blocked: `{"KOSPI": ["UNRESOLVED_BASIS_OR_TAXONOMY"]}`.
Each KOSDAQ relation binds the complete page-chain hash and top-stock occurrence references.
Concentration is descriptive and cannot establish why the index or a stock moved.
