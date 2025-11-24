"""Base service for iCards MCP server."""

import logging
import os
from typing import Any

import httpx

from app.config.config import config

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common HTTP functionality."""

    def __init__(self):
        """Initialize the base service with HTTP client."""
        self.base_url = config.get("API_BASE_URL")
        self.timeout = config.get("API_TIMEOUT")

        # Get auth token from environment or temp file (for MCP proxy)
        auth_token = os.getenv("AUTH_TOKEN") or os.getenv("FLASHCARD_API_TOKEN")

        # If not found, try to read from temp file (written by server middleware)
        if not auth_token:
            try:
                import tempfile
                temp_file = os.path.join(tempfile.gettempdir(), "icards_auth_token.txt")
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        auth_token = f.read().strip()
            except Exception:
                pass

        # Log initialization details (with partial token for security) - only in debug
        token_preview = f"{auth_token[:20]}..." if auth_token and len(auth_token) > 20 else "None"
        logger.debug(f"🔧 BaseService initialized - API: {self.base_url}, Token: {token_preview}")

        # Create headers
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        # Add authorization header if token is available
        if auth_token:
            # If token already starts with "Bearer ", use as-is, otherwise add it
            if auth_token.startswith("Bearer "):
                headers["Authorization"] = auth_token
            else:
                headers["Authorization"] = f"Bearer {auth_token}"

        # Create HTTP client with timeout and auth
        self.client = httpx.AsyncClient(timeout=self.timeout, headers=headers)

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"🌐 GET {url}")
        if params:
            logger.debug(f"   Params: {params}")

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            json_response = response.json()
            
            # Log response summary
            if isinstance(json_response, dict):
                if "decks" in json_response:
                    logger.debug(f"✅ Response: {len(json_response.get('decks', []))} decks")
                elif "flashcards" in json_response:
                    logger.debug(f"✅ Response: {len(json_response.get('flashcards', []))} flashcards")
                elif "data" in json_response:
                    logger.debug(f"✅ Response: data field present")
            
            return json_response
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP {e.response.status_code} for GET {url}")
            logger.error(f"   Response: {e.response.text[:200]}")
            raise
        except Exception as e:
            logger.error(f"❌ Error making GET request to {url}: {str(e)}")
            raise

    async def _post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
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

    async def _put(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
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

    async def _delete(self, endpoint: str) -> dict[str, Any]:
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

    def _normalize_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize API responses to a consistent format.

        Handles different response structures from the API:
        - {"decks": [...]} - already normalized
        - {"data": [...]} - needs normalization based on content type
        - {"success": true, "data": [...]} - needs normalization

        Detects content type:
        - Items with 'front'/'back' → {"flashcards": [...]}
        - Items with 'name' → {"decks": [...]}

        Args:
            response: The API response to normalize

        Returns:
            Normalized response with consistent structure
        """
        logger.debug(f"🔄 Normalizing response...")
        logger.debug(f"   Response keys: {list(response.keys())}")

        # If response has 'data' field but no 'decks'/'flashcards' field, normalize it
        if "data" in response and "decks" not in response and "flashcards" not in response:
            data_items = response.get("data", [])
            logger.debug(f"   Found 'data' field with {len(data_items) if isinstance(data_items, list) else 'unknown'} items")

            # Keep original response metadata but normalize the array key
            normalized = {**response}

            if data_items and isinstance(data_items, list):
                # Detect content type based on first item
                first_item = data_items[0] if data_items else None
                if first_item and isinstance(first_item, dict):
                    logger.debug(f"   First item keys: {list(first_item.keys())}")
                    if "front" in first_item and "back" in first_item:
                        # This is flashcards
                        logger.debug(f"   ✅ Detected flashcards → normalized['flashcards'] = {len(data_items)} items")
                        normalized["flashcards"] = data_items
                    elif "name" in first_item:
                        # This is decks
                        logger.debug(f"   ✅ Detected decks → normalized['decks'] = {len(data_items)} items")
                        normalized["decks"] = data_items
                    else:
                        # Unknown type, keep as data
                        logger.debug(f"   ⚠️ Unknown type, keeping as 'data'")
                        normalized["data"] = data_items
                else:
                    # Empty or not a dict, keep as data
                    logger.debug(f"   ⚠️ Empty or not a dict, keeping as 'data'")
                    normalized["data"] = data_items
            else:
                # Empty list or not a list, keep as data
                logger.debug(f"   ⚠️ Empty list or not a list")
                normalized["data"] = data_items

            # Remove 'data' to avoid duplication (only if we normalized it)
            if "decks" in normalized or "flashcards" in normalized:
                if "data" in normalized:
                    logger.debug(f"   Removing duplicate 'data' field")
                    del normalized["data"]

            logger.debug(f"   Final normalized keys: {list(normalized.keys())}")
            return normalized

        # If response doesn't need normalization, return as-is
        logger.debug(f"   No normalization needed")
        return response
