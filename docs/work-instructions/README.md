# thesis-monitor Work Instructions

Repository path: `docs/work-instructions/`

## Purpose

This directory stores immutable execution instructions for Codex work.

## Rules

1. One Markdown file per bounded phase or repair.
2. File name: `YYYYMMDD-<phase>-<short-title>.md`.
3. Each instruction records instruction version, intended base SHA, scope, forbidden changes, acceptance criteria, and completion-report format.
4. Codex must record the exact instruction commit SHA in its completion report.
5. Once implementation begins, do not silently edit the active instruction file. Material changes require a new version/file and a new commit.
6. Implementation branches should start from the latest main descendant that contains the instruction commit, unless the instruction explicitly says otherwise.
7. Work-instruction commits are documentation/evidence and must not smuggle experimental runtime code into main.
8. Completion reports must state whether the implementation complied with the exact committed instruction.
