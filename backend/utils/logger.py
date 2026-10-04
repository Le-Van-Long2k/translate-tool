import logging
import os
from datetime import datetime


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)
        filename = os.path.join("logs", datetime.now().strftime("log_%Y-%m-%d.log"))

        handler = logging.FileHandler(filename, encoding="utf-8")

        formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s")

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Block logs from third-party libraries
    noisy_loggers = [
        "httpx",
        "urllib3",
        "httpcore",
        "matplotlib",
        "gradio",
        "huggingface_hub",
        "asyncio",
        "PIL",
        "multipart",
        "python_multipart",
        "python_multipart.multipart",
    ]

    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.WARNING)
        logging.getLogger(name).propagate = False

    return logger
