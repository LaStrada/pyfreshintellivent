# Development, CI and releases

Use Poetry 2.5.1 for the same environment manager as CI. Runtime targets Python
3.12–3.14. Install the lockfile with `poetry install`; run the commands in README.

Coverage includes every package source file, including files not imported by tests.
Both statements and branches must reach 100%; this also guarantees a >=95% floor
for each runtime module. Do not lower the threshold or exclude executable error
paths to make a build pass. A negative gate check with an unimported module was
performed and correctly failed. Golden protocol packets must come from independent
protocol evidence, not be generated solely by the encoder under test.

GitHub Actions runs tests on Linux 3.12–3.14, macOS 3.14 and Windows 3.14, then
builds an sdist/wheel and imports the installed wheel outside the source tree.
It verifies the `py.typed` marker. CI uses read-only permissions; dependency
updates are proposed by Dependabot. Coverage reports and
distributions are artifacts, not releases. Existing required checks retain their
names. Once the workflow is merged, additionally require the new 3.14/platform/
package checks in branch protection if all supported environments should block
merges; no protection rules were weakened or silently replaced by this work.

## Action versions

Follow the Airthings BLE convention: use current stable major tags such as
`actions/checkout@v7`, not commit SHAs or unreleased branches. Check official
releases and migration notes before choosing a version; a green run does not
establish that a copied version is current. Dependabot proposes future major
updates. Keep this convention across all workflows unless a maintainer asks
for a different policy.

## Release checklist

1. Review the stacked changes and migration notes as one versioned API change.
2. Complete and record the hardware acceptance matrix, including authentication
   confirmation on the owner's firmware. Resolve any protocol disagreement.
3. Confirm a clean checkout, locked dependencies, all CI checks and package metadata.
4. Obtain an explicit release decision. `1.0.0b1` is reserved in this branch but
   has not been uploaded. Never overwrite an existing published version.
5. Publish a beta through a separately reviewed workflow/environment, preferably
   PyPI Trusted Publishing with an environment approval. No long-lived token in Git.
6. Test installation of that exact released wheel before pinning it in HA Core.

Automated publishing is intentionally absent until the major rewrite passes the
hardware gate. A successful CI run alone is not authorization to deploy it to HA.
