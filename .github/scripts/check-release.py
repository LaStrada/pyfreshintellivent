"""Reject release tags or prerelease flags that disagree with package metadata."""

import json
import os
import tomllib
from pathlib import Path

from packaging.version import Version


def validate_release(version: str, release: dict[str, object]) -> None:
    """Require the exact package version and the corresponding release type."""
    if release["tag_name"] != f"v{version}":
        raise ValueError("Release tag must match the package version")
    parsed = Version(version)
    if str(parsed) != version:
        raise ValueError("Package version must use canonical PEP 440 spelling")
    if parsed.local is not None:
        raise ValueError("PyPI does not accept local version identifiers")
    prerelease = parsed.is_prerelease
    if release["prerelease"] is not prerelease:
        raise ValueError("GitHub prerelease flag must match the package version")


def main() -> None:
    """Validate published releases; manual runs only test CI and packaging."""
    version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
    if os.environ["GITHUB_EVENT_NAME"] == "release":
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        validate_release(version, event["release"])
    print(f"Package version: {version}")


if __name__ == "__main__":
    main()
