"""Flashcard service for iCards MCP server."""

import logging
from typing import Any

from app.constants import (
    FLASHCARDS_BULK_CREATE,
    FLASHCARDS_BY_DECK,
    FLASHCARDS_CREATE,
    FLASHCARDS_DELETE,
    FLASHCARDS_GET,
    FLASHCARDS_LIST,
    FLASHCARDS_SEARCH,
    FLASHCARDS_UPDATE,
    format_endpoint,
)

from .base_service import BaseService

logger = logging.getLogger(__name__)


class FlashcardService(BaseService):
    """Service for flashcard operations using iCards REST API."""

    _instance = None

    def __init__(self):
        """Initialize the flashcard service."""
        super().__init__()

    @classmethod
    def get_instance(cls):
        """Get singleton instance of FlashcardService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_flashcard(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new flashcard.

        Args:
            data: Flashcard data including front, back, deck_name, etc.

        Returns:
            Created flashcard data.
        """
        logger.debug("Creating flashcard")
        try:
            return await self._post(FLASHCARDS_CREATE, data)
        except Exception as e:
            logger.error(f"Error creating flashcard: {str(e)}")
            raise

    async def get_flashcard(self, flashcard_id: int) -> dict[str, Any]:
        """
        Get a specific flashcard by ID.

        Args:
            flashcard_id: The flashcard ID.

        Returns:
            Flashcard data.
        """
        logger.debug(f"Getting flashcard {flashcard_id}")
        try:
            endpoint = format_endpoint(FLASHCARDS_GET, flashcard_id=flashcard_id)
            return await self._get(endpoint)
        except Exception as e:
            logger.error(f"Error getting flashcard {flashcard_id}: {str(e)}")
            raise

    async def update_flashcard(self, flashcard_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """
        Update a flashcard.

        Args:
            flashcard_id: The flashcard ID.
            data: Updated flashcard data.

        Returns:
            Updated flashcard data.
        """
        logger.debug(f"Updating flashcard {flashcard_id}")
        try:
            endpoint = format_endpoint(FLASHCARDS_UPDATE, flashcard_id=flashcard_id)
            return await self._put(endpoint, data)
        except Exception as e:
            logger.error(f"Error updating flashcard {flashcard_id}: {str(e)}")
            raise

    async def delete_flashcard(self, flashcard_id: int) -> dict[str, Any]:
        """
        Delete a flashcard.

        Args:
            flashcard_id: The flashcard ID.

        Returns:
            Deletion confirmation.
        """
        logger.debug(f"Deleting flashcard {flashcard_id}")
        try:
            endpoint = format_endpoint(FLASHCARDS_DELETE, flashcard_id=flashcard_id)
            return await self._delete(endpoint)
        except Exception as e:
            logger.error(f"Error deleting flashcard {flashcard_id}: {str(e)}")
            raise

    async def list_flashcards(
        self,
        deck_name: str | None = None,
        deck_id: int | None = None,
        limit: int | None = 50,
        offset: int | None = 0,
        sort_by: str | None = "created",
        filter_difficulty: int | None = None,
        tags: list[str] | None = None,
        all_cards: bool = False,
    ) -> dict[str, Any]:
        """
        List flashcards with optional filtering.

        Args:
            deck_name: Filter by deck name (deprecated, use deck_id).
            deck_id: Filter by deck ID (preferred).
            limit: Maximum number of results.
            offset: Number of results to skip.
            sort_by: Sort criteria.
            filter_difficulty: Filter by difficulty level.
            tags: Filter by tags.
            all_cards: If True, adds all=true parameter to get all cards without pagination.

        Returns:
            List of flashcards with pagination info.
        """
        logger.debug(f"Listing flashcards with filters: deck_id={deck_id}, deck_name={deck_name}, limit={limit}, all_cards={all_cards}")
        try:
            params = {}
            if all_cards:
                params["all"] = "true"
            elif limit:
                params["pageSize"] = limit  # Use correct parameter name
            if offset:
                params["offset"] = offset
            if sort_by:
                params["sort_by"] = sort_by
            if filter_difficulty:
                params["difficulty"] = filter_difficulty
            if tags:
                params["tags"] = ",".join(tags)

            # Use deck_id if provided, otherwise fall back to deck_name
            if deck_id:
                endpoint = format_endpoint(FLASHCARDS_BY_DECK, deck_id=deck_id)
                response = await self._get(endpoint, params)
                return self._normalize_response(response)
            if deck_name:
                params["deck_name"] = deck_name
                response = await self._get(FLASHCARDS_LIST, params)
                return self._normalize_response(response)
            # List all flashcards without deck filter
            response = await self._get(FLASHCARDS_LIST, params)
            return self._normalize_response(response)
        except Exception as e:
            logger.error(f"Error listing flashcards: {str(e)}")
            raise

    async def search_flashcards(self, query: str, deck_name: str | None = None) -> dict[str, Any]:
        """
        Search flashcards by content.

        Args:
            query: Search query.
            deck_name: Optional deck filter.

        Returns:
            Search results.
        """
        logger.debug(f"Searching flashcards: query='{query}', deck='{deck_name}'")
        try:
            params = {"q": query}
            if deck_name:
                params["deck_name"] = deck_name

            return await self._get(FLASHCARDS_SEARCH, params)
        except Exception as e:
            logger.error(f"Error searching flashcards: {str(e)}")
            raise

    async def bulk_create_flashcards(self, flashcards: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Create multiple flashcards at once.

        Args:
            flashcards: List of flashcard data.

        Returns:
            Bulk creation results.
        """
        logger.debug(f"Bulk creating {len(flashcards)} flashcards")
        try:
            data = {"flashcards": flashcards}
            return await self._post(FLASHCARDS_BULK_CREATE, data)
        except Exception as e:
            logger.error(f"Error bulk creating flashcards: {str(e)}")
            raise
