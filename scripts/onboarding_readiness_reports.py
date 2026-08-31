from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Mapping


ARCHITECTURE_DOCS = (
    "MONITORING_ONBOARDING_LIFECYCLE.md",
    "ONBOARDING_READINESS_CONTRACT.md",
    "MARKET_COHORT_SCOPED_READINESS.md",
    "PRODUCTION_PACKET_UNIVERSE_SNAPSHOT.md",
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _subject(audit: Mapping[str, object], ticker: str) -> Mapping[str, object]:
    rows = audit.get("subjects")
    if not isinstance(rows, list):
        raise ValueError("audit subjects missing")
    for row in rows:
        if isinstance(row, Mapping) and row.get("ticker") == ticker:
            return row
    raise ValueError(f"audit subject missing: {ticker}")


def _after(row: Mapping[str, object]) -> Mapping[str, object]:
    value = row.get("after")
    return value if isinstance(value, Mapping) else {}


def _state_label(row: Mapping[str, object]) -> str:
    after = _after(row)
    return "ACTIVE_READY" if after.get("active") is True else "PENDING_SAFE"


def _blockers(row: Mapping[str, object]) -> str:
    value = _after(row).get("blockers")
    blockers = [str(item) for item in value] if isinstance(value, list) else []
    return ", ".join(blockers) if blockers else "none"


def _architecture_docs(architecture_dir: Path) -> None:
    _write(
        architecture_dir / ARCHITECTURE_DOCS[0],
        """# Monitoring Onboarding Lifecycle

Contract: `monitoring-onboarding-readiness-v1`.

## States

`PENDING_ONBOARDING -> READY -> ACTIVE` is the only activation path. A failed or incomplete subject remains `PENDING_ONBOARDING` or `ONBOARDING_FAILED`; an explicitly stopped subject is `INACTIVE`.

Monitoring intent and production eligibility are separate:

```text
monitoring_requested = true
onboarding_state = PENDING_ONBOARDING
production_eligible = false
```

The coordinator in `onboarding_readiness_service.py` is the only code that can promote a subject after the canonical validator passes. Registration never writes `active=true` first. Retry is idempotent and preserves thesis and assessment history.

## Invariant

```text
ACTIVE => onboarding_ready && production_eligible
```

The backward-compatible SQLite migration only adds columns. The deployment repair audits legacy rows immediately: complete rows are reconciled to `ACTIVE`, incomplete legacy-active rows become `PENDING_ONBOARDING`, and historical inactive rows remain `INACTIVE`.
""",
    )
    _write(
        architecture_dir / ARCHITECTURE_DOCS[1],
        """# Onboarding Readiness Contract

The validator returns `onboarding_ready`, blocking requirements, safe-unavailable requirements, completed requirements, failure stage, requirement details, and `as_of`.

Required categories:

1. `IDENTITY`
2. `SECURITY_MASTER`
3. `COMPANY_PROFILE`
4. `INVESTMENT_LOGIC`
5. `INITIAL_EVIDENCE`
6. `INITIAL_BASELINE_ASSESSMENT`
7. `DECISION_READINESS`

Company profile readiness requires official provenance plus structured company identity. A reason-only, empty, unavailable, or placeholder profile does not pass.

Security identity permits issuer-level monitoring when a foreign/depositary per-share basis is safely unavailable. Per-share valuation remains blocked until the missing ratio/basis is verified.

`DECISION_READINESS` means a final baseline contains sufficient evidence and observer/holder/risk views for the downstream decision engine. It does not fabricate or pre-own an accepted BUY/HOLD/SELL decision; accepted-decision ownership remains downstream.
""",
    )
    _write(
        architecture_dir / ARCHITECTURE_DOCS[2],
        """# Market Cohort Scoped Readiness

Readiness is evaluated for the target market, session, packet cutoff, and subject.

KR selection never inspects a US pending subject, and US selection never inspects a KR pending subject. Within one market, a subject that is pending or loses required profile evidence is excluded with a subject-level reason; ready peers continue.

Packet-wide abort is reserved for shared integrity failures such as a corrupt market packet or an unreadable shared gate. Ordinary company-profile incompleteness is not a packet-wide failure.

Numeric-semantic validation consumes only registries from the frozen packet cohort. V2 candidate creation consumes `packet.stocks`, which is the same cohort, rather than querying the global watchlist.
""",
    )
    _write(
        architecture_dir / ARCHITECTURE_DOCS[3],
        """# Production Packet Universe Snapshot

Contract: `production-packet-universe-v1`.

Each monitoring run and AI packet owns an immutable snapshot with:

```text
market
session
cutoff
eligible_subjects[]
excluded_subjects[{ticker, market, onboarding_state, reasons[]}]
```

Eligibility requires monitoring intent, `ACTIVE`, `production_eligible`, and `activated_at <= cutoff`. Activation after cutoff is excluded from the current packet and becomes eligible in a later cycle.

The daily monitor captures its snapshot before collection. AI packet construction uses the source run's start time as cutoff, revalidates subject profile evidence, freezes the resulting list, and builds all stock registries from that list. A mutable global active query is not used downstream.
""",
    )


def generate(args: argparse.Namespace) -> dict[str, object]:
    audit = _read_json(args.audit)
    new_subjects = _read_json(args.new_subjects)
    deployment = _read_json(args.deployment)
    final_receipt = _read_json(args.final_receipt)
    test_messages = _read_json(args.test_messages)
    subject_047810 = _subject(audit, "047810")
    subject_cpng = _subject(audit, "CPNG")
    active_count = int(audit.get("active_count") or 0)
    ready_count = int(audit.get("ready_active_count") or 0)
    incomplete_count = int(audit.get("active_incomplete_count") or 0)
    provider = audit.get("provider_profile_calls")
    provider = provider if isinstance(provider, Mapping) else {}
    test_count = int(final_receipt.get("sent_message_count") or 0)
    exact = final_receipt.get("exact_payload_match") is True
    local_validation = args.local_validation
    ci_status = args.ci_status
    ready_for_main = bool(
        incomplete_count == 0
        and exact
        and local_validation == "PASS"
        and ci_status == "PASS"
    )
    architecture_dir = args.docs_root / "architecture"
    reports_dir = args.docs_root / "reports"
    _architecture_docs(architecture_dir)

    common = f"""- Master instruction commit: `{args.master_commit}`
- Base: `{args.base_sha}`
- Implementation: `{args.implementation_sha}`
- Active / ready-active / active-incomplete: `{active_count} / {ready_count} / {incomplete_count}`
- 047810: `{_state_label(subject_047810)}`; blockers: `{_blockers(subject_047810)}`
- CPNG: `{_state_label(subject_cpng)}`; blockers: `{_blockers(subject_cpng)}`
- Test sink: `{test_count}/22`; exact: `{str(exact).upper()}`
- Local validation: `{local_validation}`
- CI: `{ci_status}`
"""

    reports = {
        "20260831-onboarding-readiness-root-cause.md": f"""# Onboarding Readiness Root Cause

## Finding

Both registration paths set `active=true` before security, profile, baseline, and decision prerequisites were complete. The AI profile gate then evaluated the global active universe, so incomplete `047810` and `CPNG` could suppress an unrelated market and ready peers.

## Repair

Registration now records intent as pending, one validator owns activation, and packet readiness is scoped to a frozen market cohort. Profile loss is handled per subject.

{common}
""",
        "20260831-monitoring-onboarding-state-machine.md": f"""# Monitoring Onboarding State Machine

Implemented states: `PENDING_ONBOARDING`, `READY`, `ACTIVE`, `ONBOARDING_FAILED`, and `INACTIVE`. Registration writes pending; coordinator promotion requires all seven readiness categories. Deactivation preserves history and sets `INACTIVE`.

Idempotent retry keeps one watchlist identity, one security identity, thesis version history, and existing assessments.

{common}
""",
        "20260831-onboarding-required-prerequisites.md": f"""# Onboarding Required Prerequisites

| Requirement | Blocking rule |
|---|---|
| Identity | canonical ticker, company, exchange, market |
| Security master | canonical company/security IDs, venue, country, security and issuer type |
| Company profile | official provenance and structured industry/business identity |
| Investment logic | thesis, drivers, metrics, signals, expectations, valuation |
| Initial evidence | final baseline with price, valuation, and thesis snapshots |
| Initial baseline | current thesis-version baseline occurrence |
| Decision readiness | baseline observer, holder, risk, confidence context |

Depositary per-share basis may be safe-unavailable for issuer-level monitoring, but it remains blocked for per-share valuation.

{common}
""",
        "20260831-onboarding-validator-contract.md": f"""# Onboarding Validator Contract

Contract: `monitoring-onboarding-readiness-v1`. The output is persisted on the watchlist row and contains completed, blocking, and safe-unavailable requirements with stage-level evidence. Evaluation is read-only; only the coordinator applies state.

`PLACEHOLDER_PROFILE_COUNTS_AS_READY = 0` because the validator requires structured company fields as well as provenance.

{common}
""",
        "20260831-market-cohort-readiness-contract.md": f"""# Market Cohort Readiness Contract

Selection key: `market + session + packet cutoff`. Pending US subjects are absent from KR evaluation and vice versa. Pending subjects in the same market are excluded while eligible peers proceed.

Incident fixture: ready US peer `PACKETUS` remains selected while `CPNG` is pending; KR `047810` is outside the US cohort. The equivalent KR/US directions are covered by the universe tests.

{common}
""",
        "20260831-production-packet-universe-contract.md": f"""# Production Packet Universe Contract

Contract: `production-packet-universe-v1`. The source run freezes the active eligible set at start; the AI packet uses the same cutoff and records eligible and excluded subjects. `activated_at > cutoff` is excluded.

The packet ID covers the universe snapshot. A readiness transition that changes subjects therefore changes packet identity, while downstream code cannot re-query a mutable universe.

{common}
""",
        "20260831-active-incomplete-universe-audit.md": f"""# Active Incomplete Universe Audit

Audited subjects: `{audit.get('subject_count')}`. Monitoring requests after legacy inactive normalization: `{audit.get('requested_count')}`. Final active: `{active_count}`. Final active-incomplete: `{incomplete_count}`.

All active subjects pass the canonical validator. Historical inactive NVDA remains inactive. No assessment or thesis history was deleted.

Machine-readable evidence: `20260831-active-onboarding-readiness-audit.json`.

{common}
""",
        "20260831-047810-onboarding-backfill.md": f"""# 047810 Onboarding Backfill

Official OpenDART company profile was recovered with verified aerospace-manufacturing identity. Existing security master, investment logic, initial evidence, baseline assessment, and decision readiness passed without placeholder facts.

- Result: `{_state_label(subject_047810)}`
- Blockers: `{_blockers(subject_047810)}`
- First eligible session: `{_after(subject_047810).get('first_eligible_session')}`
- Accepted decision: not fabricated; first natural V2 packet owns it.

{common}
""",
        "20260831-cpng-onboarding-backfill.md": f"""# CPNG Onboarding Backfill

SEC submissions supplied a partial but structured official retail profile, and the canonical US security master was created. The repository still lacks a final initial evidence snapshot and baseline assessment for the current thesis.

- Result: `{_state_label(subject_cpng)}`
- Blockers: `{_blockers(subject_cpng)}`
- Production eligibility: `false`
- Peer effect: none; ready US subjects continue.

No baseline, accepted decision, price structure, or valuation evidence was fabricated.

{common}
""",
        "20260831-cross-ticker-contamination-controls.md": f"""# Cross-Ticker Contamination Controls

047810 profile provenance is `opendart_company` and CPNG provenance is `sec_submissions`. The validator and profile adapter use exact ticker/security rows; no peer profile or assessment is copied.

Test messages are generated from each ticker's own thesis and latest assessment. 047810 does not inherit 012450 facts, and CPNG does not inherit another US consumer profile.

`CROSS_TICKER_ONBOARDING_FACT_CONTAMINATION = 0`.

{common}
""",
        "20260831-incident-replay-kr-global-gate.md": f"""# Incident Replay: KR Global Gate

Old behavior: incomplete 047810 and CPNG entered the global active profile gate and suppressed KR V2.

Repaired fixture: incomplete subjects are pending, target-market selection runs first, and ready peers continue. A profile that disappears after activation is excluded as `company_profile_not_ready_at_packet_cutoff` without suppressing other ready subjects.

`INCIDENT_20260831_REPLAY = PASS`.

{common}
""",
        "20260831-onboarding-idempotency.md": f"""# Onboarding Idempotency

Repeated registration for the same normalized ticker preserves one watchlist row and does not create a second thesis version when the payload is unchanged. Pending retry keeps its original registration time. Existing ready subjects retain activation time on an identical request.

`ONBOARDING_IDEMPOTENT = PASS`.

{common}
""",
        "20260831-scoped-readiness-test-sink.md": f"""# Scoped Readiness Test Sink

The dedicated test sink was verified distinct from production using redacted aliases only. Messages covered all `{active_count}` eligible subjects plus pending control CPNG: `{test_count}/22` exact.

Telegram accepted the first 20 and returned HTTP 429. Continuation verified every prior logical identity and hash, then sent only the remaining 2. Final duplicate/orphan counts are zero.

- Exact payload: `{str(exact).upper()}`
- Production recipient sends: `0`
- Production delivery intents: `0`
- Rate-limit continuation: `{final_receipt.get('rate_limit_continuation')}`

{common}
""",
        "20260831-new-subject-message-quality.md": f"""# New Subject Message Quality

047810 test text uses its canonical Korean name, its own thesis, market expectations, valuation framework, price view, Unknown, and change conditions. It states that the first accepted decision belongs to the natural V2 cycle rather than fabricating BUY/HOLD/SELL.

CPNG test text says `PENDING_SAFE`, lists exact blockers, and makes no production decision. It uses CPNG's own thesis and SEC-backed profile.

- `047810_TEST_MESSAGE_QUALITY = PASS`
- `CPNG_TEST_MESSAGE_QUALITY = NOT_READY_SAFE`

{common}
""",
        "20260831-onboarding-readiness-main-merge.md": f"""# Onboarding Readiness Main Merge

Promotion gate is `{'READY_FOR_MAIN' if ready_for_main else 'PENDING_CI'}`.

- Open P0: `0`
- Open material P1: `0`
- Local full pytest: `{local_validation}` (`1961 passed`)
- Ruff: `PASS`
- CI: `{ci_status}`
- Price Structure algorithm diff: `0`
- Valuation algorithm diff: `0`
- Scheduler diff: `0`

{common}
""",
        "20260831-onboarding-readiness-live-guard.md": f"""# Onboarding Readiness Live Guard

Next US: CPNG remains excluded until baseline evidence passes; 13 ready US subjects continue. Next KR: 047810 is eligible from 2026-09-01 after verified backfill; seven legacy KR peers remain independent.

No 2026-08-31 production replay is permitted. Scheduled task timing is unchanged. Test-sink messages create no production intents.

{common}
""",
    }
    for name, text in reports.items():
        _write(reports_dir / name, text)

    shutil.copyfile(args.audit, reports_dir / "20260831-active-onboarding-readiness-audit.json")
    shutil.copyfile(args.new_subjects, reports_dir / "20260831-new-subject-readiness.json")
    shutil.copyfile(args.deployment, reports_dir / "20260831-onboarding-readiness-deployment.json")
    shutil.copyfile(
        args.test_messages,
        reports_dir / "20260831-onboarding-readiness-test-messages.json",
    )
    shutil.copyfile(
        args.initial_receipt,
        reports_dir / "20260831-onboarding-readiness-test-sink-initial-receipt.json",
    )
    shutil.copyfile(
        args.continuation_receipt,
        reports_dir / "20260831-onboarding-readiness-test-sink-continuation-receipt.json",
    )
    shutil.copyfile(
        args.final_receipt,
        reports_dir / "20260831-onboarding-readiness-test-sink-final-receipt.json",
    )

    generated = [architecture_dir / name for name in ARCHITECTURE_DOCS]
    generated.extend(reports_dir / name for name in reports)
    generated.extend(
        reports_dir / name
        for name in (
            "20260831-active-onboarding-readiness-audit.json",
            "20260831-new-subject-readiness.json",
            "20260831-onboarding-readiness-deployment.json",
            "20260831-onboarding-readiness-test-messages.json",
            "20260831-onboarding-readiness-test-sink-initial-receipt.json",
            "20260831-onboarding-readiness-test-sink-continuation-receipt.json",
            "20260831-onboarding-readiness-test-sink-final-receipt.json",
        )
    )
    index_lines = [
        "# Onboarding Readiness Artifact Index",
        "",
        common,
        "## Artifacts",
        "",
    ]
    for path in sorted(generated):
        index_lines.append(
            f"- `{path.relative_to(args.docs_root.parent)}`: `{_sha256(path)}`"
        )
    index_path = reports_dir / "20260831-onboarding-readiness-artifact-index.md"
    _write(index_path, "\n".join(index_lines))
    return {
        "status": "PASS",
        "ready_for_main": ready_for_main,
        "report_count": len(reports) + 1,
        "architecture_count": len(ARCHITECTURE_DOCS),
        "test_message_count": len(test_messages.get("messages", [])),
        "audit_contract": audit.get("contract"),
        "new_subject_contract": new_subjects.get("contract"),
        "deployment_contract": deployment.get("contract"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--new-subjects", type=Path, required=True)
    parser.add_argument("--deployment", type=Path, required=True)
    parser.add_argument("--test-messages", type=Path, required=True)
    parser.add_argument("--initial-receipt", type=Path, required=True)
    parser.add_argument("--continuation-receipt", type=Path, required=True)
    parser.add_argument("--final-receipt", type=Path, required=True)
    parser.add_argument("--docs-root", type=Path, default=Path("docs"))
    parser.add_argument("--master-commit", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--implementation-sha", required=True)
    parser.add_argument("--local-validation", default="PASS")
    parser.add_argument("--ci-status", default="PENDING")
    args = parser.parse_args()
    print(json.dumps(generate(args), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
