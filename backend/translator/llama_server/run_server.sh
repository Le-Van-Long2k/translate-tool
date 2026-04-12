#!/bin/bash

/home/test/llama.cpp/build/bin/llama-server \
  -m /home/test/llama.cpp/custom-models/gemma-4-e2b-it-Q8_0.gguf \
  -ngl all \
  -c 2048 \
  -b 1024 \
  -ub 1024 \
  -fa on \
  -ctk q8_0 \
  -ctv q8_0 \
  -t 8 \
  -tb 8 \
  --host 127.0.0.1 \
  --port 8121 \
  --no-cache-prompt \
  --cache-reuse 0 \
  --slot-prompt-similarity 0 \
  --clear-idle \
  --reasoning off \
  --parallel 1