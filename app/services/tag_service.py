"""Tag service for iCards MCP server."""

import logging
from typing import Dict, Any, List, Optional

from .base_service import BaseService
from app.constants import (
    TAGS_CREATE, TAGS_GET, TAGS_UPDATE, TAGS_DELETE, TAGS_LIST,
    TAGS_SEARCH, TAGS_BULK,
    FLASHCARDS_TAGS, DECKS_TAGS,
    format_endpoint,
)

logger = logging.getLogger(__name__)


class TagService(BaseService):
    """Service for tag operations using iCards REST API."""

    _instance = None

    def __init__(self):
        """Initialize the tag service."""
        super().__init__()

    @classmethod
    def get_instance(cls):
        """Get singleton instance of TagService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def create_tag(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tag.

        Args:
            data: Tag data including name, color, description, etc.

        Returns:
            Created tag data.
        """
        logger.debug("Creating tag")
        try:
            return await self._post(TAGS_CREATE, data)
        except Exception as e:
            logger.error(f"Error creating tag: {str(e)}")
            raise

    async def get_tag(self, tag_id: int) -> Dict[str, Any]:
        """
        Get a specific tag by ID.

        Args:
            tag_id: The tag ID.

        Returns:
            Tag data.
        """
        logger.debug(f"Getting tag {tag_id}")
        try:
            endpoint = format_endpoint(TAGS_GET, tag_id=tag_id)
            return await self._get(endpoint)
        except Exception as e:
            logger.error(f"Error getting tag {tag_id}: {str(e)}")
            raise

    async def update_tag(self, tag_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a tag.

        Args:
            tag_id: The tag ID.
            data: Updated tag data.

        Returns:
            Updated tag data.
        """
        logger.debug(f"Updating tag {tag_id}")
        try:
            endpoint = format_endpoint(TAGS_UPDATE, tag_id=tag_id)
            return await self._put(endpoint, data)
        except Exception as e:
            logger.error(f"Error updating tag {tag_id}: {str(e)}")
            raise

    async def delete_tag(self, tag_id: int) -> Dict[str, Any]:
        """
        Delete a tag.

        Args:
            tag_id: The tag ID.

        Returns:
            Deletion confirmation.
        """
        logger.debug(f"Deleting tag {tag_id}")
        try:
            endpoint = format_endpoint(TAGS_DELETE, tag_id=tag_id)
            return await self._delete(endpoint)
        except Exception as e:
            logger.error(f"Error deleting tag {tag_id}: {str(e)}")
            raise

    async def list_tags(self) -> Dict[str, Any]:
        """
        List all tags.

        Returns:
            List of all tags.
        """
        logger.debug("Listing all tags")
        try:
            return await self._get(TAGS_LIST)
        except Exception as e:
            logger.error(f"Error listing tags: {str(e)}")
            raise

    async def search_tags(self, query: str) -> Dict[str, Any]:
        """
        Search tags by name or description.

        Args:
            query: Search query.

        Returns:
            Search results.
        """
        logger.debug(f"Searching tags: query='{query}'")
        try:
            params = {"q": query}
            return await self._get(TAGS_SEARCH, params)
        except Exception as e:
            logger.error(f"Error searching tags: {str(e)}")
            raise


    async def add_tags_to_flashcard(self, flashcard_id: int, tag_ids: List[int]) -> Dict[str, Any]:
        """
        Add tags to a flashcard.

        Args:
            flashcard_id: The flashcard ID.
            tag_ids: List of tag IDs to add.

        Returns:
            Operation result.
        """
        logger.debug(f"Adding tags {tag_ids} to flashcard {flashcard_id}")
        try:
            data = {"tag_ids": tag_ids}
            endpoint = format_endpoint(FLASHCARDS_TAGS, flashcard_id=flashcard_id)
            return await self._post(endpoint, data)
        except Exception as e:
            logger.error(f"Error adding tags to flashcard: {str(e)}")
            raise

    async def remove_tags_from_flashcard(self, flashcard_id: int, tag_ids: List[int]) -> Dict[str, Any]:
        """
        Remove tags from a flashcard.

        Args:
            flashcard_id: The flashcard ID.
            tag_ids: List of tag IDs to remove.

        Returns:
            Operation result.
        """
        logger.debug(f"Removing tags {tag_ids} from flashcard {flashcard_id}")
        try:
            endpoint = format_endpoint(FLASHCARDS_TAGS, flashcard_id=flashcard_id)
            params = {"tag_ids": ",".join(str(tid) for tid in tag_ids)}
            return await self._get(endpoint, params=params)
        except Exception as e:
            logger.error(f"Error removing tags from flashcard: {str(e)}")
            raise

    async def get_flashcard_tags(self, flashcard_id: int) -> Dict[str, Any]:
        """
        Get all tags for a specific flashcard.

        Args:
            flashcard_id: The flashcard ID.

        Returns:
            List of tags associated with the flashcard.
        """
        logger.debug(f"Getting tags for flashcard {flashcard_id}")
        try:
            endpoint = format_endpoint(FLASHCARDS_TAGS, flashcard_id=flashcard_id)
            return await self._get(endpoint)
        except Exception as e:
            logger.error(f"Error getting flashcard tags: {str(e)}")
            raise

    async def add_tags_to_deck(self, deck_id: int, tag_ids: List[int]) -> Dict[str, Any]:
        """
        Add tags to a deck.

        Args:
            deck_id: The deck ID.
            tag_ids: List of tag IDs to add.

        Returns:
            Operation result.
        """
        logger.debug(f"Adding tags {tag_ids} to deck {deck_id}")
        try:
            data = {"tag_ids": tag_ids}
            endpoint = format_endpoint(DECKS_TAGS, deck_id=deck_id)
            return await self._post(endpoint, data)
        except Exception as e:
            logger.error(f"Error adding tags to deck: {str(e)}")
            raise

    async def remove_tags_from_deck(self, deck_id: int, tag_ids: List[int]) -> Dict[str, Any]:
        """
        Remove tags from a deck.

        Args:
            deck_id: The deck ID.
            tag_ids: List of tag IDs to remove.

        Returns:
            Operation result.
        """
        logger.debug(f"Removing tags {tag_ids} from deck {deck_id}")
        try:
            endpoint = format_endpoint(DECKS_TAGS, deck_id=deck_id)
            params = {"tag_ids": ",".join(str(tid) for tid in tag_ids)}
            return await self._get(endpoint, params=params)
        except Exception as e:
            logger.error(f"Error removing tags from deck: {str(e)}")
            raise

    async def get_deck_tags(self, deck_id: int) -> Dict[str, Any]:
        """
        Get all tags for a specific deck.

        Args:
            deck_id: The deck ID.

        Returns:
            List of tags associated with the deck.
        """
        logger.debug(f"Getting tags for deck {deck_id}")
        try:
            endpoint = format_endpoint(DECKS_TAGS, deck_id=deck_id)
            return await self._get(endpoint)
        except Exception as e:
            logger.error(f"Error getting deck tags: {str(e)}")
            raise

    async def bulk_tag_operation(self, operation: str, resource_type: str, resource_ids: List[int], tag_ids: List[int]) -> Dict[str, Any]:
        """
        Perform bulk tag operations.

        Args:
            operation: Operation type (add/remove).
            resource_type: Type of resource (flashcard/deck).
            resource_ids: List of resource IDs.
            tag_ids: List of tag IDs.

        Returns:
            Bulk operation results.
        """
        logger.debug(f"Bulk {operation} tags for {resource_type}s: {resource_ids}")
        try:
            data = {
                "operation": operation,
                "resource_type": resource_type,
                "resource_ids": resource_ids,
                "tag_ids": tag_ids
            }
            return await self._post(TAGS_BULK, data)
        except Exception as e:
            logger.error(f"Error in bulk tag operation: {str(e)}")
            raise
