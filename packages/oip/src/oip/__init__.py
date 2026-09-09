"""OIP — Open Ingestion Protocol — for agents.

A small, vendor-neutral toolkit for agents (and humans) implementing
OIP-compliant producers. Ships the spec, JSON Schemas, a worked example,
starter code, and a validator.

Usage from anywhere via `uv`:
    uvx oip spec
    uvx oip schema manifest
    uvx oip validate ./my-data-dir
"""
import re as _re
from importlib import resources as _resources
from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("oip")
except _PackageNotFoundError:  # running from a checkout without an install
    __version__ = "0.0.0+unknown"


def _spec_version() -> str:
    """Parse the OIP spec version from the bundled spec's title line.

    The spec file is the single source of the protocol version: `oip spec`
    prints it and this constant is read from it, so the CLI's reported
    version cannot drift from the spec it ships.
    """
    title = (
        _resources.files("oip._data").joinpath("spec.md").read_text().split("\n", 1)[0]
    )
    match = _re.search(r"\(v(\d+\.\d+(?:\.\d+)?)\)", title)
    if match is None:
        raise RuntimeError(f"no spec version in the bundled spec's title: {title!r}")
    return match.group(1)


OIP_VERSION = _spec_version()
