"""Utility functions for iCards MCP server.

This module contains helper functions for managing flashcards and decks.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

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
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
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


def format_flashcard_response(flashcard_data: Dict[str, Any]) -> Dict[str, Any]:
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
        "tags": flashcard_data.get("tags", [])
    }


def format_deck_response(deck_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format deck data for API response."""
    return {
        "id": deck_data.get("id"),
        "name": deck_data.get("name", "").strip(),
        "description": deck_data.get("description", ""),
        "card_count": deck_data.get("card_count", 0),
        "created_at": deck_data.get("created_at"),
        "updated_at": deck_data.get("updated_at"),
        "is_active": deck_data.get("is_active", True),
        "tags": deck_data.get("tags", []),
        "difficulty_distribution": deck_data.get("difficulty_distribution", {}),
        "study_streak": deck_data.get("study_streak", 0),
        "last_studied": deck_data.get("last_studied")
    }


def calculate_study_progress(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate study progress metrics from a list of cards."""
    if not cards:
        return {
            "total_cards": 0,
            "studied_cards": 0,
            "mastered_cards": 0,
            "progress_percentage": 0,
            "average_difficulty": 0,
            "study_streak": 0
        }

    total_cards = len(cards)
    studied_cards = len([c for c in cards if c.get("review_count", 0) > 0])
    mastered_cards = len([c for c in cards if c.get("correct_count", 0) >= 5])  # Cards with 5+ correct answers

    # Calculate average difficulty (1-5 scale)
    difficulties = [c.get("difficulty_level", 1) for c in cards if c.get("difficulty_level")]
    avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0

    return {
        "total_cards": total_cards,
        "studied_cards": studied_cards,
        "mastered_cards": mastered_cards,
        "progress_percentage": round((studied_cards / total_cards) * 100, 1) if total_cards > 0 else 0,
        "average_difficulty": round(avg_difficulty, 2),
        "study_streak": 0  # Would need session tracking for this
    }


def generate_study_recommendations(deck_progress: Dict[str, Any]) -> List[str]:
    """Generate study recommendations based on deck progress."""
    recommendations = []

    progress_pct = deck_progress.get("progress_percentage", 0)
    avg_difficulty = deck_progress.get("average_difficulty", 0)
    mastered_cards = deck_progress.get("mastered_cards", 0)
    total_cards = deck_progress.get("total_cards", 0)

    if progress_pct < 25:
        recommendations.append("Focus on learning new cards - you're just starting!")
    elif progress_pct < 50:
        recommendations.append("Good progress! Continue reviewing new cards regularly.")
    elif progress_pct < 75:
        recommendations.append("Keep it up! You're making great progress.")
    else:
        recommendations.append("Excellent! Most cards are studied. Focus on difficult ones.")

    if avg_difficulty > 3.5:
        recommendations.append("Your deck seems challenging. Consider breaking complex cards into simpler ones.")
    elif avg_difficulty < 2.5:
        recommendations.append("Your deck seems easy. Consider adding more challenging content.")

    if mastered_cards > 0:
        master_pct = (mastered_cards / total_cards) * 100 if total_cards > 0 else 0
        recommendations.append(".1f")

    if total_cards < 10:
        recommendations.append("Add more cards to your deck for better learning results.")

    return recommendations


def parse_study_session_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and format study session data."""
    return {
        "session_id": session_data.get("session_id"),
        "deck_name": session_data.get("deck_name"),
        "started_at": session_data.get("started_at"),
        "completed_at": session_data.get("completed_at"),
        "cards_studied": session_data.get("cards_studied", 0),
        "correct_answers": session_data.get("correct_answers", 0),
        "incorrect_answers": session_data.get("incorrect_answers", 0),
        "accuracy_percentage": session_data.get("accuracy_percentage", 0),
        "duration_minutes": session_data.get("duration_minutes", 0),
        "new_cards_learned": session_data.get("new_cards_learned", 0),
        "cards_reviewed": session_data.get("cards_reviewed", 0),
        "session_type": session_data.get("session_type", "mixed"),
        "difficulty_focus": session_data.get("difficulty_focus")
    }


def create_flashcard_template(deck_type: str = "general") -> Dict[str, Any]:
    """Create a flashcard template based on deck type."""
    templates = {
        "vocabulary": {
            "front": "Word/Phrase in target language",
            "back": "Translation/Meaning + pronunciation guide + example sentence",
            "tags": ["vocabulary", deck_type],
            "difficulty_level": 2
        },
        "grammar": {
            "front": "Grammar rule or structure",
            "back": "Explanation + examples + common mistakes to avoid",
            "tags": ["grammar", deck_type],
            "difficulty_level": 3
        },
        "kanji": {
            "front": "Kanji character",
            "back": "Reading + meaning + stroke order + example words",
            "tags": ["kanji", "japanese"],
            "difficulty_level": 4
        },
        "phrases": {
            "front": "Phrase in context",
            "back": "Translation + cultural notes + when to use it",
            "tags": ["phrases", deck_type],
            "difficulty_level": 2
        },
        "general": {
            "front": "Question/Prompt",
            "back": "Answer/Explanation",
            "tags": ["general"],
            "difficulty_level": 1
        }
    }

    return templates.get(deck_type, templates["general"])
