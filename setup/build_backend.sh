#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"

echo "==> Build backend theo Makefile"
cd "$BACKEND_DIR"
make build_first_backend
make stop