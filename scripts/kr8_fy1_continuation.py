"""Source-only continuation plumbing. No acquisition or new model semantics."""

from scripts.kr8_fy1_models import Kr8Execution


class Kr8Continuation(Kr8Execution):
    SUCCESS_TERMINAL = 'R2B_R9_REV40_R2_KR8_FROZEN_SOURCE_8_MESSAGE_PASS_READY_FOR_BLIND_REVIEW'


from app.services.kr_current_valuation_projection import source_only_projection  # noqa: E402,F401
