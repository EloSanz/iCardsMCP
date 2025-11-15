"""Deck service for iCards MCP server."""

import logging
from typing import Any

from app.constants import (
    DECKS_CLONE,
    DECKS_CREATE,
    DECKS_DELETE,
    DECKS_GENERATE,
    DECKS_GET,
    DECKS_LIST_MCP,
    DECKS_STATS,
    DECKS_SEARCH,
    DECKS_UPDATE,
    format_endpoint,
)

from .base_service import BaseService

logger = logging.getLogger(__name__)


class DeckService(BaseService):
    """Service for deck operations using iCards REST API."""

    _instance = None

    def __init__(self):
        """Initialize the deck service."""
        super().__init__()

    @classmethod
    def get_instance(cls):
        """Get singleton instance of DeckService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_deck(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new deck.

        Args:
            data: Deck data including name, description, etc.

        Returns:
            Created deck data.
        """
        logger.debug("Creating deck")
        try:
            return await self._post(DECKS_CREATE, data)
        except Exception as e:
            logger.error(f"Error creating deck: {str(e)}")
            raise

    async def get_deck(self, deck_id: int) -> dict[str, Any]:
        """
        Get a specific deck by ID.

        Args:
            deck_id: The deck ID.

        Returns:
            Deck data.
        """
        logger.debug(f"Getting deck {deck_id}")
        try:
            endpoint = format_endpoint(DECKS_GET, deck_id=deck_id)
            return await self._get(endpoint)
        except Exception as e:
            logger.error(f"Error getting deck {deck_id}: {str(e)}")
            raise

    async def update_deck(self, deck_id: int, data: dict[str, Any]) -> dict[str, Any]:
        """
        Update a deck.

        Args:
            deck_id: The deck ID.
            data: Updated deck data.

        Returns:
            Updated deck data.
        """
        logger.debug(f"Updating deck {deck_id}")
        try:
            endpoint = format_endpoint(DECKS_UPDATE, deck_id=deck_id)
            return await self._put(endpoint, data)
        except Exception as e:
            logger.error(f"Error updating deck {deck_id}: {str(e)}")
            raise

    async def delete_deck(self, deck_id: int) -> dict[str, Any]:
        """
        Delete a deck.

        Args:
            deck_id: The deck ID.

        Returns:
            Deletion confirmation.
        """
        logger.debug(f"Deleting deck {deck_id}")
        try:
            endpoint = format_endpoint(DECKS_DELETE, deck_id=deck_id)
            return await self._delete(endpoint)
        except Exception as e:
            logger.error(f"Error deleting deck {deck_id}: {str(e)}")
            raise

    async def list_decks(self) -> dict[str, Any]:
        """
        List all decks (MCP optimized - without cover images).

        Returns:
            List of all decks without coverUrl for better performance.
        """
        logger.debug("Listing all decks (MCP optimized)")
        try:
            return await self._get(DECKS_LIST_MCP)
        except Exception as e:
            logger.error(f"Error listing decks: {str(e)}")
            raise

    async def list_decks_mcp(self) -> dict[str, Any]:
        """
        List all decks for MCP (lightweight version without cover images).

        Returns:
            Dict with 'decks' key containing list of deck objects.
        """
        logger.debug("Listing decks for MCP (lightweight)")
        try:
            response = await self._get(DECKS_LIST_MCP)
            # Normalize response to ensure 'decks' key exists
            return self._normalize_response(response)
        except Exception as e:
            logger.error(f"Error listing decks for MCP: {str(e)}")
            raise

    async def get_deck_by_name(self, deck_name: str) -> dict[str, Any]:
        """
        Get a deck by name.

        Args:
            deck_name: The deck name.

        Returns:
            Deck data.
        """
        logger.debug(f"Getting deck by name: {deck_name}")
        try:
            params = {"name": deck_name}
            result = await self._get(DECKS_SEARCH, params)
            decks = result.get("decks", [])
            if decks:
                return decks[0]  # Return first match
            raise ValueError(f"Deck '{deck_name}' not found")
        except Exception as e:
            logger.error(f"Error getting deck by name '{deck_name}': {str(e)}")
            raise

    async def generate_deck_ai(self, topic: str, language: str = "english") -> dict[str, Any]:
        """
        Generate a deck using AI.

        Args:
            topic: The topic for the deck.
            language: Target language for the deck.

        Returns:
            Generated deck data.
        """
        logger.debug(f"Generating AI deck for topic: {topic}, language: {language}")
        try:
            data = {"topic": topic, "language": language}
            return await self._post(DECKS_GENERATE, data)
        except Exception as e:
            logger.error(f"Error generating AI deck: {str(e)}")
            raise

    async def clone_deck(self, deck_id: int, new_name: str) -> dict[str, Any]:
        """
        Clone an existing deck.

        Args:
            deck_id: The source deck ID.
            new_name: Name for the cloned deck.

        Returns:
            Cloned deck data.
        """
        logger.debug(f"Cloning deck {deck_id} to '{new_name}'")
        try:
            data = {"name": new_name}
            endpoint = format_endpoint(DECKS_CLONE, deck_id=deck_id)
            return await self._post(endpoint, data)
        except Exception as e:
            logger.error(f"Error cloning deck {deck_id}: {str(e)}")
            raise

    async def get_deck_stats(self, deck_id: int) -> dict[str, Any]:
        """
        Get detailed statistics for a specific deck.

        This endpoint provides comprehensive statistics including organization
        metrics, study progress, and distribution data used by MCP tools.

        Args:
            deck_id: The deck ID to get statistics for.

        Returns:
            Comprehensive deck statistics including organization status.
        """
        logger.debug(f"Getting statistics for deck {deck_id}")
        try:
            endpoint = format_endpoint(DECKS_STATS, deck_id=deck_id)
            response = await self._get(endpoint)
            return self._normalize_response(response)
        except Exception as e:
            logger.error(f"Error getting deck statistics for {deck_id}: {str(e)}")
            raise
