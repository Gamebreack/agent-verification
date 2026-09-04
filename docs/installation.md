# Installation and Invocation

## Project-local use

Keep `.agents/skills/verify` in the repository root. Codex, Cursor, and OpenCode discover this Agent Skills location. Restart the host if it was already running when the skill was added.

Invoke it as follows:

| Host | Invocation |
|---|---|
| Codex CLI or IDE | `$verify auto` |
| Cursor | choose `/verify`, then provide the mode and target |
| OpenCode | `/verify auto` through the included command adapter |

The OpenCode adapter lives at `.opencode/commands/verify.md`; it forwards arguments and does not duplicate verification policy.

## User-wide use

Copy or symlink the `verify` directory to the host's user skill location:

- Codex: `~/.agents/skills/verify`
- Cursor: `~/.cursor/skills/verify`
- OpenCode: `~/.agents/skills/verify` or `~/.config/opencode/skills/verify`

The canonical source remains `.agents/skills/verify`. Avoid maintaining separate modified copies per host.

## ChatGPT web and mobile

Repository-local skills are not directly installable in ChatGPT web/mobile. Those surfaces require plugin packaging and installation. Plugin distribution is intentionally a post-MVP release task.

## Verify installation

Confirm the host lists `verify`, then run it against a small working-tree change. The final report should identify its resolved target, selected panel, executed checks, findings, and verdict. If the host cannot create clean-context subagents, the report must state `degraded independence`.

## Host documentation

- [Codex Agent Skills](https://developers.openai.com/codex/build-skills)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [OpenCode Agent Skills](https://opencode.ai/docs/skills/)
- [OpenCode commands](https://opencode.ai/docs/commands/)
