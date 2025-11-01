"""Module to load instructions from a markdown file."""

import os
import logging

logger = logging.getLogger(__name__)


def load_instructions(instructions_path: str) -> str:
    """
    Load instructions from a markdown file.

    Args:
        instructions_path: Path to the instructions file
    Returns:
        str: String containing the instructions in markdown format
    """
    if not os.path.exists(instructions_path):
        logger.warning(f"Instructions file not found: {instructions_path}. Using empty instructions.")
        return ""

    try:
        with open(instructions_path, "r", encoding="utf-8") as f:
            logger.debug(f"Loading instructions from {instructions_path}")
            return f.read()
    except Exception as e:
        logger.error(f"Error loading instructions: {str(e)}")
        return ""
