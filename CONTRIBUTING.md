# Contributing to OIP

Thanks for your interest. OIP's value depends on a wide spread of
producers and consumers implementing the same shape; every
implementation, comment, divergent fork, and PR makes the spec stronger.

This file is the human-facing contributor guide. The agent-facing rules
live in [`AGENTS.md`](./AGENTS.md); both files agree.

## Reporting bugs and security issues

- **Regular bug or feature request:** open a GitHub issue. Include
  what you did, what happened, what you expected, and the relevant
  output. Logs and minimal reproductions land patches faster than
  prose.
- **Security vulnerability:** do NOT open a public issue. Use the
  GitHub private advisory flow described in
  [`SECURITY.md`](./SECURITY.md). Encrypted, audit-trailed,
  coordinated disclosure.

## What this repo is

OIP is a **specification repo first, code repo second**. The protocol
itself is the artefact; the Python package is a convenient way to ship
it.

| Path | Role |
| --- | --- |
| `SPEC.md` | The protocol. Source of truth. |
| `CHECKLIST.md` | Implementer's go/no-go list. Mirrors SPEC.md. |
| `schemas/` | JSON Schemas for `manifest.json`, `document.json`, `region`. |
| `examples/` | Concrete worked examples (e.g. `transcriber.json`). |
| `packages/oip/` | Python toolkit: `uvx oip` CLI + validator + scaffolder. |
| `packages/oip/src/oip/_data/` | Bundled copy of the spec + schemas, served at runtime. |

## The lockstep rule

If you change `SPEC.md`, you almost certainly also need to change:

- `CHECKLIST.md` (if the new behaviour gates implementer acceptance),
- `schemas/*.json` (if the wire shape changed),
- `packages/oip/src/oip/_data/spec.md`, `_data/checklist.md`,
  `_data/schemas/*.json` (these are the bundled copies the toolkit
  ships in the wheel; they must equal the top-level files
  byte-for-byte),
- and add or update a test under `packages/oip/tests/`.

CI enforces the bundled-data mirror with a `diff -u` step. PRs that
break the mirror don't merge. This rule exists because the toolkit is
the most likely thing an agent will actually consume; if `uvx oip spec`
lies about the protocol, the spec might as well not exist.

## Development setup

```bash
git clone https://github.com/Novia-RDI-Seafaring/OIP
cd OIP/packages/oip
uv sync --extra dev          # installs typer, jsonschema, pytest, ruff
```

Run the tests:

```bash
cd packages/oip
uv run --extra dev pytest -q
uv run --extra dev ruff check src tests
```

Try the toolkit locally:

```bash
cd packages/oip
uv run oip --help
uv run oip spec
uv run oip validate ../../examples/  # validate the bundled example
```

## Workflow

The repo is **trunk-based**: one long-lived branch (`main`), short-lived
feature branches off it, every change through a pull request. There is
no `develop` / `dev` branch. Never force-push to `main`.

### 1. Branch

Name the branch by what the change is:

| Prefix | For |
| --- | --- |
| `feat/<topic>` | new functionality |
| `fix/<topic>` | bug fixes |
| `docs/<topic>` | docs, README, CHANGELOG, asset prose |
| `chore/<topic>` | tooling, CI, dependencies, plumbing |
| `refactor/<topic>` | internal restructuring without behaviour change |
| `test/<topic>` | tests only |
| `spec/<topic>` | spec changes (open an issue first to discuss) |

### 2. Make the change

Keep PRs focused. One coherent change per PR is easier to review and
easier to revert if needed.

For toolkit changes, run `uv run --extra dev pytest -q` locally.
For spec changes, follow the lockstep rule above and verify the bundled
data still matches with `diff -u SPEC.md packages/oip/src/oip/_data/spec.md`.

### 3. Spec change rules

`SPEC.md` is versioned by `oip_version` (e.g. `0.2`). Changes fall into
three categories:

- **Editorial** — clarifications, examples, fixed typos. No version bump.
- **Backward-compatible additions** — new optional fields, new SHOULDs,
  new conventional source-ref kinds. Bump minor.
