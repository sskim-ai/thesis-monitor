"""Diagnostic redirect facts only; this does not authorize following Location."""
from typing import Literal
from urllib.parse import parse_qsl, urljoin, urlsplit
import re

from app.services.unified_snapshot_contract import ContractModel


class SecretSafeRedirectMetadata(ContractModel):
    status: int
    location_present: bool
    location_host: str | None
    location_path: str | None
    query_keys: tuple[str, ...]
    same_origin: bool
    scheme_relation: Literal['SAME_HTTPS', 'DOWNGRADE', 'OTHER', 'MISSING']
    content_type: str | None
    route_class: Literal['EXACT_SAME_API_SEMANTICS', 'UNRESOLVED']
    follow_authorized: Literal[False] = False


def redirect_metadata(request, response, secrets=()):
    locations = response.headers.get_list('location')
    location = locations[0] if len(locations) == 1 else None
    original = urlsplit(str(request.url))
    try:
        target = urlsplit(urljoin(str(request.url), location)) if location else None
        if target:
            target.port
    except ValueError:
        target = None
    known = r'/api/(?:list|fnlttSinglAcntAll)\.json'
    same = bool(target and (target.scheme, target.hostname, target.port) ==
                (original.scheme, original.hostname, original.port))
    relation = ('MISSING' if not target else 'SAME_HTTPS' if target.scheme == original.scheme == 'https'
                else 'DOWNGRADE' if original.scheme == 'https' and target.scheme == 'http' else 'OTHER')
    query = parse_qsl(target.query, keep_blank_values=True) if target else []
    exact = bool(same and target and not target.username and not target.password and not target.fragment
                 and re.fullmatch(known, target.path) and target.path == original.path
                 and sorted(query) == sorted(parse_qsl(original.query, keep_blank_values=True)))
    host = target.hostname if target else None
    # Only the official public API paths are retained. Unknown path components
    # may be credentials even when their value is not in the current config.
    path = (target.path if re.fullmatch(known, target.path) else '[UNRECOGNIZED_PATH]') if target else None
    keys = tuple(sorted(k if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}', k)
                        and not any(s and s in k for s in secrets) else '[REDACTED]' for k, _ in query))
    if host and (host != 'opendart.fss.or.kr' or any(s and s in host for s in secrets)):
        host = '[REDACTED]'
    content_type = response.headers.get('content-type', '').split(';', 1)[0].lower()
    content_type = content_type if content_type in {'application/json', 'text/html', 'text/plain', 'application/xml'} else None
    return SecretSafeRedirectMetadata(status=response.status_code, location_present=bool(location),
        location_host=host, location_path=path, query_keys=keys, same_origin=same, scheme_relation=relation,
        content_type=content_type, route_class='EXACT_SAME_API_SEMANTICS' if exact else 'UNRESOLVED')
