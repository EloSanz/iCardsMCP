"""Tools for the iCards MCP server."""

from typing import Optional, List, Literal

import logging
from pydantic import Field

from app.mcp.utils import (
    validate_deck_name,
    validate_flashcard_content,
    format_flashcard_response,
    format_deck_response,
    create_flashcard_template,
    get_api_base_url
)
from app.services import FlashcardService, DeckService, TagService
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
        tags={"flashcards", "creation", "content"}
    )
    async def add_flashcard(
        front: str = Field(..., description="The front side of the flashcard (question/prompt)"),
        back: str = Field(..., description="The back side of the flashcard (answer)"),
        deck_name: str = Field("default", description="The name of the deck to add the card to"),
        deck_type: DeckType = Field("general", description="Type of deck for content guidance"),
        difficulty_level: DifficultyLevel = Field(1, description="Difficulty level (1-5)"),
        tags: Optional[List[str]] = Field(None, description="Optional tags for categorization")
    ) -> dict:
        """Add a new flashcard to a deck."""
        try:
            # Validate inputs
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name must be 1-100 characters and cannot contain invalid characters: < > : \" | ? *"
                }

            is_valid, error_msg = validate_flashcard_content(front, back)
            if not is_valid:
                return {
                    "error": "Invalid flashcard content",
                    "message": error_msg
                }

            # Prepare flashcard data
            flashcard_data = {
                "front": front.strip(),
                "back": back.strip(),
                "deck_name": deck_name.strip(),
                "deck_type": deck_type,
                "difficulty_level": difficulty_level,
                "tags": tags or []
            }

            # Call the actual API service
            flashcard_service = FlashcardService.get_instance()

            flashcard_data = {
                "front": front.strip(),
                "back": back.strip(),
                "deck_name": deck_name.strip(),
                "deck_type": deck_type,
                "difficulty_level": difficulty_level,
                "tags": tags or []
            }

            api_response = await flashcard_service.create_flashcard(flashcard_data)
            response_data = format_flashcard_response(api_response)

            return {
                "success": True,
                "flashcard": response_data,
                "message": f"Flashcard added to deck '{deck_name}' successfully",
                "deck_type": deck_type,
                "difficulty_level": difficulty_level
            }

        except Exception as e:
            logger.error(f"Error adding flashcard: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not add flashcard: {str(e)}"
            }

    # Tool 2: List Decks
    @mcp_server.tool(
        name="list_decks",
        description="""
        List all available flashcard decks.

        Returns information about all decks including card counts, progress metrics,
        and study statistics. Useful for overview and navigation.
        """,
        tags={"decks", "overview", "navigation"}
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
                    "last_updated": api_response.get("timestamp", "2025-01-01T00:00:00Z")
                }
            }

        except Exception as e:
            logger.error(f"Error listing decks: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not list decks: {str(e)}"
            }

    # Tool 3: Get Deck Info
    @mcp_server.tool(
        name="get_deck_info",
        description="""
        Get detailed information about a specific deck.

        Includes card statistics, study progress, difficulty distribution,
        and learning recommendations.
        """,
        tags={"decks", "information", "progress", "analysis"}
    )
    async def get_deck_info(
        deck_name: str = Field(..., description="Name of the deck to get information about")
    ) -> dict:
        """Get detailed information about a specific deck."""
        try:
            deck_service = DeckService.get_instance()

            # Get all decks from MCP endpoint (already normalized by service)
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            # Find deck by name (case-insensitive)
            deck_data = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_data = deck
                    break

            if not deck_data:
                available_decks = [d.get("name", "") for d in all_decks]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks
                }

            # Format the deck information
            formatted_deck = format_deck_response(deck_data)

            return {
                "deck": formatted_deck,
                "metadata": {
                    "description": f"Information for deck '{deck_name}'",
                    "source": "iCards API - MCP endpoint",
                }
            }

        except Exception as e:
            logger.error(f"Error getting deck info for {deck_name}: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not get deck information: {str(e)}"
            }

    # Tool 4: Create Flashcard Template
    @mcp_server.tool(
        name="create_flashcard_template",
        description="""
        Create a flashcard template based on deck type.

        Provides suggested front/back content structure and difficulty level
        for different types of learning content.
        """,
        tags={"templates", "guidance", "content-creation"}
    )
    async def create_flashcard_template_tool(
        deck_type: DeckType = Field("general", description="Type of deck to create template for")
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
                    "Add relevant tags for better organization"
                ],
                "metadata": {
                    "template_version": "1.0",
                    "recommended_difficulty": template["difficulty_level"],
                    "tags": template["tags"]
                }
            }

        except Exception as e:
            logger.error(f"Error creating template for deck type {deck_type}: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not create template: {str(e)}"
            }

    # Tool 5: List Flashcards in Deck
    @mcp_server.tool(
        name="list_flashcards",
        description="""
        List all flashcards in a specific deck.

        Returns detailed information about each card including review statistics,
        difficulty levels, and tags. Useful for deck management and study planning.
        """,
        tags={"flashcards", "listing", "deck-content", "study-planning"}
    )
    async def list_flashcards(
        deck_name: str = Field(..., description="Name of the deck to list flashcards from"),
        limit: int = Field(50, description="Maximum number of cards to return (max 100)"),
        offset: Optional[int] = Field(0, description="Number of cards to skip"),
        sort_by: Optional[Literal["created", "difficulty", "reviews", "correct_rate"]] = Field("created", description="Sort cards by this criteria"),
        filter_difficulty: Optional[DifficultyLevel] = Field(None, description="Filter cards by difficulty level")
    ) -> dict:
        """List flashcards in a specific deck."""
        try:
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid"
                }

            if limit and (limit < 1 or limit > 100):
                return {
                    "error": "Invalid limit",
                    "message": "Limit must be between 1 and 100"
                }

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
                    "available_decks": available_decks
                }

            # Get flashcards for this specific deck using deck_id
            flashcard_service = FlashcardService.get_instance()
            api_response = await flashcard_service.list_flashcards(
                deck_id=deck_id,
                limit=limit,
                offset=offset or 0,
                sort_by=sort_by,
                filter_difficulty=filter_difficulty
            )

            # Normalize response
            flashcard_service_base = BaseService()
            normalized_response = flashcard_service_base._normalize_response(api_response)

            # Extract flashcards
            flashcards = normalized_response.get("flashcards", [])

            return {
                "deck_name": deck_name,
                "deck_id": deck_id,
                "flashcards": flashcards,
                "total_count": len(flashcards),
                "pagination": {
                    "limit": limit,
                    "offset": offset or 0,
                },
                "metadata": {
                    "description": f"Flashcards in deck '{deck_name}' (ID: {deck_id})",
                    "source": "iCards API",
                    "sort_by": sort_by,
                    "filter_difficulty": filter_difficulty
                }
            }

        except Exception as e:
            logger.error(f"Error listing flashcards in '{deck_name}': {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not list flashcards: {str(e)}"
            }

    @mcp_server.tool(
        name="count_flashcards",
        description="""
        Count the total number of flashcards in a specific deck without retrieving the actual card data.
        This is much faster than list_flashcards when you only need to know the quantity.
        Useful for quickly checking deck size or progress tracking.
        """,
        tags={"flashcards", "counting", "deck-info", "statistics"}
    )
    async def count_flashcards(
        deck_name: str = Field(..., description="Name of the deck to count flashcards in")
    ) -> dict:
        """Count flashcards in a specific deck without retrieving data."""
        try:
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid"
                }

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
                    "available_decks": available_decks
                }

            # Get just one flashcard to obtain the total count from the response
            flashcard_service = FlashcardService.get_instance()
            api_response = await flashcard_service.list_flashcards(
                deck_id=deck_id,
                limit=1,  # Get just one card to get the total count
                offset=0
            )

            # Normalize response
            flashcard_service_base = BaseService()
            normalized_response = flashcard_service_base._normalize_response(api_response)

            # Extract total count from API response
            total_count = normalized_response.get("total", 0)

            return {
                "deck_name": deck_name,
                "deck_id": deck_id,
                "total_flashcards": total_count,
                "metadata": {
                    "description": f"Total flashcard count for deck '{deck_name}' (ID: {deck_id})",
                    "source": "iCards API",
                    "method": "count_only"
                }
            }

        except Exception as e:
            logger.error(f"Error counting flashcards in '{deck_name}': {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not count flashcards: {str(e)}"
            }

