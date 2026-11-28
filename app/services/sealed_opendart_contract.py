"""Provider-owned headers for the opt-in sealed OpenDART acquisition path."""


def opendart_headers(*, document=False):
    accept = ('application/x-msdownload, application/zip, application/octet-stream, application/xml, application/json'
              if document else 'application/json')
    return {'Accept': accept, 'User-Agent': 'ThesisMonitor/1.0'}


def header_contract():
    return dict(headers=sorted((k.lower(), v) for k, v in opendart_headers().items()),
                follow_redirects=False)
