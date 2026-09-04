# 2026-09-04 US Transport Error Taxonomy

| Input class | Canonical class | Retryable |
|---|---|---|
| `UnknownIssuer`, `unknown issuer`, missing local issuer | `TLS_CERTIFICATE_UNKNOWN_ISSUER` | No |
| expired certificate | `TLS_CERTIFICATE_EXPIRED` | No |
| hostname/subject-name mismatch | `TLS_CERTIFICATE_HOSTNAME_MISMATCH` | No |
| other certificate verification/handshake failure | `TLS_CERTIFICATE_OTHER` | No |
| resolver failure | `DNS_FAILURE` | Yes, bounded |
| connect timeout | `CONNECT_TIMEOUT` | Yes, bounded |
| connection refused | `CONNECTION_REFUSED` | Yes, bounded |
| local network unavailable | `LOCAL_NETWORK_CONNECTIVITY_FAILURE` | Yes, bounded |
| app-server stream/connect failure | `CODEX_APP_SERVER_TRANSPORT_FAILURE` | Yes, bounded |
| unknown transport failure | `OTHER_TRANSPORT_FAILURE` | No |

Certificate failures fail after one wrapper transport attempt. Transient classes retain the existing bounded retry path. The audit receipt keeps only a normalized safe token such as `UnknownIssuer`; raw logs are not copied into user-visible output.

`UNKNOWN_ISSUER_CLASSIFICATION = TLS_CERTIFICATE_UNKNOWN_ISSUER`

`UNKNOWN_ISSUER_RETRY_STORM = 0`
