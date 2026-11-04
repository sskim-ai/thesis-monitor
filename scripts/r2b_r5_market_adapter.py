"""Compatibility import for historical proof callers; same canonical functions."""
import sys
from app.services import canonical_market_projection as canonical
sys.modules[__name__] = canonical
