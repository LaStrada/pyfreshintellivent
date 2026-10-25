# Development, checks and releases

Use the Poetry version configured in the [CI workflow](../.github/workflows/ci.yml).
[Package metadata](../pyproject.toml) declares supported Python versions; the
workflow matrix defines the versions currently tested in CI.

## Before committing

For Python or dependency changes, run the full check sequence locally:

```sh
poetry install
poetry check --lock
poetry run black --check pyfreshintellivent tests
poetry run isort --check-only pyfreshintellivent tests
poetry run ruff check pyfreshintellivent tests
poetry run pylint pyfreshintellivent
poetry run mypy pyfreshintellivent
poetry run pytest
poetry build
```

| Tool | Purpose |
| --- | --- |
| Poetry | Locked dependencies, metadata checks and package builds |
| Black | Python formatting |
| isort | Import ordering using the Black profile |
| Ruff | Configured Python error checks |
| Pylint | Runtime code quality |
| mypy | Static type checks |
| pytest and coverage | Behavior tests and coverage enforcement |

Check changed examples with Black, isort and Ruff too. Use `--help` to check CLI
parsing without connecting to hardware.

For documentation changes, verify claims against source, check relative links
and run `git diff --check`. For workflow changes, run `actionlint`; when modifying
PR-label automation, also run `node --test .github/tests/pr-labels.test.cjs`.
Resolve relevant failures before committing.

## Tests and CI

Coverage includes every package source file, including modules not imported by
tests. Statements and branches must reach 100%. Do not lower the threshold or
exclude executable error paths to make a build pass. Protocol fixtures should be
independent of the encoder under test.

The [CI workflow](../.github/workflows/ci.yml) defines the enabled checks and
Python/platform matrix. Keep local validation aligned with that workflow and
preserve required check names when changing jobs. Coverage reports and built
packages are validation artifacts, not published releases.

Use current stable major GitHub Action tags. Check official release notes and
migration requirements before upgrading; dependency-update PRs need the same
review as other changes. Keep CI permissions read-only except for jobs that
explicitly require a write operation, such as applying PR labels.

## Home Assistant dependency compatibility

The library supports Python 3.12, 3.13 and 3.14 without compatibility shims.
Its dependency floors match the shared packages below. Check both Home Assistant's
stable release and a specific development revision before raising those floors.

Dependency references checked on 2026-10-25:

| Home Assistant reference | Required Python | Shared Bluetooth dependencies |
| --- | --- | --- |
| Stable `2026.10.3`: [project metadata](https://github.com/home-assistant/core/blob/2026.10.3/pyproject.toml), [Bluetooth manifest](https://github.com/home-assistant/core/blob/2026.10.3/homeassistant/components/bluetooth/manifest.json) | `>=3.14.2` | `bleak==3.0.2`, `bleak-retry-connector==4.7.1`, `async-interrupt==1.2.2` |
| Development revision `a9c9e65f35af8e934d77ab5023641697d82007ef`: [project metadata](https://github.com/home-assistant/core/blob/a9c9e65f35af8e934d77ab5023641697d82007ef/pyproject.toml), [Bluetooth manifest](https://github.com/home-assistant/core/blob/a9c9e65f35af8e934d77ab5023641697d82007ef/homeassistant/components/bluetooth/manifest.json) | `>=3.14.2` | `bleak==3.0.2`, `bleak-retry-connector==4.7.1`, `async-interrupt==1.2.2` |

When changing dependencies:

1. Recheck Core's `pyproject.toml` and Bluetooth manifest for stable and development
   references; record the exact tag or commit used.
2. Test the library with those exact shared pins, as well as its supported Python
   versions. Dependency resolution and API tests do not establish that the full
   Home Assistant integration suite passes.
3. Keep compatible ranges in library metadata. Do not copy Core's complete set
   of transitive pins into the library.
4. When expanding CI, preserve the existing required Python 3.13 lint check name
   so branch protection continues to match it.

These references establish dependency alignment at the recorded revisions, not
compatibility with future development changes.

## Release checklist

1. Review API compatibility and the [migration guide](migration.md).
2. Complete the [hardware verification checklist](verification.md#hardware-acceptance-before-release)
   for the supported models and firmware. Resolve protocol discrepancies.
3. Confirm locked dependencies, passing checks and a successful package build.
4. Select the release version and prerelease status, then update package metadata.
   Never overwrite an existing published version.
5. Publish through a reviewed release workflow, preferably using PyPI Trusted
   Publishing with an environment approval.
6. Verify installation of the released wheel before consumers pin that version.
