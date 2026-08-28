# US Current-Time Stock Test Delivery

All `13` active-universe messages were sent once to the dedicated
test sink. Exact payload match is true for every row. Duplicate, orphan, retry, unowned retry,
production collision, production intent, and production-recipient send counts are `0`.

WRD's message intentionally contains no current or legacy Price Structure claim; its separately
labeled stored rule history remains allowed. `TEST_STOCK_FAIL_COUNT = 0`.
