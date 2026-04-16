# Isolator

Isolator separates an MP3 into individual tracks such as vocals, drums, bass, and other instruments. It is a small command-line wrapper around [Demucs](https://github.com/facebookresearch/demucs), a proven music source-separation model.

## What You Get

Given:

```bash
isolator input/song.mp3 -o output
```

The program writes stems under:

```text
output/htdemucs/song/
  vocals.wav
  drums.wav
  bass.wav
  other.wav
```

## Recommended Distribution

The easiest way to distribute this is as a Docker image. Users only need Docker installed, and the image contains Python, Demucs, CPU-only PyTorch/Torchaudio, SoundFile, and FFmpeg.

Build it:

```bash
docker build -t isolator .
```

Rebuild the image after dependency changes:

```bash
docker build --no-cache -t isolator .
```

The image pins CPU-only PyTorch/Torchaudio so it does not require NVIDIA CUDA libraries.
The `.cache/torch` mount keeps Demucs model weights on the host so repeat runs do not download the same model again.

Run it:

```bash
docker run --rm \
  -v "$PWD/input:/input" \
  -v "$PWD/output:/output" \
  -v "$PWD/.cache/torch:/root/.cache/torch" \
  isolator /input/song.mp3 -o /output
```

For a smaller audience that is comfortable with Python, you can also distribute it as a Python package.

```bash
python3.11 -m pip install .
isolator song.mp3 -o output
```

Demucs and PyTorch currently have narrower Python support than the newest Python releases, so use Python 3.10, 3.11, or 3.12.

## Local Setup

Install FFmpeg first:

```bash
brew install ffmpeg
```

Then install the app:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Run:

```bash
isolator path/to/song.mp3 -o separated
```

## Options

```bash
isolator song.mp3 -o separated
isolator song.mp3 --format mp3
isolator song.mp3 --two-stems vocals
isolator song.mp3 --device cpu
isolator song.mp3 --dry-run
```

Useful flags:

- `--format wav|mp3|flac`: output format, default `wav`
- `--two-stems NAME`: split one stem from the mix, for example `vocals`
- `--model NAME`: Demucs model, default `htdemucs`
- `--device cpu|cuda|mps`: force the compute device
- `--jobs N`: number of parallel jobs Demucs should use
- `--dry-run`: print the Demucs command without running it

## Notes

- First run can be slow because Demucs downloads model weights.
- CPU separation works but can be slow. A GPU is much faster.
- MP3 input is supported through FFmpeg.
