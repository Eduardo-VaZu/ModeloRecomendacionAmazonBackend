"""Logging uniforme para scripts y módulos."""

import logging

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format=_FORMAT, datefmt="%H:%M:%S")
    return logging.getLogger(name)
