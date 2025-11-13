"""Structured logging configuration for battery pack simulations."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
	name: str = "battery_pack",
	level: int = logging.INFO,
	log_file: Optional[Path | str] = None,
	format_string: Optional[str] = None,
) -> logging.Logger:
	"""Configure and return a structured logger.

	Args:
		name: Logger name (typically module name)
		level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
		log_file: Optional file path to write logs to
		format_string: Custom format string (uses default if None)

	Returns:
		Configured logger instance
	"""
	logger = logging.getLogger(name)
	logger.setLevel(level)

	# Remove existing handlers to avoid duplicates
	logger.handlers.clear()

	# Default format: timestamp, level, name, message
	if format_string is None:
		format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

	formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

	# Console handler
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setLevel(level)
	console_handler.setFormatter(formatter)
	logger.addHandler(console_handler)

	# File handler (if specified)
	if log_file is not None:
		log_file = Path(log_file)
		log_file.parent.mkdir(parents=True, exist_ok=True)
		file_handler = logging.FileHandler(log_file, mode="a")
		file_handler.setLevel(level)
		file_handler.setFormatter(formatter)
		logger.addHandler(file_handler)

	# Prevent propagation to root logger
	logger.propagate = False

	return logger


# Default logger instance
default_logger = setup_logger()

