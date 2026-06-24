# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (0.3 draft — see rfcs/0001)

- `consumes` block on `manifest.json` for **region producers**: tools that
  derive a new region from an existing one (for example digitizing a chart
  image into a data series) rather than ingesting a source. Declares the
  `region_kinds` and `content_kinds` the producer acts on.
- `derived_from` on regions: the parent region id a derived region came
  from. The derived region keeps the parent's `source_ref`, so provenance
  points at the original location.
- Recognised `renders` tokens convention for `ui_hints` (`chart`, `table`,
  `card`): a consumer that knows a token and finds matching `content.data`
  draws it; unknown tokens fall back to title and description. `renders`
  stays a free string, so 0.2 producers are unaffected.
- `rfcs/0001-region-producers-and-renderable-content.md` and a worked
  `examples/graph-tracer.json` (a region producer that derives a
  `chart_series` from a `chart` region).
- JSON Schema additions in `schemas/` and the bundled copy under
  `packages/oip/src/oip/_data/schemas/`. All additive and optional;
  existing producer output validates unchanged.

## [0.2.0] — 2026-05-28

### Added

- Optional `agent` block on `manifest.json` for OIP-aware **agent**
  consumers — the narrative dual of `ui_hints`. A producer that ships
  an `agent` block contributes natural-language skill content
  describing when an agent should invoke its tools and how to chain
  them. The block accepts either `skill_path` (relative to the
  manifest's directory) or `skill` (inline markdown), plus an
  optional `tool_skills_dir` for per-tool snippets.
- Section 9 of `SPEC.md` documents the `agent` block, the
  recommended skill structure, and version-bump semantics.
- JSON Schema additions in `schemas/manifest.json` and the bundled
  copy at `packages/oip/src/oip/_data/schemas/manifest.json`.
- Implementer's checklist updated: SHOULD provide an `agent` block.

### Changed

- `oip_version` bumped to `0.2`. Backwards-compatible: producers with
  `oip_version: "0.1"` continue to validate against the updated
  schema.

## [0.1.0] — 2026-05-06

### Added

- Initial OIP spec draft (`SPEC.md`, `oip_version = "0.1"`).
- JSON Schemas for `manifest.json`, `document.json`, `region`.
- Producer implementer's checklist (`CHECKLIST.md`).
- Worked example for an audio transcriber (`examples/transcriber.json`).
- `oip` Python CLI (`uvx oip` / `uv tool install oip`):
  - `oip spec` — print the full spec
  - `oip schema {manifest|document|region}` — emit JSON Schemas
  - `oip example` — emit a worked example
  - `oip checklist` — emit the implementer's checklist
  - `oip validate <data-dir>` — validate a producer's output
  - `oip new <name>` — scaffold a starter Python producer
- `llms.txt` for LLM-fetch discovery.
- Reference implementations: PDF medallion + FMU producers (in
  [Anchor v2](https://github.com/Novia-RDI-Seafaring/anchor-kb-ui-RAG)).

[Unreleased]: https://github.com/Novia-RDI-Seafaring/OIP/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Novia-RDI-Seafaring/OIP/releases/tag/v0.2.0
[0.1.0]: https://github.com/Novia-RDI-Seafaring/OIP/releases/tag/v0.1.0
