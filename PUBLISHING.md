# Publishing OIP releases

This file documents how to ship a new `oip` release to PyPI. After the
first manual publish, every subsequent release is automated: push a
`v*` tag, GitHub Actions does the rest.

## One-time setup

### 1. Reserve the name on PyPI (manual, ~5 minutes)

You need a PyPI account with **two-factor authentication enabled** (a
hard requirement for new uploads since 2024). Sign in at
<https://pypi.org/account/login/>.

From the package directory (`packages/oip/`), with the working tree
clean and on the tag you want to release (start with `v0.2.0`):

```bash
cd packages/oip
uv build
# → dist/oip-0.2.0-py3-none-any.whl
# → dist/oip-0.2.0.tar.gz

# Publish. uv will prompt for a PyPI API token.
# Create one at: https://pypi.org/manage/account/token/
# Scope: "Entire account" for the first publish, then narrow to
# "Project: oip" for subsequent ones (until trusted publishing is on).
uv publish
```

After the first publish, `pip install oip` and `uv tool install oip`
both work globally.

### 2. Configure PyPI trusted publishing (no token needed afterwards)

This is the modern PyPA-recommended pattern: GitHub Actions
authenticates to PyPI using OIDC, no API token sits in the repo or in
secrets storage.

On PyPI:

1. Go to <https://pypi.org/manage/project/oip/settings/publishing/>
2. Add a trusted publisher with:
   - **Owner:** `Novia-RDI-Seafaring`
   - **Repository name:** `OIP`
   - **Workflow filename:** `release.yml`
   - **Environment name:** `pypi`
3. On GitHub: repo → Settings → Environments → New environment → name
   it `pypi`. Configure these defence-in-depth gates:
   - **Required reviewers:** add at least one human reviewer (ideally
     two). A successful tag push then pauses the publish job until a
     reviewer approves. A compromised maintainer account alone cannot
     ship a poisoned wheel — the attacker would also need to compromise
     the reviewer.
   - **Wait timer:** `10` minutes. Gives you a window after a tag is
     pushed to notice the email/notification and revoke before the
     publish actually fires.
   - **Deployment branches and tags:** Selected — only allow `main`
     and tags matching `v*` so a publish can't be triggered from a
     random branch.

After this, the `release.yml` workflow can publish without any PyPI
credentials in the repo.

### 3. Tag protection rules (GitHub side)

On GitHub: repo → Settings → Tags → New rule:

- **Tag name pattern:** `v*`
- **Restrict creation to:** specific roles or specific users (admins
  only, ideally a single maintainer account with hardware 2FA).

A non-admin contributor whose laptop is compromised then *cannot*
create a `v*` tag — and the entire release pipeline is gated on
`v*` tag creation.

### 4. Hardware 2FA on every privileged account

The single biggest payoff for the least effort:

- **PyPI:** account → 2FA → register a hardware security key (Yubikey,
  Solo, etc.). SMS-based 2FA is defeated by SIM swapping; WebAuthn /
  hardware keys are not.
- **GitHub:** account → Settings → Password and authentication →
  register a hardware key. Disable SMS fallback.
- **Recovery email:** the email on both accounts should be at a
  domain you control (not a free Gmail/Yahoo), and that email
  account should *also* use hardware 2FA. Account-recovery via
  email is the most common single point of failure.

### 5. Supply chain defences (already wired, just confirm)

These are configured in-repo and run automatically; no UI clicks needed:

- **Lockfile** (`packages/oip/uv.lock`) — frozen-installed in CI. A
  bad dep can't sneak in via a free-resolve.
- **Renovate cooldown** (`renovate.json`) — 7 days for runtime deps,
  14 days for GitHub Actions, 30 days for majors. Blocks the
  zero-day window where a compromised package version is live but
  not yet yanked. Enable Renovate by installing the GitHub App at
  <https://github.com/apps/renovate> and selecting this repository.
