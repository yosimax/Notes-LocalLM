# AGENTS.md

Notes-LocalLM is a local-LLM test bench, not an app. There is no build, test,
lint, typecheck, or CI. Do not look for `package.json`, `tsconfig`, or a test
runner — there is none. The executable source of truth is the shell scripts.

## Layout

- `case2/` — runnable `llama-server` launch scripts + their logs and HTML outputs. This is where work happens.
- `case1/` — raw `.log` dumps only (no scripts).
- Logs and HTML land under `~/llama-models/` (see scripts), not in-repo.

## Running a model (case2/*.sh)

Scripts are `#!/bin/zsh`. Each starts a server, binds `127.0.0.1:8080`, and
writes to a log.

- Start: `nohup ~/path/to/case2/*.sh > ~/llama-models/log/DATE.log 2>&1 &`
- Stop: `kill $(lsof -t -i:8080)`
- Tail log: `less +F ~/llama-models/log/DATE.log`

## Constraints

- All servers use port `8080` — only one can run at a time. Kill the old one
  before starting a new model.
- `--ctx-size` differs per model: `131072` for the 128K Ornith-1.5 script,
  `81920` for the 80K and Qwen scripts.
- Models live in `~/llama-models/` with distinct filenames
  (e.g. `Ornith-1.5-9B-Q4_K_M.gguf`, `Ornith-1.5-9B-Q8_0.gguf`, `Qwen3.8-27B-UD-Q2_K_XL.gguf`).

## Temperature presets

- General tasks: `--temp 1.0 --presence-penalty 1.5`
- Precise coding: `--temp 0.6 --presence-penalty 0.0`
- Qwen3.8-27B thinking: `--temp 1.0`; instruct/non-thinking: `--temp 0.7 --presence-penalty 1.5`

All scripts share `--top-p 0.95 --top-k 20`, `--flash-attn on`, `--n-gpu-layers 99`,
`-b 2048 -ub 512`, `--reasoning-preserve`, `--jinja`.
