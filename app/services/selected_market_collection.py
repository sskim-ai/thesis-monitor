"""Selected optional detail omission; original mandatory Market parser retained."""
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService, _PageSet
from app.services.selected_source_plan import SelectedConsumerPolicy


class SelectedKrMarketCollection(KiwoomKrMarketContextService):
    def __init__(self,*args,consumer_policy,**kwargs):
        SelectedConsumerPolicy.model_validate(consumer_policy)
        super().__init__(*args,**kwargs)

    async def _ka10066_pages(self,*,market_code):
        # No rows or numeric zero facts: native reconciliation marks detail
        # incomplete and forbids concentration/flow qualification as before.
        return _PageSet(rows=[],pages=0,complete=False,response_hashes=[],duplicate_identities=[])
