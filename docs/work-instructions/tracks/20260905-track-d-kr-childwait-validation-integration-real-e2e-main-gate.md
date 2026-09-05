# Track D — KR Child-Wait + Validation Integration → Real E2E → Main Gate

Create a clean production integration branch from current main.

Combine:
KR child-wait repair ebc2350
bounded production validation policy
logical-condition ownership

Resolve actual operating GPT-5.6 model + reasoning effort.
Final KR/US release TEST must use that exact model/effort.

KR:
market 1 + explicit V2 8
Pilot 0
fallback 0
duplicate 0

US:
market 1 + explicit V2 14
compatibility 0
fallback 0
duplicate 0

Both PASS + full CI before main.
