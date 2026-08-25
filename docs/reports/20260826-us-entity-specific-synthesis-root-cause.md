# US Entity-Specific Synthesis Root Cause

Date: 2026-08-26 KST
Packet: `2026-08-25-us-run-37-7e04812311c2`
Instruction commit: `8cf5226ca0c5ae5553fb06b24399462ea3cf6088`
Implementation commit: `f2326c39485e600bca2cee15747deeb8465c5c8a`

## Symptom

CORZ, HUT, WULF, and TSM could pass hard fact and sentence-level quality gates while sharing a
generic "HPC execution and cash conversion" conclusion. TSM therefore read like a data-center
transition company despite packet-supported foundry drivers.

## Root Cause

Three narrow gaps combined:

1. Industry ownership scanned a broad combined evidence string and evaluated generic HPC terms
   before a semiconductor-foundry class.
2. The renderer could prefer a safe category-level sentence even when the stored core thesis
   contained a stronger entity-specific discriminator.
3. Canary quality was per-message. It had no batch contract to distinguish harmless shared
   structure from cross-industry analytical reuse.

The previous checks correctly enforced factual safety, numeric provenance, temporal safety, and
section duplication. They did not prove that a fact-safe conclusion surfaced the company's actual
stored driver.

## Repair

- Foundry ownership is resolved before generic HPC ownership when the packet contains supported
  advanced-node, wafer-ASP, foundry, or overseas-fab semantics.
- Stock synthesis leads with the best supported stored entity sentence.
- `entity-specific-synthesis-v1` extracts semantic driver features without ticker allowlists.
- `cross-message-synthesis-specificity-v1` classifies claim-bearing lines as
  `GENERIC_SHARED`, `ENTITY_SPECIFIC_SHARED_STRUCTURE`, or `ENTITY_SPECIFIC_UNIQUE`.
- Canary selection rejects only affected stock messages when a specific supported driver exists
  but a cross-industry generic claim remains.

No target output sentence, ticker/date/value, external model fact, validator threshold, or canary
limit was hard-coded.

## Benchmark Result

- TSM: `semiconductor_foundry`; advanced-node utilization and overseas-fab margin dilution.
- CORZ: billed capacity and contract-to-activation-to-billing-to-revenue conversion.
- HUT: current Compute/mining mix and contract-to-construction/activation/NOI execution.
- WULF: contract scale against EBITDA, CAPEX, compensation, and dilution conversion.
- CRCL positive control: reserve-yield dependence and non-interest revenue transition preserved.

`US_ENTITY_SPECIFIC_SYNTHESIS = PASS`