- **Breaking changes** — anything that invalidates existing producer
  output. Bump major.

Open a GitHub issue tagged `spec` to propose any non-editorial change.
Discuss before PR. The version line in `SPEC.md` is bumped per these
rules (semver — major bumps for breaking changes only).

### 4. Commits and PR title

Use [Conventional Commits](https://www.conventionalcommits.org/) for
both commit messages and the PR title:

- `feat: short description`
- `feat(spec): short description`
- `fix(validator): short description`
- `docs(readme): short description`
- `chore(deps): bump X from Y to Z`
- `refactor: short description`

The release pipeline groups changelog entries by these prefixes.

**Do not add `Co-Authored-By: Claude`** (or any AI-assistant trailer)
to commits. The user maintains this preference across all related
repos.

### 5. Open the PR

Target `main`. Fill in the template. CI must pass before the PR can
merge:

- `python` — pytest under `packages/oip/`
- `schemas + bundled data` — JSON Schema validity, lockstep mirror,
  end-to-end validation of the worked example
- `platform smoke (macos-latest)`, `platform smoke (windows-latest)` —
  the CLI launches on Mac and Windows
- `supply-chain audit` — Dependency Review
- `analyze (python)` — CodeQL

If your PR ends up behind `main` while it's waiting for review, use
**`gh pr update-branch <pr-number>`** (or click "Update branch" in
the GitHub UI). This merges main into the PR via the GitHub API and
re-runs CI on the merge commit. **Do not rebase and force-push** —
the discipline is to keep the PR's commit history stable so review
comments stay attached to the right commits.

### 6. Merge

Squash-merge is the default. The squash collapses the PR's commits
into one Conventional-Commit entry on `main`, which is what the
changelog and release notes ingestion expects.

```bash
gh pr merge <number> --squash --delete-branch
```

## What never goes on a pushed branch

- `git push --force` or `--force-with-lease`
- `git reset --hard` followed by push
- `git rebase main && git push --force-with-lease` to update a PR

Branch protection blocks the worst cases on `main`. The rules above
also apply to feature branches that have an open PR — the CI runs,
review comments, and audit trail depend on commit hashes staying
stable. If a rewrite is genuinely needed, get explicit OK from a
maintainer first.

## Releasing

Maintainers only. See [`PUBLISHING.md`](./PUBLISHING.md). Short
version: bump the version in `packages/oip/pyproject.toml` and
`packages/oip/src/oip/__init__.py`, move the `[Unreleased]` section in
`CHANGELOG.md` to a new version heading, commit on a release PR, merge,
then tag `vX.Y.Z` and push the tag. The release workflow handles the
PyPI publish (OIDC trusted publishing, no token in the repo) and the
GitHub Release.

## Reference implementations

[Anchor](https://github.com/Novia-RDI-Seafaring/anchor-kb-ui-RAG) is the
first reference consumer of OIP. Its `v2/` codebase has bundled producers
(PDF medallion, FMU inspector). Bug reports against Anchor's OIP
behaviour are welcome there; issues with the spec or the toolkit belong
here.

## Style notes

- **Prose.** Match the voice of the existing README and SPEC.
  Short sentences. Active second-person. One claim per sentence.
  Periods over em-dashes. Skip marketing intensifiers and bolded
  summary claims.
- **Code comments.** Don't narrate what the code does — well-named
  identifiers handle that. Comments earn their place when they
  capture non-obvious *why*: a hidden constraint, a workaround for
  a specific bug, behaviour that would surprise a reader.

## Code of conduct

Be kind. Assume good faith. Critique ideas, not people. The full text
follows the Contributor Covenant 2.1.

## License of contributions

By submitting a contribution, you agree that it may be distributed under
either the MIT or Apache-2.0 license at the choice of any downstream
user, matching the dual-license of the repo.

## Questions

Open a discussion or an issue. The spec is community-versioned, not
Anchor-versioned — your input shapes 1.0.
