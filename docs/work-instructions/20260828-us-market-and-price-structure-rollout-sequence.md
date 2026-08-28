# thesis-monitor — US Market + US Price Structure Sequential Rollout
## Phase 1: full US morning market message
## Phase 2: monitored US/foreign stock Price Structure selective pre-enable
## Phase 3: US-only enablement + natural proof

---

# 0. Purpose

Run the two US rollout streams in strict order:

```text
PHASE 1
US morning full message integration
→ explicit SPY/QQQ/IWM/SOXX/RSP numbers
→ market internals
→ Korea night futures
→ temporally safe macro
→ dedicated test-sink full-message review
→ deploy
→ natural proof pending/complete

PHASE 2
US monitored-stock Price Structure
→ current-data replay
→ eligibility/provenance
→ full monitored-universe test-sink messages
→ US-only selective enablement

PHASE 3
next natural US stock-monitoring cycle
→ exact live proof
```

Do not merge Phase 1 market-message renderer logic with stock Price Structure logic.

---

# 1. Phase 1 prerequisite

Execute the existing instruction:

`20260828-us-morning-full-message-integration-and-iterative-validation.md`

Minimum gate before US Price Structure operating enablement:

```text
US_FULL_MESSAGE =
TEST_PASS_READY_TO_DEPLOY
or
DEPLOYED_AWAITING_NATURAL_PROOF
or
LIVE_PASS

OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
US_PRICE_STRUCTURE_ENABLED = 0
```

Track A/B Price Structure replay/test preparation MAY run in parallel with Phase 1 test work if code ownership
does not overlap.

Track C US Price Structure enablement MUST wait until Phase 1 has no P0/material P1.

---

# 2. Phase 2 instruction

Execute:

`20260828-us-price-structure-selective-preenablement.md`

Subtracks:

```text
Track A
current-data full-universe replay

Track B
dedicated test-sink all monitored US/foreign stock messages

Track C
US-only bounded operating enablement

Track D
natural live proof
```

---

# 3. Required sequencing

```text
US market full-message test PASS
        │
        ├─────────────┐
        │             │
        ▼             ▼
market deploy     Price Structure replay
                      │
                      ▼
                full-universe test sink
                      │
                      ▼
              all gates 0/0 PASS
                      │
                      ▼
         US Price Structure selective ON
                      │
                      ▼
         next natural US stock messages
                      │
                      ▼
                   LIVE_PASS
```

---

# 4. Isolation

Throughout:

```text
KR market TOP3 = unchanged
KR Price Structure = unchanged
US market message = current validated layout
US Price Structure = OFF until Track C
Production Assist = OFF
business investment logic = unchanged
```

---

# 5. Final master state

Only declare the US rollout complete when:

```text
US_FULL_MESSAGE = LIVE_PASS
US_PRICE_STRUCTURE = LIVE_PASS
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

If the market-message natural proof is still pending but its deterministic/test gates are PASS:

US Price Structure may be enabled only if the repository/master rollout policy explicitly permits
independent product enablement and the Price Structure pre-enable gates are all PASS.

Record that decision explicitly.
