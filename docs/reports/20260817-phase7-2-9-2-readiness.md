# Phase 7.2.9.2 Experimental Readiness

Date: 2026-08-17

## Status

- Branch: `codex/phase-7-2-9-2-human-quality-hardening`
- Required base: `c2f67f842bed8d4bec8a5aefce8f469d76b4fc42`
- Implementation commit: `ab27ebc5f2a9f5908d1401639ea52b0d05b1b1e9`
- Production main and operating checkout: `aeb87a9d2aee0d4b840c0a8717319e01b375f5f5`
- Runtime Pilot: KR 3/5, US 2/5
- Production Assist: OFF
- Corrected Preview status: `pending_work_human_review`
- Main merge / production deployment: not performed

Phase 7.2.9.1's deterministic results remain preserved, but Work failed both Previews. This phase
repairs the seven recorded blockers without changing production state or promoting a retrospective
to Pilot or Production Assist evidence.

## Contracts

- Financial period: `financial-amount-period-v1`
- Financial statement basis: `financial-statement-basis-v1`
- Typed valuation: `typed-valuation-interpretation-v2`
- Valuation coherence: `valuation-coherence-v1`
- Runtime quality: `runtime-message-quality-v1`
- Receipt: `runtime-message-quality-receipt-v2`
- Policy/schema: `daily-review-v3.10` / 4

## Financial Statement Basis

CFS, OFS, conflict, and unknown are independent deterministic states. IS/CIS no longer implies
separate basis. Unique CFS is preferred; verified OFS-only amounts include `별도 기준`; mixed-basis
growth and ambiguous basis fail closed. An official reference with a different basis is period-only
evidence and cannot validate or overwrite the runtime value.

In the corrected KR packet, Korean Re's Q2 operating income is labeled `연결 기준`. Samsung's Q2
amount period is known but the isolated runtime row has unknown statement basis, so the amount and
growth are withheld instead of being presented as consolidated or separate. SK Hynix's denied
earnings and PE lineage remain unavailable.

## Occurrence-Bound Valuation

Typed references now bind one exact normalized span, metric, Fact, direction, basis status, and
comparison claim set. A safe PBR occurrence cannot authorize a denied PER occurrence elsewhere in
the same section. Duplicate spans, wrong metrics, reused references, and uncovered directional
language fail closed. Corrected KR and US output has 50 covered occurrences and zero uncovered
occurrences.

## Final Rendered Language

The exact Telegram text is checked after rendering and before receipt persistence. Particle errors,
duplicate canonical labels, and internal implementation terms are rejected. The corrected payloads
have zero findings in all three categories. This validation does not mutate or repair rendered text.

## Relation Consistency

Trailing/forward relations preserve forward period state (`exact`, `provider_defined`, or
`unknown`) and security/share/currency comparability. Relation interpretation and data caution must
state the same status. GOOGL, IBM, TSLA, and MU have eligible comparable relations; HUT remains
Unknown. MU no longer combines an exact relation with an unclear-period warning.

## Receipt And Partial Delivery

Receipt reuse verifies the full file SHA, every delivery metadata SHA, packet/output/rendered hashes,
versions, message count, status, check results, errors, and offset-aware timestamp. Sixteen receipt
integration cases pass, including validated-output tampering and an actual partial AI-delivery case.

- Pre-send integrity failure: AI send 0; one persisted deterministic fallback set remains eligible.
- Post-partial integrity failure: no additional AI send, no duplicate deterministic set, no false
  full-fallback record, and explicit manual-intervention state.
- Legacy completed archive: no rewrite, replay, or recount.

## Retrospective Results

### KR

- Source / corrected packet: `2026-08-16-kr-run-21-5844682f15da` /
  `2026-08-16-kr-run-21-23491b3e8f73`
