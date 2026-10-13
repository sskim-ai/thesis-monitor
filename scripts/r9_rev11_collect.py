"""Compatibility name for the canonical bounded acquisition implementation."""
import sys
from app.services import canonical_source_acquisition as canonical
sys.modules[__name__] = canonical
