# M12DE Official Standalone Readiness

Task: M12DE-20260921. Baseline: `8455a87f378ec01af0847c4ab8afb3ac1c5a1966`.
Instruction: `20260921-m12de-official-codex-standalone-refresh-chatgpt-auth-controller-readiness.md`.

The user authorized one official standalone installation of `rust-v0.155.1`,
one gated coarse ChatGPT login-status check, and conditional opt-in controller
binding with offline/mock regression. Model/catalog calls remain prohibited.

Local qualification passed official release digest checks, standard package
installation, executable identity, strict codesign, and coarse ChatGPT auth.
Raw auth output is not retained. The old standalone release remains preserved.

Change only the existing explicit official transport and its direct tests.
Bind a frozen qualification receipt to the exact real executable path, hash,
version, official package digest, config-schema hash, and required controls.
Do not trust PATH or a successful help command as installation qualification.

Use verified ignore-user-config/ignore-rules, shell/web/agent/memory restrictions,
and project instruction byte limit. The pinned schema says multi_agent_v2 can
override agents.enabled, so disable both. Preserve managed requirements.
Global instruction/skill surfaces remain a documented residual limitation;
`source_only_inference_certified` stays false. Tool or unknown events fail closed.

No analytical/source-use/capability/materialization owner edits. No changes to
the default production caller. Custom native runtime remains RETIRED_NOT_REQUIRED.
No production DB/scheduler/message/order actions, merge, push, or deployment.
Future tiny synthetic inference requires a separate decision, not this task.

Evidence and qualification receipts remain local outside the repository; the
completion ZIP excludes installers, binaries, credentials, and raw old model
artifacts. Scoped tests and 16 mocked historical captures are mechanics proof,
not current model availability or successful inference proof.
