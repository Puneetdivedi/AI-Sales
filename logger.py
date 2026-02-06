import logging
from logging.handlers import RotatingFileHandler
from config import Config, ensure_data_files


def _configure_root_logger():
    root = logging.getLogger()
    if root.handlers:
        return root

    ensure_data_files()
    level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
    root.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    file_handler = RotatingFileHandler(
        Config.LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)
    return root


def get_logger(name):
    _configure_root_logger()
    return logging.getLogger(name)
