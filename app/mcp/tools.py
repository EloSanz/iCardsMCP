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

# Helper function for generating insights from stats data
def _generate_stats_insights(stats_data: dict, organization_status: str, backend_provided: bool) -> list[str]:
    """Generate human-readable insights from statistics data."""
    insights = []

    # Add data source indicator
    if backend_provided:
        insights.append("📊 Datos proporcionados por el backend")
    else:
        insights.append("🧮 Estadísticas calculadas desde información disponible")

    # Organization insights
    if organization_status == "empty":
        insights.append("📝 Deck vacío - ¡Listo para agregar flashcards!")
    elif organization_status == "organized":
        insights.append("🎉 Deck completamente organizado - ¡Excelente trabajo!")
    elif organization_status == "needs_organization":
        untagged_count = stats_data.get("untaggedFlashcards", 0)
        org_percentage = stats_data.get("organizationMetrics", {}).get("organizationPercentage", 0)
        if untagged_count > 0:
            insights.append(f"⚠️ {untagged_count} flashcards necesitan organización")
        else:
            insights.append(f"⚠️ Necesita organización ({org_percentage}% tagged)")
    else:
        # Unknown status - try to infer
        total_flashcards = stats_data.get("totalFlashcards", 0)
        if total_flashcards == 0:
            insights.append("📝 Deck vacío - ¡Listo para agregar flashcards!")
        else:
            insights.append("❓ Estado de organización desconocido")

    # Study insights
    study_metrics = stats_data.get("studyMetrics", {})
    total_reviews = study_metrics.get("totalReviews", 0)
    accuracy = study_metrics.get("accuracyRate", 0)
    current_streak = study_metrics.get("currentStreak", 0)

    if total_reviews > 0:
        insights.append(f"📚 {total_reviews} reviews totales con {accuracy}% de precisión")
        if current_streak > 0:
            insights.append(f"🔥 Racha actual: {current_streak} días")
    else:
        insights.append("📖 Sin reviews aún - ¡hora de empezar a estudiar!")

    # Additional insights based on available data
    total_flashcards = stats_data.get("totalFlashcards", 0)
    if total_flashcards > 0:
        avg_difficulty = study_metrics.get("averageDifficulty", 0)
        if avg_difficulty > 0:
            insights.append(f"🎯 Dificultad promedio: {avg_difficulty}/5")

        tags_count = stats_data.get("organizationMetrics", {}).get("tagsCount", 0)
        if tags_count > 0:
            insights.append(f"🏷️ {tags_count} tags organizando el contenido")

    return insights

# Helper function for calculating basic statistics from MCP data (more reliable)
async def _calculate_basic_stats_from_mcp_data(mcp_mock_data: dict, deck_basic_info: dict) -> dict:
    """Calculate basic statistics using MCP endpoint data (more reliable than get_deck_info)."""
    try:
        logger.debug(f"_calculate_basic_stats_from_mcp_data called")

        deck_data = mcp_mock_data.get("deck", {})
        tags_data = mcp_mock_data.get("tags", [])

        # Get real stats from MCP data
        mcp_stats = deck_basic_info.get("stats", {})

        # Basic counts from MCP (more reliable)
        total_flashcards = mcp_stats.get("flashcardsCount", 0)
        tags_count = len(tags_data)

        logger.debug(f"MCP stats - total_flashcards: {total_flashcards}, tags_count: {tags_count}")

        # Since MCP doesn't provide detailed tag counts, we assume all flashcards are tagged
        # if there are tags, or estimate based on available data
        tagged_flashcards = total_flashcards if tags_count > 0 else 0
        untagged_flashcards = max(0, total_flashcards - tagged_flashcards)

        # Organization percentage
        organization_percentage = round((tagged_flashcards / total_flashcards * 100), 1) if total_flashcards > 0 else 0

        # Organization status
        if total_flashcards == 0:
            organization_status = "empty"
        elif untagged_flashcards == 0 and tags_count > 0:
            organization_status = "organized"
        else:
            organization_status = "needs_organization"

        # Build flashcards by tag (MCP doesn't provide individual counts, so we estimate)
        flashcards_by_tag = []
        if tags_count > 0 and total_flashcards > 0:
            # Distribute flashcards evenly among tags (rough estimate)
            flashcards_per_tag = total_flashcards // tags_count
            remainder = total_flashcards % tags_count

            for i, tag in enumerate(tags_data):
                count = flashcards_per_tag + (1 if i < remainder else 0)
                flashcards_by_tag.append({
                    "tagId": tag.get("id"),
                    "tagName": tag.get("name"),
                    "count": count,
                    "percentage": round((count / total_flashcards * 100), 1) if total_flashcards > 0 else 0
                })

        # Average tags per flashcard (estimated)
        average_tags_per_flashcard = round(tags_count / total_flashcards, 2) if total_flashcards > 0 else 0

        return {
            "totalFlashcards": total_flashcards,
            "untaggedFlashcards": untagged_flashcards,
            "taggedFlashcards": tagged_flashcards,
            "flashcardsByDifficulty": {},  # MCP doesn't provide difficulty distribution
            "flashcardsByTag": flashcards_by_tag,
            "organizationMetrics": {
                "organizationPercentage": organization_percentage,
                "organizationStatus": organization_status,
                "tagsCount": tags_count,
                "averageTagsPerFlashcard": average_tags_per_flashcard
            },
            "studyMetrics": {
                "totalReviews": mcp_stats.get("revisionsCount", 0),
                "correctReviews": 0,  # MCP doesn't provide this breakdown
                "incorrectReviews": 0,
                "accuracyRate": 0,    # Can't calculate without correct/incorrect breakdown
                "averageDifficulty": 0,  # MCP doesn't provide this
                "lastStudied": None,
                "currentStreak": 0
            }
        }

    except Exception as e:
        logger.error(f"Error calculating MCP-based stats: {str(e)}")
        return {}

