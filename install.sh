#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
UI_DIR="$ROOT/ui"
BACKEND_DIR="$ROOT/backend"

echo "==> Kiểm tra quyền sudo"
if [ "$(id -u)" -ne 0 ]; then
  echo "Vui lòng chạy bằng sudo"
  exit 1
fi

echo "==> 1. Cài đặt package hệ thống cơ bản"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl wget git ca-certificates \
  python3 python3-venv python3-pip \
  docker.io docker-compose-v2

docker compose version >/dev/null 2>&1 || {
  echo "Docker Compose v2 chưa được cài đặt đúng cách." >&2
  exit 1
}

echo "==> 2. Thêm user vào group docker"
usermod -aG docker "$SUDO_USER" || true

echo "==> 3. Cài đặt UI"
cd "$UI_DIR"
bash create_launcher.sh
make install

echo "==> 4. Chuẩn bị thư mục model cho backend"
mkdir -p "$BACKEND_DIR/translator/models"
mkdir -p "$BACKEND_DIR/turboocr-cache"
mkdir -p "$BACKEND_DIR/logs"

echo "==> 5. Download model cho backend"
# Model cho translator AI
wget -O "$BACKEND_DIR/translator/models/Hy-MT2-7B-Q4_K_M.gguf" \
  "https://huggingface.co/longlv2k/OCRTranslatorModel/resolve/main/Hy-MT2-7B-Q4_K_M.gguf"

# Model OCR
wget -O "$BACKEND_DIR/turboocr-cache/det_1731963663662225912.trt" \
  "https://huggingface.co/longlv2k/OCRTranslatorModel/resolve/main/det_1731963663662225912.trt"

wget -O "$BACKEND_DIR/turboocr-cache/doc_ori_3322606490310336102.trt" \
  "https://huggingface.co/longlv2k/OCRTranslatorModel/resolve/main/doc_ori_3322606490310336102.trt"

wget -O "$BACKEND_DIR/turboocr-cache/cls_16244686492485880994.trt" \
  "https://huggingface.co/longlv2k/OCRTranslatorModel/resolve/main/cls_16244686492485880994.trt"

wget -O "$BACKEND_DIR/turboocr-cache/rec_5103253172810965958.trt" \
  "https://huggingface.co/longlv2k/OCRTranslatorModel/resolve/main/rec_5103253172810965958.trt"

echo "==> 7. Build backend theo Makefile"
cd "$BACKEND_DIR"
make build_first_backend
make stop

echo
echo "========================================"
echo "Hoàn tất cài đặt!"
echo "========================================"