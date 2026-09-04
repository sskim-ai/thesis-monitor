# Live-Path E2E Full Run

## Result

- Frozen source run: `54`, KR `8/8`
- Rehearsal packet: `2026-09-03-kr-run-54-7d5959c98797`
- Production entrypoint and normal path resolution: PASS
- Signed-in model reached: PASS (`gpt-5.6-sol`, `xhigh`)
- V2 selected/ready/not-ready: `8/8/0`
- Corrected daily-review accepted total: `9`
- Combined runtime quality: PASS for all eight stock messages
- Explicit AI market/stock/total: `1/8/9`
- Persisted pending after accept: `9`
- Retry discovered: `9`
- TEST sink logical sends: `9/9`
- Fallback sends: `0`
- Duplicate sends: `0`

The first real send completed all nine Telegram rows. Archive completion then failed because the
verifier reduced an eight-stock V2 quality scope to two adaptive-canary stocks. The rows and chunk
progress were already terminal. After the verifier was corrected to use the receipt's expected
ticker scope, archive-only recovery completed with `telegram_resent=false`.
