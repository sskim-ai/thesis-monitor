"""Finite original-provider import closure, not permission to read or execute it.

The trusted parent still owns code approval, StockPlan pins and source lifetime.
V1 retains its sealed 25-file behavior. V2 is an explicit minimal code contract;
neither a caller's hash nor this structural check creates runtime authority.
"""
import re

CONTRACT_V2 = 'original-provider-import-closure-v2'
REQUIRED_V2 = frozenset({
    'app/__init__.py', 'app/config.py', 'app/parsing.py',
    'app/indicators/__init__.py', 'app/indicators/supply_demand.py',
    'app/indicators/technical.py', 'app/providers/__init__.py',
    'app/providers/base.py', 'app/providers/investor_flows.py',
    'app/providers/kiwoom.py', 'app/schemas/__init__.py',
    'app/schemas/ohlcv.py', 'app/schemas/symbols.py',
    'app/services/__init__.py', 'app/services/exceptions.py',
    'app/services/kiwoom_global_lane.py', 'app/services/ohlcv_service.py',
    'app/services/runtime_maintenance.py', 'app/services/symbol_resolver.py',
})


def validate_external_manifest(pins, contract=None):
    if contract is None:
        if len(pins) != 25:
            raise ValueError('scoped_legacy_external_manifest_count')
        return
    if contract != CONTRACT_V2 or not isinstance(pins, dict) or set(pins) != REQUIRED_V2:
        raise ValueError('scoped_external_manifest_contract_or_closure')
    for value in pins.values():
        if (not isinstance(value, dict) or set(value) != {'bytes', 'sha256'}
                or type(value['bytes']) is not int or not 0 <= value['bytes'] <= 1024*1024
                or not isinstance(value['sha256'], str)
                or re.fullmatch(r'[a-f0-9]{64}', value['sha256']) is None):
            raise ValueError('scoped_external_manifest_pin_shape')
