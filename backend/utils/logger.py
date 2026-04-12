import logging
from datetime import datetime


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        filename = datetime.now().strftime("log_%Y-%m-%d.log")

        handler = logging.FileHandler(filename, encoding="utf-8")

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Block logs from third-party libraries
    noisy_loggers = [
        "httpx",
        "urllib3",
        "gradio",
        "huggingface_hub",
        "asyncio",
    ]

    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.WARNING)
        logging.getLogger(name).propagate = False

    return logger
