# OIP — Open Ingestion Protocol (v0.2)

**Version:** 0.2 (draft) · **Status:** proposed

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
  "oip_version": "0.2",
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
  },
  "agent": {
    "skill_path": "skills/skill.md",
    "tool_skills_dir": "skills/tools/"
  }
}
```

**Required keys:** `oip_version`, `producer.name`, `producer.version`, `data_dir`, `produces`, `invocation`.

**Notes:**

- `producer.name` is the machine identifier. **MUST** be lowercase, alphanumeric + hyphens, no spaces.
- `produces.source_ref_kinds` declares every `source_ref.kind` value the producer's regions will use.
- `invocation.tools_namespace` is the prefix the producer's MCP tools are registered under. **MUST** be unique among installed producers.
- `invocation.command` is the binary name a consumer will spawn. **SHOULD** be on the user's PATH after install.
- `ui_hints` are advisory hints for OIP-aware *visual* consumers (canvases, viewers).
- `agent` (new in 0.2) is the parallel block for OIP-aware *agent* consumers — narrative skill content explaining *when* an agent should invoke this producer and *how* to chain its tools. Optional; producers without it just don't appear in the consumer's composed agent briefing. See section 9.

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
| `pdf-page-bbox`         | `page` (int), `bbox` (`[l, t, r, b]`), `page_size` (`[w, h]`), `coord_origin?` — see below |
| `audio-timestamp`       | `source_url`, `start_ms`, `end_ms`, `speaker?`           |
| `video-timestamp`       | `source_url`, `start_ms`, `end_ms`, `track?`             |
| `code-line-range`       | `path`, `start_line`, `end_line`, `language?`            |
| `web-snapshot`          | `url`, `snapshot_sha`, `xpath?`                          |
| `fmu-variable`          | `fmu_slug`, `variable_name`, `causality?`                |
| `fmu-simulation-time`   | `simulation_id`, `time_seconds`, `variable_name?`        |

Producers **MAY** add new kinds, prefixed by their namespace if domain-specific.

### `pdf-page-bbox` coordinates

A bbox is only meaningful with a declared coordinate system. Producers disagree by default (PDF user space is bottom-left; images, OCR and layout models, and renderers are top-left; some models emit normalised 0–1000 boxes), and a consumer cannot tell them apart from four numbers. So `pdf-page-bbox` fixes one convention:

- **Units:** PDF points (1/72 inch), the page's own user space. Never pixels or normalised units; a producer that works on a raster **MUST** convert using the render scale it used.
- **Origin:** top-left of the page, y increasing downward. `bbox` is `[left, top, right, bottom]` with `left <= right` and `top <= bottom`.
- **`page_size`** (`[width, height]`, points) is **REQUIRED**. It lets a consumer validate bounds and convert to any other space without opening the source.
- **`page`** is 1-based.
- **`coord_origin`** is OPTIONAL and defaults to `"top-left"`. A producer that natively emits bottom-left (PDF user space) **MAY** write `"bottom-left"` instead of converting; the bbox is then `[left, top, right, bottom]` with y increasing upward (`top >= bottom`). Consumers **MUST** convert on read (`y' = height - y`) and **SHOULD** store top-left. This is a migration escape hatch, not a second convention.

A consumer **MUST** reject or normalise a `pdf-page-bbox` whose values violate the declared convention (wrong y-order, out of page bounds), rather than render it as-is.

Example:

```json
{"kind": "pdf-page-bbox", "page": 3, "bbox": [56.4, 653.1, 291.0, 783.4], "page_size": [595.3, 841.9]}
```

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
- [ ] Provide an `agent` block for OIP-aware agent consumers (see section 9).
- [ ] Make `<slug>` derivation deterministic.
- [ ] Emit at least `text` or `markdown` content for textual regions.
- [ ] Add a `--data-dir` flag to your MCP server.

You **MAY**:

- [ ] Add additional MCP tools beyond the minimum.
- [ ] Add producer-private files under `_producer/`.

---

## 9. `agent` — narrative skills for AI consumers

**New in 0.2.** Optional. The agent-side dual of `ui_hints`: a way for a
producer to ship the natural-language guidance an AI consumer needs to
know *when* to invoke this producer's tools and *how* to chain them. A
consumer composing an agent briefing (e.g. a SKILL.md for Claude Code, an
`instructions` field for an MCP server) MAY concatenate the `agent` block
of every registered producer.

### Shape

The `agent` block is an object on `manifest.json`:

```json
{
  "agent": {
    "skill_path": "skills/skill.md",
    "tool_skills_dir": "skills/tools/"
  }
}
```

Or, for small producers who'd rather inline:

```json
{
  "agent": {
    "skill": "## `your-tool` — what it does\n\nUse this when...\n"
  }
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `skill_path` | one of (skill_path, skill) | Filesystem path to a markdown file, relative to the manifest's directory. |
| `skill` | one of | Inline markdown string. Mutually exclusive with `skill_path`. |
| `tool_skills_dir` | no | Directory containing one `.md` per tool, relative to the manifest. Reserved for tool-level skills; consumers MAY ignore this in 0.2. |

A consumer **SHOULD** treat `skill_path` and `skill` as mutually
exclusive. If both are present, `skill_path` wins.

### What goes in the skill content

OIP itself doesn't dictate the prose style — different consumers will
have different conventions (length caps, voice, anti-patterns). The
following is a recommended baseline that every consumer will accept:

- A top-level heading (`##`) naming the producer
- One short paragraph describing when an agent would invoke it
- A `### Tools` subsection listing the producer's MCP tools (one line each)
- A `### Typical situation` paragraph describing the shape of the
  situation, **not** an enumerated step-by-step procedure
- A `### Common errors` subsection (optional)

The producer **SHOULD NOT** assume any particular UI for the composed
result. Consumers may render it as plaintext, markdown, or wrap it in
their own structure.

### Length and tone guidance (informative, not normative)

Consumers MAY enforce stricter content rules (length caps, "no numbered
procedural lists," etc.). Producers SHOULD keep the `skill` content
short — the goal is to brief an agent on situation and tools, not to
write a reference manual. Tooling that composes multiple producers' skill
blocks works best when each contribution is on the order of 150-400 words.

### Versioning

The `agent` block schema rides on `oip_version`. Consumers reading a
manifest with `oip_version: "0.2"` or later MAY read the `agent` block;
consumers reading older manifests MUST treat the field as absent.

---

## 10. What OIP doesn't specify

- Embeddings or search indexes — out of scope.
- Authentication — local-first by default.
- Rendering — `ui_hints` is advisory.
- Transports beyond MCP — 0.1 only specifies `mcp-stdio`.
- Provenance verification — consumer's responsibility.
- Agent-side content style — `agent.skill` content is producer-authored;
  consumers may enforce stricter rules.

---

## 11. Versioning

`oip_version` follows semver. Backwards-incompatible changes bump the major. Consumers MUST refuse manifests whose major exceeds theirs; SHOULD read older minors.

---

*Draft 0.1. Stabilises at 1.0 once at least three independent producers and one external consumer are implemented end-to-end.*
