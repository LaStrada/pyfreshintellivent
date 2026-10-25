# Development

Use Poetry and a Python version listed in [package metadata](../pyproject.toml).

## Local checks

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

Check changed examples with Black, isort and Ruff too. Run their `--help` command
without connecting to hardware. For docs, check relative links and run
`git diff --check`.

Tests require 100% statement and branch coverage. Keep protocol fixtures
independent of the encoder being tested.

## CI and dependencies

[CI](../.github/workflows/ci.yml) defines the Python/platform matrix and Poetry
version. Use `actionlint` for workflow changes and
`node --test .github/tests/pr-labels.test.cjs` for PR-label changes. Preserve
required check names and use stable major action tags.

Before changing dependencies, test against the shared Bluetooth dependencies in
both Home Assistant stable and dev. Keep compatible library ranges; avoid copying
HA's full dependency pins into this package.

## Releases

1. Check API compatibility and update [migration notes](migration.md).
2. Review [hardware test gaps](verification.md#remaining-hardware-tests).
3. Run local checks and build the package.
4. Merge the package version change, then publish a GitHub release tagged
   `v<version>`. Mark alpha, beta and RC versions as prereleases.

The release workflow checks the tag/version and runs CI before uploading its
built distributions to PyPI. It uses the `PYPI_UPLOAD_PASSWORD` repository secret.
Run it manually for a dry run: manual runs never publish. After publication,
verify installation of the released wheel in a clean environment.
