#!/bin/zsh

## For general tasks:
##   temperature=1.0, top_p=0.95, top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0
## For precise coding tasks:
##   temperature=0.6, top_p=0.95, top_k=20, min_p=0.0, presence_penalty=0.0, repetition_penalty=1.0

llama-server -m ~/llama-models/Ornith-1.5-9B-Q8_0.gguf \
  --alias Ornith-1.5 \
  --ctx-size 81920 \
  --cache-type-k q8_0 \
  --cache-type-v q8_0 \
  --flash-attn on \
  --n-gpu-layers 99 \
  --parallel 1 \
  -b 2048 \
  -ub 512 \
  --reasoning-preserve \
  --jinja \
  --temp 0.6 --top-p 0.95 --top-k 20 --min-p 0.0 --presence-penalty 0.0 --repeat-penalty 1.0 \
  --host 127.0.0.1 --port 8080
