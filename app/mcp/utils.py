"""Utility functions for iCards MCP server.

This module contains helper functions for managing flashcards and decks.
"""

import logging
from typing import Any

from app.config.config import Config

logger = logging.getLogger(__name__)

# Valid deck names and types for validation
VALID_DECK_TYPES = ["vocabulary", "grammar", "kanji", "phrases", "general", "custom"]


def get_api_base_url() -> str:
    """Get the API base URL from configuration."""
    return Config.get("API_BASE_URL")


def validate_deck_name(deck_name: str) -> bool:
    """Validate deck name format."""
    if not deck_name or not isinstance(deck_name, str):
        return False
    if len(deck_name.strip()) == 0:
        return False
    if len(deck_name) > 100:  # Reasonable limit
        return False
    # Check for invalid characters
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
    return not any(char in deck_name for char in invalid_chars)


def validate_flashcard_content(front: str, back: str) -> tuple[bool, str]:
    """Validate flashcard content."""
    if not front or not front.strip():
        return False, "Front content cannot be empty"

    if not back or not back.strip():
        return False, "Back content cannot be empty"

    if len(front) > 1000:
        return False, "Front content too long (max 1000 characters)"

    if len(back) > 2000:
        return False, "Back content too long (max 2000 characters)"

    return True, ""


def format_flashcard_response(flashcard_data: dict[str, Any]) -> dict[str, Any]:
    """Format flashcard data for API response."""
    return {
        "id": flashcard_data.get("id"),
        "front": flashcard_data.get("front", "").strip(),
        "back": flashcard_data.get("back", "").strip(),
        "deck_name": flashcard_data.get("deck_name", "default"),
        "created_at": flashcard_data.get("created_at"),
        "updated_at": flashcard_data.get("updated_at"),
        "review_count": flashcard_data.get("review_count", 0),
        "correct_count": flashcard_data.get("correct_count", 0),
        "difficulty_level": flashcard_data.get("difficulty_level", 1),
        "next_review_date": flashcard_data.get("next_review_date"),
        "tags": flashcard_data.get("tags", []),
    }


def format_deck_response(deck_data: dict[str, Any]) -> dict[str, Any]:
    """Format deck data for API response."""
    # Extract flashcards count from stats object if available
    stats = deck_data.get("stats", {})
    card_count = stats.get("flashcardsCount", deck_data.get("card_count", 0))
    
    return {
        "id": deck_data.get("id"),
        "name": deck_data.get("name", "").strip(),
        "description": deck_data.get("description", ""),
        "card_count": card_count,
        "created_at": deck_data.get("created_at"),
        "updated_at": deck_data.get("updated_at"),
        "is_active": deck_data.get("is_active", True),
        "tags": deck_data.get("tags", []),
        "difficulty_distribution": deck_data.get("difficulty_distribution", {}),
        "study_streak": deck_data.get("study_streak", 0),
        "last_studied": deck_data.get("last_studied"),
    }


def create_flashcard_template(deck_type: str = "general") -> dict[str, Any]:
    """Create a flashcard template based on deck type."""
    templates = {
        "vocabulary": {
            "front": "Word/Phrase in target language",
            "back": "Translation/Meaning + pronunciation guide + example sentence",
            "tags": ["vocabulary", deck_type],
            "difficulty_level": 2,
        },
        "grammar": {
            "front": "Grammar rule or structure",
            "back": "Explanation + examples + common mistakes to avoid",
            "tags": ["grammar", deck_type],
            "difficulty_level": 3,
        },
        "kanji": {
            "front": "Kanji character",
            "back": "Reading + meaning + stroke order + example words",
            "tags": ["kanji", "japanese"],
            "difficulty_level": 4,
        },
        "phrases": {
            "front": "Phrase in context",
            "back": "Translation + cultural notes + when to use it",
            "tags": ["phrases", deck_type],
            "difficulty_level": 2,
        },
        "general": {
            "front": "Question/Prompt",
            "back": "Answer/Explanation",
            "tags": ["general"],
            "difficulty_level": 1,
        },
    }

    return templates.get(deck_type, templates["general"])
