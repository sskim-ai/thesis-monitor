# 2026-09-04 KR Natural Run Lineage

## Authoritative Run

- Scheduler: `com.seungsoo.thesis-monitor.kr-close`
- Entrypoint: `python -m app.jobs.monitor_daily --market kr`
- Scheduled producer slots: 16:05, 16:20, 16:50 KST
- `monitorrun.id=56`, `daily_kr`, success, 8/8, failure 0
- Run: 16:05:31.183 -> 16:06:27.403 KST
- Authoritative delivery packet: `2026-09-04-kr-run-56-ea785fbd2c9e`
- Primary worker: `codex-kr-primary`, scheduled 16:15
- Backup worker: `codex-kr-backup`, scheduled 16:55
- Retry worker slots: 16:22, 16:25, 16:30
- Fallback slot: 17:10

## Packet Inventory

| Packet | Generated UTC | Stocks | Authoritative delivery | SHA-256 |
|---|---:|---:|---|---|
| `2026-09-04-kr-run-56-128e4097e823` | 2026-09-04T07:20:06.337531+00:00 | 8 | NO | `35573e41753b9a0241dcb789dc47d48687d0ca63ca09df411d6d46b1d8702873` |
| `2026-09-04-kr-run-56-6a9ef43bb878` | 2026-09-04T07:50:07.236723+00:00 | 8 | NO | `794925a9a73752925a6f36bc8c39cd23d5e41f0f9da9eccbf9d2a659acf9f528` |
| `2026-09-04-kr-run-56-ea785fbd2c9e` | 2026-09-04T07:06:27.418320+00:00 | 8 | YES | `b0436de5d5f0a223385f32a9bfd14b4724b10c836ee3fbe31d70697e3caac388` |

## Generation Identity

- Analysis: `analysis-3a64e08e95f9dd9816401afa`
- Accepted regular content: `content-8779159382a3d85ca57885b7`
- Selector/claim: `939e44d1-3e85-4b31-9a20-ab53bd742ad5`
- Delivery: `delivery-65d328f01a46170aec890f24`
- Claim lease: 30 minutes; primary acquired at 16:16:05.738 KST
- Primary exit: task completed after regular 9/9 send; child V2 command exit code 1 after caller interrupt
