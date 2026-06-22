---
name: local-llm
description: Run a prompt over local text through the on-device Ollama model (qwen3.6:35b-mlx, Apple MLX). Use to summarize or process transcripts, logs, or docs locally — no API cost, nothing leaves the machine.
---

# Local LLM (Ollama)

Model: `qwen3.6:35b-mlx` — Apple MLX MoE (35B/3B active), 256K context (input+output shared).

## Run
Write the prompt to a file, then append the input file:
```bash
set -o pipefail
ollama run --nowordwrap qwen3.6:35b-mlx "$(cat /tmp/prompt.txt)

$(cat /tmp/input.txt)" </dev/null 2>>/tmp/llm_err.log | sed '/Thinking\.\.\./,/done thinking/d' > /tmp/out.txt
```
- Keep `</dev/null` — hangs when backgrounded otherwise.
- `set -o pipefail` — without it `$?` is `sed`'s, so an ollama failure reads as success.
- stderr (spinner + errors) → `/tmp/llm_err.log`; check it when `$?` is nonzero.
- Redirect stdout to a file; `grep`/`Read` it on demand.
- `sed` drops the thinking block. Keep thinking: remove the `sed`. Disable thinking: add `/no_think` to the prompt.
- Short prompt: inline it instead of `cat /tmp/prompt.txt`.

## Notes
- List models: `ollama list`. Live-loaded model: `ollama ps`.
- Model stays loaded during generation + a 5-min keep-alive, then unloads.