- Logical payloads: market 1 + stocks 7
- Numeric binding: automatic 98, manual 0, rejected 0, formatter 0, unresolved 0
- Full validator / runtime gate: PASS / PASS
- Packet SHA-256: `f5cb6a8b682d846263d9990c22e6770509ef9c9220f4159d4a402257acac5c62`
- Output SHA-256: `c8131741ee7c14c8409eb6d20dec79821c460faa55a14252ee426697b7e2cde7`
- Payload SHA-256: `d92a4f00635c56c80215f9ce21407f2f1f0beb7c83c700cd36a18da336219ace`
- Receipt SHA-256: `48857f3c0519cf29755c1de9a536629e1f7076a477170c65e08d5a643eecb067`

### US

- Source / corrected packet: `2026-08-16-us-run-20-f9b252d77940` /
  `2026-08-16-us-run-20-fb918a643ae6`
- Logical payloads: market 1 + stocks 13
- Numeric binding: automatic 169, manual 0, rejected 0, formatter 0, unresolved 0
- Full validator / runtime gate: PASS / PASS
- Packet SHA-256: `e9fafec975f317f581fb13e9d365a66ef45bf5b5eb260b6e7e4aaa489f263e54`
- Output SHA-256: `248d90cafdc51663e276dc37c1c9f83a29cd5e87678f29efeb3fea4c4cbcde82`
- Payload SHA-256: `ee39600753ef19b7f29382dbd10095697d8bafbef767f46a6d98cf7e26418c31`
- Receipt SHA-256: `3faef48ff134beb22c8012770ed7dec18f9a7943a55358675b0de3ca01782e3d`

Both Previews remain pending direct Work review.

## Isolation

- Source DB copy SHA-256: `4cfd7bb8cef53954de141c8201f510d0c9bd6c2a1ce3299ae22ad42a18826d39`
- Operating DB SHA-256: `987bfb4b82c8017054f8c3cef1213177246868f902dd134be0c4f4fd34e3eb78`
- Pilot state SHA-256: `8aad97ed4110efb0f7bccd83aa5bd9e78c570e218ef59784c52dcf5cadf24450`
- Provider calls / Telegram sends / operating mutations / Pilot mutations: 0 / 0 / 0 / 0

## Artifacts

- [KR full Preview](20260817-phase7-2-9-2-kr-telegram-preview.md)
- [US full Preview](20260817-phase7-2-9-2-us-telegram-preview.md)
- [KR statement-basis matrix](20260817-phase7-2-9-2-kr-financial-statement-basis-matrix.json)
- [Samsung basis audit](20260817-phase7-2-9-2-samsung-cfs-ofs-audit.json)
- [SK Hynix qualitative audit](20260817-phase7-2-9-2-skhynix-denied-qualitative-audit.json)
- [Hanwha RR audit](20260817-phase7-2-9-2-hanwha-rr-basis-audit.json)
- [Typed valuation occurrence matrix](20260817-phase7-2-9-2-typed-valuation-occurrence-matrix.json)
- [US relation audit](20260817-phase7-2-9-2-us-trailing-forward-relation-audit.json)
- [MU before/after](20260817-phase7-2-9-2-mu-relation-caution-before-after.json)
- [Final language audit](20260817-phase7-2-9-2-final-rendered-language-audit.json)
- [Receipt integration matrix](20260817-phase7-2-9-2-receipt-integrity-negative-matrix.json)
- [Pre-send fallback audit](20260817-phase7-2-9-2-pre-send-fallback-audit.json)
- [Partial-delivery audit](20260817-phase7-2-9-2-partial-delivery-integrity-audit.json)
- [Legacy archive audit](20260817-phase7-2-9-2-legacy-archive-compatibility-audit.json)
- [Isolation audit](20260817-phase7-2-9-2-isolation-mutation-audit.json)

## Remaining Gaps

- TSM and WRD remain identity Unknown; authoritative ingestion is outside this phase.
- SKHY current-ADS denominator/share/currency basis remains insufficient, so multiples stay withheld.
- KR local index, breadth, and market-wide flow remain unavailable.
- The corrected Previews require direct Work review before merge or deployment.
