from app.services.security_master_service import SECURITY_ALIASES
from app.utils.tickers import COMPANY_NAME_ALIASES, normalize_ticker


def test_003690_current_identity_is_korean_re() -> None:
    assert COMPANY_NAME_ALIASES["003690"] == "코리안리"
    assert normalize_ticker("코리안리") == "003690"
    assert normalize_ticker("Korean Re") == "003690"
    assert "코리안리" in SECURITY_ALIASES["003690"]
    assert "korean re" in SECURITY_ALIASES["003690"]
