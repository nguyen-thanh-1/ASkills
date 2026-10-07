# Changelog

## Unreleased — 2026-10-07

### Added

- Unified canonical library with 2,706 unique skill IDs.
- Eighteen generated work-domain collections and a machine-readable catalog.
- Official Anthropic and OpenAI imports with explicit source-precedence policy.
- Specialized `skill-creator-anthropic` and `pdf-layout-review` variants where
  same-name upstream skills provide materially different workflows.
- Cross-platform Python tooling for catalog generation, validation, and import checks.
- English and Vietnamese repository guides, architecture, curation, and security docs.

### Changed

- Promoted the Agentic Awesome Skills canonical tree to the repository-level
  `skills/` source of truth.
- Replaced selected vendor-specific community variants with official upstream
  implementations while retaining displaced copies in the local source archive.
- Renamed `android_ui_verification` to the standards-compliant
  `android-ui-verification` ID and updated its local reference.

### Validation

- Repository validation reports zero structural errors.
- All 62 official imports pass the strict skill-creator quick validator.
- Catalog generation is deterministic across repeated builds.
- Remaining editorial warnings are recorded in `catalog/validation-report.json`.
