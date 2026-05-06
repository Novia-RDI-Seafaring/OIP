# OIP — Open Ingestion Protocol (v0.1)

**Version:** 0.1 (draft) · **Status:** proposed

A vendor-neutral specification for **ingestion tools that produce structured, source-grounded knowledge**. Any tool that conforms to OIP can be consumed by any OIP-aware application — the same way any LSP-compliant language server works in any LSP-aware editor.

OIP is *not* tied to any specific consumer.

---

## Roles

- **Producer** — a tool that ingests source material (audio, PDFs, code repos, web pages, etc.) and writes OIP-compliant artefacts to disk.
- **Consumer** — a tool that reads OIP artefacts and offers them to users / agents (a UI, a search index, an MCP server).

A single tool can be both. This document is primarily written for **producer authors**.

---

## Conformance levels

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY** in this document are interpreted as in RFC 2119.

A producer is **OIP 0.1 compliant** if it satisfies every **MUST** below.

---

## 1. On-disk artefact tree

A producer writes to a base directory whose path is **configurable by the user** (typically via `--data-dir` or an env var). Inside it, the layout is fixed:

```
<oip-data-dir>/
├── manifest.json                ← REQUIRED. OIP advertisement.
├── sources/<slug>/              ← OPTIONAL. The original input, immutable.
│   └── <filename>
└── artefacts/<slug>/            ← REQUIRED for every ingested document.
    ├── document.json            ← REQUIRED. Document metadata.
    ├── regions.json             ← REQUIRED. Addressable regions.
    ├── content/                 ← REQUIRED. Region contents (text, png, svg, …).
    │   ├── <region-id>.txt
    │   ├── <region-id>.md
    │   ├── <region-id>.png
    │   └── …
    └── _producer/               ← OPTIONAL. Producer-private extras.
```

A producer **MUST** write at minimum: `manifest.json`, and per ingested document `artefacts/<slug>/document.json` and `artefacts/<slug>/regions.json`.

A producer **MUST NOT** require consumers to read anything inside `_producer/` — that subdirectory is private to the producer.

A consumer **MUST** ignore any file or directory it doesn't recognise. A consumer **MUST NOT** assume `sources/<slug>/<filename>` exists.

`<slug>` is a stable identifier the producer assigns to one ingested document. It **SHOULD** be derived deterministically from the source so re-ingesting produces the same slug.

---

## 2. `manifest.json`

A producer **MUST** write this file at the root of its data directory.

```json
{
  "oip_version": "0.1",
  "producer": {
    "name": "your-tool-name",
    "display_name": "Human-Readable Name",
    "version": "0.1.0",
    "homepage": "https://github.com/you/your-tool"
  },
  "data_dir": "/abs/path/to/this/data/dir",
  "produces": {
    "source_kinds": ["audio/wav", "audio/mpeg"],
    "region_kinds": ["transcript_segment"],
    "source_ref_kinds": ["audio-timestamp"]
  },
  "invocation": {
    "kind": "mcp-stdio",
    "command": "your-tool-mcp",
    "args": ["--data-dir", "/abs/path/to/this/data/dir"],
    "tools_namespace": "your_namespace"
  },
  "ui_hints": {
    "node_types": [
      {"name": "yourns:segment", "renders": "card with timestamp + text"}
    ],
    "edge_styles": {},
    "source_ref_handlers": {
      "audio-timestamp": "open the audio at start_ms"
    }
  }
}
```

**Required keys:** `oip_version`, `producer.name`, `producer.version`, `data_dir`, `produces`, `invocation`.

**Notes:**

- `producer.name` is the machine identifier. **MUST** be lowercase, alphanumeric + hyphens, no spaces.
- `produces.source_ref_kinds` declares every `source_ref.kind` value the producer's regions will use.
- `invocation.tools_namespace` is the prefix the producer's MCP tools are registered under. **MUST** be unique among installed producers.
- `invocation.command` is the binary name a consumer will spawn. **SHOULD** be on the user's PATH after install.

---

## 3. `document.json`

One per ingested document at `artefacts/<slug>/document.json`.

```json
{
  "slug": "interview-2026-01-15",
  "title": "Interview — 2026-01-15",
  "source_kind": "audio/mpeg",
  "source_path": "sources/interview-2026-01-15/interview.mp3",
  "source_url": null,
  "ingested_at": "2026-05-06T12:00:00Z",
  "ingested_by": "your-tool-name/0.1.0",
  "size_units": {"duration_ms": 1872000},
  "tags": [],
  "extras": {}
}
```

**Required keys:** `slug`, `title`, `source_kind`, `ingested_at`, `ingested_by`, `size_units`.

`size_units` is a free-form dict keyed by what makes sense for the medium. Conventional keys: `page_count`, `duration_ms`, `loc_count`, `byte_count`.

