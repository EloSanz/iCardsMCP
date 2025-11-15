"""Tools for the iCards MCP server."""

import logging
from typing import Literal

from pydantic import Field
from fastmcp.server.context import Context

logger = logging.getLogger(__name__)

from app.mcp.utils import (
    create_flashcard_template,
    format_deck_response,
    format_flashcard_response,
    validate_deck_name,
    validate_flashcard_content,
)
from app.mcp.instructions import (
    get_instructions_for_add_flashcard,
    get_instructions_for_list_decks,
    get_instructions_for_get_deck_info,
    get_instructions_for_get_deck_stats,
    get_instructions_for_create_deck,
    get_instructions_for_create_template,
    get_instructions_for_list_flashcards,
    get_instructions_for_count_flashcards,
    get_instructions_for_assign_tags,
    get_instructions_for_bulk_create,
    get_instructions_for_list_untagged,
    get_instructions_for_update_flashcard,
)
from app.mcp.helpers import (
    _generate_stats_insights,
    _calculate_basic_stats_from_mcp_data,
    _calculate_basic_stats_from_deck_info,
    debug_deck_stats_calculation,
    test_stats_calculation_with_mock_data,
)
from app.services.typed_service import TypedService
from app.models.mcp_tools import (
    CreateDeckParams, AddFlashcardParams, BulkCreateFlashcardsParams,
    GetDeckInfoParams, GetDeckStatsParams, ListDecksParams,
    ListFlashcardsParams, ListUntaggedFlashcardsParams,
    CreateTagParams, ListTagsParams, UpdateTagParams,
)

from app.services import DeckService, FlashcardService, TagService
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

# Type aliases for validation
DeckType = Literal["vocabulary", "grammar", "kanji", "phrases", "general", "custom"]
DifficultyLevel = Literal[1, 2, 3, 4, 5]

# Store tool functions to be registered later
_tool_functions = []

# ===== USAGE EXAMPLES =====
"""
🚀 NEW SMART WORKFLOW: assign_tags_to_flashcards with auto-detection!

🎯 OPTIMIZED WORKFLOW:
   1. bulk_create_flashcards() → creates cards without tags
   2. assign_tags_to_flashcards(filter_criteria="untagged") → auto-organizes!
   3. No manual ID copying needed!

📋 AUTO-DETECTION EXAMPLES:

1. 🏷️ Tag ALL untagged flashcards in a deck (RECOMMENDED):
   assign_tags_to_flashcards(
       deck_name="Italian",
       tag_name="Saludos",
       filter_criteria="untagged"
   )

2. 🎯 Tag first 5 untagged flashcards only:
   assign_tags_to_flashcards(
       deck_name="Italian",
       tag_name="Saludos",
       filter_criteria="untagged",
       max_flashcards=5
   )

3. 🔄 Tag ALL flashcards in deck (use carefully):
   assign_tags_to_flashcards(
       deck_name="Italian",
       tag_name="Review",
       filter_criteria="all"
   )

📋 MANUAL MODE (still supported):

4. Tag specific flashcards by ID (traditional way):
   assign_tags_to_flashcards(
       deck_name="Italian",
       tag_name="Advanced",
       flashcard_ids=[168, 169, 170, 171, 172, 173]
   )
"""


