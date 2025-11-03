"""
Configuration file for the iCards MCP server.
This has different configurations for each scope (local, prod).
The scope is used to determine which configuration to use based on the SCOPE environment variable.
The default configuration is local when SCOPE is not set.

If you need to add a new scope, just add a new configuration object and add it to the get method.
"""

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants to avoid duplication
INSTRUCTIONS_FILENAME = "api_instructions.md"


local_config = {
    "LOG_LEVEL": "DEBUG",
    "MCP_ICARDS_NAME": "iCards-MCP-Local",
    "MCP_ICARDS_DESCRIPTION": "iCards MCP Server - Local Development",
    "MCP_ICARDS_INSTRUCTIONS_PATH": str(Path(__file__).parent.parent / "mcp" / "instructions" / INSTRUCTIONS_FILENAME),
    "SCOPE": "local",
    # API Configuration
    "API_BASE_URL": os.getenv("API_BASE_URL", "http://localhost:3000"),
    "API_TIMEOUT": 30,
}

prod_config = {
    "LOG_LEVEL": "WARNING",
    "MCP_ICARDS_NAME": "iCards-MCP-Prod",
    "MCP_ICARDS_DESCRIPTION": "iCards MCP Server - Production",
    "MCP_ICARDS_INSTRUCTIONS_PATH": str(Path(__file__).parent.parent / "mcp" / "instructions" / INSTRUCTIONS_FILENAME),
    "SCOPE": "prod",
    # API Configuration
    "API_BASE_URL": os.getenv("API_BASE_URL"),
    "API_TIMEOUT": 30,
}


class Config:
    @staticmethod
    def get(config_name: str) -> Any:
        """
        Get configuration value by name based on environment variables.

        Args:
            config_name: The name of the configuration value to retrieve

        Returns:
            The configuration value for the current environment
        """
        scope = os.getenv("SCOPE", "local")  # Default to local

        internal_config: dict[str, Any] = {}

        if scope == "prod":
            internal_config = prod_config
        elif scope == "local":
            internal_config = local_config
        else:
            internal_config = local_config  # Default to local

        config_value = internal_config.get(config_name)

        # Avoid logging sensitive configuration values
        sensitive_keys = ["API_KEY", "SECRET_KEY", "AUTH_TOKEN"]
        if config_name in sensitive_keys:
            logger.debug(f"Getting config {config_name}: [REDACTED]")
        else:
            logger.debug(f"Getting config {config_name}: {config_value}")

        return config_value

    class ScopeEnvironment(Enum):
        PROD = "prod"
        LOCAL = "local"

    @staticmethod
    def get_env() -> ScopeEnvironment:
        """
        Get environment value based on SCOPE environment variable.
        Returns ScopeEnvironment enum value. Defaults to LOCAL.
        """
        scope = os.getenv("SCOPE", "local")  # Default to local

        if scope == "prod":
            return Config.ScopeEnvironment.PROD
        if scope == "local":
            return Config.ScopeEnvironment.LOCAL
        return Config.ScopeEnvironment.LOCAL  # Default to local


# Create a global instance for backward compatibility
config = Config()
