import re


BUYBACK_PATTERNS = (
    r"\bbuyback\b",
    r"\bbuy\s+back\b",
    r"\bstock\s+buyback\b",
    r"\bshare\s+repurchase\b",
    r"\bstock\s+repurchase\b",
    r"\brepurchase\s+program\b",
    r"\brepurchase\s+authorization\b",
    r"\bauthorized\s+to\s+repurchase\b",
    r"\bcan\s+(?:now\s+)?repurchase\b",
    r"\bcan\s+(?:now\s+)?buy\s+back\b",
    r"\baccelerated\s+share\s+repurchase\b",
    r"\basr\b",
    r"자사주\s*매입",
    r"자기주식\s*취득",
)


def is_buyback_text(value: str) -> bool:
    return any(
        re.search(pattern, value, flags=re.IGNORECASE)
        for pattern in BUYBACK_PATTERNS
    )


def buyback_authorization_amount(value: str) -> float | None:
    match = re.search(
        r"(?:\$|usd\s*)?(\d+(?:\.\d+)?)\s*(billion|million|bn|mn|b|m)\b",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    amount = float(match.group(1))
    scale = (
        1_000_000_000
        if match.group(2).lower() in {"billion", "bn", "b"}
        else 1_000_000
    )
    return amount * scale
