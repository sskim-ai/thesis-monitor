# Phase 8.5.4.1 Operating Smoke

## Result

Read-only smoke from `/Users/sskim/Codex/thesis-monitor` passed `430` tests after the API restart.

Covered areas:

- night-futures session/reference contract and Kiwoom reconciliation;
- RXRX/WULF current-PBR numeric ownership;
- CORZ typed valuation interpretation;
- fallback valuation context parity;
- support/resistance overlap and current-price context;
- runtime packet completeness, numeric provenance, receipt, archive and exactly-once delivery logic.

The post-deployment KRX probe repeated the preflight result: latest data pending, stale verified pair
available, and no same-date DAY/NIGHT canonical change. API health passed. No Telegram delivery,
Scheduled Task execution, provider mutation, Pilot mutation, DB write or archive rewrite occurred.

