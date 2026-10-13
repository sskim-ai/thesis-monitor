"""Production-specific authorization over the unchanged sealed wire executor."""
from app.services.production_source_plan import ProductionRequestPlan, admit_request_plan
from app.services.sealed_fresh_dispatch import SealedDispatcher


class ProductionSourceDispatcher(SealedDispatcher):
    def __init__(self, *, plan, root, compiler_args, kis_plan, config_identities,
                 credential_presence, repository_root, secrets=()):
        self.plan = ProductionRequestPlan.model_validate(plan)
        self.admission = admit_request_plan(self.plan, compiler_args=compiler_args,
            kis_plan=kis_plan, config_identities=config_identities,
            credential_presence=credential_presence, repository_root=repository_root)
        if not self.admission["live_dispatch_allowed"]:
            raise ValueError("production_whole_plan_not_admitted")
        self._initialize(root=root, secrets=secrets)
