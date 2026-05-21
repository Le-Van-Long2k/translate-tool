# Sử dụng image NVIDIA làm base
FROM nvcr.io/nvidia/pytorch:24.12-py3

# Thiết lập thư mục làm việc
WORKDIR /app

# --- Cài đặt thư viện hệ thống cho OpenCV ---
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu-core \
    fonts-noto \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy các file cấu hình dependency trước để tận dụng cache của Docker layer
COPY pyproject.toml uv.lock ./

# Cài đặt môi trường ảo và dependencies vào thư mục .venv
# --no-install-project: Chỉ cài dependencies, chưa cài source code của chính project
RUN uv sync --frozen --no-install-project

# Biến môi trường để đảm bảo Python sử dụng đúng venv đã cài
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# install
COPY install/ /app/install/


# Mở port cho Gradio
EXPOSE 7860 
EXPOSE 8052

# CMD ["uv", "run", "gradio", "app.py"]
# CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8052"]