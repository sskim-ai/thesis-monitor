"""Private native OHLCV owner process; data-only protocol, no service changes."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import httpx

from app.services.unified_live_source_transport import BoundedTransport, SourceSafetyStop
from scripts import unified_stock_source_worker as stock_worker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("stocks", "market"))
    parser.add_argument("--owner-root", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.plan.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.sha256:
        raise SourceSafetyStop("plan_hash_mismatch")
    frozen = json.loads(raw)
    # Import the separately installed native owner in a dedicated process.
    # Already bound proof helpers have no lazy application imports.
    for key in list(sys.modules):
        if key == "app" or key.startswith("app."):
            del sys.modules[key]
    sys.path.insert(0, str(args.owner_root))
    from app.config import Settings
    from app.providers import kiwoom as owner
    settings = Settings(_env_file=args.owner_root / ".env")
    actual = stock_worker.owner_configuration(args.owner_root, settings)
    expected = frozen["native_owner"]
    if actual != expected or not actual["owner_clean"] or not actual["credentials_present"]:
        raise SourceSafetyStop("native_owner_configuration_drift")
    if actual["base_url"] != "https://api.kiwoom.com" or not actual["live_provider"]:
        raise SourceSafetyStop("non_real_owner_denied")
    def guard():
        if hashlib.sha256(args.plan.read_bytes()).hexdigest() != args.sha256:
            raise SourceSafetyStop("plan_drift")
        for name, expected_hash in frozen["code_files"].items():
            if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected_hash:
                raise SourceSafetyStop("code_drift")
        if stock_worker.owner_configuration(args.owner_root, Settings(_env_file=args.owner_root / ".env")) != expected:
            raise SourceSafetyStop("native_owner_config_drift")
    transport = BoundedTransport(root=args.output / "wire", guard=guard,
        maximum_logical=frozen["budgets"]["stock_wire" if args.mode == "stocks" else "us_market_wire"]["maximum_logical"],
        secrets=(settings.kiwoom_app_key, settings.kiwoom_secret_key))
    native = httpx.Client(transport=httpx.HTTPTransport(retries=0), follow_redirects=False)
    auth_count = 0
    def post(url, *, json, headers, timeout):
        nonlocal auth_count
        secret = url == "https://api.kiwoom.com/oauth2/token"
        if secret:
            auth_count += 1
            if auth_count > 1:
                raise SourceSafetyStop("auth_budget_exhausted")
        response = transport.post(native, url, json=json, headers=headers, secret=secret,
            request={"method": "POST", "route": url.removeprefix("https://api.kiwoom.com"),
                     "api_id": headers.get("api-id"), "body": json,
                     "cursor_sha256": hashlib.sha256(headers.get("next-key", "").encode()).hexdigest()})
        if secret and (response.status_code != 200 or not response.json().get("token")):
            raise SourceSafetyStop("auth_response_invalid")
        return response
    bounded = settings.model_copy(update={"kiwoom_max_retries": 0, "kiwoom_timeout_seconds": 600})
    try:
        if args.mode == "stocks":
            class Client:
                def __enter__(self):
                    return self

                def __exit__(self, *unused):
                    return False

                def post(self, *a, **kw):
                    return post(*a, **kw)

            original = stock_worker.WireBoundary.post
            def guarded(self, *a, **kw):
                try:
                    return original(self, *a, **kw)
                except ValueError as exc:
                    raise SourceSafetyStop("stock_request_or_integrity_boundary_failed") from exc
            stock_worker.WireBoundary.post = guarded
            stock_worker.httpx = SimpleNamespace(Client=lambda **kw: Client(), HTTPTransport=lambda **kw: None,
                                                 HTTPError=httpx.HTTPError)
            stock_worker.acquire(frozen["stock_plan"], args.output, owner, bounded)
        else:
            from app.services.ohlcv_service import OhlcvService
            from app.services.symbol_resolver import SymbolResolver
            current = None
            seen = set()
            page_counts = {}
            cursors = {}
            def market_post(url, *, json, headers, timeout):
                if url == "https://api.kiwoom.com/oauth2/token":
                    return post(url, json=json, headers=headers, timeout=timeout)
                if current is None or not url.startswith("https://api.kiwoom.com/"):
                    raise SourceSafetyStop("market_unplanned_request")
                api = headers.get("api-id")
                discovery = api == "usa10099" and url.endswith("/api/us/stkinfo")
                if discovery:
                    valid = json in [{"stex_tp": e} for e in ("ND", "NY", "NA")]
                    key, maximum = ("discovery", json.get("stex_tp")), 1
                else:
                    valid = api == "usa06012" and url.endswith("/api/us/chart") and json in [
                        {"stex_tp": e, "stk_cd": current, "strt_dt": "", "upd_stkpc_tp": "1", "exrt_appl_tp": "0"}
                        for e in ("ND", "NY", "NA")]
                    key, maximum = (current, "chart"), 2
                count = page_counts.get(key, 0)
                if not valid or count >= maximum:
                    raise SourceSafetyStop("market_request_outside_frozen_plan")
                if not discovery and (headers.get("cont-yn"), headers.get("next-key")) != cursors.get(key, ("N", "")):
                    raise SourceSafetyStop("market_chart_cursor_mismatch")
                page_counts[key] = count + 1
                response = post(url, json=json, headers=headers, timeout=timeout)
                if not discovery:
                    cursors[key] = (response.headers.get("cont-yn", "N"), response.headers.get("next-key", ""))
                return response
            owner.httpx = SimpleNamespace(post=market_post, HTTPError=httpx.HTTPError)
            service = OhlcvService(SymbolResolver(settings.sector_map_path),
                owner.KiwoomProvider(owner.KiwoomClient(bounded, owner.KiwoomAuth(bounded))))
            for line in sys.stdin:
                request = json.loads(line)
                if request == {"close": True}:
                    break
                matches = [r for r in frozen["us_market_reads"] if r["params"] == request]
                if len(matches) != 1 or request["symbol"] in seen:
                    raise SourceSafetyStop("market_logical_request_not_frozen_or_reused")
                current = request["symbol"]
                seen.add(current)
                try:
                    result = service.get_ohlcv(symbol=current, market="US", periods=["daily"],
                        count=2, include_indicators=False, indicator_limit=0, adjusted=True)
                    body, status = result.model_dump(mode="json"), 200
                except Exception as exc:
                    body, status = {"error_class": type(exc).__name__}, 502
                print(json.dumps({"status": status, "body": body}, ensure_ascii=False), flush=True)
    finally:
        native.close()
        stock_worker.write(args.output / "bounded-transport-counts.json", transport.counts())


if __name__ == "__main__":
    main()
