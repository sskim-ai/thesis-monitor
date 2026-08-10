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
    "코리안리": "003690",
    "korean re": "003690",
    "hmm": "011200",
    "현대글로비스": "086280",
    "hyundai glovis": "086280",
    "naver": "035420",
    "네이버": "035420",
    "hd현대": "267250",
    "hd 현대": "267250",
    "빅솔론": "093190",
    "팬오션": "028670",
    "지엔씨에너지": "119850",
    "제주반도체": "080220",
}

COMPANY_NAME_ALIASES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "003690": "코리안리",
    "011200": "HMM",
    "086280": "현대글로비스",
    "035420": "NAVER",
    "267250": "HD현대",
    "093190": "빅솔론",
    "028670": "팬오션",
    "119850": "지엔씨에너지",
    "080220": "제주반도체",
}


def compact_alias_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_ticker(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"\.(ks|kq|kospi|kosdaq)$", "", normalized, flags=re.IGNORECASE)
    return TICKER_ALIASES.get(compact_alias_key(normalized), normalized).upper()
