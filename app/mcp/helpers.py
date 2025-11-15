"""
Helper functions for iCards MCP server.

This module contains utility functions that support MCP tool operations,
including statistics calculations, data processing, and formatting helpers.

These functions were moved from tools.py to keep that file clean and focused
on tool definitions rather than implementation details.

Functions:
    - _generate_stats_insights: Creates human-readable insights from statistics
    - _calculate_basic_stats_from_mcp_data: Calculates stats using MCP endpoint data
    - _calculate_basic_stats_from_deck_info: Calculates stats using deck info endpoint
    - debug_deck_stats_calculation: Debug helper for stats calculations
    - test_stats_calculation_with_mock_data: Test helper with mock data
"""

import logging
from typing import Dict, Any, List

from app.services import DeckService, FlashcardService, TagService

logger = logging.getLogger(__name__)


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