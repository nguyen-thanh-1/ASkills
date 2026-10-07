# Architecture

## Design goals

The repository optimizes for discoverability, provenance, compatibility, and
low maintenance cost. It deliberately separates physical storage from logical
classification.

## Canonical layer

`skills/` is the only distributable source of truth. A skill may contain nested
support files and, in a few upstream bundles, nested child skills. The catalog
discovers every `SKILL.md` recursively.

Skill folders are not physically moved into category directories because many
upstream instructions and installers refer to stable `skills/<id>` paths. Logical
collections provide clear organization without breaking those references.

## Catalog layer

`tools/repo_skills.py build` reads every skill, normalizes its upstream category
through `config/taxonomy.yaml`, and produces:

- `catalog/skills.json` — complete machine-readable records;
- `catalog/summary.json` — counts by domain, risk, and source type;
- `collections/*.md` — browsable domain indexes;
- `CATALOG.md` — one full human-readable index.

The original upstream category is preserved in each catalog record alongside the
normalized domain. Taxonomy changes therefore do not rewrite skill content.

## Provenance layer

Downloaded repositories remain under `sources/` for local audit. They are ignored
by Git because they include large generated mirrors and are not runtime inputs.
`sources/manifest.yaml` records origin and precedence. Imported official skill
metadata is controlled by `config/official-imports.yaml`.

## Validation layer

Validation has two levels:

- Errors block a clean build: malformed YAML, missing required metadata, invalid
  or duplicate IDs, folder/name mismatches, invalid risk labels, and taxonomy errors.
- Warnings track editorial debt: missing provenance, trigger guidance,
  limitations, or local references.

Validation never executes bundled skill scripts.
