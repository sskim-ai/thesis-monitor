"""Compatibility name for the canonical owner; proof requests remain default-off."""

import sys

from app.services import new_buyer_v2_policy as canonical

sys.modules[__name__] = canonical
