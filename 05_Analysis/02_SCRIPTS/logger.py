"""
logger.py
=========
Centralised logging for the N-HYPPADEC GIS Pipeline.
Every module imports get_logger() to write timestamped log entries.
Logs are written to 05_Analysis/04_QC/ with the module name and date.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from config import ANALYSIS_QC


def get_logger(module_name: str, log_to_file: bool = True) -> logging.Logger:
    """
    Return a configured logger for the given module.

    Parameters
    ----------
    module_name : str
        Name of the calling module, e.g. '01_ingest'.
    log_to_file : bool
        Whether to write log output to a file in ANALYSIS_QC/.

    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — always added
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler — writes to 05_Analysis/04_QC/
        if log_to_file:
            ANALYSIS_QC.mkdir(parents=True, exist_ok=True)
            log_file = ANALYSIS_QC / f"LOG_{module_name}_{datetime.now().strftime('%Y%m%d')}.log"
            fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger


def log_separator(logger: logging.Logger, title: str = "") -> None:
    """Log a visual separator for readability."""
    line = "=" * 60
    if title:
        logger.info(f"{line}")
        logger.info(f"  {title}")
        logger.info(f"{line}")
    else:
        logger.info(line)
