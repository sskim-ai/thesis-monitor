# Current SR vs Stored Price Rules

## Separation

Current v3 SR answers where completed-session market structure is concentrated. Stored price rules
answer how an existing thesis or holding is managed. They can overlap, be close, or be far apart
without becoming the same object.

Current SR owns nearest support/resistance and major structure. Stored rules retain confirmation,
warning, invalidation, and registered support semantics. The renderer may describe their relation,
but cannot copy one source into the other or decide that one supersedes the other.

## Provenance

Current ranges bind to v3 zone IDs. Stored values bind to `chart:stored_price_rules` with the
specific source field. Label repair preserves numeric tokens and does not write to thesis rules,
rule history, assessments, or the database.
