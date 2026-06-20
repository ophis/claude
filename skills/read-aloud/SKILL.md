---
name: read-aloud
description: >-
  Speak text aloud with a natural local voice (Kokoro neural TTS, Mandarin Chinese, offline & keyless).
  Use whenever the user wants to HEAR something — "念出来 / 读出来 / read it aloud", or "summarize this
  and read it". Streams sentence-by-sentence through a warm resident server.
---

# Read aloud (local TTS)

Speak text through the local Kokoro server — fast, offline, no API key:
```
python3 ${CLAUDE_SKILL_DIR}/scripts/speak.py say "要念的文本"
echo "$text" | python3 ${CLAUDE_SKILL_DIR}/scripts/speak.py say   # long / multiline: pipe via stdin
```
- **Fire-and-forget:** returns instantly; audio plays async, streamed sentence-by-sentence.
- First call after a reboot spawns the server (~5–8s model load); after that it's warm/instant.
- Voice/speed: edit `VOICE` / `SPEED` atop `speak.py`, then `pkill -f "speak.py serve"` to reload.

## Write for the ear — generate it speakable, don't convert after
When the request is to read something aloud, decide that **up front** and generate the deliverable
**directly as speakable prose, in one pass** — flowing sentences ending in 。！？.!?, no markdown, tables,
code, list/heading markers, emoji, URLs, or citations. Do **not** first write a screen-formatted answer
and then convert it to speech; produce the spoken form from the start, then pass it to `say`. (Write a
second, rich on-screen version only if the user also asked to see it.)

The voice is a Mandarin model, so embedded English is read with a heavy accent and acronyms come out
awkward — **keep the spoken text Chinese**: translate or transliterate English words and acronyms
(`AI`→人工智能, `WOW`→哇, `NFC`→「N-F-C」or its meaning). Leave a Latin term only when there is genuinely
no Chinese equivalent.

## Stream as you generate
`say` is non-blocking and the server plays calls **in order**, so to start audio *before* a long answer
is finished, call it per paragraph as you write:
```
python3 ${CLAUDE_SKILL_DIR}/scripts/speak.py say "第一段……"   # plays while you write the next
python3 ${CLAUDE_SKILL_DIR}/scripts/speak.py say "第二段……"
```
For short/normal output, one call with the full text is enough — the server already streams it as it
synthesizes (audio starts after the first chunk). Per-paragraph calls cost one tool round-trip each, so
only split when the output is long enough that earlier audio is worth it.

> `say` is **stdlib-only** — runs under plain `python3` (instant, no env resolution). It spawns the
> Kokoro server via `uv run … serve` internally, so only the `serve`/`synth` modes ever touch uv.
