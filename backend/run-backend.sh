#!/usr/bin/env bash
set -eu

LOG_FILE="/tmp/translator-backend.log"
mkdir -p "$(dirname "$LOG_FILE")"

nohup docker exec translator-backend bash -lc 'uv run uvicorn main:app --host 0.0.0.0 --port 8052' >>"$LOG_FILE" 2>&1 &

echo "Backend started in background. Log: $LOG_FILE"
