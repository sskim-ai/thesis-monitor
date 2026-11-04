"""Compatibility name for the canonical owner; proof requests remain default-off."""

import sys

from app.services import new_buyer_base_contract as canonical

sys.modules[__name__] = canonical
