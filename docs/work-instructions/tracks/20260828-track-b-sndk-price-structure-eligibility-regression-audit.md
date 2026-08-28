# Track B — SNDK Price Structure Eligibility Regression Audit

Trace why SNDK moved from:

```text
ELIGIBLE_SR_ONLY
with near support/resistance
```

in the prior E2E artifact to:

```text
BLOCKED
```

before and after the Major-SR repair.

Explain the same-session price-basis difference:

```text
$1,456.93
vs
$1,499.37
```

Repair only a real shared defect.

If data cannot be reconciled, keep fail-closed and report the blocker explicitly.
