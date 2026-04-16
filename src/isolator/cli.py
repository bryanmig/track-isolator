from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


OUTPUT_FORMAT_FLAGS = {
    "wav": None,
    "mp3": "--mp3",
    "flac": "--flac",
}


@dataclass(frozen=True)
class SeparationOptions:
    input_file: Path
    output_dir: Path
    model: str
    output_format: str
    two_stems: str | None
    device: str | None
    jobs: int | None
    dry_run: bool


class ConfigError(ValueError):
    """Raised when CLI options or local dependencies are invalid."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="isolator",
        description="Separate an MP3 into isolated stems using Demucs.",
    )
    parser.add_argument("input_file", type=Path, help="Path to the MP3 or audio file to split.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("separated"),
        help="Directory where stems should be written. Default: separated",
    )
    parser.add_argument(
        "--model",
        default="htdemucs",
        help="Demucs model name. Default: htdemucs",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=sorted(OUTPUT_FORMAT_FLAGS),
        default="wav",
        help="Stem output format. Default: wav",
    )
    parser.add_argument(
        "--two-stems",
        help="Separate one stem from the rest of the mix, for example: vocals",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda", "mps"],
        help="Force Demucs to use a compute device. Default: Demucs auto-detects.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        help="Number of parallel jobs Demucs should use.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the Demucs command without running it.",
    )
    return parser


def parse_options(argv: Sequence[str] | None = None) -> SeparationOptions:
    args = build_parser().parse_args(argv)
    return SeparationOptions(
        input_file=args.input_file.expanduser(),
        output_dir=args.output.expanduser(),
        model=args.model,
        output_format=args.output_format,
        two_stems=args.two_stems,
        device=args.device,
        jobs=args.jobs,
        dry_run=args.dry_run,
    )


def validate_options(options: SeparationOptions) -> None:
    if not options.input_file.exists():
        raise ConfigError(f"Input file does not exist: {options.input_file}")
    if not options.input_file.is_file():
        raise ConfigError(f"Input path is not a file: {options.input_file}")
    if options.jobs is not None and options.jobs < 1:
        raise ConfigError("--jobs must be 1 or greater")
    if options.output_format not in OUTPUT_FORMAT_FLAGS:
        raise ConfigError(f"Unsupported output format: {options.output_format}")


def validate_runtime() -> None:
    if shutil.which("ffmpeg") is None:
        raise ConfigError("FFmpeg is required but was not found on PATH.")
    if importlib.util.find_spec("demucs") is None:
        raise ConfigError("Demucs is required. Install this project with `python -m pip install .`.")
    if importlib.util.find_spec("soundfile") is None:
        raise ConfigError("SoundFile is required for writing separated audio. Rebuild or reinstall Isolator.")
    if importlib.util.find_spec("torchaudio") is None:
        raise ConfigError("Torchaudio is required. Rebuild or reinstall Isolator.")


def build_demucs_command(options: SeparationOptions) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "demucs",
        "--name",
        options.model,
        "--out",
        str(options.output_dir),
    ]

    output_format_flag = OUTPUT_FORMAT_FLAGS[options.output_format]
    if output_format_flag:
        command.append(output_format_flag)

    if options.two_stems:
        command.append(f"--two-stems={options.two_stems}")
    if options.device:
        command.extend(["--device", options.device])
    if options.jobs is not None:
        command.extend(["--jobs", str(options.jobs)])

    command.append(str(options.input_file))
    return command


def run_separation(options: SeparationOptions) -> int:
    validate_options(options)
    command = build_demucs_command(options)

    if options.dry_run:
        print(" ".join(command))
        return 0

    validate_runtime()
    options.output_dir.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(command, check=False)
    return completed.returncode


def main(argv: Sequence[str] | None = None) -> int:
    try:
        options = parse_options(argv)
        return run_separation(options)
    except ConfigError as exc:
        print(f"isolator: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("isolator: cancelled", file=sys.stderr)
        return 130
