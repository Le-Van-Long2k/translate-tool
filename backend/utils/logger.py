import logging
from datetime import datetime


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        filename = datetime.now().strftime("log_%Y-%m-%d.log")

        handler = logging.FileHandler(filename, encoding="utf-8")

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Block logs from third-party libraries
    noisy_loggers = [
        "httpx",
        "urllib3",
        "httpcore",  # Fix lỗi hiện log connect_tcp/tls
        "matplotlib",  # Fix lỗi hiện log nạp font và backend
        "gradio",
        "huggingface_hub",
        "asyncio",
        "PIL",  # Thư viện ảnh đôi khi cũng log DEBUG
    ]

    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.WARNING)
        logging.getLogger(name).propagate = False

    return logger
