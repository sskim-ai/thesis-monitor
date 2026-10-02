"""Provider-owned headers for the opt-in sealed OpenDART acquisition path."""


def opendart_headers():
    return {'Accept': 'application/json', 'User-Agent': 'ThesisMonitor/1.0'}


def header_contract():
    return dict(headers=sorted((k.lower(), v) for k, v in opendart_headers().items()),
                follow_redirects=False)
