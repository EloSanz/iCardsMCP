"""
Configuration file for the iCards MCP server.
Simplified configuration for production deployment.
"""

import logging
import os
from pathlib import Path
from typing import Any

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
INSTRUCTIONS_FILENAME = "api_instructions.md"

# Single unified configuration
config_values = {
    "LOG_LEVEL": "INFO",
    "MCP_ICARDS_NAME": "iCards-MCP",
    "MCP_ICARDS_DESCRIPTION": "iCards MCP Server",
    # Use local docs/InstructionsMCP folder for instructions
    "MCP_ICARDS_INSTRUCTIONS_PATH": str(Path(__file__).parent.parent.parent / "docs" / "InstructionsMCP" / INSTRUCTIONS_FILENAME),
    # API Configuration
    # 1. LOCAL_API_BASE_URL (para desarrollo local desde Cursor)
    # 2. API_BASE_URL (para producción o desarrollo manual)
    # 3. Default localhost (fallback)
    "API_BASE_URL": os.getenv("LOCAL_API_BASE_URL") or os.getenv("API_BASE_URL", "http://localhost:3000"),
    "API_TIMEOUT": int(os.getenv("API_TIMEOUT", "30")),
}


class Config:
    @staticmethod
    def get(config_name: str) -> Any:
        """
        Get configuration value by name.

        Args:
            config_name: The name of the configuration value to retrieve

        Returns:
            The configuration value
        """
        config_value = config_values.get(config_name)

        # Avoid logging sensitive configuration values
        sensitive_keys = ["API_KEY", "SECRET_KEY", "AUTH_TOKEN"]
        if config_name in sensitive_keys:
            logger.debug(f"Getting config {config_name}: [REDACTED]")
        else:
            logger.debug(f"Getting config {config_name}: {config_value}")

        return config_value


# Create a global instance for backward compatibility
config = Config()
