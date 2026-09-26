# Unified Consumed Source Graph

Frozen before R2A-R4 owner implementation. This is a source-consumption audit,
not an activation or a replacement financial store. Acquisition inventory remains
`UNIFIED_ACQUISITION_CLASSES.json` (A5/B4/C12/D3).

## Actual Entry and Consumers

The production-equivalent source projection is
`scripts/m12ds_r4_r1_project_source.py:project`. Its explicit PACKET_FIELDS,
STOCK_FIELDS and MARKET_FIELDS are the outer boundary. Nested fact-catalog
rows are interpreted by their existing typed owners, not by arbitrary key names.

`scripts/m12dr_offline_source_closure.py:context` invokes
`build_decision_evidence_packet`, `packet_owned_context_for_stock` and
`build_owned_evidence_packet`. Core reads only owned core refs, their frozen fact
fields and `observations`. `m12ds_r2_shadow_reproof.py:prepare` requires an
observed proposition for each subject. An optional financial role may be absent;
an entirely empty observed-business input is NOT a valid Core input.

Pass A uses the frozen Core capability, metadata and exact source authority.
Pass B also consumes entry-range inputs and exact security/earnings valuation
authority (`m12ds_r3_valuation_authority.py`). Neither pass grants a new source.
The validators and renderer consume that same registry and validated output;
they cannot authorize another raw source or a prior assessment.

## Field Ownership

Each row covers a typed field family, including its existing typed children.
Conditional means absent is allowed, but a retained value must pass the named
owner. No optional field can be substituted with zero or a stale prior value.

