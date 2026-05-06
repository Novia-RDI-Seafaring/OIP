# OIP — Open Ingestion Protocol

A vendor-neutral specification for **ingestion tools that produce structured, source-grounded knowledge**.

Any tool that conforms to OIP can be consumed by any OIP-aware application — the same way any LSP-compliant language server works in any LSP-aware editor. PDF parsers, audio transcribers, code-region extractors, web crawlers — all interoperate without importing each other.

## What lives here

| Path | What | For |
|------|------|-----|
| [`SPEC.md`](./SPEC.md) | The spec | Humans + LLMs reading the protocol |
| [`llms.txt`](./llms.txt) | Tiny pointer for LLM fetch | An agent in another repo running WebFetch |
| [`CHECKLIST.md`](./CHECKLIST.md) | Producer implementer's go/no-go list | Tooling acceptance criteria |
| [`schemas/`](./schemas/) | JSON Schemas for `manifest.json`, `document.json`, `region` | Programmatic validation |
| [`examples/`](./examples/) | Worked example data dirs | Copy-paste reference |
| [`packages/oip-for-agents/`](./packages/oip-for-agents/) | Python CLI (`uvx oip-for-agents`) | Spec lookup, validation, scaffolding |

## Three ways agents can use OIP

### 1. Read the spec via LLM-fetch

```
WebFetch https://github.com/<org>/oip/raw/main/llms.txt
WebFetch https://github.com/<org>/oip/raw/main/SPEC.md
```

`llms.txt` is short (≤200 lines) and points at the full spec. Most agent harnesses can fetch and read both.

### 2. Run the toolkit via `uvx`

```bash
uvx oip-for-agents spec                  # full spec to stdout
uvx oip-for-agents schema manifest       # JSON Schema for manifest.json
uvx oip-for-agents schema document       # JSON Schema for document.json
uvx oip-for-agents schema region         # JSON Schema for one region
uvx oip-for-agents example transcriber   # full worked example tree
uvx oip-for-agents checklist             # implementer's checklist
uvx oip-for-agents validate <data-dir>   # validate a producer's output
uvx oip-for-agents new my-tool --lang=python   # scaffold a starter producer
```

Wraps everything in this repo as one CLI, no clone required.

### 3. Run an OIP MCP server (planned)

A small MCP server that exposes `oip.spec`, `oip.validate`, `oip.starter` as tools — so agent harnesses pick it up the same way they pick up any other MCP tool. Lands in v0.2.

## What's the relationship to Anchor?

[Anchor](https://github.com/Novia-RDI-Seafaring/anchor-kb-ui-RAG) is the first reference *consumer* of OIP — it has a canvas that aggregates regions from any OIP-compliant producer, regardless of who built that producer. Anchor's PDF medallion pipeline and FMU inspector are the first reference *producers*.

OIP itself is vendor-neutral. Its goal is interop, not Anchor adoption.

## Status

Draft 0.1. Stabilises at 1.0 once at least three independent producers and one external consumer (non-Anchor) are implemented end-to-end. Comments, divergent implementations, and PRs welcome.

## Contributing

The spec is owned by the community. Open issues and PRs against this repo. The version line in `SPEC.md` is bumped per the rules in §10 of the spec (semver — major bumps for breaking changes only).

## License

MIT OR Apache-2.0 — pick whichever fits your downstream.
