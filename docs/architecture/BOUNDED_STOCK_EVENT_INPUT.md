# Bounded Stock Event Input

R2B0-R4 extends the existing, opt-in `unified-complete-stock-owner-v1` owner.
It is not wired into production dispatch, delivery, or scheduled tasks.

`BoundNewsInput` binds the frozen `NewsRead`, canonical security universe,
original HTTP receipt bytes, normalization receipt bytes, and response bytes.
`NewsRead` verifies existing NewsQueryService aliases and Google RSS / Naver
request construction, owner fingerprints, one request, zero retries, and no
redirects. Credentials are never serialized. Raw-byte replay uses the same
provider parser, identity and relevance validators, event classifier and existing
review eligibility. A matching company name alone does not qualify an event.

The source replay independently checks publication time, availability time,
normalization identity, candidate verdicts, source hashes, and duplicates.
Only selected business events enter the existing canonical fact catalog,
numeric registry and typed decision evidence. A returned news item is not an
automatic business-union PASS.

The optional `business_cutoff` is distinct from the sealed price query/session
and financial projection cutoff. Both domains are recorded. These mixed-time
packets are materializer/provenance proofs, not historical production decisions.
This Korean review uses an explicit Asia/Seoul business clock, preserving Naver's
source-local calendar date; original publication and receipt timestamps still
undergo exact timezone-aware availability checks.
Callers omitting the new event input retain the previous owner behavior.

Existing reported-financial denials remain explicit, including mixed-filing
tuples, financial-quality errors and missing filing lineage. Denied financial
facts are not consumed as qualified earnings. A qualified event may independently
satisfy the existing reported-financial-or-business-event union; it does not
repair or reclassify denied financial evidence.

`scripts/unified_event_union_proof.py` separates freeze, one-shot acquisition and
network-free proof. The cohort is exactly the 14 US and 6 KR previously blocked
subjects. 005930 and 047810 are retained without event recollection. No OHLCV,
financial refresh, models, rendering, delivery, or production database writes
are performed. The exclusive dispatch receipt prevents automatic reuse.

SEC financial discovery and OpenDART recovery transport gaps remain separate
open debt. No source/provider or semantic threshold is broadened here.