# Helper function for calculating basic statistics from deck info (legacy)
async def _calculate_basic_stats_from_deck_info(deck_info_response: dict, deck_basic_info: dict) -> dict:
    """Calculate basic statistics from available deck information."""
    try:
        logger.debug(f"_calculate_basic_stats_from_deck_info called with response keys: {list(deck_info_response.keys()) if deck_info_response else 'None'}")

        deck_data = deck_info_response.get("deck", {})
        tags_data = deck_info_response.get("tags", [])

        logger.debug(f"Deck data keys: {list(deck_data.keys()) if deck_data else 'None'}")
        logger.debug(f"Tags data length: {len(tags_data)}")

        # Basic counts
        total_flashcards = deck_data.get("card_count", 0)
        tags_count = len(tags_data)

        logger.debug(f"Total flashcards found: {total_flashcards}")
        logger.debug(f"Tags count: {tags_count}")

        # Calculate flashcards by difficulty from available data
        difficulty_distribution = deck_data.get("difficulty_distribution", {})
        flashcards_by_difficulty = {
            "1": difficulty_distribution.get("1", 0),
            "2": difficulty_distribution.get("2", 0),
            "3": difficulty_distribution.get("3", 0),
            "4": difficulty_distribution.get("4", 0),
            "5": difficulty_distribution.get("5", 0),
        }

        # Calculate flashcards by tag
        flashcards_by_tag = []
        for tag in tags_data:
            flashcards_by_tag.append({
                "tagId": tag.get("id"),
                "tagName": tag.get("name"),
                "count": tag.get("flashcard_count", 0),
                "percentage": round((tag.get("flashcard_count", 0) / total_flashcards * 100), 1) if total_flashcards > 0 else 0
            })

        # Calculate organization metrics
        tagged_flashcards = sum(tag.get("flashcard_count", 0) for tag in tags_data)
        untagged_flashcards = max(0, total_flashcards - tagged_flashcards)
        organization_percentage = round((tagged_flashcards / total_flashcards * 100), 1) if total_flashcards > 0 else 0

        # Determine organization status
        if total_flashcards == 0:
            organization_status = "empty"
        elif untagged_flashcards == 0:
            organization_status = "organized"
        else:
            organization_status = "needs_organization"

        # Calculate average difficulty
        total_difficulty_weighted = sum(
            int(level) * count for level, count in flashcards_by_difficulty.items()
        )
        average_difficulty = round(total_difficulty_weighted / total_flashcards, 2) if total_flashcards > 0 else 0

        # Calculate average tags per flashcard
        total_tag_assignments = sum(tag.get("flashcard_count", 0) for tag in tags_data)
        average_tags_per_flashcard = round(total_tag_assignments / total_flashcards, 2) if total_flashcards > 0 else 0

        return {
            "totalFlashcards": total_flashcards,
            "untaggedFlashcards": untagged_flashcards,
            "taggedFlashcards": tagged_flashcards,
            "flashcardsByDifficulty": flashcards_by_difficulty,
            "flashcardsByTag": flashcards_by_tag,
            "organizationMetrics": {
                "organizationPercentage": organization_percentage,
                "organizationStatus": organization_status,
                "tagsCount": tags_count,
                "averageTagsPerFlashcard": average_tags_per_flashcard
            },
            "studyMetrics": {
                "totalReviews": 0,  # Not available in basic deck info
                "correctReviews": 0,
                "incorrectReviews": 0,
                "accuracyRate": 0,
                "averageDifficulty": average_difficulty,
                "lastStudied": None,
                "currentStreak": 0
            }
        }

    except Exception as e:
        logger.error(f"Error calculating basic stats: {str(e)}")
        return {}

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
Usage examples for the assign_tags_to_flashcards tool:

