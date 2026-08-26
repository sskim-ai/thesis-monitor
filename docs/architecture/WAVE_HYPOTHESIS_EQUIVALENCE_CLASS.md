# Wave Hypothesis Equivalence Class

## Contract

`wave-hypothesis-equivalence-class-v1` groups validated monthly wave hypotheses only when ticker,
source degree, wave state, and the state-aware active-structure signature match.

For `W4_CANDIDATE_W5_UNCONFIRMED`, the signature uses W1-W4. For `W5_CANDIDATE`, it uses the
available W3-W5 phase. Pivot identity and confirmation status are both part of the signature.
Grand/current/intermediate degrees are never merged.

## Purpose

The class says that candidates describe the same active phase. It does not declare every
Fibonacci formula equivalent. Each family still checks its own endpoint dependency. A W0-only
difference can therefore preserve W3/W4-dependent analysis while blocking W0-dependent analysis.

## Safety

Classes are deterministic backend output. AI may reference supplied class IDs but cannot create a
class, add a member, or cause the backend to choose one member of an ambiguity set.
