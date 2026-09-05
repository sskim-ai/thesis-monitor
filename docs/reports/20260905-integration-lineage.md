# Integration Lineage

| Layer | Commit |
|---|---|
| Base main / operating | `906b092749511dc42d5799ed335165819efee2ea` |
| Work instructions | `35dab28b0a8c714b236a7ac36582461fcb4fbf67` |
| Child-wait ownership | `dc0fdca` |
| Command-scoped timeout | `2855b65` |
| Terminal receipt isolation | `42a4a9e` |
| Logical condition + validation policy | `2e2a53a4c59c8cadf0828b1ad50510000b4a5b39` |
| Isolated E2E root handling | `140c10b17952d8dcd7020e07f92e21551d23aa8c` |
| Isolated DB reconnect | `1e7c4d67eec19dc651398af15561701a20929a2c` |
| Canonical logical root identity | `69207850cb1cde44d65b646d728fa2c72628cd23` |
| Structured valuation-span restoration | `dc6a73d147208aa5df3818239ab4ac92f4fa9a53` |
| Same-claim E2E continuation and DB guard | `03e230da22c1482339b4bb7b1c1883ce0ac01076` |

Integration branch: `codex/20260905-kr-v2-validation-policy-production-integration`.

The source shadow bundle SHA-256 is `a41eadfdf73c6a6db649f552a0d120f07986442d77afa66e193d4d060406326f`, verified locally. No broad shadow experiment was merged wholesale.

The final implementation SHA passed GitHub Actions run `33949330754` (pytest and Ruff). The US continuation reused the already accepted `gpt-5.6-sol / xhigh` 14-subject receipt under the same claim and fencing token; it did not rerun the model.
