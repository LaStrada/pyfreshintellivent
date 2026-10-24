# Contribution templates

The PR template asks for the change, one type, and validation. Bug and feature
issue templates apply `bug` and `enhancement` automatically.

The PR label workflow maps the selected type to `bug`, `enhancement`, `breaking`,
`dependencies`, or `maintenance`. Changing the selection replaces only labels
from this set; labels such as `research`, `testing`, and `help wanted` stay intact.
No selection leaves existing labels alone for bots and older PRs. Multiple or
unknown checked options fail the label check without changing labels. The job
reports errors in Actions and does not post comments.

Maintainers must keep the five type labels available in repository settings.
`breaking` means a backward-incompatible API change; `maintenance` covers
refactoring, tests, CI and documentation. These labels do not publish releases
or change version numbers.

Templates become available after merging to the default branch. PR labeling
uses the workflow from the default branch on open, description edit or reopen.
It has only PR write permission, performs no checkout, and treats PR text as data.
The ordinary read-only CI job tests the exact embedded script with a mocked API:

```sh
node --test .github/tests/pr-labels.test.cjs
```

Reference: [GitHub pull_request_target events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target).
