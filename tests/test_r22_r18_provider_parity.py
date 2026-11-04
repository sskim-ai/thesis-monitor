from app.services.fresh_source_run_contract import acquisition_plan
from tests.test_r9_rev11_full_plan import compiled


def test_ecos_preflight_period_field_matches_executable_owner():
    stock, args, compiled_plan = compiled()
    plan = acquisition_plan(stock.model_dump(mode="json"), args["identities"], kr_max_pages=1)
    assert plan["macro_queries"]["ecos"]["period_field"] == "CYCLE"
    assert compiled_plan["candidate"]["macro_queries"]["ecos"]["period_field"] == "CYCLE"
