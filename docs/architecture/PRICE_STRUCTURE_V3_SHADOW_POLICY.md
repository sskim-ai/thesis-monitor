# Price Structure v3 Shadow Policy

## Problem

A new structural engine can pass deterministic tests while still differing materially from a user
reference or lacking the required history budget. Such evidence is not sufficient for immediate
production exposure.

## Decision

`price-structure-v3-shadow-policy-v1` isolates v3 to tests, frozen archive generation, reports,
and signed-in local AI selection trials. The production packet, renderer, fallback, Telegram,
Public Action, schema, tasks, assessment persistence, and current SR engine do not import it.

Promotion to `INTEGRATED_READY_NOT_ARMED` requires the full 1200/600/300 contract, an explained SK
hynix benchmark without material method conflict, generalization, provenance, confluence,
look-ahead and numeric safety, stable ID-only AI selection, full CI, no P0/material P1, and zero
visible diff.

Current state is `SHADOW`: 17 archive-only model calls passed, 14 subjects had stable selection,
six had valid abstention, and unstable Fib eligibility is zero. The daily 1200 interface cap and
SK hynix method conflict remain material P1.

## Why

Shadow isolation preserves the engineering value of the implementation without converting an
incomplete evidence claim into user-visible behavior.

## Rejected Alternative

Enabling only favorable tickers, shrinking the history contract, accepting the SK discrepancy
without review, or waiting for unrelated natural/KRX tracks were rejected.

## Safety Constraint

No manual Telegram, manual task, DB mutation, Pilot mutation, official assessment mutation, or
Production Assist change is authorized. The next action is a bounded feature-local repair.
