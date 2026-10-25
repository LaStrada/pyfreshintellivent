"""Release guard tests without network or publishing credentials."""

import importlib.util
import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "check_release", Path(__file__).parents[1] / "scripts" / "check-release.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECK_RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_RELEASE)


class ReleaseTests(unittest.TestCase):
    """Reject mismatched tags and accidental stable/prerelease publication."""

    def test_supported_versions(self) -> None:
        for version, prerelease in [
            ("1.0.0rc1", True),
            ("1.0.0b1", True),
            ("1.0.0a1", True),
            ("1.0.0.dev1", True),
            ("1.0.0", False),
            ("1.0.0.post1", False),
        ]:
            with self.subTest(version=version):
                CHECK_RELEASE.validate_release(
                    version, {"tag_name": f"v{version}", "prerelease": prerelease}
                )

    def test_tag_must_match(self) -> None:
        for tag in ("1.0.0rc1", "v0.3.4", "v1.0.0", "v1.0.0rc2"):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "tag"):
                CHECK_RELEASE.validate_release(
                    "1.0.0rc1", {"tag_name": tag, "prerelease": True}
                )

    def test_prerelease_flag_must_match(self) -> None:
        for version, flag in (("1.0.0rc1", False), ("1.0.0", True)):
            with (
                self.subTest(version=version),
                self.assertRaisesRegex(ValueError, "flag"),
            ):
                CHECK_RELEASE.validate_release(
                    version, {"tag_name": f"v{version}", "prerelease": flag}
                )

    def test_noncanonical_version_is_rejected(self) -> None:
        for version in ("1.0.0preview1", "1.0.0c1", "1.0.0rc"):
            with (
                self.subTest(version=version),
                self.assertRaisesRegex(ValueError, "canonical"),
            ):
                CHECK_RELEASE.validate_release(
                    version, {"tag_name": f"v{version}", "prerelease": True}
                )

    def test_local_version_is_rejected(self) -> None:
        for version in ("1.0.0+local", "1.0.0rc1+local"):
            with (
                self.subTest(version=version),
                self.assertRaisesRegex(ValueError, "local version"),
            ):
                CHECK_RELEASE.validate_release(
                    version, {"tag_name": f"v{version}", "prerelease": True}
                )

    def test_event_entrypoint(self) -> None:
        for event_name in ("release", "workflow_dispatch"):
            with (
                self.subTest(event=event_name),
                tempfile.TemporaryDirectory() as folder,
            ):
                root = Path(folder)
                (root / "pyproject.toml").write_text(
                    '[project]\nversion = "1.0.0rc1"\n'
                )
                event = root / "event.json"
                event.write_text(
                    json.dumps(
                        {"release": {"tag_name": "v1.0.0rc1", "prerelease": True}}
                    )
                )
                with (
                    patch.dict(
                        os.environ,
                        {
                            "GITHUB_EVENT_NAME": event_name,
                            "GITHUB_EVENT_PATH": str(event),
                        },
                    ),
                    patch("builtins.print") as output,
                ):
                    previous = Path.cwd()
                    try:
                        os.chdir(root)
                        runpy.run_path(str(SPEC.origin), run_name="__main__")
                    finally:
                        os.chdir(previous)
                output.assert_called_once_with("Package version: 1.0.0rc1")


if __name__ == "__main__":
    unittest.main()
