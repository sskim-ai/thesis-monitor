# Decision Quality Review Scope

- Instruction commit: `86829a52c4711e1fad632cc9f558a44c08cc2ddc`
- Source evidence SHA-256: `7649e675b654194b881ba3b5eadc2d2a69f1051915669a630e5e7e43b938720b`
- Source baseline SHA-256: `9a5adce69cca5e6d00fbb500d983b64e0590d3d7debd8f546eb1ec05a1ce482b`
- Subjects: `20` (`KR 7`, `US/foreign 13`)
- Independent route: signed-in Codex CLI `gpt-5.6-sol` / `xhigh` / archive-only / label-blind
- AI attempts: `22` (`20` accepted stage outputs, `2` rejected and replaced)
- Rejected independent output: `1` CORZ exact-ref violation; no manual correction, fresh blind rerun accepted
- Rejected portfolio output: `1` proposed-set verbosity failure; no manual shortening, length-bounded schema rerun accepted
- Web enrichment, future outcome, production send, scheduler mutation, DB mutation: `0`
- Production canary remains disabled; decision engine remains `TEST_SINK_READY`.
