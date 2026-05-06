"""Tests for the OIP validator."""
from __future__ import annotations

import json
from pathlib import Path

from oip.validator import validate_data_dir


def _write_minimal_data_dir(root: Path) -> None:
    """Build a minimum-valid OIP data dir for happy-path testing."""
    manifest = {
        "oip_version": "0.1",
        "producer": {"name": "test-producer", "version": "0.1.0"},
        "data_dir": str(root),
        "produces": {
            "source_kinds": ["text/plain"],
            "region_kinds": ["sample"],
            "source_ref_kinds": ["test-anchor"],
        },
        "invocation": {
            "kind": "mcp-stdio",
            "command": "test-mcp",
            "tools_namespace": "test",
        },
    }
    (root / "manifest.json").write_text(json.dumps(manifest))

    artefact = root / "artefacts" / "demo"
    (artefact / "content").mkdir(parents=True)
    document = {
        "slug": "demo",
        "title": "Demo",
        "source_kind": "text/plain",
        "ingested_at": "2026-05-06T12:00:00Z",
        "ingested_by": "test/0.1.0",
        "size_units": {"item_count": 1},
    }
    (artefact / "document.json").write_text(json.dumps(document))

    text_path = artefact / "content" / "demo_r0000.txt"
    text_path.write_text("hello")
    regions = [{
        "id": "demo:r0000",
        "kind": "sample",
        "title": "h",
        "description": "hello",
        "source_ref": {"kind": "test-anchor", "index": 0},
        "content": {"text": "content/demo_r0000.txt"},
    }]
    (artefact / "regions.json").write_text(json.dumps(regions))


def test_minimal_valid_data_dir(tmp_path):
    _write_minimal_data_dir(tmp_path)
    errors, warnings = validate_data_dir(tmp_path)
    assert errors == [], f"unexpected errors: {errors}"


def test_missing_manifest_is_error(tmp_path):
    errors, warnings = validate_data_dir(tmp_path)
    assert any("manifest.json" in e for e in errors)


def test_invalid_manifest_json(tmp_path):
    (tmp_path / "manifest.json").write_text("not json {[")
    errors, _ = validate_data_dir(tmp_path)
    assert any("not valid JSON" in e for e in errors)


def test_manifest_missing_required_field(tmp_path):
    bad = {"oip_version": "0.1", "producer": {"name": "x", "version": "1"}}
    # missing data_dir, produces, invocation
    (tmp_path / "manifest.json").write_text(json.dumps(bad))
    errors, _ = validate_data_dir(tmp_path)
    assert any("data_dir" in e or "required" in e.lower() for e in errors)


def test_document_slug_mismatch_is_error(tmp_path):
    _write_minimal_data_dir(tmp_path)
    # tamper with the document slug
    doc_path = tmp_path / "artefacts" / "demo" / "document.json"
    doc = json.loads(doc_path.read_text())
    doc["slug"] = "wrong-slug"
    doc_path.write_text(json.dumps(doc))

    errors, _ = validate_data_dir(tmp_path)
    assert any("doesn't match folder name" in e for e in errors)


def test_undeclared_region_kind_is_warning(tmp_path):
    _write_minimal_data_dir(tmp_path)
    regions_path = tmp_path / "artefacts" / "demo" / "regions.json"
    regions = json.loads(regions_path.read_text())
    regions[0]["kind"] = "totally-new-kind"
    regions_path.write_text(json.dumps(regions))

    errors, warnings = validate_data_dir(tmp_path)
    assert errors == []
    assert any("not in manifest.produces.region_kinds" in w for w in warnings)


def test_duplicate_region_id_is_error(tmp_path):
    _write_minimal_data_dir(tmp_path)
    regions_path = tmp_path / "artefacts" / "demo" / "regions.json"
    regions = json.loads(regions_path.read_text())
    regions.append(dict(regions[0]))  # duplicate
    regions_path.write_text(json.dumps(regions))

    errors, _ = validate_data_dir(tmp_path)
    assert any("duplicate region id" in e for e in errors)


def test_missing_content_path_is_warning(tmp_path):
    _write_minimal_data_dir(tmp_path)
    regions_path = tmp_path / "artefacts" / "demo" / "regions.json"
    regions = json.loads(regions_path.read_text())
    regions[0]["content"]["text"] = "content/does-not-exist.txt"
    regions_path.write_text(json.dumps(regions))

    errors, warnings = validate_data_dir(tmp_path)
    assert errors == []
    assert any("not found at" in w for w in warnings)


def test_no_artefacts_yet_is_warning_not_error(tmp_path):
    """A producer that's installed but hasn't ingested anything is valid."""
    minimal_manifest = {
        "oip_version": "0.1",
        "producer": {"name": "x", "version": "1"},
        "data_dir": str(tmp_path),
        "produces": {"source_kinds": [], "region_kinds": [], "source_ref_kinds": []},
        "invocation": {"kind": "mcp-stdio", "command": "x", "tools_namespace": "x"},
    }
    (tmp_path / "manifest.json").write_text(json.dumps(minimal_manifest))
    errors, warnings = validate_data_dir(tmp_path)
    assert errors == []
    assert any("no artefacts" in w.lower() for w in warnings)
