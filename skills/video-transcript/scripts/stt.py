# /// script
# requires-python = ">=3.9"
# dependencies = ["mlx-whisper"]
# ///
"""Transcribe an audio file on the Apple Silicon GPU via mlx-whisper (Metal, no API).

Usage: uv run stt.py <audio-file> [lang]
`lang` is optional - auto-detected if omitted (pass e.g. `zh` for Chinese to skip detection).
Uses the `large-v3-turbo` model; first run downloads ~1.6GB to ~/.cache/huggingface.
Requires ffmpeg on PATH (`brew install ffmpeg`). Apple Silicon only (MLX is Metal-based).
"""
import sys

import mlx_whisper

if len(sys.argv) < 2:
    sys.exit("usage: uv run stt.py <audio-file> [lang]")
audio = sys.argv[1]
lang = sys.argv[2] if len(sys.argv) > 2 else None  # None -> auto-detect

result = mlx_whisper.transcribe(
    audio,
    path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
    language=lang,
)
print(result["text"])
