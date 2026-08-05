import re


TICKER_ALIASES = {
    "삼성전자": "005930",
    "samsung electronics": "005930",
    "samsung electronics co": "005930",
    "samsung electronics co ltd": "005930",
    "sk하이닉스": "000660",
    "sk hynix": "000660",
    "sk hynix inc": "000660",
    "에스케이하이닉스": "000660",
}

COMPANY_NAME_ALIASES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
}


def compact_alias_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_ticker(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"\.(ks|kq|kospi|kosdaq)$", "", normalized, flags=re.IGNORECASE)
    return TICKER_ALIASES.get(compact_alias_key(normalized), normalized).upper()
