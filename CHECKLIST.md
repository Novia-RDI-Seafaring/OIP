# OIP producer implementation — go/no-go checklist

Use this as your acceptance criteria. When every box is checked, your tool
is OIP 0.1 compliant.

## Setup

- [ ] Pick `producer.name` (lowercase, alphanumeric + hyphens, no spaces).
- [ ] Pick `tools_namespace` (short, unique among other producers you'll
      coexist with — `pdf`, `transcribe`, `code`, `fmu`).
- [ ] Pick your `source_ref.kind` strings. Use conventional ones if they fit
      (`pdf-page-bbox`, `audio-timestamp`, etc.); namespace your own
      (`yourns-frame`, `yourns-rect`).

## On-disk layout

- [ ] Writes `<data-dir>/manifest.json` at the root.
- [ ] Writes `<data-dir>/artefacts/<slug>/document.json` per ingested doc.
- [ ] Writes `<data-dir>/artefacts/<slug>/regions.json` per ingested doc.
- [ ] Writes region contents under `<data-dir>/artefacts/<slug>/content/`.
- [ ] All paths in `regions[*].content.*` are relative to `artefacts/<slug>/`.
- [ ] All paths in `document.source_path` are relative to `<data-dir>` or null.
- [ ] `<slug>` is deterministic — re-ingesting the same input yields the same slug.

## Manifest correctness

- [ ] `oip_version` is `"0.1"`.
- [ ] `producer.name`, `producer.version` are set.
- [ ] `data_dir` is an absolute path.
- [ ] `produces.source_kinds` lists every MIME type you can ingest.
- [ ] `produces.region_kinds` lists every `kind` your regions emit.
- [ ] `produces.source_ref_kinds` lists every `source_ref.kind` your
      regions emit. Consumers use this to know which kinds to dispatch.
- [ ] `invocation.kind` is `"mcp-stdio"`.
- [ ] `invocation.command` resolves to your MCP binary on PATH.
- [ ] `invocation.tools_namespace` matches the prefix on your MCP tool names.

## MCP server

- [ ] Binary on PATH (e.g. `your-tool-mcp`).
- [ ] Accepts `--data-dir DIR` flag at minimum.
- [ ] Exposes `<ns>.ingest(...)` returning `{ slug, region_count, ... }`.
- [ ] Exposes `<ns>.list_documents()`.
- [ ] Exposes `<ns>.get_document(slug)`.
- [ ] Exposes `<ns>.get_regions(slug, ...)` — optionally with filters.
- [ ] Exposes `<ns>.get_region_content(region_id, format)`.
- [ ] Errors are returned as JSON like `{"error": "<message>"}` rather than
      raised as MCP-level errors. This is convention, not RFC.

## Validation passes

- [ ] `oip validate <your-data-dir>` reports no errors.
- [ ] At least one document has been ingested and validates.
- [ ] At least one region per document validates.
- [ ] The MCP server starts cleanly: `your-tool-mcp --data-dir <dir>` runs
      without errors and the stdio handshake completes.

## Installer

- [ ] You ship a `your-tool oip install` command (or equivalent) that:
  - Writes `manifest.json` to the user's data dir.
  - Writes a copy to `${XDG_CONFIG_HOME:-~/.config}/oip/producers.d/<name>.json`.
- [ ] You have a `your-tool oip install --print` mode that emits the
      manifest to stdout without writing anything (useful for review).

## Stretch (you SHOULD)

- [ ] `ui_hints.node_types[]` declares at least one node type with a
      human-readable `renders` description.
- [ ] `ui_hints.source_ref_handlers` describes how to dispatch each of
      your `source_ref.kind` values to a UI behaviour.
- [ ] Your README has a one-paragraph "Anchor / OIP" section pointing
      readers at `oip` for the spec.
- [ ] Your tests include at least one round-trip: ingest → write →
      validate.

## Sanity check before publishing

- [ ] `pip install your-tool` (or `uv tool install`) → tool works.
- [ ] `your-tool oip install` runs without errors.
- [ ] In an OIP consumer (e.g. `anchor extensions list`) your tool
      appears under "system" with the right namespace and source kinds.
