# Delivery State Machine Repair

The repository-native notification rows remain authoritative. No parallel queue or DB migration
was added.

Supported lifecycle:

```text
packet_bound_pending_hold -> held -> ai_assisted_pending -> ai_assisted_sent
                                      | deadline/terminal failure
                                      v
                                  fallback_pending -> fallback_sent
```

`partial_integrity_rejected` is terminal for automatic fallback and requires manual intervention.
Sent AI and sent fallback states cannot be taken over by a reuse packet. Late validation against a
terminal set is archived under `late-validation-results/` and cannot overwrite the canonical
validation result or mutate delivery rows.

CLI results include `orchestration_outcome`: `AI_V2_DELIVERED`, `AI_V2_PENDING`,
`FALLBACK_DELIVERED`, or `NO_DELIVERY_ERROR`. `already_sent` retains the delivered outcome.
