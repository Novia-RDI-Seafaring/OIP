"""Scaffold a starter OIP producer project (Python)."""
from __future__ import annotations

from pathlib import Path


def scaffold_python(target: Path, *, name: str, namespace: str) -> list[Path]:
    """Emit a minimum-viable Python OIP producer skeleton at `target`.

    Returns the list of files written.
    """
    target.mkdir(parents=True)
    pkg_name = name.replace("-", "_")
    written: list[Path] = []

    # pyproject.toml
    pyproject = f'''\
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{name}"
version = "0.1.0"
description = "OIP-compliant producer (replace this description)."
requires-python = ">=3.10"
readme = "README.md"
dependencies = [
    "typer>=0.12",
    "mcp>=1.27.0",
]

[project.scripts]
{name} = "{pkg_name}.cli:app"
{namespace}-mcp = "{pkg_name}.mcp_server:main"

[tool.hatch.build.targets.wheel]
packages = ["src/{pkg_name}"]
'''

    # README
    readme = f'''\
# {name}

An OIP-compliant producer. See https://github.com/<your-org>/oip for the
spec; this scaffold gets you a working skeleton.

## Quick start

```bash
uv pip install -e .

# Register with the system-wide OIP discovery directory
{name} oip install --data-dir ~/{name}-data

# Start the MCP server (stdio)
{namespace}-mcp --data-dir ~/{name}-data
```

## What you need to fill in

1. `src/{pkg_name}/pipeline.py` — your actual ingestion logic
2. `src/{pkg_name}/manifest.py` — declare your source_kinds, region_kinds, source_ref_kinds
3. `src/{pkg_name}/adapter.py` — convert pipeline output → OIP artefacts on disk

The skeleton hands you a working ingest path (with a fake pipeline) so you
can validate end-to-end before swapping in real logic.

## Validate your output

```bash
uvx oip validate ~/{name}-data
```
'''

    # __init__
    init = f'"""OIP producer: {name}."""\n__version__ = "0.1.0"\n'

    # manifest module
    manifest = f'''\
"""OIP manifest for {name}."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

NAME = "{name}"
DISPLAY_NAME = "{name.replace('-', ' ').title()}"
VERSION = "0.1.0"
TOOLS_NAMESPACE = "{namespace}"


def manifest(data_dir: Path) -> dict:
    return {{
        "oip_version": "0.1",
        "producer": {{
            "name": NAME,
            "display_name": DISPLAY_NAME,
            "version": VERSION,
            "homepage": "https://github.com/<your-org>/{name}",
        }},
        "data_dir": str(data_dir.resolve()),
        "produces": {{
            # TODO: list MIME types you can ingest
            "source_kinds": ["text/plain"],
            # TODO: list the region kinds your tool emits
            "region_kinds": ["sample_region"],
            # TODO: list the source_ref kinds your regions use
            "source_ref_kinds": ["{namespace}-anchor"],
        }},
        "invocation": {{
            "kind": "mcp-stdio",
            "command": shutil.which("{namespace}-mcp") or "{namespace}-mcp",
            "args": ["--data-dir", str(data_dir.resolve())],
            "tools_namespace": TOOLS_NAMESPACE,
        }},
        "ui_hints": {{
            "node_types": [
                {{"name": f"{{TOOLS_NAMESPACE}}:sample", "renders": "TODO describe this node"}},
            ],
        }},
    }}


def write_manifest(data_dir: Path) -> Path:
    """Write the manifest at <data_dir>/manifest.json."""
    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / "manifest.json"
    target.write_text(json.dumps(manifest(data_dir), indent=2))
    return target
'''

    # adapter module — turns your pipeline output into OIP artefacts
    adapter = f'''\
"""Translate pipeline output → OIP-shaped artefacts on disk.

Replace the `_dummy_run` body with calls into your actual pipeline.
The `write_oip_artefacts` shape is fixed by OIP and shouldn't change.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


def write_oip_artefacts(source_path: Path, *, data_dir: Path, slug: str | None = None) -> dict:
    """Run the pipeline and write OIP artefacts. Returns a summary dict."""
    slug = slug or _slugify(source_path.stem)
    sources = data_dir / "sources" / slug
    artefacts = data_dir / "artefacts" / slug
    content = artefacts / "content"
    sources.mkdir(parents=True, exist_ok=True)
    content.mkdir(parents=True, exist_ok=True)

    # Stash a copy/symlink of the source
    target_source = sources / source_path.name
    if not target_source.exists():
        try:
            target_source.symlink_to(source_path.resolve())
        except OSError:
            target_source.write_bytes(source_path.read_bytes())

    # TODO: replace this with your actual pipeline run
    items = _dummy_run(source_path)

    # document.json
    document = {{
        "slug": slug,
        "title": source_path.stem,
        "source_kind": "text/plain",
        "source_path": f"sources/{{slug}}/{{source_path.name}}",
        "source_url": None,
        "ingested_at": _utcnow_iso(),
        "ingested_by": f"{name}/0.1.0",
        "size_units": {{"item_count": len(items)}},
        "tags": [],
        "extras": {{}},
    }}
    (artefacts / "document.json").write_text(json.dumps(document, indent=2))

    # regions.json
    regions = []
    for i, item in enumerate(items):
        rid = f"{{slug}}:r{{i:04d}}"
        text_path = content / f"{{rid.replace(':', '_')}}.txt"
        text_path.write_text(item["text"])
        regions.append({{
            "id": rid,
            "kind": "sample_region",
            "title": item["text"][:60],
            "description": item["text"],
            "source_ref": {{
                "kind": "{namespace}-anchor",
                "index": i,
            }},
            "content": {{"text": str(text_path.relative_to(artefacts))}},
            "tags": [],
            "entities": [],
        }})
    (artefacts / "regions.json").write_text(json.dumps(regions, indent=2))

    return {{"slug": slug, "region_count": len(regions)}}


# ── replace this with your actual pipeline ────────────────────────────


def _dummy_run(source_path: Path) -> list[dict]:
    """A placeholder pipeline. Reads lines from a text file."""
    if not source_path.exists():
        return [{{"text": "(no source)"}}]
    return [{{"text": line.strip()}} for line in source_path.read_text().splitlines() if line.strip()]


def _slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower() or "doc"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
'''

    # MCP server
    mcp_server = f'''\
"""`{namespace}-mcp` — stdio MCP server. Implements the OIP minimum tool surface."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from {pkg_name}.adapter import write_oip_artefacts
from {pkg_name}.manifest import write_manifest

logger = logging.getLogger(__name__)
_DATA_DIR: Path = Path("./data")

app = Server("{name}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="{namespace}.ingest",
            description="Ingest a source file. Writes OIP artefacts under data_dir.",
            inputSchema={{"type": "object",
                          "properties": {{"source_path": {{"type": "string"}},
                                          "slug": {{"type": "string"}}}},
                          "required": ["source_path"]}},
        ),
        Tool(
            name="{namespace}.list_documents",
            description="List every ingested document.",
            inputSchema={{"type": "object", "properties": {{}}}},
        ),
        Tool(
            name="{namespace}.get_document",
            description="Return one document.json by slug.",
            inputSchema={{"type": "object",
                          "properties": {{"slug": {{"type": "string"}}}},
                          "required": ["slug"]}},
        ),
        Tool(
            name="{namespace}.get_regions",
            description="Return regions for a document.",
            inputSchema={{"type": "object",
                          "properties": {{"slug": {{"type": "string"}}}},
                          "required": ["slug"]}},
        ),
        Tool(
            name="{namespace}.get_region_content",
            description="Return text/markdown content for one region.",
            inputSchema={{"type": "object",
                          "properties": {{"region_id": {{"type": "string"}},
                                          "format": {{"type": "string",
                                                      "enum": ["text", "markdown"],
                                                      "default": "text"}}}},
                          "required": ["region_id"]}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        text = await asyncio.to_thread(_dispatch, name, arguments)
    except Exception as exc:  # noqa: BLE001
        text = json.dumps({{"error": str(exc)}})
    return [TextContent(type="text", text=text)]


def _dispatch(name: str, args: dict) -> str:
    if name == "{namespace}.ingest":
        path = Path(args["source_path"]).resolve()
        if not path.exists():
            return json.dumps({{"error": f"not found: {{path}}"}})
        summary = write_oip_artefacts(path, data_dir=_DATA_DIR, slug=args.get("slug"))
        write_manifest(_DATA_DIR)  # refresh manifest in case kinds changed
        return json.dumps(summary, indent=2)
    if name == "{namespace}.list_documents":
        artefacts = _DATA_DIR / "artefacts"
        if not artefacts.is_dir():
            return json.dumps([])
        return json.dumps([
            json.loads((d / "document.json").read_text())
            for d in sorted(artefacts.iterdir())
            if (d / "document.json").exists()
        ], indent=2)
    if name == "{namespace}.get_document":
        p = _DATA_DIR / "artefacts" / args["slug"] / "document.json"
        return p.read_text() if p.exists() else json.dumps({{"error": "not found"}})
    if name == "{namespace}.get_regions":
        p = _DATA_DIR / "artefacts" / args["slug"] / "regions.json"
        return p.read_text() if p.exists() else json.dumps({{"error": "not found"}})
    if name == "{namespace}.get_region_content":
        rid = args["region_id"]
        slug = rid.split(":", 1)[0]
        suffix = ".md" if args.get("format") == "markdown" else ".txt"
        path = _DATA_DIR / "artefacts" / slug / "content" / (rid.replace(":", "_") + suffix)
        return path.read_text() if path.exists() else json.dumps({{"error": "not found"}})
    return json.dumps({{"error": f"unknown tool: {{name}}"}})


def main() -> None:
    global _DATA_DIR
    parser = argparse.ArgumentParser(description="{name} MCP (stdio) — OIP-compliant")
    parser.add_argument("--data-dir", "-d", default="./data")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    _DATA_DIR = Path(args.data_dir).resolve()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    async def _run():
        write_manifest(_DATA_DIR)
        async with stdio_server() as (read, write):
            await app.run(read, write, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
'''

    # CLI module — provides `<name> oip install`
    cli = f'''\
"""User-facing CLI for {name}."""
from __future__ import annotations

import json
import os
from pathlib import Path

import typer

app = typer.Typer(help="{name} — OIP-compliant ingestion producer.")
oip_app = typer.Typer(help="OIP integration: register with consumers like Anchor.")
app.add_typer(oip_app, name="oip")


@oip_app.command("install")
def oip_install(
    data_dir: Path = typer.Option(Path.home() / "{name}-data", "--data-dir", "-d"),
    print_only: bool = typer.Option(False, "--print", help="Emit manifest to stdout, don't write."),
):
    """Register this producer's manifest with the system-wide OIP discovery dir."""
    from {pkg_name}.manifest import manifest, NAME

    m = manifest(data_dir)
    if print_only:
        typer.echo(json.dumps(m, indent=2))
        return

    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "manifest.json").write_text(json.dumps(m, indent=2))

    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    target_dir = base / "oip" / "producers.d"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{{NAME}}.json"
    target.write_text(json.dumps(m, indent=2))

    typer.echo(f"registered → {{target}}")
    typer.echo(f"data_dir   → {{data_dir}}")


if __name__ == "__main__":
    app()
'''

    files = {
        "pyproject.toml": pyproject,
        "README.md": readme,
        f"src/{pkg_name}/__init__.py": init,
        f"src/{pkg_name}/manifest.py": manifest,
        f"src/{pkg_name}/adapter.py": adapter,
        f"src/{pkg_name}/mcp_server.py": mcp_server,
        f"src/{pkg_name}/cli.py": cli,
    }

    for rel, content in files.items():
        full = target / rel
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
        written.append(full)

    return written