| Stage / field family | Source role / class | Existing owner and validator | Requirement / absence |
|---|---|---|---|
| All: packet_id, market, assessment_date, generated_at | run controller | unified run identity, market session parity | required, reject mismatch |
| All: schema_version, analysis_policy_version, output_schema_version, structure_algorithm_version, knowledge, chart_knowledge | frozen code/config | existing schema/policy/Knowledge identities | required contract, not provider data |
| Core/A/B: ticker, company_name, industry, sector, business_model, revenue_sources, company_profile | stored_thesis_and_business_metadata / C | project_local_seed; security identity | selected subject/identity required; optional profile fields absent |
| Core/A/B: thesis_version, thesis | stored_thesis_and_business_metadata / C | active thesis/version at cutoff; configured-condition authority | required; configured signals are not observed evidence |
| Core/A/B: knowledge_routing, chart_knowledge_routing | frozen code/config + declared company metadata | Knowledge routing owner | deterministic dependency; never imported AI output |
| Core/A/B: current_price_context, price_and_positioning, chart_context, technical_context | stock_chart_adjusted_daily_weekly_monthly + stock_valuation_unadjusted_price / A | OhlcvClient, OHLC integrity, PriceContext, packet_owned_context_for_stock | required acquired role set; feature availability remains owner-governed |
| Core/A/B: evidence / event fact rows | news_and_filing_events / B | CollectionService, identity/relevance, publication/source-use gate | optional role; one eligible observed business proposition is required from the union of business sources |
| Core/A/B: fact_catalog reported business rows | sec_financial_fundamental_domains or opendart_financial_fundamental_domains / C | selected financial field quality, financial_amount_period_lineage, exact current source authority | conditional; absent fields allowed; no generic provider-wide grant |
| Core/A/B: fact_catalog canonical cash-flow rows; cash_flow_user_visible | canonical_cashflow_working_capital / C | build_cash_flow_reasoning_context; canonical fact lineage; current formal/PIT | conditional; suppressed/context-only verdict preserved; no rendering in this task |
| Core/A/B: fact_catalog canonical inventory/relation rows; working_capital_user_visible | canonical_cashflow_working_capital / C | build_working_capital_reasoning_context, selected relation/input lineage | conditional; optional absent; no new WC formula |
| Core/A/B: other typed financial_context rows | SEC/OpenDART financial role / C | adapt_fact_catalog_financial_context and exact source lineage projection | only selected/consumed rows; unselected domains not blockers |
| A/B: valuation and valuation fact rows | official financial roles / C + unadjusted price / A | ValuationSnapshotService, financial-quality-taint, security basis, earnings_receipt | conditional multiples; unverified denominator cannot grant entry authority |
| A/B: forward estimate valuation rows | eligible_valuation_estimates / C | ValuationSnapshotService; earnings_receipt exact forward EPS/period/security checks | optional; provider-defined forwardPE alone lacks accepted denominator authority |
| All: numeric_registry | corresponding fact_catalog owners | numeric-fact-ref / exact source and numeric ownership | derivative registry, no independent source; exact same fact identity |
| All: data_cautions | corresponding owner verdict | existing typed data-quality gates | explicit unavailable allowed; not an observed business fact |
| Market: session, coverage, adapter_context, current_observation_fact_ids, prior_market_session_fact_ids | us_market_prices or kr_local_indices_sectors_breadth / A | m12ds_r3_market.market_context; exact completed-session parity | required market role; individual invalid series excluded |
| Market: fact_catalog indices/sector/style/big-tech | us_market_prices / A | MARKET_SYMBOLS, OhlcvMarketProvider.collect, macro temporal/session owner | whole configured request set required; no partial prior-attempt substitution |
| Market: adapter_context indices/sectors/size_context/breadth | kr_local_indices_sectors_breadth / A | KiwoomKrMarketContextService.collect; matched session and page lineage | required KR aggregate |
| Market: adapter_context market_flows | kr_market_investor_flows / A | ka10051/ka10066 page/reconciliation owner | optional; missing/invalid aggregate explicitly unavailable |
| Market: exchange breadth fact rows | us_exchange_breadth / B | parse_nasdaq_daily_market_file; completed session/exchange scope | optional; no synthetic breadth value |
| Market: night_futures, night_futures_audit, night_futures_cautions | night_and_publication_context / B | KRX parser, product/session/reference-basis/publication gates | mandatory US two products; original night time preserved |
| Market: macro rate/credit/liquidity/risk rows | rates_credit_liquidity_risk / C | project_macro_records, classify_observation | optional; reference-only is not current daily signal |
| Market: macro energy rows | energy / C | project_macro_records, classify_observation | optional |
| Market: macro Korean rows | korea_macro / C | project_macro_records, classify_observation | optional |
| Market: published central-bank events | central_bank_published_events / C | project_published_events, release/publication cutoff | optional; inferred_implications/unknowns excluded |
| Market: prior US session cross-assets | kr_overnight_cross_assets / C | project_macro_records, SESSION_BOUND_SERIES | optional; never relabel as KR current query |
| Market: earnings calendar | earnings_calendar / B | FinnhubEarningsProvider | optional future calendar, not reported earnings |
| Market: reference_fact_ids, macro_temporal_eligibility | respective market/macro owners | classify_observation; market_context | owner-derived temporal classification, not new provider |
| Market: fx from excluded Alpha route | excluded_kr_fx / D | unified source policy | unavailable, no cached substitution |
| All: Alpha secondary valuation/events, mock, Massive | excluded_secondary_valuation_events + excluded_mock_massive / D | unified source policy, recursive lineage rejection | prohibited, no value |

## Reachability and Closure Meaning

US multi-symbol market, Kiwoom page sets and KRX night aggregate are reachable
mandatory owners. Event multi-read and Nasdaq are reachable optional owners:
absence can be explicit, but selecting values requires actual child replay.
An unimplemented mandatory aggregate or stock packet materializer blocks complete
assembly. An unused financial taxonomy or unavailable optional estimate does not.

The legacy `_stock_packet` and `_market_packet` are not pure source adapters:
they also read assessments, implicit caches/report paths and stored briefings.
Calling them against an old assessment is not an acceptable shortcut. No older
accepted AI output is a source. No whole-cohort qualification follows merely
from passing individual owner tests.
