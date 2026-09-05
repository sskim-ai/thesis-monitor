# Logical Condition Coverage Contract

The claim-side coverage modes are:

| Mode | Meaning | Gate |
|---|---|---|
| `FULL` | Complete source condition | Exact structured operator/tree equivalence required |
| `NON_EXHAUSTIVE_EXAMPLE` | One illustrative source branch | Exactly one owned leaf required |
| `PARTIAL` | Explicit incomplete subset | Must not silently claim the full branch set |

For `FULL`, `ANY_OF -> ALL_OF`, `ALL_OF -> ANY_OF`, and branch deletion are semantic failures. A single branch is allowed only as `NON_EXHAUSTIVE_EXAMPLE`. Branch order is not semantic, but branch identity and nesting are. The validator does not read Korean or English conjunctions from output prose.
