# Run-51 Test and Live Runtime Environment Diff

The old successful test path inherited a writable local Codex state environment. The natural
scheduler path inherited the default signed-in state root but could not write its app-server
SQLite database. Prompt/schema/cwd resolution was already correct, so the state root is the first
divergence.

After repair, test, frozen replay, onboarding, primary, backup, schema repair, and candidate repair
all use the same helper and the same model/effort/sandbox contract. Bounded differences are packet
identity, claim namespace, output directory, and test versus production delivery routing.

- First divergence: writable Codex app-server state
- Model: `gpt-5.6-sol`
- Effort: `xhigh`
- Tool sandbox: `read-only`
- Scheduler timing/ownership changes: `0/0`
- Runtime environment diff: `DOCUMENTED_BOUNDED_DIFF`
