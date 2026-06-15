# RFC 0001 — Region producers and renderable content

**Target version:** 0.3 (draft) · **Status:** proposed · **Type:** backward-compatible additions

This RFC proposes three additive changes to OIP. Together they let a tool
that operates on *one region of an already-ingested document* ship as a
normal OIP producer, write structured data a consumer can draw, and have
that drawing be portable across consumers.

The forcing case is chart digitization: turning a pump-curve image inside
a datasheet into a real `(x, y)` series. The changes are not specific to
charts. They generalise the producer model so the next derived extractor
(table reconstruction, symbol recognition, 3D reconstruction) fits the
same shape.

---

## 1. Motivation

OIP 0.2 models a producer as *source to artefacts*. A producer ingests a
whole document (a PDF, an audio file) and writes `document.json` plus
`regions.json`. Discovery, invocation, `ui_hints`, and the `agent` block
already let a consumer find a producer, spawn it, render its regions, and
brief an agent on its tools. A conformant producer already "just works"
in any OIP-aware consumer.

Three things are missing once the unit of work is a *region* rather than
a *source*.

A datasheet PDF is ingested by a PDF producer. One of its regions is a
performance chart: `kind: "chart"`, a `pdf-page-bbox` source_ref, a PNG
crop as content. A second tool can read that crop and recover the plotted
series. That tool does not ingest the PDF. It consumes one region another
producer already wrote, and derives a new region from it. OIP has no way
to declare this relationship, no place to put the recovered numeric
series, and no portable way to say "draw this as a chart."

This RFC adds the three missing pieces.

---

## 2. Proposed change A — region producers (`consumes`)

### 2.1 Manifest

A producer MAY declare that it consumes existing regions rather than (or
in addition to) ingesting sources. Add an optional `consumes` block to
`manifest.json`, parallel to `produces`:

```json
{
  "consumes": {
    "region_kinds": ["chart"],
    "content_kinds": ["png"]
  },
  "produces": {
    "region_kinds": ["chart_series"],
    "source_ref_kinds": ["derived-region"]
  }
}
```

A producer with a `consumes` block is a **region producer**. A producer
with only `produces` is a **source producer** (the 0.2 model, unchanged).
A producer MAY be both.

`consumes.region_kinds` lists the region kinds the tool can act on.
`consumes.content_kinds` lists the content forms it needs present on those
regions (for charts, the `png` crop). A consumer offers a region producer
only the regions whose `kind` and available `content` match.

### 2.2 Derivation and provenance

A region producer writes new regions into the **same** `artefacts/<slug>/`
tree as the document it derived from. It MUST NOT create a new document.

A derived region MUST carry a `derived_from` field naming the parent
region id, and its `source_ref` MUST resolve to the same original
location as the parent. The simplest rule: copy the parent's `source_ref`
verbatim, so a digitized series points at the same page and bbox as the
chart it came from. Provenance is preserved without the consumer doing
any work.

```json
{
  "id": "lkh-pump:p4-chart-seriesB",
  "kind": "chart_series",
  "derived_from": "lkh-pump:p4-r1",
  "source_ref": {
    "kind": "pdf-page-bbox",
    "page": 4,
    "bbox": [56.5, 783.4, 252.8, 605.7]
  },
  "content": { "data": "content/lkh-pump_p4-chart-seriesB.json" }
}
```

`derived_from` is new and OPTIONAL. A consumer that does not understand it
MUST ignore it (per the existing unknown-field rule). Consumers that do
understand it MAY draw the derivation edge.

### 2.3 MCP surface

A region producer SHOULD expose a tool that takes a region reference and
any extraction parameters, and writes the derived region(s):

```
<namespace>.derive(slug, region_id, <params>) -> { region_ids, ... }
```

The minimum read tools from section 6 stay as they are. A region producer
does not need `ingest`.

---

## 3. Proposed change B — structured region content

### 3.1 The gap

OIP 0.2 content is file-backed and textual or visual: `text`, `markdown`,
`png`, `svg`. A recovered chart series is neither. It is structured
numeric data: axes, scales, one or more series of points.

### 3.2 The `data` content kind

Add `data` as a content kind. It points at a JSON file under `content/`.
OIP does not fix the shape of that JSON in general; the region `kind`
implies it, the same way a `transcript_segment` implies what its text
means. OIP defines one conventional shape per renderable token (see
change C) so portability is possible.

```json
"content": {
  "data": "content/lkh-pump_p4-chart-seriesB.json"
}
```

