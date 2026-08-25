# KR + US Market Data Gap Inventory

- Evidence class: `CURRENT_CODE_REPLAY` gaps from immutable packet capture

## KR

| Field | Available | Provider | Structured | Natural captured | Adapter supports | User value | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| KOSPI/KOSDAQ | No | Not captured | No | No | Yes | High | KR structured acquisition backlog |
| Breadth | No | Not captured | No | No | Yes | High | publication/provider evidence |
| Sector/size | No | Not captured | No | No | Yes | Medium | provider feasibility |
| Market-wide flow | No | Not captured | No | No | Yes, KRW only | High | official/free source audit |
| Index contribution | No | Not captured | No | No | via compatible relation | Medium | defer until inputs exist |
| Publication timing | Partial | KRX telemetry | Yes | readiness only | Yes | Safety | continue natural telemetry |

## US

| Field | Available | Provider | Structured | Natural captured | Adapter supports | User value | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SPY/QQQ/IWM | Yes | stored canonical facts | Yes | Yes | Yes | High | natural proof |
| SOXX proxy | Yes | stored canonical fact | Yes | Yes | Yes | Medium | preserve proxy label |
| Breadth | No | Not captured | No | No | Yes | High | free provider backlog |
| Equal-weight | No | Not captured | No | No | Yes | Medium | acquisition backlog |
| Sector breadth | No | Not captured | No | No | Yes | Medium | acquisition backlog |
| Market-wide participant flow | No | Unsupported | No | No | intentionally rejects KR taxonomy | Low | remain Unknown |
| Session context | Yes | existing calendar | Yes | Yes | Yes | High | natural proof |

Unavailable free data is an acquisition backlog, not an engineering failure.
