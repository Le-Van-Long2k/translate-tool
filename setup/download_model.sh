#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"

echo "==> Kiểm tra quyền sudo"
if [ "$(id -u)" -ne 0 ]; then
  echo "Vui lòng chạy bằng sudo"
  exit 1
fi

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

ct2-transformers-converter \
  --model facebook/nllb-200-distilled-600M \
  --output_dir "$BACKEND_DIR/translator/models/nllb-600m-ct2" \
  --quantization int8 \
  --force