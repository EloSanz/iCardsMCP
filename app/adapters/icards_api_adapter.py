"""
HTTP Adapter for iCards API
Example of a complete HTTP adapter implementation for iCards MCP server.

Este archivo muestra cómo se estructura un adaptador HTTP completo que:
1. Maneja autenticación y headers personalizados
2. Implementa lógica de reintento
3. Maneja errores específicos de la API
4. Procesa respuestas y las normaliza
5. Implementa timeouts y rate limiting
"""

import logging
import time
from typing import Any

import httpx

from app.config.config import config
from app.constants import (
    # Deck endpoints
    DECKS_CREATE,
    DECKS_DELETE,
    DECKS_GET,
    DECKS_LIST,
    DECKS_UPDATE,
    # Flashcard endpoints
    FLASHCARDS_CREATE,
    FLASHCARDS_DELETE,
    FLASHCARDS_GET,
    FLASHCARDS_LIST,
    FLASHCARDS_TAGS,
    FLASHCARDS_UPDATE,
    # Utility endpoints
    HEALTH,
    # Tag endpoints
    TAGS_CREATE,
    TAGS_DELETE,
    TAGS_GET,
    TAGS_LIST,
    TAGS_UPDATE,
    VERSION,
    # Helper function
    format_endpoint,
)

logger = logging.getLogger(__name__)


