# read-aloud — setup & dependencies

Speak text aloud with a natural local voice (Kokoro neural TTS, Mandarin). Offline, keyless; streams
sentence-by-sentence through a warm resident server. Usage is in `SKILL.md`; this is the one-time setup.

## You install these
- **uv** — runs the TTS engine (`brew install uv`). PEP 723 inline dependencies, auto-installed on first
  run; there is nothing to `pip install` yourself.
- **macOS** — playback uses the built-in `afplay`, which renders to your current default output device.
- Apple Silicon recommended (faster synthesis) but not required — Kokoro is tiny and runs on CPU.

## uv / the model handle the rest (no action needed)
- **Python ≥3.10** — uv fetches it for the server/synth modes. The `say` client itself is stdlib-only and
  runs under your system `python3`.
- **Deps**, installed by uv on first run: `kokoro`, `misaki[zh]` (Chinese g2p), `soundfile`, `numpy`.
  Chinese needs no extra system packages; English voices would additionally need `espeak-ng`.
- **TTS model** — `hexgrad/Kokoro-82M` (~hundreds of MB), downloaded to `~/.cache/huggingface` on first
  use. On-device, keyless (runs with `HF_HUB_OFFLINE` after the first fetch).

## How it runs
- The first `say` after a reboot spawns a resident server that loads the model once (~5–8 s); every call
  after that is instant, and audio **streams** as it synthesizes (starts after the first chunk, playing
  while the rest is still being made).
- Playback uses `afplay`, which renders to your current **default output device and follows it live** — so
  switching headphones/speakers, even mid-sentence, moves the audio over to the new device.
- After editing `VOICE` / `SPEED`, reload the server: `pkill -f "speak.py serve"`.
