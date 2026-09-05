# GPT-5.5 Selection Root Cause

Date: 2026-09-05 KST

Status: shadow-only; no production mutation or delivery.

The earlier `gpt-5.5` run was not a hidden fallback. CLI `0.142.5` first rejected `gpt-5.6-sol`; the prior shadow script was then explicitly changed to `MODEL = "gpt-5.5"`. Classification: `EXPLICIT_SCRIPT_OVERRIDE`. Its promotion weight is `0`.
