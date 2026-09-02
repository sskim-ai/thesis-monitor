# V2 HOLD Neutrality Contract

## Definition

HOLD is the current directional neutral band. It is derived when neither BUY nor SELL reaches 6, including `5:5`, `5.5:4.5`, and `4.5:5.5`.

HOLD does not mean preserve the previous decision. A prior BUY followed by a current `5:5` candidate resolves to HOLD when the required adjudication accepts the current candidate. The same rule applies to a prior SELL.

## Prior State Boundary

Prior accepted state is continuity evidence, not a label target. A label change still enters the accepted-decision adjudication path. The adjudicator may keep the prior decision only with a compatible accepted balance and evidence-bound directional drivers. It may accept the current HOLD only with a HOLD-band accepted balance.

The following shortcuts are prohibited:

- carrying BUY forward because the current balance is neutral;
- carrying SELL forward because the current balance is neutral;
- changing the candidate's current balance to fit the prior label;
- rendering the raw candidate before accepted-plan resolution.

## Compatibility

New onboarding decisions persist accepted balance and drivers. Existing readiness payloads created before this contract remain readable; when legacy payloads do contain balance metadata, the balance must validate and agree with the accepted label.
