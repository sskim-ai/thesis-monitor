"""Research-only literal disclaimers; all remaining claim guards stay active."""
import re
from app.services.directional_balance_service import directional_balance_language_errors

CONTRACT = 'research-explicit-return-disclaimer-v1'
# Only the denied concept itself is masked, never the surrounding sentence.
# Numbers, assertions in another clause and the original score guard survive.
_DISCLAIMERS = (
    re.compile(r'기대\s*수익률(?:이나\s*기업가치\s*안전마진)?(?:은|는|이|가)?\s*아닙?니다(?=[.!?\s]|$)'),
    re.compile(r'기대\s*수익률(?:이나\s*기업가치\s*안전마진)?(?:은|는|이|가)?\s*아니다(?=[.!?\s]|$)'),
    re.compile(r'\bnot\s+(?:an?\s+)?expected\s+return\b', re.I),
    re.compile(r'\bexpected\s+return\s+is\s+not\s+(?:established|implied|asserted)\b', re.I),
)

def research_language_errors(texts):
    sanitized=[]
    for text in texts:
        for pattern in _DISCLAIMERS:
            text=pattern.sub('EXPLICIT_RETURN_DISCLAIMER',text)
        sanitized.append(text)
    return directional_balance_language_errors(sanitized)
