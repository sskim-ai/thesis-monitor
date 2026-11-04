# Canonical source and empty runtime

The current checkout is the canonical development source. Legacy scheduled jobs
are disabled during the GC3R reset. No replacement service is installed or started.
The repository's original database schema and migrations remain in `app/database.py`
and `app/models/`; the research schema remains in `vnext_research_store.py`.

Run `scripts/bootstrap_empty_offline.py` with the repository on `PYTHONPATH`, a
credential-free environment and a new absolute destination. It creates empty
application and research schemas with providers, models and sending disabled.
The 22 identity entries in `rebuild_cohort_v1.json` are planning configuration,
not current registration, prospective eligibility or Source/Market authority.
The private user seed is retained outside Git and is not automatically imported.

After reset, price history, captures, Owner/Replay receipts and judgments must be
collected and qualified anew. Historical proofs do not grant current use rights.
Strict READY remains 0/22, Source Current 0/28 and Market Current 0/2. The existing
10/12 GiB source guards and financial call grants are unchanged.

Original administration checkout and its virtual environment may remain because
installed interpreter paths refer there. Old schedule definitions are retained
privately for review; enabling them requires a new validated configuration and
authorization. The old manual parent JSON pins are historical and must not be
treated as live configuration after the reset.
