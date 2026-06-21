#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["kokoro>=0.9.4", "misaki[zh]", "soundfile", "numpy"]
# ///
"""Local Kokoro neural TTS (Mandarin, offline, keyless). Three modes:

  python3 speak.py say "文本"      (say)    -> speak text via the warm resident server (stdlib-only,
                                              instant; text may also come from stdin). Main entrypoint.
  uv run speak.py serve [text]    (server) -> load Kokoro ONCE, keep it warm, speak text sent over a
                                              unix socket (optional `text` is spoken right after load).
  uv run speak.py "文本" [out.wav]  (synth)  -> one-shot: stream-play it, or write a wav.

`say` auto-spawns the server (handing it the first line) if it isn't up. The heavy kokoro/torch import
lives only in server/synth modes under `uv run`; audio streams sentence-by-sentence.

Edited VOICE/SPEED? The running server has the old values — `pkill -f "speak.py serve"` and the next
`say` respawns it with your changes."""
import os
import shutil
import socket
import subprocess
import sys
import tempfile

VOICE = "zf_xiaoxiao"  # zh: zf_xiaoxiao/zf_xiaoni/zf_xiaobei/zf_xiaoyi (f), zm_yunxi/zm_yunyang (m)
SPEED = 1.2            # 1.0 = default; >1 faster, <1 slower
SPLIT = r"[。！？!?；;\n]+"  # split into sentences; without this Kokoro truncates long one-line text
CHUNK_SECS = 6.0      # group sentences into ~this-long afplay chunks; fewer chunks = fewer inter-chunk gaps
IDLE_SECS = float(os.environ.get("SPEAK_IDLE_SECS", "900"))  # server self-exits after this idle; next say respawns
SELF = os.path.abspath(__file__)
SOCK = os.path.join(os.path.dirname(SELF), ".speak.sock")  # next to this script, not hardcoded
UV = shutil.which("uv") or "/opt/homebrew/bin/uv"


def build_pipeline():
    import logging
    import warnings
    warnings.filterwarnings("ignore")             # torch/jieba deprecation noise
    os.environ.setdefault("HF_HUB_OFFLINE", "1")  # model is cached -> no network, no HF warning
    from kokoro import KPipeline
    try:
        import jieba
        jieba.setLogLevel(logging.ERROR)          # "Building prefix dict ..." logs
    except Exception:
        pass
    return KPipeline(lang_code="z", repo_id="hexgrad/Kokoro-82M")  # 'z' = Mandarin (needs misaki[zh])


def _seg_audio(r):
    import numpy as np
    a = getattr(r, "audio", None)
    if a is None and isinstance(r, (tuple, list)):
        a = r[-1]
    if a is None:
        return None
    if hasattr(a, "detach"):
        a = a.detach().cpu().numpy()
    return np.asarray(a, dtype="float32")


def play_stream(pipeline, text, cancel=None):
    """Streaming via afplay, chunked. A producer thread synthesizes + trims each sentence and groups them
    into ~CHUNK_SECS-long temp wavs; the main thread plays the chunks in order with afplay. Each chunk is
    trimmed flush at BOTH edges (no leading/trailing silence), so the only thing between two chunks is the
    afplay-relaunch gap itself — which lands right at a sentence boundary and reads as a natural pause.
    Within a chunk, sentences get a tiny breath. afplay follows the default output device even mid-playback;
    audio starts after the first chunk (plays while the rest synthesizes)."""
    import queue
    import threading
    import time
    import numpy as np
    import soundfile as sf
    q = queue.Queue(maxsize=3)
    pad = np.zeros(int(24000 * 0.08), dtype="float32")  # breath BETWEEN sentences inside a chunk only

    def emit(segs, n):
        if not segs:
            return
        parts = []
        for j, s in enumerate(segs):
            if j:
                parts.append(pad)  # between sentences, never at the chunk's edges
            parts.append(s)
        p = os.path.join(tempfile.gettempdir(), f"speak_{os.getpid()}_{n}.wav")
        sf.write(p, np.concatenate(parts), 24000)
        q.put(p)

    def produce():
        segs, secs, n = [], 0.0, 0
        for r in pipeline(text, voice=VOICE, speed=SPEED, split_pattern=SPLIT):
            if cancel and cancel.is_set():
                break                      # stop synthesizing the rest on interrupt
            a = _seg_audio(r)
            if a is None:
                continue
            idx = np.where(np.abs(a) > 1e-3)[0]  # strip Kokoro's leading/trailing silence
            if len(idx) == 0:
                continue
            segs.append(a[idx[0]:idx[-1] + 1])
            secs += len(segs[-1]) / 24000
            if secs >= CHUNK_SECS:
                emit(segs, n)
                n += 1
                segs, secs = [], 0.0
        if not (cancel and cancel.is_set()):
            emit(segs, n)
        q.put(None)

    threading.Thread(target=produce, daemon=True).start()
    while True:
        p = q.get()
        if p is None:
            break
        if not (cancel and cancel.is_set()):
            proc = subprocess.Popen(["afplay", p])  # afplay tracks the default output device, even mid-playback
            while proc.poll() is None:
                if cancel and cancel.is_set():
                    proc.terminate()       # stop now; remaining queued chunks are dropped unplayed
                    break
                time.sleep(0.05)
        try:
            os.remove(p)
        except OSError:
            pass


