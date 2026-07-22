"""
Logging sozlamalari.
Har bir muhim amal shu logger orqali yoziladi (registratsiya, transfer,
withdraw, admin amallari va h.k.).
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from app.config import config


def setup_logger() -> logging.Logger:
    os.makedirs(os.path.dirname(config.log_path) or ".", exist_ok=True)

    logger = logging.getLogger("yumi_almaz")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        config.log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
