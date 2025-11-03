"""Tools for the iCards MCP server."""

import logging
from typing import Literal

from pydantic import Field

logger = logging.getLogger(__name__)

from app.mcp.utils import (
    create_flashcard_template,
    format_deck_response,
    format_flashcard_response,
    validate_deck_name,
    validate_flashcard_content,
)
from app.services import DeckService, FlashcardService
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

# Type aliases for validation
DeckType = Literal["vocabulary", "grammar", "kanji", "phrases", "general", "custom"]
DifficultyLevel = Literal[1, 2, 3, 4, 5]

# Store tool functions to be registered later
_tool_functions = []


def register_icards_tools(mcp_server):
    """Register all iCards MCP tools with the MCP server instance."""

    # Tool 1: Add Flashcard
    @mcp_server.tool(
        name="add_flashcard",
        description="""
        Add a new flashcard to a deck.

        Creates a new flashcard with front/back content and associates it with a deck.
        Validates content length and format before creating.

        Supports different deck types: vocabulary, grammar, kanji, phrases, general, custom.
        """,
        tags={"flashcards", "creation", "content"},
    )
    async def add_flashcard(
        front: str = Field(..., description="The front side of the flashcard (question/prompt)"),
        back: str = Field(..., description="The back side of the flashcard (answer)"),
        deck_name: str = Field("default", description="The name of the deck to add the card to"),
        difficulty_level: DifficultyLevel = Field(2, description="Difficulty level (1-3, default: 2)"),
        tag_name: str | None = Field(None, description="Optional tag name for categorization (single tag)"),
    ) -> dict:
        """Add a new flashcard to a deck."""
        try:
            # Validate inputs
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": 'Deck name must be 1-100 characters and cannot contain invalid characters: < > : " | ? *',
                }

            is_valid, error_msg = validate_flashcard_content(front, back)
            if not is_valid:
                return {"error": "Invalid flashcard content", "message": error_msg}

            # Get deck ID from deck name
            deck_service = DeckService.get_instance()
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            deck_id = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_id = deck.get("id")
                    break

            if not deck_id:
                return {
                    "error": "Deck not found",
                    "message": f"No deck found with name '{deck_name}'",
                    "available_decks": [d.get("name") for d in all_decks],
                }

            # Get tag ID if tag_name is provided
            tag_id = None
            if tag_name:
                from app.services import TagService

                tag_service = TagService.get_instance()
                tags_response = await tag_service.list_tags(deck_id)
                tags = tags_response.get("tags", [])

                for tag in tags:
                    if tag.get("name", "").lower() == tag_name.lower():
                        tag_id = tag.get("id")
                        break

                if not tag_id:
                    return {
                        "error": "Tag not found",
                        "message": f"No tag found with name '{tag_name}' in deck '{deck_name}'",
                        "available_tags": [t.get("name") for t in tags],
                    }

            # Prepare flashcard data for backend API
            # Backend expects: front, back, deckId, difficulty (1-3), tagId (optional)
            flashcard_data = {
                "front": front.strip(),
                "back": back.strip(),
                "deckId": deck_id,
                "difficulty": min(difficulty_level, 3),  # Backend only supports 1-3
            }

            if tag_id:
                flashcard_data["tagId"] = tag_id

            # Call the actual API service
            flashcard_service = FlashcardService.get_instance()
            api_response = await flashcard_service.create_flashcard(flashcard_data)
            response_data = format_flashcard_response(api_response)

            return {
                "success": True,
                "flashcard": response_data,
                "message": f"Flashcard added to deck '{deck_name}' successfully",
                "difficulty": difficulty_level,
            }

        except Exception as e:
            logger.error(f"Error adding flashcard: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not add flashcard: {str(e)}"}

    # Tool 2: List Decks
    @mcp_server.tool(
        name="list_decks",
        description="""
        List all available flashcard decks.

        Returns information about all decks including card counts, progress metrics,
        and study statistics. Useful for overview and navigation.
        """,
        tags={"decks", "overview", "navigation"},
    )
    async def list_decks() -> dict:
        """List all available flashcard decks."""
        try:
            # Call the service which handles API communication and normalization
            deck_service = DeckService.get_instance()
            api_response = await deck_service.list_decks_mcp()

            # Extract normalized decks array
            decks = api_response.get("decks", [])
            formatted_decks = [format_deck_response(deck) for deck in decks]

            return {
                "decks": formatted_decks,
                "total_decks": len(formatted_decks),
                "total_cards": sum(d.get("card_count", 0) for d in formatted_decks),
                "metadata": {
                    "description": "Complete list of available flashcard decks (lightweight MCP version)",
                    "source": "iCards API - MCP endpoint",
                    "last_updated": api_response.get("timestamp", "2025-01-01T00:00:00Z"),
                },
            }

        except Exception as e:
            logger.error(f"Error listing decks: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not list decks: {str(e)}"}

    # Tool 3: Get Deck Info
    @mcp_server.tool(
        name="get_deck_info",
        description="""
        Get detailed information about a specific deck.

        Includes:
        - Basic deck information (name, description, creation date)
        - Card statistics (total count, difficulty distribution)
        - Tags available in the deck with flashcard counts
        - Study progress and activity

        This tool provides comprehensive deck information in a single call.
        """,
        tags={"decks", "information", "progress", "analysis", "tags"},
    )
    async def get_deck_info(
        deck_name: str = Field(..., description="Name of the deck to get information about"),
    ) -> dict:
        """Get detailed information about a specific deck including tags and flashcard count."""
        try:
            deck_service = DeckService.get_instance()

            # Get all decks from MCP endpoint (already normalized by service)
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            # Find deck by name (case-insensitive)
            deck_data = None
            deck_id = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_data = deck
                    deck_id = deck.get("id")
                    break

            if not deck_data or not deck_id:
                available_decks = [d.get("name", "") for d in all_decks]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
                }

            # Get tags for this deck
            from app.services import TagService

            tag_service = TagService.get_instance()
            tags_response = await tag_service.list_tags(deck_id)
            tags_data = tags_response.get("data", []) if isinstance(tags_response.get("data"), list) else []

            # Get actual flashcard count
            flashcard_service = FlashcardService.get_instance()
            flashcards_response = await flashcard_service.list_flashcards(deck_id=deck_id, all_cards=True)

            # Normalize response
            flashcard_service_base = BaseService()
            normalized_flashcards = flashcard_service_base._normalize_response(flashcards_response)
            flashcards = normalized_flashcards.get("flashcards", [])
            actual_card_count = len(flashcards)

            # Calculate difficulty distribution
            difficulty_distribution = {}
            for card in flashcards:
                diff = card.get("difficulty", 2)
                difficulty_distribution[diff] = difficulty_distribution.get(diff, 0) + 1

            # Format the deck information
            formatted_deck = format_deck_response(deck_data)
            formatted_deck["card_count"] = actual_card_count  # Override with actual count
            formatted_deck["difficulty_distribution"] = difficulty_distribution

            # Format tags with flashcard counts
            formatted_tags = []
            for tag in tags_data:
                formatted_tags.append(
                    {
                        "id": tag.get("id"),
                        "name": tag.get("name"),
                        "flashcard_count": tag.get("flashcardCount", 0),
                        "created_at": tag.get("createdAt"),
                    }
                )

            return {
                "deck": formatted_deck,
                "tags": formatted_tags,
                "tag_count": len(formatted_tags),
                "statistics": {
                    "total_flashcards": actual_card_count,
                    "total_tags": len(formatted_tags),
                    "difficulty_distribution": difficulty_distribution,
                    "average_difficulty": (
                        round(sum(diff * count for diff, count in difficulty_distribution.items()) / actual_card_count, 2)
                        if actual_card_count > 0
                        else 0
                    ),
                },
                "metadata": {
                    "description": f"Complete information for deck '{deck_name}'",
                    "source": "iCards API - MCP endpoint",
                    "includes": ["basic_info", "tags", "flashcard_count", "difficulty_distribution"],
                },
            }

        except Exception as e:
            logger.error(f"Error getting deck info for {deck_name}: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not get deck information: {str(e)}"}

    # Tool 4: Create Flashcard Template
    @mcp_server.tool(
        name="create_flashcard_template",
        description="""
        Create a flashcard template based on deck type.

        Provides suggested front/back content structure and difficulty level
        for different types of learning content.
        """,
        tags={"templates", "guidance", "content-creation"},
    )
    async def create_flashcard_template_tool(
        deck_type: DeckType = Field("general", description="Type of deck to create template for"),
    ) -> dict:
        """Create a flashcard template based on deck type."""
        try:
            template = create_flashcard_template(deck_type)

            return {
                "template": template,
                "deck_type": deck_type,
                "description": f"Template for {deck_type} flashcards",
                "usage_tips": [
                    "Use the suggested structure as a starting point",
                    "Customize content to fit your learning style",
                    "Adjust difficulty level based on your knowledge",
                    "Add relevant tags for better organization",
                ],
                "metadata": {
                    "template_version": "1.0",
                    "recommended_difficulty": template["difficulty_level"],
                    "tags": template["tags"],
                },
            }

        except Exception as e:
            logger.error(f"Error creating template for deck type {deck_type}: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not create template: {str(e)}"}

    # Tool 5: List Flashcards in Deck
    @mcp_server.tool(
        name="list_flashcards",
        description="""
        List flashcards in a specific deck.

        Returns detailed information about each card including review statistics,
        difficulty levels, and tags. Useful for deck management and study planning.

        By default returns 50 cards. Use all_cards=True to get all flashcards (no limit).
        """,
        tags={"flashcards", "listing", "deck-content", "study-planning"},
    )
    async def list_flashcards(
        deck_name: str = Field(..., description="Name of the deck to list flashcards from"),
        limit: int | None = Field(50, description="Maximum number of cards to return (1-100). Ignored if all_cards=True"),
        offset: int | None = Field(0, description="Number of cards to skip. Ignored if all_cards=True"),
        sort_by: Literal["created", "difficulty", "reviews", "correct_rate"] | None = Field(
            "created", description="Sort cards by this criteria"
        ),
        filter_difficulty: DifficultyLevel | None = Field(None, description="Filter cards by difficulty level"),
        all_cards: bool = Field(
            False, description="If True, retrieves ALL cards in the deck (no limit). Use for complete analysis."
        ),
    ) -> dict:
        """List flashcards in a specific deck."""
        try:
            if not validate_deck_name(deck_name):
                return {"error": "Invalid deck name", "message": "Deck name format is invalid"}

            if not all_cards and limit and (limit < 1 or limit > 100):
                return {"error": "Invalid limit", "message": "Limit must be between 1 and 100"}

            # First, get the deck ID from the deck name
            deck_service = DeckService.get_instance()
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            # Find deck by name (case-insensitive)
            deck_id = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_id = deck.get("id")
                    break

            if not deck_id:
                available_decks = [d.get("name", "") for d in all_decks]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
                }

            # Get flashcards for this specific deck using deck_id
            flashcard_service = FlashcardService.get_instance()

            if all_cards:
                # Get ALL cards using all=true parameter
                api_response = await flashcard_service.list_flashcards(
                    deck_id=deck_id, all_cards=True, sort_by=sort_by, filter_difficulty=filter_difficulty
                )
            else:
                # Get limited cards with pagination
                api_response = await flashcard_service.list_flashcards(
                    deck_id=deck_id, limit=limit, offset=offset or 0, sort_by=sort_by, filter_difficulty=filter_difficulty
                )

            # Normalize response
            flashcard_service_base = BaseService()
            normalized_response = flashcard_service_base._normalize_response(api_response)

            # Extract flashcards
            flashcards = normalized_response.get("flashcards", [])

            response = {
                "deck_name": deck_name,
                "deck_id": deck_id,
                "flashcards": flashcards,
                "total_count": len(flashcards),
                "metadata": {
                    "description": f"Flashcards in deck '{deck_name}' (ID: {deck_id})",
                    "source": "iCards API",
                    "sort_by": sort_by,
                    "filter_difficulty": filter_difficulty,
                    "all_cards": all_cards,
                },
            }

            # Only add pagination info if not fetching all cards
            if not all_cards:
                response["pagination"] = {
                    "limit": limit,
                    "offset": offset or 0,
                }

            return response

        except Exception as e:
            logger.error(f"Error listing flashcards in '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not list flashcards: {str(e)}"}

    @mcp_server.tool(
        name="count_flashcards",
        description="""
        Count the total number of flashcards in a specific deck.
        Makes a single API call with all=true parameter to get all flashcards at once.
        Returns the exact count without pagination limits.
        """,
        tags={"flashcards", "counting", "deck-info", "statistics"},
    )
    async def count_flashcards(
        deck_name: str = Field(..., description="Name of the deck to count flashcards in"),
    ) -> dict:
        """Count flashcards in a specific deck with single API call."""
        try:
            if not validate_deck_name(deck_name):
                return {"error": "Invalid deck name", "message": "Deck name format is invalid"}

            # First, get the deck ID from the deck name
            deck_service = DeckService.get_instance()
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            # Find deck by name (case-insensitive)
            deck_id = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_id = deck.get("id")
                    break

            if not deck_id:
                available_decks = [d.get("name", "") for d in all_decks]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
                }

            # Get all flashcards in one request using all=true parameter
            # This is the correct way according to API documentation
            flashcard_service = FlashcardService.get_instance()

            # Use all=true to get ALL flashcards in one request (no pagination needed)
            api_response = await flashcard_service.list_flashcards(
                deck_id=deck_id,
                all_cards=True,  # This adds all=true to get all cards
            )

            # Normalize response
            flashcard_service_base = BaseService()
            normalized_response = flashcard_service_base._normalize_response(api_response)

            # Count all flashcards
            flashcards = normalized_response.get("flashcards", [])
            total_count = len(flashcards)

            logger.debug(f"Successfully counted {total_count} flashcards for deck {deck_id} using all=true")

            return {
                "deck_name": deck_name,
                "deck_id": deck_id,
                "total_flashcards": total_count,
                "metadata": {
                    "description": f"Total flashcard count for deck '{deck_name}' (ID: {deck_id})",
                    "source": "iCards API",
                    "method": "all_true_parameter",
                },
            }

        except Exception as e:
            logger.error(f"Error counting flashcards in '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not count flashcards: {str(e)}"}
