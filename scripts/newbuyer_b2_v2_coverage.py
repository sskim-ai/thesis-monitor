"""Compatibility import for unchanged source-only coverage semantics."""
import sys
from app.services import current_source_coverage as canonical
sys.modules[__name__] = canonical
