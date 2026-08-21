# Phase 9.1D Semantic and Causal Audit

The initial runtime scope accepts only total Inventory and exact Trade AR. The narrow snapshot is
passed to the unchanged `working-capital-shadow-consumption-v1` renderer and validator.

Retrospective results:

- broad AR, Trade AP, broad AP, contract asset, and accrued-liability selections: 0;
- component inventory promoted to total Inventory: 0;
- DSO, Inventory Days, DPO, or CCC claims: 0;
- customer non-payment, demand collapse, excess inventory, supplier delay, or working-capital
  causality assertions: 0;
- thesis, valuation, or warning mutations: 0;
- semantic validation errors across 20 subjects: 0.

The renderer describes a canonical growth relation as a checking signal and explicitly avoids
claiming cause. A compatible same-date cash-flow period adds context only; OCF/FCF is not recomputed
and no causal bridge is generated.
