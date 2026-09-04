# 2026-09-04 KR Natural Candidate Inventory

## Counts

- Authoritative universe: market 1 + stocks 8 = 9
- Regular candidate: 9
- Final validated regular candidate: 9
- Primary persisted structured V2 candidate: 0
- Later non-authoritative backup V2 candidate: 8, archive-only
- Initial regular candidate SHA-256: `07fcdc7fd7b8f0d9e3ad1d9c5c4cbcc8e8200b4e6a94b4e778a508d752ff5c91`
- Corrected accepted regular SHA-256: `c3f766bd4eec402ac2f8addcc8bd7a3bba2fd2c12cd04d4e87b5ab393d78aff4`

| Subject | Regular candidate | Regular state | Primary V2 | V2 reason |
|---|---|---|---|---|
| KR market | YES | accepted regular schema 4 | N/A | V2 is stock-scoped |
| 000660 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |
| 003690 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |
| 005490 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |
| 005930 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |
| 010120 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |
| 012450 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |
| 047810 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |
| 086280 | YES | accepted regular schema 4 | NO | caller interrupted before first persisted V2 batch |

The progress-shaped 000660 stdout object is not counted as a persisted V2 candidate because generation was interrupted before `candidate_batch_created` and before any claim-bound V2 artifact existed.
