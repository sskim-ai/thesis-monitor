# Track B — KR Daily 1200 Window Chaining or Verified Degradation Contract

## Preconditions

Track A capability proven.

## Path A

If older history is safely retrievable:

```text
latest window
+ older bounded window
→ same basis
→ dedupe
→ sort
→ completed filter
→ exact trim 1200
```

## Path B

If provider hard-limits accessible history:

```text
canonical requested = 1200
provider cap = 1000
actual = 1000
status = PARTIAL_SAFE/provider_limit
```

Do not rewrite canonical target to 1000.

## Hard safety

```text
no synthetic bars
no weekly/monthly→daily
no duplicate merged bar
no corporate-action basis conflict
no partial current bar in completed history
```
