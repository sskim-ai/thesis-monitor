"""Single balance owner added to the unchanged evidence/severity policy."""
from app.services.accepted_directional_balance_service import accepted_directional_balance
from scripts.m12ds_r3_policy import (  # noqa: F401
    CONTRACT, Effect, ADVERSE, observations, materialize_core, canonical_core,
    axis_capability, policy_audit, frozen_fact_fields, number, canonical_sha256,
)
from scripts import m12ds_r3_policy as r3


def validate_decision(row, cap, ranges):
    receipt = r3.validate_decision(row,cap,ranges)
    try:
        accepted_directional_balance(row['directional_buy_score'],row['overall_direction'])
    except (ValueError, TypeError):
        receipt['errors'].append('canonical_direction_balance_invalid')
    receipt['status'] = 'FAIL' if receipt['errors'] else 'PASS'
    return receipt
