---
description: Run evidence-gated independent verification (supports --contract <path>)
---

Load the `verify` Agent Skill and apply it to: $ARGUMENTS

If no arguments are supplied, use `panel` mode against the default target: branch-aware, meaning the branch against its merge base plus the working tree when the branch has commits not on its base, otherwise the working-tree diff. A plan or design document is an artifact target; a pull request is a target only when named. The skill's Invocation section defines the target rules.
