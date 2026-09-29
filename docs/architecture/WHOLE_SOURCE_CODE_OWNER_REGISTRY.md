# Whole-Source Code Owner Registry

The canonical owner is `app/services/whole_source_code_owner_registry.py`.
Its fresh profile always requires exactly 16 files, including the selected
financial, latest-published FX and current-effective technical owners. Roles are
audit metadata only and do not allocate source-use authority.

The registry is frozen from current repository bytes. Each immutable entry owns
its path, role, mandatory flag, SHA-256, version and semantic registry ID.
Entries are sorted canonically; duplicates, missing/extra owners, role drift,
missing files and symlink substitution fail closed.

Fresh `whole_inputs` uses this registry for metadata and both existing run-seed
code-identity fields. Those fields bind the digest of the full typed registry,
not an independently constructed path map. The redundant fingerprint map must
also equal the registry exactly. `compose_full_source` independently freezes
and verifies the same registry against repository bytes. Both replays record
and compare producer, seed, consumer and replay registry identities.

The legacy persisted-source profile is selected from the same inventory and
retains its original four-file fingerprint digest and seed serialization.
It cannot satisfy the fresh profile.

The broader existing execution freeze also fingerprints every app/script
Python file, including the registry module and producer. A code change requires
a new implementation freeze and source generation. Old provider receipts are
historical regression evidence, never current source inputs under new code.

Tests use the canonical owner, plus an actual production `whole_inputs` ->
`compose_full_source` -> two-replay path. Only transport capture boundaries
are supplied by fictional fixtures; metadata, seed, stock owners and consumer
validation remain production functions. A separate historical fixture records
REV19's exact 16-vs-13 failure. No investment, source, delivery or policy
threshold is changed.