1. Assign "Grammar" tag to all flashcards in "English" deck:
   assign_tags_to_flashcards(
       deck_name="English",
       tag_name="Grammar",
       filter_criteria="all"
   )

2. Assign "Vocabulary" tag to flashcards without tags in "Spanish" deck:
   assign_tags_to_flashcards(
       deck_name="Spanish",
       tag_name="Vocabulary",
       filter_criteria="untagged"
   )

3. Assign "Advanced" tag to difficult flashcards (level 3) in "French" deck:
   assign_tags_to_flashcards(
       deck_name="French",
       tag_name="Advanced",
       filter_criteria="by_difficulty",
       difficulty_level=3
   )

4. Assign "Greetings" tag to flashcards containing "hello" in "English" deck:
   assign_tags_to_flashcards(
       deck_name="English",
       tag_name="Greetings",
       filter_criteria="by_content",
       content_filter="hello"
   )

5. Assign tag to first 10 flashcards in "German" deck:
   assign_tags_to_flashcards(
       deck_name="German",
       tag_name="Basics",
       max_flashcards=10
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
                tags_response = await tag_service.get_deck_tags(deck_id)
                tags = tags_response.get("data", [])

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
                "_instructions": get_instructions_for_add_flashcard(deck_name),
            }

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
        Create a new flashcard deck with interactive cover image choice.

        This tool creates a new deck with a custom name and optional description.
        The deck will be created as private by default.

        ✨ INTERACTIVE ELICITATION: If you don't specify generate_cover, the tool will
        ask you interactively whether you want to generate an AI cover image.

        Features:
        • Creates a new deck with custom name and description
        • Interactive questioning for cover image generation
        • Validates deck name format and length
        • Returns complete deck information after creation

        Usage:
        • Specify generate_cover=true/false for direct control
        • Omit generate_cover to be asked interactively (recommended)

        Perfect for organizing flashcards by topic, subject, or learning goals.
        """,
        tags={"decks", "creation", "organization"},
    )
    async def create_deck(
        ctx: Context,
        name: str = Field(..., description="Name of the new deck (3-100 characters)"),
        generate_cover: bool | None = Field(None, description="Whether to generate an AI cover image (if not specified, user will be asked)"),
        description: str = Field("", description="Optional description of the deck"),
    ) -> dict:
        """Create a new flashcard deck."""
        try:
            # Validate inputs
            if not name or not name.strip():
                return {
                    "error": "Invalid deck name",
                    "message": "Deck name cannot be empty",
                }

            name_stripped = name.strip()
            if len(name_stripped) < 3 or len(name_stripped) > 100:
                return {
                    "error": "Invalid deck name length",
                    "message": "Deck name must be between 3 and 100 characters",
                }

            # Check for invalid characters (similar to other deck validations)
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            if any(char in name_stripped for char in invalid_chars):
                return {
                    "error": "Invalid deck name",
                    "message": 'Deck name cannot contain invalid characters: < > : " | ? *',
                }

            # Handle elicitation for generate_cover if not specified
            if generate_cover is None:
                try:
                    # Ask user if they want to generate a cover image
                    result = await ctx.elicit(
                        message="¿Quieres generar una imagen de portada con IA para este mazo? (Esto puede generar costos adicionales)",
                        response_type=bool
                    )
                    generate_cover = result
                    logger.info(f"User chose to generate cover: {generate_cover}")
                except Exception as e:
                    logger.warning(f"Elicitation failed, defaulting to no cover: {str(e)}")
                    generate_cover = False

            # Prepare deck data for API
            deck_data = {
                "name": name_stripped,
                "generateCover": generate_cover,
            }

            if description and description.strip():
                deck_data["description"] = description.strip()

            # Create the deck using the service
            deck_service = DeckService.get_instance()
            api_response = await deck_service.create_deck(deck_data)

            # Format the response (API returns deck object directly, like add_flashcard)
            response_data = format_deck_response(api_response)

            # Create descriptive message based on cover generation choice
            cover_message = "with AI-generated cover" if generate_cover else "without cover image"
            full_message = f"Deck '{name_stripped}' created successfully {cover_message}"

            return {
                "success": True,
                "deck": response_data,
                "message": full_message,
                "cover_generated": generate_cover,
                "_instructions": get_instructions_for_create_deck(name_stripped),
            }

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

    # Tool 7: Assign Tags to Flashcards (by specific IDs)
    @mcp_server.tool(
        name="assign_tags_to_flashcards",
        description="""
        Assign tags to specific flashcards by their unique IDs for precise organization.

        This tool provides exact control over flashcard categorization by:
        • Requiring specific flashcard IDs (get them from list_flashcards first)
        • Creating the tag automatically if it doesn't exist
        • Processing up to 50 flashcards in a single operation
        • Providing detailed success/failure reports

        Common use cases:
        • Apply "Grammar" tags to grammar-focused cards
        • Mark "Vocabulary" cards for word learning
        • Categorize content by difficulty or topic
        • Organize flashcards for targeted study sessions

        Note: Use list_flashcards first to obtain the flashcard IDs you want to tag.
        """,
        tags={"flashcards", "tags", "organization", "categorization"},
    )
    async def assign_tags_to_flashcards(
        deck_name: str = Field(..., description="Name of the deck containing the flashcards"),
        tag_name: str = Field(..., description="Name of the tag to assign (will be created if it doesn't exist)"),
        flashcard_ids: list[int] = Field(
            ..., 
            description="List of flashcard IDs to tag (get these from list_flashcards). Maximum 50 IDs.",
            min_length=1,
            max_length=50
        ),
    ) -> dict:
        """Assign a tag to specific flashcards by their IDs."""
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

            if not flashcard_ids or len(flashcard_ids) > 50:
                return {
                    "error": "Invalid flashcard_ids",
                    "message": "You must provide between 1 and 50 flashcard IDs",
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
                available_decks = [d.get("name") for d in all_decks]
                return {
                    "error": "Deck not found",
                    "message": f"Deck '{deck_name}' not found",
                    "available_decks": available_decks,
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

    # Debug helper - only for development
    async def debug_deck_stats_calculation(deck_name: str) -> dict:
        """Debug helper to test stats calculation without backend calls."""
        try:
            # Get deck ID
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
                return {"error": "Deck not found", "available_decks": [d.get("name") for d in all_decks if d.get("name")]}

            # Test the calculation directly
            deck_info_response = await deck_service.get_deck_info(deck_id)
            stats_data = await _calculate_basic_stats_from_deck_info(deck_info_response, deck_basic_info)

            return {
                "deck_info_response": deck_info_response,
                "calculated_stats": stats_data,
                "debug_info": {
                    "deck_id": deck_id,
                    "deck_name": deck_name,
                    "deck_basic_info": deck_basic_info
                }
            }

        except Exception as e:
            return {"error": str(e)}

    # Test helper with mock data
    def test_stats_calculation_with_mock_data():
        """Test the stats calculation with mock data similar to Japanese Learning."""
        # Mock data similar to what Japanese Learning should return
        mock_deck_info = {
            "deck": {
                "id": 6,
                "name": "Japanese Learning",
                "card_count": 11,
                "difficulty_distribution": {"1": 8, "2": 3}
            },
            "tags": [
                {"id": 1, "name": "Saludos", "flashcard_count": 4},
                {"id": 2, "name": "Expresiones de Cortesía", "flashcard_count": 5},
                {"id": 3, "name": "Frases de Comida", "flashcard_count": 2}
            ]
        }

        mock_deck_basic = {"id": 6, "name": "Japanese Learning", "card_count": 11}

        # Test the calculation
        import asyncio

        async def run_test():
            result = await _calculate_basic_stats_from_deck_info(mock_deck_info, mock_deck_basic)
            print("🧪 Test Results:")
            print(f"  Total flashcards: {result.get('totalFlashcards')}")
            print(f"  Organization status: {result.get('organizationMetrics', {}).get('organizationStatus')}")
            print(f"  Organization percentage: {result.get('organizationMetrics', {}).get('organizationPercentage')}%")
            print(f"  Tags count: {result.get('organizationMetrics', {}).get('tagsCount')}")
            return result

        return asyncio.run(run_test())

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
