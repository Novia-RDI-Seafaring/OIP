# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Novia-RDI-Seafaring/OIP/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Novia-RDI-Seafaring/OIP/releases/tag/v0.1.0
