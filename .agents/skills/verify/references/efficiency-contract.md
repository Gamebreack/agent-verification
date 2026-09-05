# Reviewer Efficiency Contract

These rules apply to every reviewer loaded by this skill. Read before dispatching.

## Method constraints

1. **No general repo review.** Inspect only the surfaces and findings relevant to your mandate. Do not read files unrelated to your role.
2. **No rediscovery.** Do not re-fetch evidence already present in the Verification Contract or in another reviewer's findings. Cite the source instead.
3. **Batch independent inspection.** When multiple reads or commands are needed, batch them. Do not sequentialize what can be parallel.
4. **Expand only from a concrete hypothesis.** Do not broaden scope based on speculation. If you find something outside your mandate, return `OUT_OF_SCOPE` rather than investigating.
5. **Stop when sufficient.** When your mandate is established or refuted, stop. Prefer `NO FINDINGS` over low-value exploration.
6. **No implementation reasoning.** Do not use knowledge of the implementation to evaluate intent. Treat the Verification Contract as the source of truth.

## Output discipline

- One finding per claim. Do not combine unrelated defects.
- Cite specific files, lines, commands, or observations. No generic risk language.
- Propose severity based on demonstrated impact, not preference.
- If your mandate yields no findings, return `NO FINDINGS` — do not invent concerns.

## Forbidden behaviors

- Editing, fixing, or proposing code changes to the target.
- Delegating to another agent.
- Reading files outside the Verification Contract's scope.
- Reporting findings already covered by another reviewer.
- Inventing risks to justify inclusion in the panel.