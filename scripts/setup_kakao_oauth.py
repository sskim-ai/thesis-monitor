from __future__ import annotations

import html
import secrets
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from app.config import get_settings
from app.services.notification_service import KakaoSelfNotifier


REDIRECT_URI = "http://localhost:4000/redirect"
AUTHORIZATION_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"
SCOPES_URL = "https://kapi.kakao.com/v2/user/scopes"
CALLBACK_TIMEOUT_SECONDS = 300


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    server: "OAuthCallbackServer"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/redirect":
            self.send_error(404)
            return

        query = parse_qs(parsed.query)
        returned_state = query.get("state", [""])[0]
        error = query.get("error", [""])[0]
        error_description = query.get("error_description", [""])[0]
        code = query.get("code", [""])[0]

        if returned_state != self.server.expected_state:
            self.server.error = "OAuth state did not match"
        elif error:
            self.server.error = f"{error}: {error_description}" if error_description else error
        elif not code:
            self.server.error = "Kakao did not return an authorization code"
        else:
            self.server.authorization_code = code

        if self.server.error:
            title = "Kakao authorization failed"
            message = html.escape(self.server.error)
        else:
            title = "Kakao authorization complete"
            message = "You can close this tab and return to Codex."

        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{title}</title></head><body>"
            f"<h1>{title}</h1><p>{message}</p></body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class OAuthCallbackServer(HTTPServer):
    expected_state: str
    authorization_code: str | None = None
    error: str | None = None


def wait_for_authorization_code(state: str) -> str:
    server = OAuthCallbackServer(("127.0.0.1", 4000), OAuthCallbackHandler)
    server.expected_state = state
    server.timeout = 1
    deadline = time.monotonic() + CALLBACK_TIMEOUT_SECONDS

    print("Kakao login/consent page opened. Complete it within 5 minutes.")
    while time.monotonic() < deadline and not server.authorization_code and not server.error:
        server.handle_request()
    server.server_close()

    if server.error:
        raise RuntimeError(server.error)
    if not server.authorization_code:
        raise TimeoutError("Timed out waiting for the Kakao OAuth callback")
    return server.authorization_code


def exchange_code(code: str) -> None:
    settings = get_settings()
    if not settings.kakao_rest_api_key or not settings.kakao_client_secret:
        raise RuntimeError("KAKAO_REST_API_KEY and KAKAO_CLIENT_SECRET must be configured")

    form = {
        "grant_type": "authorization_code",
        "client_id": settings.kakao_rest_api_key,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "client_secret": settings.kakao_client_secret,
    }
    response = httpx.post(TOKEN_URL, data=form, timeout=20)
    if response.is_error:
        raise RuntimeError(f"Kakao token exchange failed with HTTP {response.status_code}")

    payload = response.json()
    refresh_token = payload.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise RuntimeError("Kakao token response did not contain a refresh token")

    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise RuntimeError("Kakao token response did not contain an access token")

    scope_response = httpx.get(
        SCOPES_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params={"scopes": '["talk_message"]'},
        timeout=20,
    )
    if scope_response.is_error:
        raise RuntimeError(f"Kakao scope lookup failed with HTTP {scope_response.status_code}")

    scopes = scope_response.json().get("scopes", [])
    talk_message = next(
        (scope for scope in scopes if scope.get("id") == "talk_message"),
        None,
    )
    if not talk_message or not talk_message.get("using") or not talk_message.get("agreed"):
        using = bool(talk_message and talk_message.get("using"))
        agreed = bool(talk_message and talk_message.get("agreed"))
        raise RuntimeError(
            f"talk_message permission is not ready (using={using}, agreed={agreed})"
        )

    KakaoSelfNotifier()._store_refresh_token(refresh_token)


def main() -> None:
    settings = get_settings()
    if not settings.kakao_rest_api_key:
        raise RuntimeError("KAKAO_REST_API_KEY is not configured")

    state = secrets.token_urlsafe(32)
    query = urlencode(
        {
            "client_id": settings.kakao_rest_api_key,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "talk_message",
            "state": state,
        }
    )
    subprocess.run(["open", f"{AUTHORIZATION_URL}?{query}"], check=True)
    code = wait_for_authorization_code(state)
    exchange_code(code)
    print("Kakao refresh token saved securely; talk_message permission verified.")


if __name__ == "__main__":
    main()
