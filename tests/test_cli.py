from __future__ import annotations

import sys
import unittest
from pathlib import Path

from isolator.cli import ConfigError, build_demucs_command, parse_options, validate_options


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(self._testMethodName)
        self.temp_dir.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        for path in sorted(self.temp_dir.glob("*"), reverse=True):
            path.unlink()
        self.temp_dir.rmdir()

    def test_builds_default_demucs_command(self) -> None:
        song = self.temp_dir / "song.mp3"
        song.write_bytes(b"fake mp3")
        output = self.temp_dir / "out"
        options = parse_options([str(song), "-o", str(output)])

        command = build_demucs_command(options)

        self.assertEqual(
            command,
            [
                sys.executable,
                "-m",
                "demucs",
                "--name",
                "htdemucs",
                "--out",
                str(output),
                str(song),
            ],
        )

    def test_builds_two_stem_mp3_command(self) -> None:
        song = self.temp_dir / "song.mp3"
        song.write_bytes(b"fake mp3")
        output = self.temp_dir / "out"
        options = parse_options(
            [
                str(song),
                "-o",
                str(output),
                "--format",
                "mp3",
                "--two-stems",
                "vocals",
                "--device",
                "cpu",
                "--jobs",
                "2",
            ]
        )

        command = build_demucs_command(options)

        self.assertEqual(
            command[-6:],
            [
                "--two-stems=vocals",
                "--device",
                "cpu",
                "--jobs",
                "2",
                str(song),
            ],
        )
        self.assertIn("--mp3", command)

    def test_rejects_missing_input(self) -> None:
        options = parse_options([str(self.temp_dir / "missing.mp3")])

        with self.assertRaisesRegex(ConfigError, "Input file does not exist"):
            validate_options(options)

    def test_rejects_invalid_jobs(self) -> None:
        song = self.temp_dir / "song.mp3"
        song.write_bytes(b"fake mp3")
        options = parse_options([str(song), "--jobs", "0"])

        with self.assertRaisesRegex(ConfigError, "--jobs must be 1 or greater"):
            validate_options(options)


if __name__ == "__main__":
    unittest.main()
