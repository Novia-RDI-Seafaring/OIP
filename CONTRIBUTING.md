# Contributing to OIP

Thanks for considering a contribution. OIP's value depends on a wide
spread of producers and consumers implementing the same shape; every
implementation, comment, divergent fork, and PR makes the spec stronger.

## Where things live

- **`SPEC.md`** — the protocol specification. Changes to this file are the
  most consequential; please open an issue first to discuss.
- **`schemas/`** — JSON Schemas for `manifest.json`, `document.json`,
  `region`. Keep these in sync with the spec.
- **`examples/`** — concrete worked examples. PRs adding new examples for
  new source kinds (audio, video, code, web, ...) very welcome.
- **`packages/oip/`** — the Python CLI (`uvx oip ...`). Validators,
  scaffolding, schema lookup.
- **`CHECKLIST.md`** — implementer's go/no-go list. Should mirror SPEC.md
  exactly.

## Spec changes

The spec is versioned by `oip_version` (e.g. `0.1`). Changes are categorised:

- **Editorial** — clarifications, examples, fixed typos. No version bump.
- **Backward-compatible additions** — new optional fields, new SHOULDs,
  new conventional source-ref kinds. Bump minor.
- **Breaking changes** — anything that invalidates existing producer
  output. Bump major.

Open a GitHub issue tagged `spec` to propose a change. Discuss before PR.

## Implementation changes (`packages/oip/`)

Standard PR flow:

1. Fork + branch from `main`.
2. Add tests for new behaviour. We use pytest, function-style.
3. Run `uv run pytest` locally; CI must pass.
4. Open a PR with a short summary of the change and motivation.

## Reference implementation (Anchor)

[Anchor](https://github.com/Novia-RDI-Seafaring/anchor-kb-ui-RAG) is the
first reference consumer of OIP. Its `v2/` codebase has bundled producers
(PDF, FMU). Bug reports against Anchor's OIP behaviour are welcome there;
issues with the spec or the toolkit belong here.

## Code of conduct

Be kind. Assume good faith. Critique ideas, not people. The full text
follows the Contributor Covenant 2.1.

## License of contributions

By submitting a contribution, you agree that it may be distributed under
either the MIT or Apache-2.0 license at the choice of any downstream
user, matching the dual-license of the repo.

## Questions

Open an issue. The spec is community-versioned, not Anchor-versioned —
your input shapes 1.0.
