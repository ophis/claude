# /// script
# requires-python = ">=3.9"
# dependencies = ["youtube-transcript-api>=1.1,<2"]
# ///
"""Fetch a YouTube transcript by URL or video id.

Usage: uv run transcript.py <youtube-url-or-id> [lang]
Prints the transcript as plain text. Exits non-zero (clean message) if the
video has no captions. Default language: en.
"""
import re
import sys


def extract_id(s: str) -> str:
    if re.fullmatch(r"[\w-]{11}", s):  # already a bare id
        return s
    m = re.search(r"(?:v=|/shorts/|/embed/|youtu\.be/)([\w-]{11})", s)
    if m:
        return m.group(1)
    sys.exit(f"no video id found in: {s}")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: uv run transcript.py <youtube-url-or-id> [lang]")
    vid = extract_id(sys.argv[1])
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"

    from youtube_transcript_api import YouTubeTranscriptApi

    try:  # 1.x API, with fallback to the legacy static method
        fetched = YouTubeTranscriptApi().fetch(vid, languages=[lang, "en"])
        text = " ".join(s.text for s in fetched)
    except AttributeError:
        raw = YouTubeTranscriptApi.get_transcript(vid, languages=[lang, "en"])
        text = " ".join(d["text"] for d in raw)
    except Exception as e:
        # ponytail: no captions / disabled / unavailable — surface cleanly so the
        # caller knows to fall back to the yt-dlp + whisper path (see SKILL.md).
        sys.exit(f"no transcript for {vid}: {type(e).__name__}: {e}")

    print(text)


if __name__ == "__main__":
    main()
