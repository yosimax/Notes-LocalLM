#!/bin/zsh

# usage:
#  server start
#    nohup ~/llama-models/Qwen3.8-27B.sh > ~/llama-models/log/20260911_1.log 2>&1 &
#  server stop
#    kill $(lsof -t -i:8080)
#  view log
#    less +F -MNX ~/llama-models/log/20260911_1.log
#
# Thinking Mode:
#  temperature=1.0, top_p=0.95, top_k=20, min_p=0.0, presence_penalty=0.0, repetition_penalty=1.0
#   --temp 1.0 --top-p 0.95 --top-k 20 --min-p 0.0 --presence-penalty 0.0 --repeat-penalty 1.0 \
# Instruct (or non-thinking) mode:
#  temperature=0.7, top_p=0.80, top_k=20, min_p=0.0, presence_penalty=1.5, repetition_penalty=1.0

##  --reasoning-preserve \
## --resoning off

llama-server \
  -m ~/llama-models/Qwen3.8-27B-UD-Q2_K_XL.gguf \
  --alias Qwen3.8-27B \
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
  --temp 0.7 --top-p 0.80 --top-k 20 --min-p 0.0 --presence-penalty 1.5 --repeat-penalty 1.0 \
  --host 127.0.0.1 --port 8080
