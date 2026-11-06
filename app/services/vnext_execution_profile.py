"""Pinned model identities, separate from economic-output contracts."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionProfile:
    contract: str
    model: str
    effort: str
    timeout_seconds: int = 600
    retries: int = 0

    def model_request(self):
        return dict(model=self.model,effort=self.effort,
                    timeout_seconds=self.timeout_seconds,retries=self.retries)


ASTRA_XHIGH_V1 = ExecutionProfile('ASTRA_XHIGH_EXECUTION_V1','gpt-6-astra','xhigh')
SOL_HIGH_V1 = ExecutionProfile('SOL_61_HIGH_EXECUTION_V1','gpt-6.1-sol','high')


def require_profile(profile):
    if type(profile) is not ExecutionProfile or profile not in (ASTRA_XHIGH_V1,SOL_HIGH_V1):
        raise ValueError('exact_supported_execution_profile_required')
    return profile
