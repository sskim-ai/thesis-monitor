# Event Owner Reachability Before R2A-R3 Implementation

Entry: `CollectionService.collect_events` -> `_fetch_provider_events`.
Events are optional Class B. Original legacy collection mutates Event, financial,
capital-action, dividend and telemetry rows; unified projection must not call
these persistence paths. Existing event relevance/document identity/financial
validation can run on detached objects. No prior AI assessment is an input.

| Owner | Reads and count | Publication/entity | Cache/fallback and retry |
| --- | --- | --- | --- |
| GoogleNewsRSSProvider.fetch_events | One RSS GET per collection attempt; redirects currently allowed | item pubDate; relevance against SecurityMaster aliases | No provider cache; malformed/missing date legacy defaults to today; unified must reject missing dates |
| NaverNewsProvider.fetch_events | One search GET with private credential headers | pubDate; alias relevance | No provider cache; missing credentials returns empty |
| SecEdgarProvider._resolve_cik/fetch_events | Local SEC_TICKER_CIK or company_tickers GET, then submissions GET | filingDate, accession, CIK, ticker; document identity | No event HTTP cache; HTTP/value errors return empty; no item document fetch |
| OpenDARTProvider.fetch_events | corp code resolution; list GET; per item preliminary document, financial CFS/OFS fallback, dividend, share status, treasury, supply contract and decision GETs | rcept_dt/rcept_no/corp_code, source row identities | Some nested errors become Unknown; corporation resolver may open downloaded corp-code cache/network |
| OpenDART document helper | Main page plus discovered viewer/document GETs through supplied client | receipt/title/table context | Source HTML exists before RawEvent; cannot reconstruct it afterward |
| OpenDART corp-code resolver | seed constant or disk ZIP/XML and upstream corp-code download | stock_code/corp_code | Unified must use bound existing identity or deny before this uninstrumented cache/network branch |
| NewsAPIProvider | Skeleton returns empty even when configured | None | Explicit unavailable, never mock substitute |
| CompanyIRProvider | Skeleton returns empty | None | Explicit unavailable |
| AlphaVantageProvider | May fetch news, profile and finance | Provider response | Prohibited live and cache; never instantiate as unified event owner |
| MockProvider | Local synthetic events | Fixture | Prohibited as unified data provider |
| CollectionService | monitor_retry_attempts attempts with configured exponential delay; OpenDART reparse lookback reads financial/Event rows | validates document identity, actor, relevance, event fingerprint; deduplicates | Legacy duplicate Event reads then write/refresh; these are not original-source cache receipts |
| CollectionService.get_thesis_events | Calls collect then reads persisted Event rows | Existing document/eligibility filters | Not a unified entry; can backfill or return unbound historical events and must remain outside adapter reachability |

Unified qualification requires explicit provider/route budgets, actual byte
receipts (including failed/retried reads), and owner normalization. Cached wire
sources may only be opened with an original bound receipt/provider/hash; Event
or RawEvent rows alone cannot impersonate cache wire evidence. Original times
remain in the cache lineage. Unqualified branches yield explicit optional
denials without fallback; they are not declared qualified merely by registry
membership. The provider-level receipt hooks do not enable any live call here.
