"""Flashcard service for iCards MCP server."""

import logging
from typing import Dict, Any, List, Optional

from .base_service import BaseService
from app.constants import (
    FLASHCARDS_CREATE, FLASHCARDS_GET, FLASHCARDS_UPDATE, FLASHCARDS_DELETE,
    FLASHCARDS_LIST, FLASHCARDS_SEARCH,
    format_endpoint,
)

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

    async def create_flashcard(self, data: Dict[str, Any]) -> Dict[str, Any]:
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

    async def get_flashcard(self, flashcard_id: int) -> Dict[str, Any]:
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

    async def update_flashcard(self, flashcard_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
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

    async def delete_flashcard(self, flashcard_id: int) -> Dict[str, Any]:
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
        deck_name: Optional[str] = None,
        limit: Optional[int] = 50,
        offset: Optional[int] = 0,
        sort_by: Optional[str] = "created",
        filter_difficulty: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        List flashcards with optional filtering.

        Args:
            deck_name: Filter by deck name.
            limit: Maximum number of results.
            offset: Number of results to skip.
            sort_by: Sort criteria.
            filter_difficulty: Filter by difficulty level.
            tags: Filter by tags.

        Returns:
            List of flashcards with pagination info.
        """
        logger.debug(f"Listing flashcards with filters: deck={deck_name}, limit={limit}")
        try:
            params = {}
            if deck_name:
                params["deck_name"] = deck_name
            if limit:
                params["limit"] = limit
            if offset:
                params["offset"] = offset
            if sort_by:
                params["sort_by"] = sort_by
            if filter_difficulty:
                params["difficulty"] = filter_difficulty
            if tags:
                params["tags"] = ",".join(tags)

            return await self._get(FLASHCARDS_LIST, params)
        except Exception as e:
            logger.error(f"Error listing flashcards: {str(e)}")
            raise

    async def search_flashcards(self, query: str, deck_name: Optional[str] = None) -> Dict[str, Any]:
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

    async def bulk_create_flashcards(self, flashcards: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            return await self._post("/api/flashcards/bulk", data)
        except Exception as e:
            logger.error(f"Error bulk creating flashcards: {str(e)}")
            raise


