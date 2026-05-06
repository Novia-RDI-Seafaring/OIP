"""Smoke tests for the oip CLI."""
from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from oip.cli import app


def _runner():
    return CliRunner()


def test_version_prints_both_versions():
    result = _runner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert "oip" in result.output
    assert "oip_version" in result.output
    assert "0.1" in result.output


def test_spec_emits_markdown():
    result = _runner().invoke(app, ["spec"])
    assert result.exit_code == 0
    assert "OIP" in result.output
    assert "manifest.json" in result.output


def test_checklist_emits():
    result = _runner().invoke(app, ["checklist"])
    assert result.exit_code == 0
    assert "checklist" in result.output.lower()
    assert "manifest.json" in result.output


def test_schema_manifest():
    result = _runner().invoke(app, ["schema", "manifest"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["title"] == "OIP manifest.json"


def test_schema_document():
    result = _runner().invoke(app, ["schema", "document"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["title"] == "OIP document.json"


def test_schema_region():
    result = _runner().invoke(app, ["schema", "region"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["title"] == "OIP region"


def test_schema_unknown_fails():
    result = _runner().invoke(app, ["schema", "bogus"])
    assert result.exit_code != 0


def test_example_emits_json():
    result = _runner().invoke(app, ["example"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "files" in payload


def test_new_scaffold_emits_files(tmp_path):
    result = _runner().invoke(app, ["new", "demo-tool", "--target", str(tmp_path)])
    assert result.exit_code == 0
    out = tmp_path / "demo-tool"
    assert (out / "pyproject.toml").is_file()
    assert (out / "README.md").is_file()
    assert (out / "src" / "demo_tool" / "__init__.py").is_file()
    assert (out / "src" / "demo_tool" / "manifest.py").is_file()
    assert (out / "src" / "demo_tool" / "adapter.py").is_file()
    assert (out / "src" / "demo_tool" / "mcp_server.py").is_file()
    assert (out / "src" / "demo_tool" / "cli.py").is_file()


def test_new_refuses_invalid_name(tmp_path):
    result = _runner().invoke(app, ["new", "BadName", "--target", str(tmp_path)])
    assert result.exit_code != 0


def test_new_refuses_existing_target(tmp_path):
    (tmp_path / "demo").mkdir()
    result = _runner().invoke(app, ["new", "demo", "--target", str(tmp_path)])
    assert result.exit_code != 0


def test_validate_on_freshly_scaffolded_starter(tmp_path):
    """End-to-end: scaffold a starter, run its mcp_server logic to write
    artefacts, then validate them. Today we can't actually run the
    starter (would need to install + invoke), so we just confirm the
    scaffold emits + nothing crashes."""
    result = _runner().invoke(app, ["new", "demo", "--target", str(tmp_path)])
    assert result.exit_code == 0
