# Development, CI and releases

Use the Poetry version configured in the [CI workflow](../.github/workflows/ci.yml).
Supported Python versions are declared in [package metadata](../pyproject.toml);
the workflow matrix defines the versions currently tested in CI. Install the lockfile with `poetry install`; run the
commands in README.

## Before committing

Run the relevant checks locally before committing, rather than relying on the
first CI run after a push. The [README development commands](../README.md#development)
provide the full Python check sequence; use the same Poetry environment and
lockfile as CI.

| Check | Purpose | Scope |
| --- | --- | --- |
| `poetry check --lock` | Validate package metadata and lockfile consistency | Project configuration |
| Black | Check formatting | Library and tests |
| isort | Check import order using the Black profile | Library and tests |
| Ruff | Detect configured Python errors | Library and tests |
| Pylint | Check runtime code quality | Library |
| mypy | Check static types | Library |
| pytest with coverage | Verify behavior and the coverage threshold | Library and tests |
| `poetry build` | Verify wheel and source distribution build | Package |

For Python or dependency changes, run the full sequence before committing.
Check changed examples with Black, isort and Ruff too; use `--help` to check CLI
parsing without connecting to hardware. For documentation-only changes, review
behavior claims against source, verify relative links and run `git diff --check`.
For workflow changes, run `actionlint`; for PR-label automation changes, also run
`node --test .github/tests/pr-labels.test.cjs` where that automation is present.
Do not commit with a known relevant failure or silently skip a failing check.

The independent [CI maintenance change](https://github.com/LaStrada/pyfreshintellivent/pull/63)
adds the Python/OS matrix, package smoke test and contribution checks. Merge that
change separately before relying on those checks. The workflow in this checkout
is the source of truth for the checks currently enabled. Local success does not
replace CI checks. Black owns formatting and isort owns import
ordering in this project; Ruff is currently used for linting, not as a second
formatter. A toolchain consolidation should be a separate reviewed change.

Coverage includes every package source file, including files not imported by tests.
Both statements and branches must reach 100%; this also guarantees a >=95% floor
for each runtime module. Do not lower the threshold or exclude executable error
paths to make a build pass. A negative gate check with an unimported module was
performed and correctly failed. Golden protocol packets must come from independent
protocol evidence, not be generated solely by the encoder under test.

With the CI maintenance change, GitHub Actions runs the configured Python matrix
on Linux and tests on macOS and Windows, then builds an sdist/wheel and imports
the installed wheel outside the source tree.
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