class IcardsApiAdapter:
    """
    HTTP Adapter for iCards REST API.

    Este adaptador maneja todas las comunicaciones HTTP con la API de iCards,
    incluyendo autenticación, reintentos, manejo de errores, y normalización
    de respuestas.
    """

    def __init__(self):
        """Initialize the iCards API adapter."""
        self.base_url = config.get("API_BASE_URL").rstrip("/")
        self.timeout = config.get("API_TIMEOUT", 30)
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds

        # Configurar headers base
        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "iCards-MCP/1.0",
        }

        # Configurar auth si existe
        auth_token = config.get("AUTH_TOKEN")
        if auth_token:
            self.base_headers["Authorization"] = f"Bearer {auth_token}"

        # Crear cliente HTTP con configuración avanzada
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.base_headers,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

        logger.info(f"Initialized iCards API adapter for {self.base_url}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data for POST/PUT
            params: Query parameters for GET
            headers: Additional headers

        Returns:
            Normalized response data

        Raises:
            httpx.HTTPStatusError: For HTTP errors
            Exception: For other errors
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"{method} {url} (attempt {attempt + 1}/{self.max_retries})")

                # Preparar request según método
                if method.upper() == "GET":
                    response = await self.client.get(url, params=params, headers=request_headers)
                elif method.upper() == "POST":
                    response = await self.client.post(url, json=data, headers=request_headers)
                elif method.upper() == "PUT":
                    response = await self.client.put(url, json=data, headers=request_headers)
                elif method.upper() == "DELETE":
                    response = await self.client.delete(url, headers=request_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()

                # Procesar respuesta
                if response.status_code == 204:  # No Content
                    return {"success": True}

                response_data = response.json()

                # Normalizar respuesta según convención de la API
                return self._normalize_response(response_data)

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"

                # Manejar errores específicos
                if e.response.status_code == 401:
                    logger.error("Authentication failed - check AUTH_TOKEN")
                    raise Exception("Authentication required") from e
                if e.response.status_code == 403:
                    logger.error("Access forbidden")
                    raise Exception("Access denied") from e
                if e.response.status_code == 404:
                    logger.error(f"Resource not found: {url}")
                    raise Exception("Resource not found") from e
                if e.response.status_code == 422:
                    logger.error(f"Validation error: {e.response.text}")
                    raise Exception("Invalid request data") from e
                if e.response.status_code >= 500:
                    # Retry on server errors
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Server error, retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    logger.error(f"Server error after {self.max_retries} attempts")
                    raise Exception("Server error") from e
                # No retry for other errors
                logger.error(f"HTTP error: {error_msg}")
                raise

            except httpx.RequestError as e:
                # Network errors - retry
                if attempt < self.max_retries - 1:
                    logger.warning(f"Network error, retrying in {self.retry_delay}s: {str(e)}")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                logger.error(f"Network error after {self.max_retries} attempts: {str(e)}")
                raise Exception("Network error") from e

            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

        # This should never be reached, but just in case
        raise Exception("Request failed after all retries")

    def _normalize_response(self, response_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize API response to consistent format.

        Args:
            response_data: Raw response from API

        Returns:
            Normalized response data
        """
        # La API de iCards podría tener diferentes formatos de respuesta
        # Aquí normalizamos a un formato consistente

        if isinstance(response_data, dict):
            # Si ya es un dict, probablemente está bien
            return response_data
        if isinstance(response_data, list):
            # Si es una lista, wrappeamos
            return {"items": response_data, "count": len(response_data)}
        # Otros tipos
        return {"data": response_data}

    # ===== FLASHCARD ENDPOINTS =====

    async def create_flashcard(self, flashcard_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new flashcard."""
        logger.info(f"Creating flashcard in deck: {flashcard_data.get('deck_name')}")
        return await self._make_request("POST", FLASHCARDS_CREATE, data=flashcard_data)

    async def get_flashcard(self, flashcard_id: int) -> dict[str, Any]:
        """Get flashcard by ID."""
        logger.info(f"Getting flashcard {flashcard_id}")
        endpoint = format_endpoint(FLASHCARDS_GET, flashcard_id=flashcard_id)
        return await self._make_request("GET", endpoint)

    async def update_flashcard(self, flashcard_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update flashcard."""
        logger.info(f"Updating flashcard {flashcard_id}")
        endpoint = format_endpoint(FLASHCARDS_UPDATE, flashcard_id=flashcard_id)
        return await self._make_request("PUT", endpoint, data=data)

    async def delete_flashcard(self, flashcard_id: int) -> dict[str, Any]:
        """Delete flashcard."""
        logger.info(f"Deleting flashcard {flashcard_id}")
        endpoint = format_endpoint(FLASHCARDS_DELETE, flashcard_id=flashcard_id)
        return await self._make_request("DELETE", endpoint)

    async def list_flashcards(self, **params) -> dict[str, Any]:
        """List flashcards with optional filters."""
        logger.info(f"Listing flashcards with params: {params}")
        return await self._make_request("GET", FLASHCARDS_LIST, params=params)

    # ===== DECK ENDPOINTS =====

    async def create_deck(self, deck_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new deck."""
        logger.info(f"Creating deck: {deck_data.get('name')}")
        return await self._make_request("POST", DECKS_CREATE, data=deck_data)

    async def get_deck(self, deck_id: int) -> dict[str, Any]:
        """Get deck by ID."""
        logger.info(f"Getting deck {deck_id}")
        endpoint = format_endpoint(DECKS_GET, deck_id=deck_id)
        return await self._make_request("GET", endpoint)

    async def update_deck(self, deck_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update deck."""
        logger.info(f"Updating deck {deck_id}")
        endpoint = format_endpoint(DECKS_UPDATE, deck_id=deck_id)
        return await self._make_request("PUT", endpoint, data=data)

    async def delete_deck(self, deck_id: int) -> dict[str, Any]:
        """Delete deck."""
        logger.info(f"Deleting deck {deck_id}")
        endpoint = format_endpoint(DECKS_DELETE, deck_id=deck_id)
        return await self._make_request("DELETE", endpoint)

    async def list_decks(self) -> dict[str, Any]:
        """List all decks."""
        logger.info("Listing all decks")
        return await self._make_request("GET", DECKS_LIST)

    # ===== TAG ENDPOINTS =====

    async def create_tag(self, tag_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new tag."""
        logger.info(f"Creating tag: {tag_data.get('name')}")
        return await self._make_request("POST", TAGS_CREATE, data=tag_data)

    async def get_tag(self, tag_id: int) -> dict[str, Any]:
        """Get tag by ID."""
        logger.info(f"Getting tag {tag_id}")
        endpoint = format_endpoint(TAGS_GET, tag_id=tag_id)
        return await self._make_request("GET", endpoint)

    async def update_tag(self, tag_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """Update tag."""
        logger.info(f"Updating tag {tag_id}")
        endpoint = format_endpoint(TAGS_UPDATE, tag_id=tag_id)
        return await self._make_request("PUT", endpoint, data=data)

    async def delete_tag(self, tag_id: int) -> dict[str, Any]:
        """Delete tag."""
        logger.info(f"Deleting tag {tag_id}")
        endpoint = format_endpoint(TAGS_DELETE, tag_id=tag_id)
        return await self._make_request("DELETE", endpoint)

    async def list_tags(self) -> dict[str, Any]:
        """List all tags."""
        logger.info("Listing all tags")
        return await self._make_request("GET", TAGS_LIST)

    async def add_tags_to_flashcard(self, flashcard_id: int, tag_ids: list[int]) -> dict[str, Any]:
        """Add tags to flashcard."""
        logger.info(f"Adding tags {tag_ids} to flashcard {flashcard_id}")
        data = {"tag_ids": tag_ids}
        endpoint = format_endpoint(FLASHCARDS_TAGS, flashcard_id=flashcard_id)
        return await self._make_request("POST", endpoint, data=data)

    async def remove_tags_from_flashcard(self, flashcard_id: int, tag_ids: list[int]) -> dict[str, Any]:
        """Remove tags from flashcard."""
        logger.info(f"Removing tags {tag_ids} from flashcard {flashcard_id}")
        data = {"tag_ids": tag_ids}
        endpoint = format_endpoint(FLASHCARDS_TAGS, flashcard_id=flashcard_id)
        return await self._make_request("DELETE", endpoint, data=data)

    # ===== UTILITY METHODS =====

    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = await self._make_request("GET", HEALTH)
            return response.get("status") == "healthy"
        except Exception:
            return False

    async def get_api_version(self) -> str:
        """Get API version."""
        try:
            response = await self._make_request("GET", VERSION)
            return response.get("version", "unknown")
        except Exception:
            return "unknown"

    async def close(self):
        """Close the HTTP client."""
        logger.info("Closing iCards API adapter")
        await self.client.aclose()


# Singleton instance
_icards_adapter_instance = None


def get_icards_adapter() -> IcardsApiAdapter:
    """Get singleton instance of iCards API adapter."""
    global _icards_adapter_instance
    if _icards_adapter_instance is None:
        _icards_adapter_instance = IcardsApiAdapter()
    return _icards_adapter_instance
