"""Base service for iCards MCP server."""

import logging
import os
import httpx
from typing import Dict, Any, Optional

from app.config.config import config

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common HTTP functionality."""

    def __init__(self):
        """Initialize the base service with HTTP client."""
        self.base_url = config.get("API_BASE_URL")
        self.timeout = config.get("API_TIMEOUT")

        # Get auth token from environment
        auth_token = os.getenv("AUTH_TOKEN") or os.getenv("FLASHCARD_API_TOKEN")

        # Create headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Add authorization header if token is available
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        # Create HTTP client with timeout and auth
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=headers
        )

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"GET {url} with params: {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for GET {url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error making GET request to {url}: {str(e)}")
            raise

    async def _post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request to the API."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"POST {url} with data: {data}")

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for POST {url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error making POST request to {url}: {str(e)}")
            raise

    async def _put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request to the API."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"PUT {url} with data: {data}")

        try:
            response = await self.client.put(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for PUT {url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error making PUT request to {url}: {str(e)}")
            raise

    async def _delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request to the API."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"DELETE {url}")

        try:
            response = await self.client.delete(url)
            response.raise_for_status()
            return response.json() if response.content else {"success": True}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for DELETE {url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error making DELETE request to {url}: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize API responses to a consistent format.

        Handles different response structures from the API:
        - {"decks": [...]} - already normalized
        - {"data": [...]} - needs normalization to {"decks": [...]}
        - {"success": true, "data": [...]} - needs normalization

        Args:
            response: The API response to normalize

        Returns:
            Normalized response with consistent structure
        """
        # If response has 'data' field but no 'decks' field, normalize it
        if "data" in response and "decks" not in response:
            # Keep original response metadata but normalize the array key
            normalized = {**response}
            normalized["decks"] = response.get("data", [])
            # Remove 'data' to avoid duplication
            if "data" in normalized:
                del normalized["data"]
            return normalized

        # If response doesn't have either, return as-is
        return response
