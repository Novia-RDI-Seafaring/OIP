# Agent guidance — Novia-RDI-Seafaring/OIP

OIP (Open Ingestion Protocol) is a **specification repo first, code repo
second**. Treat the spec as the artefact; the Python package is just a
convenient way to ship it.

## What this repo is

- **`SPEC.md`** — the protocol. Source of truth.
- **`schemas/`** — JSON Schemas mirroring SPEC.md.
- **`examples/`** — concrete worked examples.
- **`CHECKLIST.md`** — implementer's go/no-go list.
- **`packages/oip/`** — Python CLI (`uvx oip`) that ships the above as
  data, plus a validator and a project scaffolder.

If you change `SPEC.md`, you almost certainly also need to change
`schemas/`, `CHECKLIST.md`, and `packages/oip/src/oip/_data/` (which
re-bundles the spec for offline `uvx oip` use). They stay in lockstep.

## What this repo is NOT

- Not a producer implementation. Reference producers live in the
  [Anchor v2](https://github.com/Novia-RDI-Seafaring/anchor-kb-ui-RAG)
  repo (`v2/src/anchor/extensions/anchor_pdfs/`,
  `v2/src/anchor/extensions/anchor_fmus/`).
- Not a consumer implementation. Anchor's canvas core (`v2/src/anchor/core/`)
  is the reference consumer.
- Not a runtime. There's no daemon, no DB, no service.

## Working rules

- **Spec changes need motivation.** Open an issue with the rationale
  before editing `SPEC.md`. Editorial fixes (typos, clarifications) can
  be PR'd directly.
- **`oip_version` discipline.** Currently `0.1`. Backward-compatible
  additions bump minor. Breaking changes bump major. Don't bump silently.
- **Bundled data must mirror tracked files.** `packages/oip/src/oip/_data/`
  is currently a copy of the top-level files. If you edit one, sync the
  other. (CI will complain via the validate-example job if it drifts.)
- **No `Co-Authored-By: Claude`** trailer in commits. The user maintains
  this preference across all repos.
- **Use `uv` for Python.** Not `pip`. `uv add`, `uv sync --extra dev`,
  `uv run pytest`.
- **Tests live next to the package.** `packages/oip/tests/`. Run with
  `cd packages/oip && uv run pytest`.

## Common tasks

### Adding a new conventional source-ref kind

1. Update `SPEC.md` "Conventional source-ref kinds" section.
2. Update `CHECKLIST.md` if it references specific kinds.
3. Update `packages/oip/src/oip/_data/spec.md` and `_data/checklist.md`
   to match.
4. Add a test case in `packages/oip/tests/test_validator.py` showing
   the new kind passes validation.
5. Bump `oip_version` to next minor in `packages/oip/src/oip/__init__.py`
   AND in the spec's `oip_version` constant.

### Adding a new CLI subcommand

1. Edit `packages/oip/src/oip/cli.py`.
2. Add a smoke test in `packages/oip/tests/test_cli.py` using
   `typer.testing.CliRunner`.
3. Update `README.md` and `packages/oip/README.md` if it's a notable
   user-facing change.

### Cutting a release

1. Update `CHANGELOG.md` (move `[Unreleased]` → new version).
2. Bump version in `packages/oip/pyproject.toml` AND
   `packages/oip/src/oip/__init__.py`.
3. Tag: `git tag v0.1.1 && git push --tags`.
4. The publish workflow runs on tag push and uploads to PyPI.

## What lives where (1-line tour)

```
SPEC.md                                   # the protocol, RFC-style
CHECKLIST.md                              # implementer's go/no-go
README.md                                 # repo overview
CHANGELOG.md                              # versioned change log
CONTRIBUTING.md                           # PR/issue guidance
LICENSE-MIT, LICENSE-APACHE               # dual license
llms.txt                                  # short LLM-fetchable pointer
schemas/{manifest,document,region}.json   # JSON Schemas
examples/transcriber.json                 # worked example
.github/workflows/ci.yml                  # tests + wheel build
.github/workflows/publish.yml             # PyPI publish on tag
packages/oip/                             # Python CLI package
  pyproject.toml                          # name="oip", scripts=oip
  src/oip/cli.py                          # Typer commands
  src/oip/validator.py                    # validate_data_dir
  src/oip/scaffold.py                     # scaffold_python
  src/oip/_data/                          # bundled spec/schemas/example
  tests/                                  # pytest function-style
```

## When you're stuck

- Spec ambiguity? Read `examples/transcriber.json` — it's the smallest
  thing that exercises the full shape.
- "Is this a MUST or a SHOULD?" → grep `SPEC.md` for the keyword. If
  it's neither, it's currently undefined behaviour.
- Reference consumer behaviour? Read `v2/src/anchor/core/extensions/`
  in the Anchor repo (sibling to this one in the user's filesystem).
