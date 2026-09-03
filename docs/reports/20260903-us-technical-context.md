# 2026-09-03 US Packet-Owned Technical Context

## Summary

| State | Count |
| --- | ---: |
| FULL | 0 |
| PARTIAL_SAFE | 14 |
| UNAVAILABLE | 0 |
| INVALID | 0 |

Acquisition recorded 44 requests, 44 successes, two bounded retries, zero
timeouts, and no cohort-wide technical failure.

| Ticker | Context ID | D/W/M | Feature fingerprint |
| --- | --- | --- | --- |
| CORZ | `technical-context:16988988d3cedb43b255b867` | PARTIAL/PARTIAL/PARTIAL | `32689d02929a50541f5366d9eb86acde80d545561b4bdb0c774230b0a731f1ad` |
| CPNG | `technical-context:67263966aea78f85415d8ba0` | PARTIAL/PARTIAL/PARTIAL | `292ff98a6ef717d853951dfb849fb57385f69d042ae9f8f83cf77b0c61325a61` |
| CRCL | `technical-context:8abc55230a6e4335f260b0cd` | PARTIAL/PARTIAL/PARTIAL | `8676424e2219bf86a95942e1ba17aa4bc3204cf58a643ef69955db9cfd45d03a` |
| GOOGL | `technical-context:95d5694ec3a2becbf437e348` | PARTIAL/PARTIAL/PARTIAL | `cce4f40a64fe2346961cdf19fa0786a97397781973e973fe629dff14d23f1d4e` |
| HUT | `technical-context:4f9fea6bcab01da02ea9c9cb` | PARTIAL/PARTIAL/PARTIAL | `e5d054900ea8a039175fc894e977c05baab3a5f13744df99488f08b37df94cbf` |
| IBM | `technical-context:4830c88296327967d1da5e2e` | PARTIAL/PARTIAL/PARTIAL | `66f0396250ce2e094fd7679b8d48c4e1a266afe8ad8419c9240a8688b4a59b66` |
| MU | `technical-context:cc05033c859e0a15c2eb0745` | PARTIAL/PARTIAL/PARTIAL | `a97c2b2a44fcfdd0db74d5391113c6dcd8d5e4179e61eaed82462cd3f0f490e1` |
| RXRX | `technical-context:84b8ffeca962f5a2ef184b7b` | PARTIAL/PARTIAL/PARTIAL | `5f8ee869c827b234f39392087e38661c1cdf5455a40ebf577959bceb6e960afb` |
| SKHY | `technical-context:3d29fadf0979a0007d5c7f76` | PARTIAL/PARTIAL/PARTIAL | `c3f6e397056b9ac48b0b542b47a127df5a2a0a20ccc36354b3e15c3e29fc96bc` |
| SNDK | `technical-context:fbc28b98da5ec7f776be75c1` | PARTIAL/PARTIAL/PARTIAL | `8811b3d2cc3151a79237a8eb8b1cc4977fda5c9d0c5aabf7d5c22fa08a510346` |
| TSLA | `technical-context:ff522979777f4b1aecb7a0b9` | PARTIAL/PARTIAL/PARTIAL | `cb126abbcb27b72468cdc9a68008771289a24c8c4e2b1cef2058b2fc16241f7e` |
| TSM | `technical-context:7a411b2bc548682fe1d9af14` | PARTIAL/PARTIAL/PARTIAL | `67f982e8759286aa41a00a2c5928d8552e14f879bbfda66f7d3d21e4e163f5e7` |
| WRD | `technical-context:37004eda43175e052f307667` | PARTIAL/PARTIAL/PARTIAL | `e1e9bd133f9e3f03a56a8229a559d963662df766ed0dd0647a24dddd21ca2e89` |
| WULF | `technical-context:b24bcffcc990ebfa948dbf0a` | PARTIAL/PARTIAL/PARTIAL | `cc7f3427d4bcad7a937786a18c793a7930272e7ab32f6638118b2ce211513f16` |

CPNG preserved four malformed raw rows and two stable bad-source outcomes after
two refetches; dependent features were blocked while the rest remained safe.
HUT kept the 2026-09-02 regular close separate from completed-bar features ending
2026-09-01. MU retained broad D/W/M history. SKHY remained sparse but explicitly
partial rather than fabricated.

- `ONE_US_TECHNICAL_FAILURE_BLOCKS_COHORT = 0`
- `US_DECISION_STAGE_LOCAL_OHLCV_HTTP = 0`

