# REV47 Completed-Session Close Qualification

Terminal: `R2B_R9_REV47_US_COMPLETED_CLOSE_SUPPLEMENT_GAP`.

This is a local evidence-capture failure, **not** a demonstrated usa20590
provider failure. REV47 is not complete and is not ready for main integration.

## Immutable Inputs

- Base: `075d9aa559b3dd5899745164bedff4db2914f770`.
- Instruction commit: `fb94363a` (full identity is in the local result bundle).
- Both REV46 ZIP SHA sidecars, CRCs and manifests passed.
- All 5,352 inherited source files retained their original hashes.
- The authorized `.env` hash is unchanged. No additional environment edit.
- Original source generation: `rev46-us14-resume1-20261002T064847Z`.

## Official Documentation

The Kiwoom website links to its official Kiwoom-Securities repository.
The [official API specification](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/953e5dbff123f437ab4d11a78a95191a685eb51f/kiwoom/_data/kiwoom_api_spec.json)
documents usa20590, `/api/us/mrkcond`, `stex_tp`, `stk_cd`, `base_dt`, and USD
daily OHLC fields. Original specification SHA-256:
`42a7b3912c9d9588c83bdc2db7779c8d2e038703a2b5562e54ef46ae905cba79`.

Price wire prefixes denote direction; the original signed strings are preserved.
The normalized positive price magnitude is not a currency conversion.

## Control Results

Target: 2026-10-01. Each of the five controls was requested once; no price retry.

| Ticker | usa06012 latest | usa20590 daily close | Result |
| --- | ---: | ---: | --- |
| CORZ | 16.50 | unavailable | Local response capture failed |
| HUT | 87.42 | 86.36 | HTTP/API/date/OHLC pass |
| WRD | 5.12 | 5.20 | HTTP/API/date/OHLC pass |
| GOOGL | 339.56 | 338.24 | HTTP/API/date/OHLC pass |
| TSLA | 355.40 | 354.11 | HTTP/API/date/OHLC pass |

GOOGL and TSLA's old values were inside their OHLC ranges but still differed.
Being inside the range is therefore not sufficient completed-close authority.
The REV47 audit disqualifies the latest usa06012 close for all 14 securities.
This is an audit policy receipt, not a claim that production has been changed.

The initial capture helper passed a string token to a byte scanner after CORZ
responded, before saving its body. That response cannot be recovered from the
retained artifacts. A second local helper import-name collision stopped before
any further price call. Four unissued controls were then completed. Authentication
requests total three; historical-price requests total five; duplicate price calls
and transport retries are zero. CORZ was not called again.

## Bounded Offline Repair

`scripts/completed_close_capture.py` durably retains market response bytes and
their hash before parser or scanner execution. It accepts string/byte secrets,
records sanitized failures, forbids overwrites and does not authorize provider
retries after a response. It has no network transport and is not imported by the
production runtime.

Focused capture/legacy-price tests: 36 passed. Knowledge tests: 2 passed.
Repository Ruff and Investment Knowledge check passed. Full pytest and the
merged-main suite were not run: execution stopped at Stage A, before integration.

## Unfinished Gates

Stage A has four verifiable controls, not five. Stage B, the v2 production price
owner, corporate-action/technical-series integration, whole-source seal,
US models/messages, fresh KR proof, and main integration remain unperformed.
No latest-chart fallback, model call, message delivery, main merge, push,
deployment, restart, scheduler edit or production DB mutation occurred.

Recovery requires an explicit exception for one new CORZ request, or another
authorized way to obtain its exact immutable response. Do not reuse an old close
or silently repeat successful controls. After five verifiable controls, complete
only the nine unrequested securities before resuming the original gated sequence.