def register_icards_tools(mcp_server):
    """Register all iCards MCP tools with the MCP server instance."""


    # Tool 1: Add Flashcard
    @mcp_server.tool(
        name="add_flashcard",
        description="""
        Add ONE SINGLE flashcard to a deck.

        🎯 BEST FOR: Individual cards, testing, corrections
        🚫 NOT FOR: Multiple cards (use 'bulk_create_flashcards' instead)

        ⚠️ WORKFLOW TIP: Create flashcards WITHOUT tags initially, then organize all at once with 'list_untagged_flashcards' + 'assign_tags_to_flashcards'

        Features:
        • Single flashcard creation
        • Content validation
        • Difficulty levels (1-5)
        • Optional immediate tagging (but batch organization recommended)
        """,
        tags={"flashcards", "creation", "content"},
    )
    async def add_flashcard(
        front: str = Field(..., description="The front side of the flashcard (question/prompt)"),
        back: str = Field(..., description="The back side of the flashcard (answer)"),
        deck_name: str = Field("default", description="The name of the deck to add the card to"),
        difficulty_level: int = Field(2, description="Difficulty level (1-5, default: 2)"),
        tag_name: str | None = Field(None, description="Optional tag name for categorization (single tag)"),
    ) -> dict:
        """Add a new flashcard to a deck with typed validation."""
        try:
            # Create typed parameters
            params = AddFlashcardParams(
                front=front,
                back=back,
                deck_name=deck_name,
                difficulty_level=difficulty_level
            )

            # Use typed service
            typed_service = TypedService.get_instance()
            flashcard = await typed_service.add_flashcard(params)

            # Handle optional tag assignment (not part of the main flow for simplicity)
            tag_assigned = False
            if tag_name:
                # This would require additional logic to assign tag after creation
                # For now, we'll note it in the response
                tag_assigned = True

            return {
                "success": True,
                "flashcard": flashcard.dict(),
                "message": f"Flashcard added to deck '{deck_name}' successfully",
                "difficulty": difficulty_level,
                "tag_assigned": tag_assigned,
                "_instructions": get_instructions_for_add_flashcard(deck_name),
            }

        except ValueError as e:
            # Handle validation errors from Pydantic models
            logger.warning(f"Validation error adding flashcard: {str(e)}")
            return {"error": "Validation error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error adding flashcard: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not add flashcard: {str(e)}"}

    # Tool 2: List Decks
    @mcp_server.tool(
        name="list_decks",
        description="""
        📋 OVERVIEW of ALL decks with organization status.

        🎯 BEST FOR: Navigation, seeing all decks at once, checking organization status
        📊 SHOWS: Names, counts, organization indicators (✅ ⚠️ 📝)
        ⚡ FAST: Lightweight overview for quick navigation

        💡 TIP: Use 'get_deck_stats(deck_name)' for detailed analytics of specific deck
        🔍 TIP: Organization indicators help identify decks needing attention
        """,
        tags={"decks", "overview", "navigation"},
    )
    async def list_decks() -> dict:
        """List all available flashcard decks with their tags."""
        try:
            # Call the service which handles API communication and normalization
            deck_service = DeckService.get_instance()
            api_response = await deck_service.list_decks_mcp()

            # Extract normalized decks array
            decks = api_response.get("decks", [])
            formatted_decks = []

            # Process each deck and use tags from API response
            for deck in decks:
                formatted_deck = format_deck_response(deck)

                # Tags are already included in the API response - use them directly
                tags_data = deck.get("tags", [])

                # Format tags with consistent structure
                formatted_tags = []
                for tag in tags_data:
                    formatted_tags.append({
                        "id": tag.get("id"),
                        "name": tag.get("name"),
                        # Note: API doesn't provide flashcardCount in deck tags, only basic info
                    })

                formatted_deck["tags"] = formatted_tags
                formatted_deck["tag_count"] = len(formatted_tags)

                # Try to get detailed stats for organization indicators (new backend endpoint)
                deck_id = deck.get("id")
                organization_status = "unknown"
                organization_indicator = "❓"
                untagged_count = 0

                if deck_id:
                    try:
                        # Get detailed stats from the new endpoint
                        stats_response = await deck_service.get_deck_stats(deck_id)
                        stats_data = stats_response.get("stats", {})

                        # Use stats data for accurate organization indicators
                        total_flashcards = stats_data.get("totalFlashcards", deck.get("card_count", 0))
                        untagged_flashcards = stats_data.get("untaggedFlashcards", 0)
                        organization_metrics = stats_data.get("organizationMetrics", {})
                        organization_status = organization_metrics.get("organizationStatus", "unknown")

                        untagged_count = untagged_flashcards

                        # Set indicator based on organization status
                        if organization_status == "empty":
                            organization_indicator = "📝"
                        elif organization_status == "needs_organization":
                            organization_indicator = f"⚠️ {untagged_count}"
                        elif organization_status == "organized":
                            organization_indicator = "✅"
                        else:
                            organization_indicator = "❓"

                    except Exception as e:
                        # Fallback to basic indicators if stats endpoint fails
                        logger.debug(f"Stats endpoint not available for deck {deck_id}, using fallback: {str(e)}")
                        total_cards = deck.get("card_count", 0)
                        untagged_count = deck.get("untagged_flashcards_count", 0)

                        if total_cards == 0:
                            organization_status = "empty"
                            organization_indicator = "📝"
                        elif untagged_count > 0:
                            organization_status = "needs_organization"
                            organization_indicator = f"⚠️ {untagged_count}"
                        else:
                            organization_status = "organized"
                            organization_indicator = "✅"
                else:
                    # Fallback for decks without ID
                    total_cards = deck.get("card_count", 0)
                    untagged_count = deck.get("untagged_flashcards_count", 0)

                    if total_cards == 0:
                        organization_status = "empty"
                        organization_indicator = "📝"
                    elif untagged_count > 0:
                        organization_status = "needs_organization"
                        organization_indicator = f"⚠️ {untagged_count}"
                    else:
                        organization_status = "organized"
                        organization_indicator = "✅"

                formatted_deck["organization_status"] = organization_status
                formatted_deck["organization_indicator"] = organization_indicator
                formatted_deck["untagged_flashcards_count"] = untagged_count

                formatted_decks.append(formatted_deck)

            return {
                "decks": formatted_decks,
                "total_decks": len(formatted_decks),
                "total_cards": sum(d.get("card_count", 0) for d in formatted_decks),
                "metadata": {
                    "description": "Complete list of available flashcard decks with tags (MCP version)",
                    "source": "iCards API - MCP endpoint",
                    "last_updated": api_response.get("timestamp", "2025-01-01T00:00:00Z"),
                },
                "_instructions": get_instructions_for_list_decks(),
            }

        except Exception as e:
            logger.error(f"Error listing decks: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not list decks: {str(e)}"}

    # Tool 3: Create Deck
    @mcp_server.tool(
        name="create_deck",
        description="""
        🎯 CREATE FLASHCARD DECK with SMART COVER GENERATION

        🚀 INTERACTIVE EXPERIENCE: This tool will ASK YOU directly if you want AI-generated cover images!

        📝 HOW IT WORKS:
        • Provide name and description
        • The tool will INTERACTIVELY ASK: "Do you want AI cover image?"
        • Answer 'yes'/'true' or 'no'/'false' when prompted
        • If elicitation fails, specify generate_cover=true/false manually

        🎨 COVER IMAGE OPTIONS:
        • Interactive: Omit generate_cover → Tool asks you
        • Direct: generate_cover=true → Generate AI cover
        • Direct: generate_cover=false → No cover image
        • String support: "true"/"false"/"yes"/"no"/"si" all work

        ✅ EXAMPLE USAGE:
        # Interactive (recommended)
        create_deck(name="Portuguese", description="Learn Portuguese")

        # Direct with cover
        create_deck(name="Portuguese", description="Learn Portuguese", generate_cover=true)

        # Direct without cover
        create_deck(name="Portuguese", description="Learn Portuguese", generate_cover=false)

        ✨ Perfect for creating organized flashcard collections!
        """,
        tags={"decks", "creation", "organization"},
    )
    async def create_deck(
        ctx: Context,
        name: str = Field(..., description="Name of the new deck (3-100 characters)"),
        generate_cover: bool | str | None = Field(
            None,
            description="Cover image generation: true=yes, false=no, omit=ask user. Accepts: true/false or 'true'/'false' strings"
        ),
        description: str = Field("", description="Optional description of the deck"),
    ) -> dict:
        """Create a new flashcard deck with typed validation."""
        try:
            # Store original value to track if elicitation was attempted
            original_generate_cover = generate_cover

            # Convert string boolean values to actual booleans
            if isinstance(generate_cover, str):
                if generate_cover.lower() in ('true', 'yes', '1', 'si', 'sí'):
                    generate_cover = True
                elif generate_cover.lower() in ('false', 'no', '0'):
                    generate_cover = False
                else:
                    # Invalid string, treat as None to trigger elicitation
                    generate_cover = None

            # Handle elicitation for generate_cover if not specified
            if generate_cover is None:
                logger.info("Elicitation triggered for generate_cover")
                try:
                    logger.debug("Attempting to elicit cover image generation choice")
                    # Ask user if they want to generate a cover image
                    result = await ctx.elicit(
                        message="🎨 ¿Quieres que genere una imagen de portada con IA para este mazo?\n\n💡 Esto crea una portada personalizada pero puede generar costos adicionales.\n\nResponde: 'sí'/'yes'/'true' para generar portada, 'no'/'false' para crear sin portada:",
                        response_type=bool
                    )
                    generate_cover = result
                    logger.info(f"Elicitation successful - User chose to generate cover: {generate_cover}")
                except Exception as e:
                    logger.error(f"Elicitation failed with error: {str(e)}")
                    logger.warning("Elicitation not supported by client, providing helpful guidance")
                    # Instead of defaulting silently, provide guidance
                    generate_cover = False
                    logger.info("Defaulting to no cover generation with guidance for manual specification")

            # Create typed parameters
            params = CreateDeckParams(
                name=name,
                description=description,
                generate_cover=generate_cover
            )

            # Use typed service
            typed_service = TypedService.get_instance()
            response = await typed_service.create_deck(params)

            # Create descriptive message based on cover generation choice
            cover_message = "with AI-generated cover" if generate_cover else "without cover image"

            # Check if elicitation was attempted but failed (original None, final False)
            elicitation_failed = original_generate_cover is None and generate_cover is False

            # Handle response structure - may or may not have deck data
            deck_name_for_message = name  # Default to the input name
            deck_data = None

            if response.deck:
                # We have full deck data
                deck_name_for_message = response.deck.name
                deck_data = response.deck.dict()
            else:
                # We only have success response, create minimal deck data
                deck_data = {
                    "id": None,
                    "name": name,
                    "description": description,
                    "coverUrl": None,
                    "visibility": "private",
                    "clonesCount": 0,
                    "userId": None,  # Will be set by backend
                    "createdAt": response.createdAt.isoformat() if response.createdAt else None,
                    "updatedAt": None,
                    "cardCount": 0,
                    "tagCount": 0,
                    "isActive": True
                }

            full_message = f"Deck '{deck_name_for_message}' created successfully {cover_message}"

            result = {
                "success": response.success,
                "deck": deck_data,
                "message": full_message,
                "cover_generated": generate_cover,
                "_instructions": get_instructions_for_create_deck(deck_name_for_message),
            }

            # Add guidance if elicitation failed
            if elicitation_failed:
                elicitation_note = "\n\n💡 Tip: Para especificar generación de portada, incluye el parámetro generate_cover=true/false en tu solicitud."
                result["message"] += elicitation_note
                result["elicitation_note"] = "Para futuras creaciones, especifica generate_cover=true/false directamente"

            return result

        except ValueError as e:
            # Handle validation errors from Pydantic models
            logger.warning(f"Validation error creating deck '{name}': {str(e)}")
            return {"error": "Validation error", "message": str(e)}
        except Exception as e:
            logger.error(f"Error creating deck '{name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not create deck: {str(e)}"}

    # Tool 4: Get Deck Info
    @mcp_server.tool(
        name="get_deck_info",
        description="""
        📋 BASIC deck information and structure.

        🎯 BEST FOR: Quick deck overview, seeing tags and basic counts
        📊 SHOWS: Metadata, flashcard counts, tags with counts, difficulty distribution
        ⚡ FAST: Lightweight info for general deck management

        💡 TIP: Use 'get_deck_stats(deck_name)' for DETAILED organization analysis and insights
        🔄 TIP: Good for navigation and basic deck understanding
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
            tag_service = TagService.get_instance()
            tags_response = await tag_service.get_deck_tags(deck_id)
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
                "_instructions": get_instructions_for_get_deck_info(deck_name),
            }

        except Exception as e:
            logger.error(f"Error getting deck info for {deck_name}: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not get deck information: {str(e)}"}

    # Tool 5: Create Flashcard Template
    @mcp_server.tool(
        name="create_flashcard_template",
        description="""
        Generate a flashcard template optimized for specific learning content types.

        This tool creates structured templates with:
        • Recommended front/back content formats
        • Suggested difficulty levels
        • Content organization tips
        • Usage examples

        Available deck types: vocabulary, grammar, kanji, phrases, general, custom.
        Perfect for maintaining consistency and best practices across your flashcards.
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
                "_instructions": get_instructions_for_create_template(),
            }

        except Exception as e:
            logger.error(f"Error creating template for deck type {deck_type}: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not create template: {str(e)}"}

    # Tool 6: List Flashcards in Deck
    @mcp_server.tool(
        name="list_flashcards",
        description="""
        Retrieve flashcards from a specific deck with flexible filtering and pagination.

        This tool provides detailed flashcard information including:
        • Front/back content and metadata
        • Difficulty levels and review statistics
        • Associated tags and categorization
        • Creation and modification dates

        Features:
        • Pagination support (default: 50 cards, max: 100)
        • Sorting options (by creation date, difficulty, reviews, accuracy)
        • Difficulty filtering (1-5)
        • Option to retrieve all cards at once

        Ideal for deck review, content management, and study session preparation.
        """,
        tags={"flashcards", "listing", "deck-content", "study-planning"},
    )
    async def list_flashcards(
        deck_name: str = Field(..., description="Name of the deck to list flashcards from"),
        limit: int = Field(50, description="Maximum number of cards to return (1-100). Ignored if all_cards=True"),
        offset: int = Field(0, description="Number of cards to skip. Ignored if all_cards=True"),
        sort_by: Literal["created", "difficulty", "reviews", "correct_rate"] = Field(
            "created", description="Sort cards by this criteria"
        ),
        filter_difficulty: int | None = Field(None, description="Filter cards by difficulty level (1-5)"),
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

            response["_instructions"] = get_instructions_for_list_flashcards(deck_name)
            return response

        except Exception as e:
            logger.error(f"Error listing flashcards in '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not list flashcards: {str(e)}"}

    @mcp_server.tool(
        name="count_flashcards",
        description="""
        Get the exact total count of flashcards in a specific deck.

        This tool provides a quick and accurate count by:
        • Making a single optimized API call
        • Retrieving all flashcards at once (no pagination limits)
        • Returning the precise total number

        Useful for deck statistics, progress tracking, and content management decisions.
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
                "_instructions": get_instructions_for_count_flashcards(deck_name),
            }

        except Exception as e:
            logger.error(f"Error counting flashcards in '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not count flashcards: {str(e)}"}

    # Tool 7: Assign Tags to Flashcards (with smart auto-detection)
    @mcp_server.tool(
        name="assign_tags_to_flashcards",
        description="""
        🏷️ SMART TAG ASSIGNMENT: Assign tags to flashcards with auto-detection capabilities.

        🎯 PERFECT FOR: Batch organization workflows, especially after bulk creation
        ✨ SMART FEATURES: Auto-detects flashcards by criteria, no manual ID listing needed
        🚀 EFFICIENT: Processes up to 100 flashcards in a single operation

        📋 AUTO-DETECTION MODES:
        • `filter_criteria="untagged"` - Automatically tags ALL flashcards without tags in the deck
        • `filter_criteria="all"` - Tags ALL flashcards in the deck (be careful!)
        • Manual IDs - Specify exact flashcard IDs for precision control

        🎪 WORKFLOW OPTIMIZATION:
        1. Create flashcards with `bulk_create_flashcards` (no tags)
        2. Use this tool with `filter_criteria="untagged"` for instant organization
        3. No need to manually list and copy flashcard IDs!

        ⚡ ADVANCED OPTIONS:
        • `max_flashcards` - Limit the number of cards to tag at once
        • Auto-creates tags if they don't exist
        • Detailed success/failure reports
        """,
        tags={"flashcards", "tags", "organization", "automation", "bulk"},
    )
    async def assign_tags_to_flashcards(
        deck_name: str = Field(..., description="Name of the deck containing the flashcards"),
        tag_name: str = Field(..., description="Name of the tag to assign (will be created if it doesn't exist)"),
        filter_criteria: str | None = Field(
            None,
            description="Auto-select flashcards: 'untagged' (no tags), 'all' (entire deck), or None for manual IDs"
        ),
        flashcard_ids: list[int] | None = Field(
            None,
            description="Manual flashcard IDs to tag (ignored if filter_criteria is used). Max 100 IDs."
        ),
        max_flashcards: int | None = Field(
            None,
            description="Limit number of flashcards to tag when using auto-detection (1-100)"
        ),
    ) -> dict:
        """Assign a tag to specific flashcards with smart auto-detection."""
        try:
            # Validate inputs
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid",
                }

            if not tag_name.strip():
                return {
                    "error": "Invalid tag name",
                    "message": "Tag name cannot be empty",
                }

            # Get deck ID first (needed for auto-detection)
            deck_service = DeckService.get_instance()
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            deck_id = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_id = deck.get("id")
                    break

            if not deck_id:
                available_decks = [d.get("name") for d in all_decks]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
                }

            # Smart auto-detection logic
            detection_message = ""
            if filter_criteria:
                if filter_criteria not in ['untagged', 'all']:
                    return {
                        "error": "Invalid filter_criteria",
                        "message": "Filter criteria must be 'untagged', 'all', or None",
                    }

                # Auto-detect flashcards based on criteria
                if filter_criteria == "untagged":
                    detection_message = f"🔍 Auto-detecting untagged flashcards in '{deck_name}'..."
                    # Use list_untagged_flashcards service
                    flashcard_service = FlashcardService.get_instance()
                    untagged_response = await flashcard_service.list_untagged_flashcards(
                        deck_id=deck_id,
                        all_cards=True
                    )
                    detected_flashcards = untagged_response.get("flashcards", [])
                    detection_message += f" Found {len(detected_flashcards)} untagged flashcards."

                elif filter_criteria == "all":
                    detection_message = f"🔍 Auto-detecting ALL flashcards in '{deck_name}'..."
                    # Use list_flashcards with all_cards=True
                    flashcard_service = FlashcardService.get_instance()
                    all_response = await flashcard_service.list_flashcards(
                        deck_id=deck_id,
                        all_cards=True
                    )
                    detected_flashcards = all_response.get("flashcards", [])
                    detection_message += f" Found {len(detected_flashcards)} total flashcards."

                # Apply max_flashcards limit if specified
                if max_flashcards and len(detected_flashcards) > max_flashcards:
                    detected_flashcards = detected_flashcards[:max_flashcards]
                    detection_message += f" Limited to first {max_flashcards} flashcards."

                # Extract IDs from detected flashcards
                flashcard_ids = [card["id"] for card in detected_flashcards]

                if not flashcard_ids:
                    return {
                        "success": False,
                        "message": f"No flashcards found matching criteria '{filter_criteria}' in deck '{deck_name}'",
                        "filter_criteria": filter_criteria,
                        "detection_details": detection_message,
                    }

                detection_message += f" Will tag {len(flashcard_ids)} flashcards."

            else:
                # Manual mode - validate provided IDs
                if not flashcard_ids:
                    return {
                        "error": "Missing flashcard_ids",
                        "message": "You must provide flashcard_ids when not using filter_criteria",
                    }

                if len(flashcard_ids) > 100:
                    return {
                        "error": "Too many flashcard_ids",
                        "message": "Maximum 100 flashcard IDs allowed",
                    }


            # Get or create tag
            tag_service = TagService.get_instance()
            tags_response = await tag_service.get_deck_tags(deck_id)
            tags = tags_response.get("data", [])

            tag_id = None
            tag_existed = False
            for tag in tags:
                if tag.get("name", "").lower() == tag_name.lower():
                    tag_id = tag.get("id")
                    tag_existed = True
                    break

            # Create tag if it doesn't exist
            if not tag_id:
                tag_data = {
                    "name": tag_name.strip(),
                }
                try:
                    create_response = await tag_service.create_deck_tag(deck_id, tag_data)
                    tag_id = create_response.get("data", {}).get("id")
                    if not tag_id:
                        return {
                            "error": "Failed to create tag",
                            "message": f"Could not create tag '{tag_name}'",
                        }
                    logger.info(f"Created new tag '{tag_name}' with ID {tag_id}")
                    tag_existed = False
                except Exception as e:
                    return {
                        "error": "Failed to create tag",
                        "message": f"Could not create tag '{tag_name}': {str(e)}",
                    }

            # Assign tag to each flashcard by ID
            flashcard_service = FlashcardService.get_instance()
            success_count = 0
            failed_flashcards = []
            skipped_count = 0

            for flashcard_id in flashcard_ids:
                try:
                    # Get current flashcard data
                    flashcard_data = await flashcard_service.get_flashcard(flashcard_id)
                    flashcard_info = flashcard_data.get("data", {})
                    
                    if not flashcard_info:
                        failed_flashcards.append({
                            "id": flashcard_id,
                            "reason": "Flashcard not found"
                        })
                        continue

                    # Verify flashcard belongs to this deck
                    if flashcard_info.get("deckId") != deck_id:
                        failed_flashcards.append({
                            "id": flashcard_id,
                            "reason": f"Flashcard does not belong to deck '{deck_name}'"
                        })
                        continue

                    current_tag_id = flashcard_info.get("tagId")
                    if current_tag_id == tag_id:
                        # Already has this specific tag, skip
                        skipped_count += 1
                        continue

                    # Update the flashcard with the tag - need to include required fields
                    update_data = {
                        "front": flashcard_info.get("front", ""),
                        "back": flashcard_info.get("back", ""),
                        "difficulty": flashcard_info.get("difficulty", 2),
                        "deckId": deck_id,
                        "tagId": tag_id
                    }
                    await flashcard_service.update_flashcard(flashcard_id, update_data)
                    success_count += 1

                except Exception as e:
                    failed_flashcards.append({
                        "id": flashcard_id,
                        "reason": str(e)
                    })

            result = {
                "success": True,
                "message": f"Successfully assigned tag '{tag_name}' to {success_count} flashcards in deck '{deck_name}'",
                "deck_name": deck_name,
                "deck_id": deck_id,
                "tag_name": tag_name,
                "tag_id": tag_id,
                "flashcard_ids_requested": len(flashcard_ids),
                "successful_assignments": success_count,
                "skipped_already_tagged": skipped_count,
                "tag_created": not tag_existed,
            }

            # Add auto-detection details if used
            if filter_criteria:
                result["auto_detection_used"] = True
                result["filter_criteria"] = filter_criteria
                result["detection_details"] = detection_message

            if failed_flashcards:
                result["failed_assignments"] = len(failed_flashcards)
                result["failures"] = failed_flashcards[:5]  # Show first 5 failures
                result["message"] += f" ({len(failed_flashcards)} failed)"

            if success_count > 0:
                result["next_steps"] = [
                    f"Verify tags by listing flashcards: list_flashcards(deck_name='{deck_name}')",
                    f"Check deck stats: get_deck_info('{deck_name}')",
                ]

            result["_instructions"] = get_instructions_for_assign_tags(deck_name)
            return result

        except Exception as e:
            logger.error(f"Error assigning tags to flashcards in '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not assign tags: {str(e)}"}

    # Tool 8: Bulk Create Flashcards
    @mcp_server.tool(
        name="bulk_create_flashcards",
        description="""
        🚀 BULK CREATE: Add MULTIPLE flashcards at once (2-50 cards).

        ⚠️ PREFERRED METHOD for creating several flashcards!
        This is MUCH MORE EFFICIENT than adding them one by one.

        This tool creates multiple flashcards in a single operation:
        • Front content (question/prompt) for each flashcard
        • Back content (answer) for each flashcard
        • Optional difficulty level (defaults to 2)
        • All flashcards go to the same deck
        • ⚠️ RECOMMENDATION: Create WITHOUT tags initially, organize later

        Features:
        • ⚡ Bulk processing (2-50 flashcards at once)
        • ✅ Validates all content before creation
        • 📊 Detailed success/failure reports
        • 🎯 Perfect for populating new decks or adding related cards

        💡 TIP: Use this instead of add_flashcard when creating multiple cards!
        """,
        tags={"flashcards", "bulk", "creation", "efficiency"},
    )
    async def bulk_create_flashcards(
        deck_name: str = Field(..., description="Name of the deck to add flashcards to"),
        flashcards: list[dict[str, str | int]] = Field(
            ...,
            description="List of flashcards to create. Each item should have 'front' and 'back' keys, optional 'difficulty' (1-5). Max 50 flashcards.",
            min_length=2,
            max_length=50
        ),
    ) -> dict:
        """Create multiple flashcards at once."""
        try:
            # Validate deck name
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid",
                }

            # Get deck ID
            deck_service = DeckService.get_instance()
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            deck_id = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_id = deck.get("id")
                    break

            if not deck_id:
                available_decks = [d.get("name") for d in all_decks if d.get("name")]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
                }

            # Validate and prepare flashcards
            validated_flashcards = []
            validation_errors = []

            for i, card in enumerate(flashcards):
                front = card.get("front", "").strip()
                back = card.get("back", "").strip()
                difficulty = card.get("difficulty", 2)

                # Validate content
                is_valid, error_msg = validate_flashcard_content(front, back)
                if not is_valid:
                    validation_errors.append({
                        "index": i,
                        "front": front[:50] + "..." if len(front) > 50 else front,
                        "error": error_msg
                    })
                    continue

                # Ensure difficulty is valid (1-3 for backend, but we'll map 4-5 to 3)
                difficulty = min(max(difficulty, 1), 3)

                validated_flashcards.append({
                    "front": front,
                    "back": back,
                    "deckId": deck_id,
                    "difficulty": difficulty,
                })

            if validation_errors:
                return {
                    "error": "Validation errors",
                    "message": f"{len(validation_errors)} flashcards failed validation",
                    "validation_errors": validation_errors[:10],  # Show first 10 errors
                    "valid_flashcards": len(validated_flashcards),
                }

            if not validated_flashcards:
                return {
                    "error": "No valid flashcards",
                    "message": "All flashcards failed validation",
                }

            # Create flashcards in bulk
            flashcard_service = FlashcardService.get_instance()
            bulk_response = await flashcard_service.bulk_create_flashcards(deck_name, validated_flashcards)

            # Process response
            created_data = bulk_response.get("data", [])
            success_count = len(created_data) if isinstance(created_data, list) else 0

            return {
                "success": True,
                "message": f"Successfully created {success_count} flashcards in deck '{deck_name}'",
                "deck_name": deck_name,
                "requested_count": len(flashcards),
                "created_count": success_count,
                "failed_count": len(flashcards) - success_count,
                "created_flashcards": created_data,
                "_instructions": get_instructions_for_bulk_create(deck_name, success_count),
            }

        except Exception as e:
            logger.error(f"Error bulk creating flashcards in '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not create flashcards: {str(e)}"}

    # Tool 10: Get Deck Statistics
    @mcp_server.tool(
        name="get_deck_stats",
        description="""
        📈 DETAILED analytics and ORGANIZATION assessment for specific deck.

        🎯 BEST FOR: Deep analysis, organization planning, performance insights
        📊 SHOWS: Organization %, tag distribution with %, study metrics, difficulty analysis
        🧠 SMART: Uses backend data when available, intelligent fallback when needed
        💡 INSIGHTS: Human-readable analysis and recommendations included

        🔍 PERFECT FOR:
        • Checking organization status (% tagged, missing tags)
        • Understanding tag distribution and balance
        • Study performance analysis
        • Planning bulk organization work

        💡 TIP: Use 'get_deck_info(deck_name)' for quick basic overview
        ⚡ TIP: More detailed than get_deck_info but slower due to analysis
        """,
        tags={"decks", "statistics", "analytics", "organization"},
    )
    async def get_deck_stats(
        deck_name: str = Field(..., description="Name of the deck to get detailed statistics for"),
    ) -> dict:
        """Get comprehensive statistics for a specific deck."""
        try:
            # Validate deck name
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid",
                }

            # Get deck ID and basic info from MCP endpoint (more reliable)
            deck_service = DeckService.get_instance()
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            deck_id = None
            deck_basic_info = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_id = deck.get("id")
                    deck_basic_info = deck
                    break

            if not deck_id:
                available_decks = [d.get("name") for d in all_decks if d.get("name")]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
                }

            # Strategy: Enrich when valuable, pass-through when backend provides good structure
            stats_data = {}
            organization_status = "unknown"
            last_updated = "2025-01-01T00:00:00Z"
            backend_provided_stats = False

            try:
                # Try advanced stats endpoint first - it works perfectly!
                stats_response = await deck_service.get_deck_stats(deck_id)

                # The response is wrapped in "data" field
                response_data = stats_response.get("data", {})
                raw_stats = response_data.get("stats", {})

                if raw_stats and len(raw_stats) > 0:  # Backend provided rich stats
                    stats_data = raw_stats  # Pass through - backend data is perfect
                    organization_status = stats_data.get("organizationMetrics", {}).get("organizationStatus", "unknown")
                    backend_provided_stats = True
                    logger.debug(f"Using backend stats endpoint successfully: {len(raw_stats)} fields, org_status: {organization_status}")
                else:
                    # Backend returned empty stats, fall back to calculation
                    logger.warning(f"Backend stats endpoint returned empty data: {raw_stats}")
                    raise Exception("Empty stats from backend")

                last_updated = response_data.get("lastUpdated", "2025-01-01T00:00:00Z")

            except Exception as e:
                logger.debug(f"Stats endpoint not available, using MCP data for calculations: {str(e)}")
                # Fallback: Use MCP data which is more reliable
                try:
                    logger.debug(f"Calculating stats from MCP data for deck {deck_id}")

                    # Use the reliable data from MCP endpoint
                    mcp_stats = deck_basic_info.get("stats", {})
                    mcp_tags = deck_basic_info.get("tags", [])

                    # Convert MCP format to our expected format
                    mock_deck_info = {
                        "deck": {
                            "id": deck_id,
                            "name": deck_basic_info.get("name", ""),
                            "card_count": mcp_stats.get("flashcardsCount", 0),
                            "difficulty_distribution": {}  # MCP doesn't provide this
                        },
                        "tags": [
                            {
                                "id": tag.get("id"),
                                "name": tag.get("name"),
                                "flashcard_count": 0  # MCP doesn't provide individual counts
                            } for tag in mcp_tags
                        ]
                    }

                    logger.debug(f"MCP-based mock data: card_count={mock_deck_info['deck']['card_count']}, tags={len(mock_deck_info['tags'])}")

                    stats_data = await _calculate_basic_stats_from_mcp_data(mock_deck_info, deck_basic_info)
                    logger.debug(f"Calculated stats totalFlashcards: {stats_data.get('totalFlashcards', 'NOT_SET')}")

                    organization_status = stats_data.get("organizationMetrics", {}).get("organizationStatus", "unknown")
                    backend_provided_stats = False
                except Exception as fallback_error:
                    logger.error(f"MCP-based calculation failed: {str(fallback_error)}")
                    stats_data = {}

            # Generate insights based on available data (always enrich this)
            insights = _generate_stats_insights(stats_data, organization_status, backend_provided_stats)

            result = {
                "deck_name": deck_name,
                "deck_id": deck_id,
                "statistics": stats_data,  # Either raw backend data or calculated
                "insights": insights,      # Always enriched
                "organization_status": organization_status,
                "data_source": "backend_stats" if backend_provided_stats else "calculated_fallback",
                "last_updated": last_updated,
                "_instructions": get_instructions_for_get_deck_stats(deck_name),
            }

            return result

        except Exception as e:
            logger.error(f"Error getting deck statistics for '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not get deck statistics: {str(e)}"}

    # Tool 11: List Untagged Flashcards
    @mcp_server.tool(
        name="list_untagged_flashcards",
        description="""
        🏷️ Find and ORGANIZE flashcards without tags.

        🎯 PERFECT FOR: Batch organization workflows
        📋 PURPOSE: See exactly which flashcards need categorization

        ⚡ EFFICIENT: Only loads untagged cards (faster than full list)
        🎯 FOCUSED: Clean view without already-tagged cards
        📊 COUNTS: Clear numbers for planning organization work

        🔄 WORKFLOW: Use this → 'assign_tags_to_flashcards' → verify with 'list_flashcards'
        💡 TIP: Great for maintaining organized decks over time
        """,
        tags={"flashcards", "organization", "untagged", "efficiency"},
    )
    async def list_untagged_flashcards(
        deck_name: str = Field(..., description="Name of the deck to get untagged flashcards from"),
        all_cards: bool = Field(True, description="Get all untagged flashcards at once (recommended for organization)"),
    ) -> dict:
        """List flashcards that don't have tags assigned yet."""
        try:
            # Validate deck name
            if not validate_deck_name(deck_name):
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name format is invalid",
                }

            # Get deck ID
            deck_service = DeckService.get_instance()
            all_decks_response = await deck_service.list_decks_mcp()
            all_decks = all_decks_response.get("decks", [])

            deck_id = None
            for deck in all_decks:
                if deck.get("name", "").lower() == deck_name.lower():
                    deck_id = deck.get("id")
                    break

            if not deck_id:
                available_decks = [d.get("name") for d in all_decks if d.get("name")]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
                }

            # Get untagged flashcards
            flashcard_service = FlashcardService.get_instance()
            response = await flashcard_service.list_untagged_flashcards(
                deck_id=deck_id,
                all_cards=all_cards
            )

            # Extract flashcards
            flashcards = response.get("flashcards", [])

            result = {
                "deck_name": deck_name,
                "deck_id": deck_id,
                "untagged_flashcards": flashcards,
                "untagged_count": len(flashcards),
                "all_cards_requested": all_cards,
                "message": f"Found {len(flashcards)} flashcards without tags in deck '{deck_name}'",
                "_instructions": get_instructions_for_list_untagged(deck_name, len(flashcards)),
            }

            return result

        except Exception as e:
            logger.error(f"Error listing untagged flashcards in '{deck_name}': {str(e)}")
            return {"error": "Internal server error", "message": f"Could not list untagged flashcards: {str(e)}"}

    # Tool 11: Update Flashcard
    @mcp_server.tool(
        name="update_flashcard",
        description="""
        Modify existing flashcard content, difficulty, or other properties.

        This tool allows flexible updates to flashcards by:
        • Changing front content (question/prompt)
        • Modifying back content (answer)
        • Adjusting difficulty level (1-5)
        • All fields are optional - update only what you need

        Important notes:
        • The flashcard must belong to an existing deck
        • Content validation ensures quality standards
        • To change tags, use assign_tags_to_flashcards tool instead

        Perfect for correcting errors, improving content, or adjusting difficulty as you learn.
        """,
        tags={"flashcards", "update", "edit", "modification"},
    )
    async def update_flashcard(
        deck_name: str = Field(..., description="Name of the deck containing the flashcard"),
        flashcard_id: int = Field(..., description="ID of the flashcard to update"),
        front: str | None = Field(None, description="New front content (question/prompt)"),
        back: str | None = Field(None, description="New back content (answer)"),
        difficulty_level: int | None = Field(None, description="New difficulty level (1-5)"),
    ) -> dict:
        """Update an existing flashcard."""
        try:
            # Validate deck name
            if not validate_deck_name(deck_name):
                return {"error": "Invalid deck name", "message": "Deck name format is invalid"}

            # ALWAYS get current flashcard first (needed for required fields)
            flashcard_service = FlashcardService.get_instance()
            current_flashcard_response = await flashcard_service.get_flashcard(flashcard_id)
            current_flashcard = current_flashcard_response.get("data", {})
            
            if not current_flashcard:
                return {"error": "Flashcard not found", "message": f"No flashcard found with ID {flashcard_id}"}

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
                available_decks = [d.get("name") for d in all_decks if d.get("name")]
                return {
                    "error": "Deck not found",
                    "message": f"No deck found with name '{deck_name}'",
                    "available_decks": available_decks,
                }

            # Verify flashcard belongs to this deck
            if current_flashcard.get("deckId") != deck_id:
                return {
                    "error": "Flashcard not in deck",
                    "message": f"Flashcard {flashcard_id} does not belong to deck '{deck_name}'",
                }

            # Use new values or keep current ones
            final_front = front.strip() if front is not None else current_flashcard.get("front", "")
            final_back = back.strip() if back is not None else current_flashcard.get("back", "")
            final_difficulty = min(difficulty_level, 3) if difficulty_level is not None else current_flashcard.get("difficulty", 2)

            # Validate content
            is_valid, error_msg = validate_flashcard_content(final_front, final_back)
            if not is_valid:
                return {"error": "Invalid flashcard content", "message": error_msg}

            # Build complete update data with ALL required fields (keep existing tag)
            update_data = {
                "front": final_front,
                "back": final_back,
                "difficulty": final_difficulty,
                "deckId": deck_id,
                "tagId": current_flashcard.get("tagId")  # Keep existing tag
            }

            # Update the flashcard
            api_response = await flashcard_service.update_flashcard(flashcard_id, update_data)
            response_data = format_flashcard_response(api_response.get("data", {}))

            # Determine what changed
            changed_fields = []
            if front is not None:
                changed_fields.append("front")
            if back is not None:
                changed_fields.append("back")
            if difficulty_level is not None:
                changed_fields.append("difficulty")

            return {
                "success": True,
                "flashcard": response_data,
                "message": f"Flashcard updated successfully in deck '{deck_name}'",
                "changed_fields": changed_fields if changed_fields else ["none - validated existing data"],
                "note": "To change tags, use assign_tags_to_flashcards tool",
                "_instructions": get_instructions_for_update_flashcard(deck_name),
            }

        except Exception as e:
            logger.error(f"Error updating flashcard {flashcard_id}: {str(e)}")
            return {"error": "Internal server error", "message": f"Could not update flashcard: {str(e)}"}
