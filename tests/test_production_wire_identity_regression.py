"""Actual-launcher KR failure: overlapping synthetic credentials must redact fully."""
import json

import httpx
import pytest

from app.services.sealed_fresh_dispatch import wire_identity


@pytest.mark.parametrize("secrets", [
    ("synthetic-naver", "synthetic-naver-secret"),
    ("synthetic-naver-secret", "synthetic-naver"),
])
def test_sealed_naver_request_identity_is_independent_of_secret_prefix_order(secrets):
    request = httpx.Request("GET", "https://openapi.naver.com/v1/search/news.json",
        params={"query": '"Synthetic 000660"', "display": "10", "start": "1", "sort": "date"},
        headers={"X-Naver-Client-Id": "synthetic-naver", "X-Naver-Client-Secret": "synthetic-naver-secret"})
    public = json.loads(wire_identity(request, secrets))
    assert public["headers"] == [["x-naver-client-id", "[REDACTED]"],
                                 ["x-naver-client-secret", "[REDACTED]"]]
    assert public["url"].endswith("query=%22Synthetic+000660%22&display=10&start=1&sort=date")
