# Installation and Invocation

## Project-local use

Keep `.agents/skills/verify` in the repository root. Every compliant host discovers Agent Skills from this layout, either directly or via a host-specific symlink (see the table below). Restart the host if it was already running when the skill was added.

| Host | Discovery path | Invocation |
|---|---|---|
| Codex CLI or IDE | `.agents/skills/verify` | `verify [mode] [target] [--contract <path>]` |
| Cursor | `.agents/skills/verify` | choose `/verify`, then provide mode and target |
| OpenCode | `.agents/skills` + `.opencode/commands/verify.md` | `/verify [mode] [target]` through the included command adapter |
| Antigravity | `.agents/skills` | `/verify` in interactive TUI; invoke contextually in print/non-interactive mode |
| Claude Code | `.claude/skills/verify` (symlink to `.agents/skills/verify`) | invoke the `verify` skill |

The OpenCode adapter lives at `.opencode/commands/verify.md`; it forwards arguments and does not duplicate verification policy.

## User-wide use

Copy or symlink the `verify` directory to the host's user skill location:

- Codex: `~/.agents/skills/verify`
- Cursor: `~/.cursor/skills/verify`
- OpenCode: `~/.agents/skills/verify` or `~/.config/opencode/skills/verify`
- Antigravity: `~/.gemini/antigravity-cli/skills/`
- Claude Code: `~/.claude/skills/verify`

The canonical source remains `.agents/skills/verify`. Avoid maintaining separate modified copies per host.

## Verify installation

Confirm the host lists `verify`, then run it against a small working-tree change. The final report should identify its resolved target, selected panel, executed checks, findings, and verdict. If the host cannot create clean-context subagents, the report must state `degraded independence`.

## Host documentation

- [Codex Agent Skills](https://developers.openai.com/codex/build-skills)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [OpenCode Agent Skills](https://opencode.ai/docs/skills/)
- [OpenCode commands](https://opencode.ai/docs/commands/)
- [Antigravity skills](https://antigravity.google/docs/skills/)
- [Antigravity CLI plugins & skills](https://antigravity.google/docs/cli/plugins/)
- [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills)