A consumer that does not recognise the region kind MAY still show the
region by its `title` and `description`. Structured `data` is additive.

---

## 4. Proposed change C — recognised `renders` tokens

### 4.1 The gap

`ui_hints.node_types[].renders` is free text today, for example `"card
with timestamp + text"`. That is fine as a hint to a human building a
consumer. It is not enough for a chart to draw itself in a consumer the
producer author has never seen. The consumer needs to know the data
contract behind the word.

### 4.2 Recognised tokens

Define a small, growing set of **recognised render tokens**. Each token
names a data shape a consumer MAY know how to draw. The string stays free
text for anything outside the set, so 0.2 producers keep working.

Initial set:

| Token     | Data contract (the `data` JSON) |
|-----------|----------------------------------|
| `chart`   | `{ x_label, y_label, x_scale, y_scale, series: [{ label, points: [[x, y], ...] }] }` |
| `table`   | `{ columns: [...], rows: [[...], ...] }` |
| `card`    | no `data` required; `title` + `description` only |

A producer signals a recognised token by setting `renders` to exactly the
token string:

```json
"ui_hints": {
  "node_types": [
    { "name": "graphtracer:chart_series", "renders": "chart" }
  ]
}
```

A consumer that recognises `chart` and finds a `data` content file shaped
like the contract draws a chart. A consumer that does not recognise the
token falls back to `title` + `description`. Nothing breaks.

This subsumes the earlier idea of an `a2ui` render option: `a2ui` becomes
one more recognised token with its own data contract, registered the same
way.

---

## 5. Non-goal — interaction stays with the consumer

Chart digitization needs calibration ticks and waypoints. A human can
click them. An agent with vision can place them. It is tempting to let a
producer declare "I need the user to click four ticks" and have the
consumer collect them.

This RFC does **not** add an interaction primitive to OIP, on purpose.

The producer exposes one headless tool that takes the points as
parameters:

```
graphtracer.trace_chart(image_or_region, x_ticks, y_ticks, waypoints, params)
```

Who gathers the points is the consumer's concern. A canvas consumer
collects clicks. An agent consumer reads the image and supplies pixels.
Both call the same headless tool. Keeping the round trip out of the
protocol keeps producers simple and keeps the choice of human or agent
where it belongs, in the consumer.

This is an open question, not a closed door. If several producers need the
same interaction round trip, a later RFC can revisit it.

---

## 6. Compatibility

All three changes are additive. `consumes`, `derived_from`, the `data`
content kind, and recognised `renders` tokens are new optional fields and
new conventional string values. Every 0.2 producer validates unchanged. A
0.2 consumer ignores what it does not recognise and loses no existing
behaviour.

Under the versioning rules in CONTRIBUTING.md this is a minor bump:
`oip_version` 0.3.

---

## 7. Reference producer

`graph-data-extractor` (a chart tracing tool) is the worked reference for
this RFC. It would ship:

- a `consumes: { region_kinds: ["chart"], content_kinds: ["png"] }` block
  and a `produces: { region_kinds: ["chart_series"] }` block,
- a `graphtracer.trace_chart(...)` tool that takes ticks and waypoints and
  writes a `chart_series` region whose `data` JSON follows the `chart`
  contract and whose `source_ref` copies the parent chart region,
- a `ui_hints` entry mapping `chart_series` to `renders: "chart"`,
- an `agent` block telling an agent when a region is a chart worth tracing
  and how to supply ticks and waypoints.

A consumer that ingests a datasheet with its PDF producer, then runs the
chart producer on the chart region, ends with a chart node on screen whose
data is real and whose provenance points at the page and bbox it came
from. The consumer wrote no chart-specific code. It read the manifest.

---

## 8. Open questions

1. `derive` tool naming and whether the parameter is `(slug, region_id)`
   or a fully-qualified region id.
2. Whether `data` JSON shapes belong in `schemas/` (one per recognised
   token) or stay prose contracts in the spec.
3. Whether `derived_from` should allow multiple parents (a region fused
   from several).
4. The interaction round trip from section 5, if real demand appears.

---

## 9. Worked `data` file

`content/lkh-pump_p4-chart-seriesB.json` for the `chart` token:

```json
{
  "x_label": "Q (m3/h)",
  "y_label": "H (m)",
  "x_scale": "linear",
  "y_scale": "linear",
  "series": [
    {
      "label": "LKH-85",
      "points": [[0, 94], [50, 95], [100, 95], [150, 94],
                 [200, 91], [250, 86], [300, 80], [350, 68], [400, 50]]
    }
  ]
}
```
