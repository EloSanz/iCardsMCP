"""
Typed service layer for iCards MCP server.

This service provides a typed interface to the iCards API using Pydantic models
for validation, serialization, and type safety. It acts as a bridge between
the MCP tools and the existing services.
"""

import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from app.models import (
    # Base models
    Deck, Flashcard, Tag, User,
    # Request models
    DeckCreate, DeckUpdate, DeckStats,
    FlashcardCreate, FlashcardUpdate, FlashcardBulkCreate,
    TagCreate, TagUpdate,
    # Response models
    DeckListResponse, DeckMCPResponse, DeckStatsResponse, DeckCreateResponse,
    FlashcardListResponse, TagListResponse,
    # MCP tool models
    CreateDeckParams, AddFlashcardParams, BulkCreateFlashcardsParams,
    GetDeckInfoParams, GetDeckStatsParams, ListDecksParams,
    ListFlashcardsParams, ListUntaggedFlashcardsParams,
    CreateTagParams, ListTagsParams, UpdateTagParams,
)

from .deck_service import DeckService
from .flashcard_service import FlashcardService
from .tag_service import TagService

logger = logging.getLogger(__name__)


class TypedService:
    """Typed service layer with Pydantic model validation."""

    _instance = None

    def __init__(self):
        """Initialize the typed service."""
        self.deck_service = DeckService.get_instance()
        self.flashcard_service = FlashcardService.get_instance()
        self.tag_service = TagService.get_instance()

    @classmethod
    def get_instance(cls):
        """Get singleton instance of TypedService."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ===== DECK OPERATIONS =====

    async def create_deck(self, params: CreateDeckParams) -> DeckCreateResponse:
        """
        Create a new deck with typed validation.

        Args:
            params: Validated creation parameters

        Returns:
            Created deck response object
        """
        logger.debug(f"Creating deck: {params.name}")

        # Convert to API request model
        request_data = {
            "name": params.name,
            "description": params.description or "",
            "generateCover": params.generate_cover
        }

        # Call existing service
        response = await self.deck_service.create_deck(request_data)

        # Parse response into typed model - handle different response structures
        try:
            # Try to parse as DeckCreateResponse first
            return DeckCreateResponse.model_validate(response)
        except Exception as e:
            logger.warning(f"Could not parse as DeckCreateResponse, trying fallback: {str(e)}")

            # Fallback: try to extract deck data and create minimal response
            deck_data = response.get("deck", response)
            if isinstance(deck_data, dict):
                try:
                    # Try to create a minimal Deck object
                    deck = Deck(**deck_data)
                    return DeckCreateResponse(
                        success=True,
                        message="Deck created successfully",
                        deck=deck
                    )
                except Exception as e2:
                    logger.warning(f"Could not create Deck object from data: {str(e2)}")

            # Last resort: return success response without deck data
            return DeckCreateResponse(
                success=response.get("success", True),
                message=response.get("message", "Deck created successfully")
            )

    async def get_deck_info(self, params: GetDeckInfoParams) -> Deck:
        """
        Get detailed deck information.

        Args:
            params: Deck lookup parameters

        Returns:
            Complete deck information
        """
        logger.debug(f"Getting deck info: {params.deck_name}")

        # Find deck by name first
        decks_response = await self.deck_service.list_decks_mcp()
        decks = decks_response.get("decks", [])

        target_deck = None
        for deck in decks:
            if deck.get("name", "").lower() == params.deck_name.lower():
                target_deck = deck
                break

        if not target_deck:
            raise ValueError(f"Deck '{params.deck_name}' not found")

        deck_id = target_deck.get("id")
        if not deck_id:
            raise ValueError(f"Invalid deck data for '{params.deck_name}'")

        # Get full deck information
        deck_response = await self.deck_service.get_deck(deck_id)

        # Get tags for this deck
        tags_response = await self.tag_service.get_deck_tags(deck_id)
        tags = tags_response.get("data", []) if isinstance(tags_response, dict) else []

        # Combine deck data with tags
        deck_data = deck_response.copy()
        deck_data["tags"] = tags

        return Deck(**deck_data)

    async def get_deck_stats(self, params: GetDeckStatsParams) -> DeckStats:
        """
        Get comprehensive deck statistics.

        Args:
            params: Deck lookup parameters

        Returns:
            Detailed deck statistics
        """
        logger.debug(f"Getting deck stats: {params.deck_name}")

        # Find deck by name
        decks_response = await self.deck_service.list_decks_mcp()
        decks = decks_response.get("decks", [])

        target_deck = None
        for deck in decks:
            if deck.get("name", "").lower() == params.deck_name.lower():
                target_deck = deck
                break

        if not target_deck:
            raise ValueError(f"Deck '{params.deck_name}' not found")

        deck_id = target_deck.get("id")

        # Try to get stats from dedicated endpoint
        try:
            stats_response = await self.deck_service.get_deck_stats(deck_id)
            if isinstance(stats_response, dict) and stats_response.get("data"):
                return DeckStats(**stats_response["data"])
        except Exception as e:
            logger.warning(f"Could not get stats from dedicated endpoint: {e}")

        # Fallback: calculate from available data
        return await self._calculate_deck_stats(deck_id, target_deck)

    async def list_decks(self, params: ListDecksParams) -> DeckMCPResponse:
        """
        List all decks with MCP optimization.

        Args:
            params: List parameters (currently unused)

        Returns:
            MCP-optimized deck list response
        """
        logger.debug("Listing all decks (typed)")

        response = await self.deck_service.list_decks_mcp()

        # Parse into typed response
        decks_data = []
        for deck_dict in response.get("decks", []):
            try:
                deck = Deck(**deck_dict)
                decks_data.append(deck)
            except Exception as e:
                logger.warning(f"Failed to parse deck: {e}, data: {deck_dict}")

        return DeckMCPResponse(
            success=True,
            message="Decks retrieved successfully",
            data=decks_data,
            count=len(decks_data),
            totalCards=response.get("total_cards", 0),
            timestamp=datetime.now()
        )

    # ===== FLASHCARD OPERATIONS =====

    async def add_flashcard(self, params: AddFlashcardParams) -> Flashcard:
        """
        Add a single flashcard with typed validation.

        Args:
            params: Validated flashcard creation parameters

        Returns:
            Created flashcard object
        """
        logger.debug(f"Adding flashcard to deck: {params.deck_name}")

        # Find deck by name
        deck_id = await self._find_deck_id_by_name(params.deck_name)

        # Create flashcard data
        flashcard_data = {
            "front": params.front,
            "back": params.back,
            "deckId": deck_id,
            "difficulty": params.difficulty_level.value
        }

        # Call existing service
        response = await self.flashcard_service.create_flashcard(flashcard_data)

        # Parse response
        flashcard_dict = response.get("flashcard", response)
        return Flashcard(**flashcard_dict)

    async def bulk_create_flashcards(self, params: BulkCreateFlashcardsParams) -> Dict[str, Any]:
        """
        Create multiple flashcards at once.

        Args:
            params: Validated bulk creation parameters

        Returns:
            Bulk creation results
        """
        logger.debug(f"Bulk creating {len(params.flashcards)} flashcards in deck: {params.deck_name}")

        # Convert to service format
        flashcards_data = []
        for card in params.flashcards:
            flashcards_data.append({
                "front": card.get("front", ""),
                "back": card.get("back", ""),
                "difficulty": card.get("difficulty", 1)
            })

        # Call existing service
        response = await self.flashcard_service.bulk_create_flashcards(
            params.deck_name,
            flashcards_data
        )

        return response

    async def list_flashcards(self, params: ListFlashcardsParams) -> FlashcardListResponse:
        """
        List flashcards with filtering.

        Args:
            params: List and filter parameters

        Returns:
            Typed flashcard list response
        """
        logger.debug(f"Listing flashcards with params: {params}")

        # Call existing service
        response = await self.flashcard_service.list_flashcards(
            deck_name=params.deck_name,
            limit=params.limit
        )

        # Parse into typed response
        flashcards_data = []
        for card_dict in response.get("flashcards", []):
            try:
                flashcard = Flashcard(**card_dict)
                flashcards_data.append(flashcard)
            except Exception as e:
                logger.warning(f"Failed to parse flashcard: {e}, data: {card_dict}")

        return FlashcardListResponse(
            success=True,
            message="Flashcards retrieved successfully",
            data=flashcards_data,
            count=len(flashcards_data),
            timestamp=datetime.now()
        )

    async def list_untagged_flashcards(self, params: ListUntaggedFlashcardsParams) -> Dict[str, Any]:
        """
        List untagged flashcards for a deck.

        Args:
            params: Untagged flashcard query parameters

        Returns:
            Untagged flashcards data
        """
        logger.debug(f"Listing untagged flashcards for deck: {params.deck_name}")

        # Find deck by name
        deck_id = await self._find_deck_id_by_name(params.deck_name)

        # Call existing service
        response = await self.flashcard_service.list_untagged_flashcards(
            deck_id=deck_id,
            all_cards=params.all_cards
        )

        return response

    # ===== TAG OPERATIONS =====

    async def create_tag(self, params: CreateTagParams) -> Tag:
        """
        Create a new tag.

        Args:
            params: Validated tag creation parameters

        Returns:
            Created tag object
        """
        logger.debug(f"Creating tag: {params.name} in deck: {params.deck_name}")

        # Find deck by name
        deck_id = await self._find_deck_id_by_name(params.deck_name)

        # Create tag data
        tag_data = {
            "name": params.name,
            "deckId": deck_id,
            "color": params.color,
            "description": params.description
        }

        # Call existing service
        response = await self.tag_service.create_deck_tag(deck_id, tag_data)

        # Parse response
        tag_dict = response.get("tag", response)
        return Tag(**tag_dict)

    async def list_tags(self, params: ListTagsParams) -> TagListResponse:
        """
        List tags with optional filtering.

        Args:
            params: Tag list parameters

        Returns:
            Typed tag list response
        """
        logger.debug(f"Listing tags with params: {params}")

        if params.deck_name:
            # List tags for specific deck
            deck_id = await self._find_deck_id_by_name(params.deck_name)
            response = await self.tag_service.get_deck_tags(deck_id)
        else:
            # List all tags
            response = await self.tag_service.list_tags()

        # Parse into typed response
        tags_data = []
        tags_list = response.get("data", response) if isinstance(response, dict) else response

        for tag_dict in tags_list:
            try:
                tag = Tag(**tag_dict)
                tags_data.append(tag)
            except Exception as e:
                logger.warning(f"Failed to parse tag: {e}, data: {tag_dict}")

        return TagListResponse(
            success=True,
            message="Tags retrieved successfully",
            data=tags_data,
            count=len(tags_data),
            timestamp=datetime.now()
        )

    async def update_tag(self, params: UpdateTagParams) -> Tag:
        """
        Update an existing tag.

        Args:
            params: Validated tag update parameters

        Returns:
            Updated tag object
        """
        logger.debug(f"Updating tag {params.tag_id}")

        # Prepare update data
        update_data = {}
        if params.name is not None:
            update_data["name"] = params.name
        if params.color is not None:
            update_data["color"] = params.color
        if params.description is not None:
            update_data["description"] = params.description

        # Call existing service
        response = await self.tag_service.update_tag(params.tag_id, update_data)

        # Parse response
        tag_dict = response.get("tag", response)
        return Tag(**tag_dict)

    # ===== HELPER METHODS =====

    async def _find_deck_id_by_name(self, deck_name: str) -> int:
        """
        Find deck ID by name.

        Args:
            deck_name: Name of the deck to find

        Returns:
            Deck ID

        Raises:
            ValueError: If deck is not found
        """
        decks_response = await self.deck_service.list_decks_mcp()
        decks = decks_response.get("decks", [])

        for deck in decks:
            if deck.get("name", "").lower() == deck_name.lower():
                deck_id = deck.get("id")
                if deck_id:
                    return deck_id

        raise ValueError(f"Deck '{deck_name}' not found")

    async def _calculate_deck_stats(self, deck_id: int, deck_info: Dict[str, Any]) -> DeckStats:
        """
        Calculate deck statistics from available data.

        Args:
            deck_id: Deck ID
            deck_info: Basic deck information

        Returns:
            Calculated deck statistics
        """
        logger.debug(f"Calculating stats for deck {deck_id}")

        # Get flashcards for this deck
        flashcards_response = await self.flashcard_service.list_flashcards(deck_id=deck_id, all_cards=True)
        flashcards = flashcards_response.get("flashcards", [])

        # Get tags for this deck
        tags_response = await self.tag_service.get_deck_tags(deck_id)
        tags = tags_response.get("data", []) if isinstance(tags_response, dict) else []

        # Calculate statistics
        total_flashcards = len(flashcards)
        total_tags = len(tags)

        # Count tagged vs untagged flashcards
        tagged_count = 0
        difficulty_sum = 0
        difficulty_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        for card in flashcards:
            difficulty = card.get("difficulty", 1)
            difficulty_sum += difficulty
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

            # Check if card has tags (simplified check)
            if card.get("tagId") or card.get("tag"):
                tagged_count += 1

        untagged_count = total_flashcards - tagged_count
        organization_percentage = (tagged_count / total_flashcards * 100) if total_flashcards > 0 else 0
        average_difficulty = difficulty_sum / total_flashcards if total_flashcards > 0 else 1.0

        return DeckStats(
            flashcardsCount=total_flashcards,
            newFlashcardsCount=difficulty_counts.get(1, 0),
            reviewsCount=sum(difficulty_counts.values()) - difficulty_counts.get(1, 0),
            organizationPercentage=organization_percentage,
            untaggedFlashcardsCount=untagged_count,
            totalTags=total_tags,
            averageDifficulty=average_difficulty,
            difficultyDistribution={str(k): v for k, v in difficulty_counts.items()}
        )
