# Installation and Invocation

## Project-local use

Keep `.agents/skills/verify` in the repository root. Codex, Cursor, OpenCode, and Antigravity discover this Agent Skills location. Restart the host if it was already running when the skill was added.

Invoke it as follows:

| Host | Invocation |
|---|---|
| Codex CLI or IDE | `$verify auto` |
| Cursor | choose `/verify`, then provide the mode and target |
| OpenCode | `/verify auto` through the included command adapter |
| Antigravity (`agy`) | `/verify auto` in interactive TUI; in `-p` print mode invoke contextually (e.g., "use the verify skill on this diff") |

The OpenCode adapter lives at `.opencode/commands/verify.md`; it forwards arguments and does not duplicate verification policy.

## User-wide use

Copy or symlink the `verify` directory to the host's user skill location:

- Codex: `~/.agents/skills/verify`
- Cursor: `~/.cursor/skills/verify`
- OpenCode: `~/.agents/skills/verify` or `~/.config/opencode/skills/verify`
- Antigravity (`agy`): `~/.gemini/antigravity-cli/skills/`

The canonical source remains `.agents/skills/verify`. Avoid maintaining separate modified copies per host.

## ChatGPT web and mobile

Repository-local skills are not directly installable in ChatGPT web/mobile. Those surfaces require plugin packaging and installation. Plugin distribution is intentionally a post-MVP release task.

## Verify installation

Confirm the host lists `verify`, then run it against a small working-tree change. The final report should identify its resolved target, selected panel, executed checks, findings, and verdict. If the host cannot create clean-context subagents, the report must state `degraded independence`.

## Incremental re-verification and state (v0.3+)

Incremental re-verification stores a target-local state file. The skill never writes this file itself; a host action stores it.

- Default state path: `<cwd>/.verify/state.json`. Override with the `VERIFY_STATE_PATH` environment variable.
- After a successful verification, the state record is emitted in the JSON report (`--report json`). The host or user persists this payload to the target state file (`.verify/state.json` or `VERIFY_STATE_PATH`).
- Add `.verify/` to the target repository's `.gitignore` unless the team explicitly wants the state in version control.
- The skill refuses to use a stale or mismatched state file. See [`.agents/skills/verify/references/state-persistence.md`](../.agents/skills/verify/references/state-persistence.md) for the full rules and schema.

## Host documentation

- [Codex Agent Skills](https://developers.openai.com/codex/build-skills)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [OpenCode Agent Skills](https://opencode.ai/docs/skills/)
- [OpenCode commands](https://opencode.ai/docs/commands/)
- [Antigravity skills](https://antigravity.google/docs/skills/)
- [Antigravity CLI plugins & skills](https://antigravity.google/docs/cli/plugins/)