def write_wav(pipeline, text, out):
    import numpy as np
    import soundfile as sf
    chunks = [c for c in (_seg_audio(r) for r in pipeline(text, voice=VOICE, speed=SPEED, split_pattern=SPLIT))
              if c is not None]
    sf.write(out, np.concatenate(chunks) if chunks else np.zeros(1, "float32"), 24000)
    print(out)


def serve(initial=None):
    """Resident server: load Kokoro once, play texts received over the unix socket (serialized).
    A watchdog self-exits the process after IDLE_SECS with no playback, so the model doesn't sit in
    memory forever; the next `say` just respawns it."""
    import queue
    import threading
    import time
    pipeline = build_pipeline()  # torch + model loaded ONCE for the process lifetime
    jobs = queue.Queue()
    cancel = threading.Event()  # set by a `stop` message; aborts the playing job + drains the queue
    state = {"active": time.time(), "busy": False}

    def worker():
        while True:
            t = jobs.get()
            cancel.clear()  # fresh job: forget any prior stop
            state["busy"] = True
            if t:
                try:
                    play_stream(pipeline, t, cancel)
                except Exception:
                    pass
            state["busy"] = False
            state["active"] = time.time()
    threading.Thread(target=worker, daemon=True).start()

    def watchdog():
        while True:
            time.sleep(30)
            if not state["busy"] and jobs.empty() and time.time() - state["active"] > IDLE_SECS:
                try:
                    os.remove(SOCK)
                except OSError:
                    pass
                os._exit(0)  # free the model; next `say` respawns the server
    threading.Thread(target=watchdog, daemon=True).start()

    if initial:
        jobs.put(initial)
        state["active"] = time.time()

    try:
        os.remove(SOCK)  # clear a stale socket from a previous (dead) server
    except OSError:
        pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        srv.bind(SOCK)
    except OSError:
        return  # another server already owns the socket
    srv.listen()
    while True:
        conn, _ = srv.accept()
        buf = bytearray()
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
        conn.close()
        if buf == b"\x00STOP":  # interrupt: abort current playback + clear pending jobs
            cancel.set()
            try:
                while True:
                    jobs.get_nowait()
            except queue.Empty:
                pass
            continue
        t = buf.decode("utf-8", "replace").strip()
        if t:
            jobs.put(t)
            state["active"] = time.time()


def send(text):
    """Send text to the resident server; spawn it (handing it this text) if it isn't up yet."""
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(1.0)
        c.connect(SOCK)
        c.sendall(text.encode("utf-8"))
        c.close()
        return
    except OSError:
        pass  # no server -> start one and let it speak this first line once loaded
    subprocess.Popen([UV, "run", SELF, "serve", text],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def stop():
    """Tell the running server to interrupt: kill current playback + drop queued text. Keeps the model warm."""
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(1.0)
        c.connect(SOCK)
        c.sendall(b"\x00STOP")
        c.close()
    except OSError:
        pass  # no server up -> nothing to stop


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":      # resident server
        serve(sys.argv[2] if len(sys.argv) > 2 else None)
    elif len(sys.argv) > 1 and sys.argv[1] == "stop":     # interrupt playback, keep the server warm
        stop()
    elif len(sys.argv) > 1 and sys.argv[1] == "say":      # speak text via the warm server (argv or stdin)
        t = sys.argv[2] if len(sys.argv) > 2 else sys.stdin.read()
        if t.strip():
            send(t.strip())
    elif len(sys.argv) > 1:                               # one-shot synth: "文本" [out.wav]
        pipe = build_pipeline()
        if len(sys.argv) > 2:
            write_wav(pipe, sys.argv[1], sys.argv[2])
        else:
            play_stream(pipe, sys.argv[1])
    else:
        sys.exit('usage: speak.py say "文本" | stop | serve | "文本" [out.wav]')