- **Dependency Review** (in `ci.yml`) — fails PRs that introduce
  known-vulnerable deps or deps under deny-listed licences.
- **CodeQL** (`codeql.yml`) — scans our own Python code for
  vulnerabilities on every PR + weekly.
- **SLSA provenance** — the `pypa/gh-action-pypi-publish` step
  generates a Sigstore attestation automatically when using OIDC.
  Users can verify the wheel was built by this exact workflow from
  this exact commit.

## Releasing a new version

Once the setup above is done, releases are tag-driven.

### Pre-flight lockstep check

Before tagging, confirm the spec, schemas, and bundled `_data/` copy
are in sync. CI catches this too, but checking locally is faster than
waiting for a tag-time failure:

```bash
diff -u SPEC.md packages/oip/src/oip/_data/spec.md
diff -u CHECKLIST.md packages/oip/src/oip/_data/checklist.md
for f in schemas/*.json; do
  diff -u "$f" "packages/oip/src/oip/_data/$f"
done
```

All three should produce no output.

### Cut the release

```bash
# 1. Bump the version in:
#    - packages/oip/pyproject.toml          (the wheel version)
#    - packages/oip/src/oip/__init__.py     (oip.__version__)
#
# 2. Move CHANGELOG.md's [Unreleased] section to a new version heading
#    with today's date, in Keep-a-Changelog format. Add the comparison
#    link at the bottom of the file.
#
# 3. Commit those changes on a release PR.
git add packages/oip/pyproject.toml packages/oip/src/oip/__init__.py CHANGELOG.md
git commit -m "release: v0.2.1"

# 4. Merge the release PR via the normal squash flow.
# 5. From an up-to-date main, tag the release commit.
git checkout main && git pull
git tag v0.2.1 -m "v0.2.1"
git push origin v0.2.1
```

The `release.yml` workflow picks up the tag push, runs pytest + the
lockstep mirror check, builds the wheel + sdist from `packages/oip/`,
publishes to PyPI via OIDC (after the environment reviewer approves
and the wait timer elapses), and creates a GitHub Release with both
artefacts attached.

## Verifying a release

After the workflow finishes (~5 minutes plus the wait-timer pause):

```bash
# PyPI page is live
open https://pypi.org/project/oip/

# Fresh install from a throwaway env works
uv run --isolated --with oip oip --help

# Bundled spec content matches the tagged source
uv run --isolated --with oip oip spec | head

# GitHub Release shows up
gh release view v0.2.1
```

## Rolling back

PyPI **does not allow re-uploading a version**. If a release is broken,
**yank** it (still discoverable in the API but not installed by default)
and ship a patch:

```bash
# Yank the bad version
twine yank oip 0.2.1 --reason "bundled _data/ out of sync with spec"

# Ship a patch
# Bump version to 0.2.2, update CHANGELOG, tag v0.2.2, push.
```

Hard-deletion is only available within 72 hours of upload via the PyPI
web UI, and only for projects with a single release.

## Version policy

OIP follows [SemVer](https://semver.org/spec/v2.0.0.html). Two version
numbers matter and they move together:

- **`oip_version`** — the protocol version line in `SPEC.md` and in the
  toolkit's bundled data. Backward-compatible additions bump minor;
  breaking wire-shape changes bump major.
- **Package version** — `packages/oip/pyproject.toml` and
  `packages/oip/src/oip/__init__.py`. Driven by changes to the toolkit
  itself (CLI, validator, scaffolder), and bumped at least to match
  any `oip_version` change.

Pre-1.0, MINOR bumps may include breaking changes if they're clearly
called out in CHANGELOG. Once we hit 1.0, MAJOR bumps are the only path
for breaks.

## What's NOT shipped

- **Reference producers** (PDF, FMU) ship from their own repos. They are
  not republished from here.
- **An MCP server** is planned but not yet shipped from the `oip` wheel.
  When it lands, it joins the same release flow described above.
