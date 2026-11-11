"""Original selected stock reassembly, not a new Market or economic policy."""
from app.services.canonical_source_inputs import fresh_authority_inputs
from app.services.canonical_source_replay import stock_inputs
from app.services.fresh_financial_stock_owner import assemble_fresh_stock
from app.services.selected_source_plan import SCOPE, decode_stock_plan
from scripts.fresh_source_only_export import source_only_fresh_stock
from scripts.m12dr_financial_source_authority import build_source_authority


def replay_stocks(*,root,frozen,outcome,policy,registration_owner,enabled=False):
    if enabled is not True:
        raise ValueError('selected_stock_replay_default_off')
    if frozen.get('scope')!=SCOPE:
        raise ValueError('selected_stock_replay_scope_required')
    plan=decode_stock_plan(frozen)
    inputs,errors=stock_inputs(root,frozen,policy,outcome,
        prospective_owners={plan.market:registration_owner})
    if errors or set(inputs)!=set(plan.subjects):
        raise ValueError('selected_original_stock_bindings_incomplete')
    stocks,authorities,exports={},{},{}
    for ticker,original in inputs.items():
        stock=assemble_fresh_stock(**original)
        authority=build_source_authority(**fresh_authority_inputs(stock,original))
        # This checks the original fresh contract before source-only export.
        exports[ticker]=source_only_fresh_stock(stock,authority)
        stocks[ticker],authorities[ticker]=stock,authority
    return dict(stocks=stocks,authorities=authorities,source_only_exports=exports,
        source_generation=plan.run_id,market_parent_issued=False,model_calls=0)
