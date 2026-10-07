# Contributing and curation

## Skill acceptance checklist

1. The folder name and frontmatter `name` are identical kebab-case IDs.
2. `description` says what the skill does and when it should activate.
3. `risk` reflects side effects: `none`, `safe`, `critical`, `offensive`, or `unknown`.
4. `source`, `source_repo`, `source_type`, and license information are truthful.
5. The body contains real workflow guidance, safety boundaries, and limitations.
6. Referenced local files exist and every bundled file supports the workflow.
7. Scripts are deterministic where practical and have been tested directly.
8. Secrets, credentials, and environment-specific absolute paths are not embedded.

## Scope discipline

Skills should add non-obvious domain guidance. Do not repeat generic agent behavior,
turn one user's preference into a universal rule, or claim permission for external
mutations. Keep `SKILL.md` concise and route conditional detail to `references/`.

## Updating upstream content

Do not overwrite a canonical skill merely because another source has the same ID.
Compare capability, recency, ecosystem fit, license, safety, and support files.
Record a deliberate replacement in `sources/manifest.yaml`, preserve the displaced
variant locally, and update `config/official-imports.yaml` when the winner is an
official source.

## Required check

```bash
python tools/repo_skills.py all
```

Errors must be fixed. Warnings should be reviewed and either repaired or retained
as explicit catalog debt; never hide warnings by weakening the validator.
