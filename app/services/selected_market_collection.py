"""Selected optional detail omission; original mandatory Market parser retained."""
from app.services.kiwoom_kr_market_context_service import KiwoomKrMarketContextService
from app.services.selected_source_plan import SelectedConsumerPolicy


class SelectedKrMarketCollection(KiwoomKrMarketContextService):
    def __init__(self,*args,consumer_policy,**kwargs):
        SelectedConsumerPolicy.model_validate(consumer_policy)
        super().__init__(*args,**kwargs)
