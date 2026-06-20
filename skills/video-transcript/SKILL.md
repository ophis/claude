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
- **Bilibili** → no caption route (yt-dlp 412s on its anti-crawl); prints the exact
  audio+STT commands to run → step 2 (Bilibili branch).
- **Other sites** (1800+ via yt-dlp) → downloads the site's subtitles. Pass `lang` to prefer one.
- Prints plain text. Exits non-zero with a clean message when **no captions exist anywhere** → step 2.

## 2. No captions anywhere → local speech-to-text (heavier)
Download the audio, then transcribe **locally on the GPU**:
```
uvx yt-dlp -f bestaudio -o '/tmp/v.%(ext)s' <url>     # quote the template (zsh globs %); yields /tmp/v.m4a|webm
uv run ~/.claude/skills/video-transcript/scripts/stt.py /tmp/v.<ext> [lang]
```
**Bilibili** (yt-dlp 412s — use the official-API helper instead, always outputs .m4a):
```
uv run ~/.claude/skills/video-transcript/scripts/bilibili.py audio <url> /tmp/v.m4a
uv run ~/.claude/skills/video-transcript/scripts/stt.py /tmp/v.m4a [lang]
```
`bilibili.py meta <url>` prints title/duration/description (yt-dlp's `--print` also 412s).
- `mlx-whisper` (Apple **MLX / Metal GPU**), `large-v3-turbo` model — **Apple Silicon only**; needs `ffmpeg` (`brew install ffmpeg`). First run downloads ~1.6GB to `~/.cache/huggingface`. Fully on-device, keyless.
- `lang` optional (auto-detected); pass e.g. `zh` to skip detection. Heavy (model + a couple min) — only when there are genuinely no captions.

## 3. Metadata (title / description)
```
uvx yt-dlp --print title --print description --print duration_string <url>   # Bilibili: use bilibili.py meta
```

## Notes
- YouTube blocks datacenter IPs; running on a local/residential IP is most reliable.
- DRM streaming (Netflix / Spotify / Disney+ …) cannot be downloaded.
- Login-gated sites: add `--cookies-from-browser chrome` to the yt-dlp commands.
