# oip — Open Ingestion Protocol toolkit

The `oip` CLI ships the OIP specification, JSON schemas, validation, and
producer scaffolding. Drop-in via `uvx oip <command>` or `uv tool install oip`.

```bash
uvx oip spec                    # full SPEC.md to stdout
uvx oip schema manifest         # JSON Schema for manifest.json
uvx oip schema document
uvx oip schema region
uvx oip example                 # complete worked example
uvx oip checklist               # implementer's go/no-go list
uvx oip validate <data-dir>     # check a producer's output
uvx oip new my-tool             # scaffold a starter producer
uvx oip version
```

## What it's for

OIP — the Open Ingestion Protocol — is a vendor-neutral spec for tools
that ingest source material (PDFs, audio, code, web pages, …) and
produce structured, source-grounded knowledge. Any OIP producer can be
read by any OIP consumer.

The spec lives at <https://github.com/Novia-RDI-Seafaring/OIP>. This
package is its CLI face — runnable from anywhere via `uvx`.

## Implementing a producer? Start here

```bash
# 1. Read the spec + checklist
uvx oip spec | less
uvx oip checklist

# 2. Scaffold a starter
uvx oip new my-tool --lang=python
cd my-tool
uv pip install -e .

# 3. Fill in your pipeline (see src/my_tool/adapter.py)
# 4. Run + validate
my-tool oip install --data-dir ./data
my-tool oip install --print  # preview the manifest
uvx oip validate ./data
```

## License

MIT OR Apache-2.0.
