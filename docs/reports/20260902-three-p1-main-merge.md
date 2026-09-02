# Three-P1 Main Merge Gate

- Base/main before repair: `2a6bbc449d6802490560cb89d83e0d1fc3e88b24`
- Work-instruction commit: `ff255fc710a3b86b0496cdedca505a7a4a5323e7`
- Runtime implementation commit: `16fa1222136b300d900682904f8391ef5c4b482a`
- Implementation Actions: run `33580859664`, Test/Lint `PASS`
- Linear ancestry: required
- User-visible message policy change: `0`
- Scheduler timing/ownership change: `0/0`

Promotion is allowed only after the report commit also passes Test/Lint. The completion response
records the exact promoted report commit and operating SHA because a commit cannot contain its own
hash.