---

## 4. `regions.json`

A list of addressable regions at `artefacts/<slug>/regions.json`.

```json
[
  {
    "id": "interview-2026-01-15:t00012000-00018500",
    "kind": "transcript_segment",
    "title": "I think the key insight is that…",
    "description": "I think the key insight is that we don't actually need a separate database…",
    "source_ref": {
      "kind": "audio-timestamp",
      "source_url": "sources/interview-2026-01-15/interview.mp3",
      "start_ms": 12000,
      "end_ms": 18500,
      "speaker": "Jane"
    },
    "content": {
      "text": "content/interview-2026-01-15_t00012000-00018500.txt",
      "markdown": "content/interview-2026-01-15_t00012000-00018500.md"
    },
    "tags": ["technical_insight"],
    "entities": ["speaker:jane", "mentions:database"]
  }
]
```

**Required keys per region:** `id`, `kind`, `source_ref`.

`id` **MUST** be globally unique within the producer's data dir. Convention: `<slug>:<address-suffix>`.

---

## 5. `source_ref` — the pointer back to the original

Every region carries a `source_ref` describing where in the source it came from. The `kind` field is open-ended but **MUST** appear in the producer's `manifest.produces.source_ref_kinds`.

### Conventional kinds

| `kind`                  | Address fields                                           |
|-------------------------|----------------------------------------------------------|
| `pdf-page-bbox`         | `page` (int), `bbox` (`[l, t, r, b]`)                    |
| `audio-timestamp`       | `source_url`, `start_ms`, `end_ms`, `speaker?`           |
| `video-timestamp`       | `source_url`, `start_ms`, `end_ms`, `track?`             |
| `code-line-range`       | `path`, `start_line`, `end_line`, `language?`            |
| `web-snapshot`          | `url`, `snapshot_sha`, `xpath?`                          |
| `fmu-variable`          | `fmu_slug`, `variable_name`, `causality?`                |
| `fmu-simulation-time`   | `simulation_id`, `time_seconds`, `variable_name?`        |

Producers **MAY** add new kinds, prefixed by their namespace if domain-specific.

---

## 6. MCP tool surface

A producer's MCP server (stdio subprocess) **SHOULD** expose at minimum:

```
<namespace>.ingest(<input>) → { slug, region_count, ... }
<namespace>.list_documents() → [ document.json, ... ]
<namespace>.get_document(slug) → document.json
<namespace>.get_regions(slug, <optional filters>) → regions.json subset
<namespace>.get_region_content(region_id, format="text"|"markdown") → string
```

`<namespace>` matches `manifest.invocation.tools_namespace`.

---

## 7. Discovery

A consumer finds OIP producers in three locations, in priority order:

1. **Per-data-dir:** `<consumer-data-dir>/.oip/producers.d/*.json`
2. **System-wide:** `${XDG_CONFIG_HOME:-~/.config}/oip/producers.d/*.json`
3. **Bundled:** producers compiled into the consumer.

A producer's installer **SHOULD** write its manifest to the system-wide directory.

---

## 8. Implementer's checklist (producer)

You **MUST**:

- [ ] Choose a `producer.name` (lowercase, hyphenated) and a `tools_namespace`.
- [ ] Choose your `source_ref.kind` strings and their address-field shapes.
- [ ] Implement the on-disk layout: `manifest.json`, `artefacts/<slug>/document.json`, `artefacts/<slug>/regions.json`, `artefacts/<slug>/content/`.
- [ ] Implement an MCP server (stdio) exposing at least the five required tools.
- [ ] Add an `<ns>-mcp` binary entry point.
- [ ] Add an installer command writing the manifest to `${XDG_CONFIG_HOME:-~/.config}/oip/producers.d/<name>.json`.

You **SHOULD**:

- [ ] Provide `ui_hints` for OIP-aware UIs.
- [ ] Make `<slug>` derivation deterministic.
- [ ] Emit at least `text` or `markdown` content for textual regions.
- [ ] Add a `--data-dir` flag to your MCP server.

You **MAY**:

- [ ] Add additional MCP tools beyond the minimum.
- [ ] Add producer-private files under `_producer/`.

---

## 9. What OIP doesn't specify

- Embeddings or search indexes — out of scope.
- Authentication — local-first by default.
- Rendering — `ui_hints` is advisory.
- Transports beyond MCP — 0.1 only specifies `mcp-stdio`.
- Provenance verification — consumer's responsibility.

---

## 10. Versioning

`oip_version` follows semver. Backwards-incompatible changes bump the major. Consumers MUST refuse manifests whose major exceeds theirs; SHOULD read older minors.

---

*Draft 0.1. Stabilises at 1.0 once at least three independent producers and one external consumer are implemented end-to-end.*
