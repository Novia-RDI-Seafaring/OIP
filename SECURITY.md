# Security policy

## Reporting a vulnerability

If you find a vulnerability in OIP, please **do not open a public
GitHub issue**. Instead, use one of these channels:

- **Preferred:** [GitHub private security advisory](https://github.com/Novia-RDI-Seafaring/OIP/security/advisories/new) — coordinated disclosure, encrypted, audit-trailed.
- **Email:** `security@novia.fi` (or the maintainer addresses listed in
  the `authors` field of [`packages/oip/pyproject.toml`](./packages/oip/pyproject.toml))
  — encrypt with the maintainer's public key if posting anything sensitive.

We will acknowledge within **3 business days** and aim to have a fix or
mitigation discussed within **14 days**. Critical vulnerabilities that
allow remote code execution, data exfiltration, or privilege escalation
get same-day attention.

## What's in scope

- The **`oip` Python package** published to PyPI, including its CLI
  (`uvx oip`, `oip validate`, `oip new`, ...).
- The **OIP specification** documents shipped from this repo:
  `SPEC.md`, `CHECKLIST.md`, the JSON Schemas under `schemas/`, and the
  worked examples under `examples/`.
- The bundled `_data/` copies under `packages/oip/src/oip/_data/` that
  the toolkit serves at runtime.

## What's out of scope

- **Producer implementations.** OIP-conforming PDF / FMU / transcriber /
  etc. tools live in their own repos (the reference producers are in
  [Anchor v2](https://github.com/Novia-RDI-Seafaring/anchor-kb-ui-RAG)).
  Report issues there.
- **Consumer implementations.** Same applies — report against the
  consumer's own repo (e.g. Anchor's canvas).
- **Vulnerabilities in third-party validators or schemas-libraries**
  (`jsonschema`, `typer`, ...) — report upstream and we will bump the
  pin once they patch.

## Security model

OIP is a **spec + toolkit**, not a service. The `oip` CLI operates
strictly on local files and never opens a network port. There is no
daemon, no DB, no server. The threat model is therefore narrow:

- `oip validate <dir>` reads JSON from the path you point it at — keep
  the same hygiene you would for any local-input parser.
- `oip new <name>` writes a scaffolded project tree under a target
  directory; the package refuses invalid names and existing targets
  defensively.
- The bundled spec/schemas/example content is read-only and lives
  inside the wheel.

If you embed the `oip.validator` module inside a larger service that
exposes it to untrusted input over the network, the security posture
becomes that of your service, not of OIP. We don't ship a hardened
network-facing surface.

## Supply chain

Defences against bad-dependency attacks (npm typosquats, PyPI account
compromises, etc.):

- **Lockfile** (`packages/oip/uv.lock`) is authoritative and
  frozen-installed in CI.
- **Renovate cooldown** (`renovate.json`): runtime deps must be at
  least 7 days old, GitHub Actions 14 days, majors 30 days. Catches
  the 0-7-day window where a compromised version is live but not yet
  yanked.
- **Dependency Review** action blocks PRs that introduce known-vulnerable
  deps or deps under deny-listed licences.
- **CodeQL** scans the toolkit's own Python code on every PR + weekly.
- **PyPI trusted publishing (OIDC)** — there is no long-lived PyPI
  token in the repo, in GitHub secrets, or on maintainer laptops. The
  publish-time OIDC token is scoped to the exact workflow file and
  expires in minutes. SLSA provenance attestation is generated
  automatically.
- **GitHub Environment protection** on the `pypi` environment requires
  a second-human approval and a wait timer before any publish job
  runs. See [`PUBLISHING.md`](./PUBLISHING.md) for the configuration.
- **OpenSSF Scorecard** signal is consulted by the dependency-review
  step at level 3.
- **Hardware 2FA** is required on every account with publish or admin
  privileges.

If you operate the `oip` toolkit in a regulated environment that needs
an SBOM, the published wheel includes provenance metadata; a CycloneDX
SBOM can be generated locally with `uv run cyclonedx-py environment`.

## Disclosure

Public advisories are filed in the
[GitHub Security Advisories tab](https://github.com/Novia-RDI-Seafaring/OIP/security/advisories)
and mirrored to the PyPI advisory feed. We aim to disclose within 90
days of initial report or 7 days after a fix lands, whichever comes
first.
