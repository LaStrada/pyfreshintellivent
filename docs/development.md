# Development, CI and releases

Use the Poetry version configured in the [CI workflow](../.github/workflows/ci.yml).
Supported Python versions are declared in [package metadata](../pyproject.toml)
and tested by the CI matrix. Install the lockfile with `poetry install`; run the
commands in README.

Coverage includes every package source file, including files not imported by tests.
Both statements and branches must reach 100%; this also guarantees a >=95% floor
for each runtime module. Do not lower the threshold or exclude executable error
paths to make a build pass. A negative gate check with an unimported module was
performed and correctly failed. Golden protocol packets must come from independent
protocol evidence, not be generated solely by the encoder under test.

GitHub Actions runs the configured Python matrix on Linux and transport tests
on macOS and Windows, then
builds an sdist/wheel and imports the installed wheel outside the source tree.
It verifies the `py.typed` marker. CI uses read-only permissions; dependency
updates are proposed by Dependabot. Coverage reports and
distributions are artifacts, not releases. Existing required checks retain their
names. Configure the supported Python, platform and package checks as required
in branch protection if failures in those environments should block merges.

## Action versions

Follow the Airthings BLE convention: use current stable major action tags,
not commit SHAs or unreleased branches. Check official
releases and migration notes before choosing a version; a green run does not
establish that a copied version is current. Dependabot proposes future major
updates. Keep this convention across all workflows unless a maintainer asks
for a different policy.

## Release checklist

1. Review the proposed changes and migration notes for compatibility.
2. Complete and record the hardware acceptance matrix, including authentication
   confirmation on the owner's firmware. Resolve any protocol disagreement.
3. Confirm a clean checkout, locked dependencies, all CI checks and package metadata.
4. Merge the reviewed changes and make an explicit release decision, including
   the version and whether it is a prerelease. Set package metadata as part of
   that release process; do not reserve a release number in this documentation.
   Never overwrite an existing published version.
5. Publish through a separately reviewed workflow/environment, preferably
   PyPI Trusted Publishing with an environment approval. No long-lived token in Git.
6. Test installation of that exact released wheel before pinning it in HA Core.

Automated publishing is intentionally absent until the major rewrite passes the
hardware gate. A successful CI run alone is not authorization to deploy it to HA.
