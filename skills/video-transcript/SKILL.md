---
name: video-transcript
description: >-
  Fetch a video's transcript/captions from a URL — YouTube and 1800+ other sites
  (Bilibili, Vimeo, Twitch, TikTok, …) — for summarizing, quoting, or analyzing a
  video. Keyless, local, runs via uv. Use whenever a task involves a video link and
  you need what was said.
---

# Video transcript

## 1. Transcript (auto-routes by site)
```
uv run ~/.claude/skills/video-transcript/scripts/transcript.py <url> [lang]
```
- **YouTube** → `youtube-transcript-api` (fast, keyless). Auto-falls back to whatever
  caption language exists, so non-English videos work **without passing `lang`**.
- **Other sites** (1800+ via yt-dlp) → downloads the site's subtitles. Pass `lang` to prefer one.
- Prints plain text. Exits non-zero with a clean message when **no captions exist anywhere** → step 2.

## 2. No captions anywhere → local speech-to-text (heavier)
Download the audio (`-f bestaudio` needs no ffmpeg; works on the same 1800+ sites), then transcribe **locally**:
```
uvx yt-dlp -f bestaudio -o /tmp/v.%(ext)s <url>        # yields /tmp/v.m4a or /tmp/v.webm
uv run ~/.claude/skills/video-transcript/scripts/stt.py /tmp/v.<ext> [lang]
```
- `faster-whisper` (CTranslate2, int8), `small` model. First run downloads ~480MB to `~/.cache/huggingface`. Fully on-device, keyless.
- `lang` optional (auto-detected); pass e.g. `zh` to skip detection. Heavy (model + a few min) — only when there are genuinely no captions.

## 3. Metadata (title / description)
```
uvx yt-dlp --print title --print description --print duration_string <url>
```

## Notes
- YouTube blocks datacenter IPs; running on a local/residential IP is most reliable.
- DRM streaming (Netflix / Spotify / Disney+ …) cannot be downloaded.
- Login-gated sites: add `--cookies-from-browser chrome` to the yt-dlp commands.
