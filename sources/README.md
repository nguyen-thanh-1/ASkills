# Upstream snapshots

This directory keeps the downloaded repositories used to assemble the canonical
`skills/` tree. It is intentionally excluded from Git because the snapshots are
large and contain generated mirrors. The canonical repository remains complete:
every distributed skill, its support files, and its license stay under `skills/`.

Sources retained in this workspace:

- `anthropic-skills/` — original `anthropics/skills` snapshot.
- `openai-skills/` — original (now deprecated) `openai/skills` snapshot.
- `agentic-awesome-skills/` — catalog application, generated mirrors, and
  maintenance tooling from `sickn33/agentic-awesome-skills`; its canonical skill
  tree was promoted to the repository root.
- `replaced-canonical/` — prior community variants or placeholder directories
  displaced by a preferred official implementation.

See `manifest.yaml` for selection rules. Never run scripts directly from a raw
snapshot without reviewing them first.
