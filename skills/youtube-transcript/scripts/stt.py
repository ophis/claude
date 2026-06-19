# /// script
# requires-python = ">=3.9"
# dependencies = ["faster-whisper"]
# ///
"""Transcribe an audio file locally with faster-whisper (no API, no key).

Usage: uv run stt.py <audio-file> [lang]
`lang` is optional — auto-detected if omitted (e.g. pass `zh` for Chinese to skip detection).
First run downloads a ~480MB model to ~/.cache; transcription is fully on-device.
"""
import sys

from faster_whisper import WhisperModel

if len(sys.argv) < 2:
    sys.exit("usage: uv run stt.py <audio-file> [lang]")
audio = sys.argv[1]
lang = sys.argv[2] if len(sys.argv) > 2 else None  # None → auto-detect

model = WhisperModel("small", device="cpu", compute_type="int8")
segments, _ = model.transcribe(audio, language=lang, vad_filter=True)
print("".join(s.text for s in segments))
