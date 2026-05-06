"""Validate a producer's data dir against the OIP schemas."""
from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema


def _load_schema(name: str) -> dict[str, Any]:
    path = resources.files("oip._data").joinpath(f"schemas/{name}.json")
    return json.loads(path.read_text())


def validate_data_dir(data_dir: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        errors.append(f"missing manifest.json at {manifest_path}")
        return errors, warnings

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"manifest.json is not valid JSON: {e}")
        return errors, warnings

    manifest_schema = _load_schema("manifest")
    for err in jsonschema.Draft202012Validator(manifest_schema).iter_errors(manifest):
        errors.append(f"manifest.json: {err.message} (at {'/'.join(map(str, err.absolute_path)) or 'root'})")

    declared_region_kinds = set(manifest.get("produces", {}).get("region_kinds", []))
    declared_source_ref_kinds = set(manifest.get("produces", {}).get("source_ref_kinds", []))

    artefacts_dir = data_dir / "artefacts"
    if not artefacts_dir.is_dir():
        warnings.append(f"no artefacts/ directory — producer hasn't ingested anything yet")
        return errors, warnings

    document_schema = _load_schema("document")
    region_schema = _load_schema("region")

    slug_count = 0
    for slug_dir in sorted(artefacts_dir.iterdir()):
        if not slug_dir.is_dir():
            continue
        slug_count += 1
        slug = slug_dir.name

        # document.json
        doc_path = slug_dir / "document.json"
        if not doc_path.exists():
            errors.append(f"artefacts/{slug}/document.json missing")
            continue
        try:
            document = json.loads(doc_path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"artefacts/{slug}/document.json: invalid JSON: {e}")
            continue
        for err in jsonschema.Draft202012Validator(document_schema).iter_errors(document):
            errors.append(f"artefacts/{slug}/document.json: {err.message}")
        if document.get("slug") != slug:
            errors.append(f"artefacts/{slug}/document.json: slug={document.get('slug')!r} doesn't match folder name {slug!r}")

        # regions.json
        regions_path = slug_dir / "regions.json"
        if not regions_path.exists():
            errors.append(f"artefacts/{slug}/regions.json missing")
            continue
        try:
            regions = json.loads(regions_path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"artefacts/{slug}/regions.json: invalid JSON: {e}")
            continue
        if not isinstance(regions, list):
            errors.append(f"artefacts/{slug}/regions.json: expected a JSON array, got {type(regions).__name__}")
            continue

        seen_ids = set()
        for i, region in enumerate(regions):
            for err in jsonschema.Draft202012Validator(region_schema).iter_errors(region):
                errors.append(f"artefacts/{slug}/regions.json[{i}]: {err.message}")
            rid = region.get("id")
            if rid in seen_ids:
                errors.append(f"artefacts/{slug}/regions.json[{i}]: duplicate region id {rid!r}")
            seen_ids.add(rid)

            kind = region.get("kind")
            if kind and declared_region_kinds and kind not in declared_region_kinds:
                warnings.append(
                    f"artefacts/{slug}/regions.json[{i}]: kind={kind!r} not in manifest.produces.region_kinds"
                )
            sref = region.get("source_ref", {})
            sref_kind = sref.get("kind") if isinstance(sref, dict) else None
            if sref_kind and declared_source_ref_kinds and sref_kind not in declared_source_ref_kinds:
                warnings.append(
                    f"artefacts/{slug}/regions.json[{i}]: source_ref.kind={sref_kind!r} not in manifest.produces.source_ref_kinds"
                )

            content = region.get("content") or {}
            for content_field, rel_path in content.items():
                if isinstance(rel_path, str):
                    full_path = slug_dir / rel_path
                    if not full_path.exists():
                        warnings.append(
                            f"artefacts/{slug}/regions.json[{i}].content.{content_field}: "
                            f"path {rel_path!r} not found at {full_path}"
                        )

    if slug_count == 0:
        warnings.append("artefacts/ contains no slugs — producer hasn't ingested anything yet")

    return errors, warnings
