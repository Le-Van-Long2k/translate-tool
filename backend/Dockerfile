FROM python:3.12-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# --- Cài đặt thư viện hệ thống cho OpenCV ---
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    # OpenCV
    libgl1 \
    libglib2.0-0 \
    # Fonts
    fonts-noto \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy pyproject.toml
COPY pyproject.toml ./

# Xóa lock cũ và tạo lại uv.lock
RUN rm -f uv.lock && \
    uv lock

# Cài dependencies theo lock mới
RUN uv sync --frozen --no-install-project

# Biến môi trường để đảm bảo Python sử dụng đúng venv đã cài
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1


EXPOSE 8052

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8052"]