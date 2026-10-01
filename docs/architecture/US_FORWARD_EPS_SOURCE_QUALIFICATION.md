# US Exact Forward EPS Source Qualification

REV41 is an offline qualification contract, not a production valuation adapter.
`scripts/us_forward_eps_qualification.py` is not imported by production code.
It does not fetch providers, calculate fPER, invoke models or mutate runtime state.

## Ownership

`Security` declares the monitored listing, provider exchange identifier, currency
and common-share versus ADS identity. A provider observation must match the exact
symbol and exchange. Public-page EPS must have its own currency; quote currency
is never substituted. Source raw SHA, route, retrieval time, source pointer,
methodology and explicit fiscal identity stay attached to every qualified value.
GAAP and normalized non-GAAP EPS are distinct, visible accounting bases.

FY1 is the first forecast fiscal year strictly after the latest completed fiscal
year, not the maximum forecast year. A missing intermediate fiscal year is a
denial, not permission to select FY2. Actual rows never become estimates. The
Yahoo adapter binds completed FY identity to an available reported fourth-quarter
actual and the annual financial-year series. Missing corroboration fails closed.
Provider month-end fiscal labels are retained as such; they are not exact SEC
52/53-week filing dates. The explicit fiscal year owns selection.

NTM requires a provider-owned rolling-twelve-month definition. It is a separate
horizon and is not inferred from `forwardPE`, blended multiples or next-year labels.
No live NTM source is enabled by this implementation.

If the provider supplies no estimate timestamp, `estimate_asof` remains null.
Acceptance then requires explicit current-estimate snapshot semantics. Retrieval
time is never used as the estimate publication date or a historical PIT guarantee.
This does not establish update cadence or a production freshness SLA.

ADS qualification additionally requires direct EPS-per-listed-ADS evidence and
an authoritative positive ordinary-shares-per-ADS ratio. Ratio evidence alone
does not identify whether an EPS field already uses that ratio. No implicit FX
or ordinary-share conversion is allowed. Issuer guidance is not analyst consensus.

## Public Yahoo Adapter

The input is the anonymously accessible public `/quote/SYMBOL/analysis/` page.
No private endpoint, credential, browser cookie or anti-bot bypass is used.
The public Earnings Estimate and Current Estimate rows must agree with the
embedded quoteSummary payload, including selected accounting method, annual
year labels, currency, analyst count and formatted values. Default and explicit
GAAP/non-GAAP payloads must agree. Unknown layouts or conflicting modules fail
closed; a later adapter can narrow that conservative guard with separate proof.

The pure parser retains raw precision only after public formatted-value parity.
Denied records expose no canonical EPS. Source failure, parser mismatch and
unavailable estimates have distinct states. Negative EPS is a valid estimate,
not evidence that a future PER calculation would be meaningful.

## Evidence And Limits

The qualification collector, request reservations, public response hashes and
replay receipts remain in the local REV41 report, outside Git. Public response
captures are not a redistribution licence or a supported API availability promise.
Any integration design must retain access/terms review, layout-change denial,
explicit accounting basis, snapshot dating and per-security missingness.

REV41 found a concrete access-authority gap: Yahoo's official terms require
prior permission for automated collection. Such permission was not established.
The saved public responses support offline semantic review only; the source is
SECONDARY_ONLY, not an approved recurring free feed. Acquisition is closed.
See `docs/reports/20261001-r2b-r9-rev41-us-forward-eps-qualification.md`.

Composite sources cannot overwrite a `(security, horizon)` owner silently.
Source ranking, cross-source filling and production consumption are not implemented.
Future integration must separately bind an accepted current close and the EPS
owner. KR KIS current-FY1 ownership remains untouched.

Focused tests cover fiscal ordering, actual/forecast polarity, currencies, ADS
basis, null timestamp semantics, public/JSON parity, transport errors, raw hash
tampering and canonical-record validation. All fixtures are synthetic.
