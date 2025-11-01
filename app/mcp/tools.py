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
            # Call the actual API service
            deck_service = DeckService.get_instance()
            api_response = await deck_service.list_decks()

            decks = api_response.get("decks", [])
            formatted_decks = [format_deck_response(deck) for deck in decks]

            return {
                "decks": formatted_decks,
                "total_decks": len(formatted_decks),
                "total_cards": sum(d["card_count"] for d in formatted_decks),
                "active_decks": len([d for d in formatted_decks if d["is_active"]]),
                "metadata": {
                    "description": "Complete list of available flashcard decks",
                    "source": "iCards API",
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
            # Call the actual API service
            deck_service = DeckService.get_instance()

            # First try to get deck by name
            try:
                deck_data = await deck_service.get_deck_by_name(deck_name)
            except ValueError:
                # If deck not found by name, return error
                available_decks = []
                try:
                    all_decks = await deck_service.list_decks()
                    available_decks = [d.get("name", "") for d in all_decks.get("decks", [])]
                except Exception:
                    available_decks = []

                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks
                }

            # Get basic deck statistics
            deck_id = deck_data.get("id")
            deck_stats = {}

            if deck_id:
                try:
                    deck_stats = await deck_service.get_deck_statistics(deck_id)
                except Exception as e:
                    logger.warning(f"Could not get deck statistics for {deck_id}: {str(e)}")

            formatted_deck = format_deck_response(deck_data)

            return {
                "deck": formatted_deck,
                "statistics": deck_stats,
                "metadata": {
                    "description": f"Detailed information for deck '{deck_name}'",
                    "source": "iCards API",
                    "analysis_type": "deck_info"
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
        limit: Optional[int] = Field(50, description="Maximum number of cards to return (max 100)"),
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

            # TODO: Call actual API when implemented
            # For now, return mock data
            if "japanese" in deck_name.lower():
                mock_flashcards = [
                    {
                        "id": f"card_{i}",
                        "front": f"Japanese word {i}",
                        "back": f"Translation {i} - Pronunciation guide",
                        "deck_name": deck_name,
                        "difficulty_level": (i % 5) + 1,
                        "review_count": i % 10,
                        "correct_count": (i % 10) // 2,
                        "tags": ["japanese", "vocabulary"],
                        "created_at": f"2025-01-{str(i+1).zfill(2)}T00:00:00Z"
                    }
                    for i in range(min(limit or 50, 50))
                ]
            else:
                mock_flashcards = [
                    {
                        "id": f"card_{i}",
                        "front": f"Question {i}",
                        "back": f"Answer {i}",
                        "deck_name": deck_name,
                        "difficulty_level": (i % 3) + 1,
                        "review_count": i % 5,
                        "correct_count": i % 3,
                        "tags": ["general"],
                        "created_at": f"2025-01-{str(i+1).zfill(2)}T00:00:00Z"
                    }
                    for i in range(min(limit or 50, 30))
                ]

            # Apply filtering
            if filter_difficulty:
                mock_flashcards = [c for c in mock_flashcards if c["difficulty_level"] == filter_difficulty]

            # Apply sorting
            if sort_by == "difficulty":
                mock_flashcards.sort(key=lambda x: x["difficulty_level"])
            elif sort_by == "reviews":
                mock_flashcards.sort(key=lambda x: x["review_count"], reverse=True)
            elif sort_by == "correct_rate":
                mock_flashcards.sort(key=lambda x: x["correct_count"] / max(x["review_count"], 1), reverse=True)

            # Apply pagination
            start_idx = offset or 0
            end_idx = start_idx + (limit or 50)
            paginated_cards = mock_flashcards[start_idx:end_idx]

            formatted_cards = [format_flashcard_response(card) for card in paginated_cards]

            return {
                "flashcards": formatted_cards,
                "deck_name": deck_name,
                "total_cards": len(mock_flashcards),
                "returned_cards": len(formatted_cards),
                "pagination": {
                    "offset": start_idx,
                    "limit": limit,
                    "has_more": end_idx < len(mock_flashcards)
                },
                "filters_applied": {
                    "difficulty_level": filter_difficulty,
                    "sort_by": sort_by
                },
                "metadata": {
                    "description": f"Flashcards in deck '{deck_name}'",
                    "source": "iCards API"
                }
            }

        except Exception as e:
            logger.error(f"Error listing flashcards for deck {deck_name}: {str(e)}")
            return {
                "error": "Internal server error",
                "message": f"Could not list flashcards: {str(e)}"
            }

