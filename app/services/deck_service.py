"""Deck service for iCards MCP server."""

import logging
from typing import Dict, Any, List, Optional

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

    async def create_deck(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new deck.

        Args:
            data: Deck data including name, description, etc.

        Returns:
            Created deck data.
        """
        logger.debug("Creating deck")
        try:
            return await self._post("/api/decks", data)
        except Exception as e:
            logger.error(f"Error creating deck: {str(e)}")
            raise

    async def get_deck(self, deck_id: int) -> Dict[str, Any]:
        """
        Get a specific deck by ID.

        Args:
            deck_id: The deck ID.

        Returns:
            Deck data.
        """
        logger.debug(f"Getting deck {deck_id}")
        try:
            return await self._get(f"/api/decks/{deck_id}")
        except Exception as e:
            logger.error(f"Error getting deck {deck_id}: {str(e)}")
            raise

    async def update_deck(self, deck_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
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
            return await self._put(f"/api/decks/{deck_id}", data)
        except Exception as e:
            logger.error(f"Error updating deck {deck_id}: {str(e)}")
            raise

    async def delete_deck(self, deck_id: int) -> Dict[str, Any]:
        """
        Delete a deck.

        Args:
            deck_id: The deck ID.

        Returns:
            Deletion confirmation.
        """
        logger.debug(f"Deleting deck {deck_id}")
        try:
            return await self._delete(f"/api/decks/{deck_id}")
        except Exception as e:
            logger.error(f"Error deleting deck {deck_id}: {str(e)}")
            raise

    async def list_decks(self) -> Dict[str, Any]:
        """
        List all decks.

        Returns:
            List of all decks.
        """
        logger.debug("Listing all decks")
        try:
            return await self._get("/api/decks")
        except Exception as e:
            logger.error(f"Error listing decks: {str(e)}")
            raise

    async def get_deck_by_name(self, deck_name: str) -> Dict[str, Any]:
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
            result = await self._get("/api/decks/search", params)
            decks = result.get("decks", [])
            if decks:
                return decks[0]  # Return first match
            else:
                raise ValueError(f"Deck '{deck_name}' not found")
        except Exception as e:
            logger.error(f"Error getting deck by name '{deck_name}': {str(e)}")
            raise

    async def get_deck_statistics(self, deck_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get deck statistics.

        Args:
            deck_id: Optional specific deck ID.

        Returns:
            Statistics data.
        """
        logger.debug(f"Getting deck statistics for deck: {deck_id}")
        try:
            endpoint = f"/api/decks/{deck_id}/statistics" if deck_id else "/api/decks/statistics"
            return await self._get(endpoint)
        except Exception as e:
            logger.error(f"Error getting deck statistics: {str(e)}")
            raise

    async def get_deck_progress(self, deck_id: int) -> Dict[str, Any]:
        """
        Get learning progress for a specific deck.

        Args:
            deck_id: The deck ID.

        Returns:
            Progress data including studied cards, mastery levels, etc.
        """
        logger.debug(f"Getting deck progress for deck {deck_id}")
        try:
            return await self._get(f"/api/decks/{deck_id}/progress")
        except Exception as e:
            logger.error(f"Error getting deck progress for {deck_id}: {str(e)}")
            raise

    async def generate_deck_ai(self, topic: str, language: str = "english") -> Dict[str, Any]:
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
            data = {
                "topic": topic,
                "language": language
            }
            return await self._post("/api/decks/generate", data)
        except Exception as e:
            logger.error(f"Error generating AI deck: {str(e)}")
            raise

    async def clone_deck(self, deck_id: int, new_name: str) -> Dict[str, Any]:
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
            return await self._post(f"/api/decks/{deck_id}/clone", data)
        except Exception as e:
            logger.error(f"Error cloning deck {deck_id}: {str(e)}")
            raise
