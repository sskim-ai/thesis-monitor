"""Finite historical test call sites, not ticker-based production authority."""

FINANCIAL_GENERATIONS = frozenset({
    "m12b-test-generation", "m12ap-test",
    "m12-fictional-test-generation", "m12ai-test", "m12ai-schema", "m12ap-fixture", "m12ap-schema",
    "two-stage-prompt-test", "two-stage-stance-prompt-test", "m12aj-fic-fin-02", "m12aj-fic-fin-01",
    "m12aj-working-capital", "m12aj-mixed", "m12aj-classification", "m12ao-deterministic",
    "m12ao-convergence-fixtures", "m12f-input-api-test", "m12f-offline-test", "m12f-offline-review",
    "m12y-source-test", "m12z-source-test", "m12u-offline", "m12aa-fic-fin-08-replay",
    "m12ac-exact-fic-fin-08-replay", "m12ac-contract-proof", "m12ad-exact-fic-fin-08-rep3-replay",
    "m12ad-model-contract-proof", "m12ae-r2-architecture-proof", "m12aj-offline-preflight",
    "m12at-deterministic-preflight", "m12au-test", "m12bi-test",
    "20260909-m12-fictional-20260909T031350Z-72c281729499",
    "20260909-m12r-fictional-20260909T043009Z-ffc3fd557f05",
    "20260909-m12g-fictional-20260909T054736Z-63aaf9f72cc7",
    "20260909-m12b-fictional-20260909T085320Z-746ef9ba1586",
    "20260909-m12d-fictional-20260909T113907Z-3ad040f73f7f",
    "20260910-m12y-fictional-20260910T043154Z-2761aab01862",
})

CANARY_PARAMETERS = frozenset(
    [("us", "SYNTHETIC_"+suffix, "0") for suffix in (
        "NEW_HOLDOUT", "NEON_CAPTURE", "NEGATIVE_FACT", "MISSING_NEGATIVE", "EARLY_STOP",
        "US_REVIEW", "US_TEST", "AUDIT", "TWO_STAGE", "ALIAS_AUDIT", "M2", "M2_REVIEW",
        "UNKNOWN_CONTRACT", "OTHER_OWNER", "US_ALPHA", "US_C2_DIRECTIONAL_US_1")]
    + [("kr", "SYNTHETIC_"+suffix, "0") for suffix in ("KR_UNAVAILABLE", "KR_TEST", "KR_ALPHA", "KR_C3_DIRECTIONAL_KR_1")]
    + [(market, f"SYNTHETIC_{market.upper()}_{n}", "0") for market, count in (("us",4),("kr",12)) for n in range(1,count+1)]
    + [(market, f"SYNTHETIC_{market.upper()}_{n}", "2300") for market in ("us","kr") for n in range(1,5)]
    + [(market, f"SYNTHETIC_{prefix}_{n}", "2300") for market,prefix in (("us","US_C4_SHARED_CONTEXT_US4"),("kr","KR_C5_SHARED_CONTEXT_KR4"),("us","SEQ_US")) for n in range(1,5)]
    + [("kr",f"SYNTHETIC_SEQ_KR_{group}{n}","2300") for group in ("A","B") for n in range(1,5)]
    + [("us",f"SYNTHETIC_WS_{letter}","2300") for letter in "ABCD"]
)

DEFAULT_DELTA_KINDS = frozenset({"stored_thesis", "single_period_operating", "verified_comparison", "ambiguous_event", "immaterial_positive_change", "conflicting_changes"})
