from __future__ import annotations

import logging
from typing import ClassVar


class LoggerFactory:
    """
    Centralized logger factory for the project.

    Responsibilities:
        - Create consistently configured loggers
        - Avoid duplicate handlers
        - Define the default log format and level
    """

    DEFAULT_LEVEL: ClassVar[int] = logging.INFO

    DEFAULT_FORMAT: ClassVar[str] = (
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )

    DATE_FORMAT: ClassVar[str] = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def get_logger(
        cls,
        name: str,
        level: int | None = None,
    ) -> logging.Logger:
        """
        Return a configured logger.

        Args:
            name:
                Logger name, usually __name__.

            level:
                Optional logging level. Defaults to DEFAULT_LEVEL.

        Returns:
            Configured logger instance.
        """

        cls._validate_name(name)

        logger = logging.getLogger(name)

        logger.setLevel(
            level
            if level is not None
            else cls.DEFAULT_LEVEL
        )

        logger.propagate = False

        if not logger.handlers:
            handler = logging.StreamHandler()

            formatter = logging.Formatter(
                fmt=cls.DEFAULT_FORMAT,
                datefmt=cls.DATE_FORMAT,
            )

            handler.setFormatter(formatter)

            logger.addHandler(handler)

        return logger

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str):
            raise TypeError(
                "Logger name must be a string."
            )

        if not name.strip():
            raise ValueError(
                "Logger name cannot be empty."
            )