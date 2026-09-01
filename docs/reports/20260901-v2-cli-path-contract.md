# V2 CLI Path Contract

Every persisted relative claim path resolves against the module-owned repository root. The subprocess boundary receives absolute cwd, prompt, output, log, and schema paths. Write parents are created before preflight; cwd, prompt, schema, and both parents are then asserted before the model starts. Claim storage remains repository-relative.

`PATH_RESOLUTION_DEPENDS_ON_LAUNCH_CWD = 0`
