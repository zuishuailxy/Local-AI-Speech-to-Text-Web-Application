"""Logging configuration for the application.

By default logs go to stderr in the existing text format.  ``LOG_FILE`` adds a
rotating file handler; ``LOG_FORMAT=json`` switches that handler to one JSON
object per line.  Audio and recognized text are never logged.
"""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler

from app.config import Settings

TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_HANDLER_MARKER = "_stt_handler"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "time": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            },
            ensure_ascii=False,
        )


def configure_logging(settings: Settings) -> None:
    app_logger = logging.getLogger("app")
    app_logger.setLevel(settings.log_level)

    for handler in list(app_logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            app_logger.removeHandler(handler)
            handler.close()

    if settings.log_file is None:
        logging.basicConfig(level=settings.log_level, format=TEXT_FORMAT)
        app_logger.propagate = True
        return

    settings.log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    formatter: logging.Formatter
    if settings.log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(TEXT_FORMAT)
    handler.setFormatter(formatter)
    setattr(handler, _HANDLER_MARKER, True)
    app_logger.addHandler(handler)
    app_logger.propagate = False


__all__ = ["JsonFormatter", "TEXT_FORMAT", "configure_logging"]
