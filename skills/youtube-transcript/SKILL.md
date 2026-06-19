---
name: youtube-transcript
description: >-
  Fetch a YouTube video's transcript/captions (and its title/description) from a URL or
  video id — for summarizing, quoting, or analyzing a video. Keyless, runs via uv. Use
  whenever the task involves a youtube.com or youtu.be link and you need what was said.
---

# YouTube transcript

## 1. Transcript (primary)
```
uv run ~/.claude/skills/youtube-transcript/scripts/transcript.py <url-or-id> [lang]
```
- Accepts any URL form (`watch?v=`, `youtu.be/`, `/shorts/`, extra `?si=`/`&t=` params) or a bare 11-char id.
- Prints the transcript as plain text. Default lang `en`; pass a code (e.g. `zh`) as the 2nd arg.
- Keyless. `uv` auto-installs `youtube-transcript-api` in an ephemeral env (PEP 723 inline deps) — nothing to pre-install.
- Exits non-zero with a clean message if the video has no captions → use the fallback below.

## 2. Title / description / metadata
```
uvx yt-dlp --print title --print description --print duration_string <url>
```
`youtube-transcript-api` only returns captions, not metadata — `yt-dlp` fills that gap.

## 3. No captions? → local speech-to-text fallback (heavier)
Only when step 1 reports captions are disabled. Download the audio (`-f bestaudio` needs
no ffmpeg), then transcribe **locally** with faster-whisper:
```
uvx yt-dlp -f bestaudio -o /tmp/yt.%(ext)s <url>      # yields /tmp/yt.m4a or /tmp/yt.webm
uv run ~/.claude/skills/youtube-transcript/scripts/stt.py /tmp/yt.<ext> [lang]
```
- `faster-whisper` (CTranslate2, int8) — ~4–5× faster on CPU than `openai-whisper`.
- First run downloads a ~480MB model to `~/.cache`; transcription is fully on-device, keyless.
- `lang` is optional (auto-detected); pass e.g. `zh` to skip detection. Heavy — only when there are genuinely no captions.

## Notes
- YouTube blocks datacenter IPs; running on a local/residential IP is most reliable.
- List available caption languages: `uvx youtube_transcript_api --list-transcripts <id>`.
