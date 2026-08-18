# Phase 8.2A.2 KRX Provider Role

Date: 2026-08-18
Policy: `krx-time-slot-provider-role-v1`
Status: LIVE ROLE NOT YET FINALIZED

## Role Matrix

| Time slot | Target session | Observed evidence | Status | Recommended role |
|---|---|---|---|---|
| 16:05 KST same-day close | same day | no exact-slot observation | `NOT_YET_PROVEN` | not primary |
| 08:05 KST next morning | prior completed day | no exact-slot observation | `NOT_YET_PROVEN` | not primary |
| T+1 reconciliation | prior completed day | no complete observation | `NOT_YET_PROVEN` | not active |
| explicit historical request | explicit archive date | 2026-08-14 validated | `SUPPORTED` | historical only |

The 20:27-21:06 same-day evening observations are all pending. They show that the 2026-08-18 data
was not ready by that later interval, but they are not mislabeled as exact 16:05 evidence. No 08:05
or T+1 complete observation exists yet.

## Evidence Gates

- One complete live-slot observation: `CANDIDATE`, never `SUPPORTED`.
- Same-day 16:05 and next-morning 08:05: five clean complete normal sessions for `SUPPORTED`.
- T+1 reconciliation: three clean complete normal sessions for `SUPPORTED`.
- Three exact-slot sessions with no complete result can establish `NOT_SUPPORTED` for that slot.
- Latest observation per session owns that session's result; unrelated clock times do not count.

These gates prevent the already validated historical capability from silently becoming same-day
production authority.

## Current Decision

KRX is authoritative for the validated historical archive path. Same-day close, next-morning, and
T+1 reconciliation roles remain undetermined. Phase 8.2A is not eligible for shadow promotion based
on publication timing evidence from this phase alone.

Recommended next action: preserve the operating baseline, collect exact-slot evidence on 3-5 normal
sessions with the four-call adaptive observer, then perform a separate Human Review and promotion
decision.
