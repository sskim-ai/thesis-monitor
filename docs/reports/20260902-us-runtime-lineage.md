# US Runtime Lineage

| Item | SHA |
| --- | --- |
| origin/main | `2a6bbc449d6802490560cb89d83e0d1fc3e88b24` |
| operating HEAD | `2a6bbc449d6802490560cb89d83e0d1fc3e88b24` |
| runtime code | `2a6bbc449d6802490560cb89d83e0d1fc3e88b24` |
| reference runtime | `26004d926247c4ef053e49b74dc8fb9654353199` |
| CLI path repair | `b5be74439b2e8e769b1605e539599835abbc8a84` |
| work instruction | `ec843952011e32a4ef81946e1e5bc10dd1c1f809` |

The operating checkout was clean and equal to `origin/main`; it contains the repaired absolute-path contract. The natural subprocess reached that contract and created its schema/prompt/log under the single claims directory. Runtime lineage is therefore `PASS`, while the model transport itself failed later.

| Flag | Value |
| --- | --- |
| AI_REVIEW_MODE | shadow |
| AI_REVIEW_PILOT_ENABLED | true |
| V1_DECISION_ROLLBACK_AVAILABLE | true |
| V2_FULL_MONITORED_STOCK_COVERAGE_TARGET | true |
| V2_PRODUCTION_ENABLED | true |
| VISIBLE_STOCK_DECISION_ENGINE | v2_accepted |

`US_RUNTIME_LINEAGE = PASS`
