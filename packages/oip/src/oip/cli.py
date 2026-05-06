"""`oip` — the OIP toolkit CLI.

All commands work without any setup beyond `uv tool install` or `uvx`.
Run `oip --help` for the surface.
"""
from __future__ import annotations

import json
import shutil
import sys
from importlib import resources
from pathlib import Path

import typer

from oip import OIP_VERSION, __version__

app = typer.Typer(help="OIP toolkit — spec, schemas, validation, scaffolding.")


# ── data accessors ─────────────────────────────────────────────────────


def _data_dir():
    return resources.files("oip._data")


def _read_data(name: str) -> str:
    return _data_dir().joinpath(name).read_text()


# ── spec / docs ───────────────────────────────────────────────────────


@app.command()
def spec() -> None:
    """Print the full OIP spec to stdout."""
    typer.echo(_read_data("spec.md"))


@app.command()
def checklist() -> None:
    """Print the producer implementer's go/no-go checklist."""
    typer.echo(_read_data("checklist.md"))


@app.command()
def version() -> None:
    """Print versions: oip and the OIP spec it ships."""
    typer.echo(f"oip {__version__}")
    typer.echo(f"oip_version    {OIP_VERSION}")


# ── schemas ───────────────────────────────────────────────────────────


@app.command()
def schema(
    kind: str = typer.Argument(..., help="manifest | document | region"),
) -> None:
    """Print one JSON Schema to stdout."""
    valid = {"manifest", "document", "region"}
    if kind not in valid:
        typer.echo(f"unknown schema: {kind!r}. Valid: {sorted(valid)}", err=True)
        raise typer.Exit(code=1)
    typer.echo(_read_data(f"schemas/{kind}.json"))


@app.command()
def example(
    name: str = typer.Argument("transcriber", help="Example name. Available: transcriber"),
) -> None:
    """Print a complete worked example data-dir tree as JSON."""
    available = {"transcriber"}
    if name not in available:
        typer.echo(f"unknown example: {name!r}. Available: {sorted(available)}", err=True)
        raise typer.Exit(code=1)
    typer.echo(_read_data(f"example.json"))


# ── validate ─────────────────────────────────────────────────────────


@app.command()
def validate(
    data_dir: Path = typer.Argument(..., help="Path to a producer's data dir"),
    strict: bool = typer.Option(False, "--strict", help="Fail on warnings, not just errors"),
) -> None:
    """Validate a producer's output against the OIP schemas.

    Walks the data dir, checks manifest.json, then every artefacts/<slug>/{document,regions}.json
    against the JSON Schemas. Reports errors per-file with line/property path.
    """
    from oip.validator import validate_data_dir

    if not data_dir.exists():
        typer.echo(f"data dir not found: {data_dir}", err=True)
        raise typer.Exit(code=1)

    errors, warnings = validate_data_dir(data_dir)
    for w in warnings:
        typer.echo(f"[warn] {w}", err=True)
    for e in errors:
        typer.echo(f"[err]  {e}", err=True)

    if errors or (strict and warnings):
        typer.echo(f"\nFAILED: {len(errors)} error(s), {len(warnings)} warning(s)", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"OK: {data_dir} is OIP {OIP_VERSION} compliant ({len(warnings)} warnings)")


# ── scaffold ─────────────────────────────────────────────────────────


@app.command()
def new(
    name: str = typer.Argument(..., help="Producer name (lowercase, hyphenated)"),
    lang: str = typer.Option("python", "--lang", "-l", help="python (more later)"),
    namespace: str | None = typer.Option(None, "--namespace", "-n", help="MCP tools namespace; default = derived from name"),
    target: Path = typer.Option(Path.cwd(), "--target", "-t", help="Where to scaffold"),
) -> None:
    """Scaffold a starter OIP producer project.

    Like `cargo new` or `cookiecutter` but for OIP: emits a minimum-viable
    producer skeleton you can fill in.
    """
    import re

    if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
        typer.echo(f"invalid name: {name!r}. Must be lowercase, alphanumeric + hyphens.", err=True)
        raise typer.Exit(code=1)

    ns = namespace or re.sub(r"[^a-z0-9]+", "_", name).strip("_")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", ns):
        typer.echo(f"invalid namespace: {ns!r}", err=True)
        raise typer.Exit(code=1)

    if lang != "python":
        typer.echo(f"unsupported lang: {lang!r}. Only 'python' is implemented today.", err=True)
        raise typer.Exit(code=1)

    out = target / name
    if out.exists():
        typer.echo(f"refusing to overwrite existing path: {out}", err=True)
        raise typer.Exit(code=1)

    from oip.scaffold import scaffold_python

    written = scaffold_python(out, name=name, namespace=ns)
    typer.echo(f"scaffolded {len(written)} files at {out}")
    for p in written:
        typer.echo(f"  + {p.relative_to(out)}")
    typer.echo("")
    typer.echo("Next:")
    typer.echo(f"  cd {out}")
    typer.echo("  uv pip install -e .")
    typer.echo(f"  {ns}-mcp --data-dir ./data")
    typer.echo("")
    typer.echo("Then validate your output:")
    typer.echo("  oip validate ./data")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
