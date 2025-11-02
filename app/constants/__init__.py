"""
Constants package for iCards MCP server.

This package contains all application constants organized by domain.
"""

from .api_endpoints import *

__all__ = [
    # API Endpoints
    "FLASHCARDS_BASE",
    "FLASHCARDS_CREATE",
    "FLASHCARDS_LIST",
    "FLASHCARDS_GET",
    "FLASHCARDS_UPDATE",
    "FLASHCARDS_DELETE",
    "FLASHCARDS_BULK_CREATE",
    "FLASHCARDS_SEARCH",
    "FLASHCARDS_DUE",
    "FLASHCARDS_DUE_BY_DECK",
    "FLASHCARDS_BY_DECK",
    "FLASHCARDS_BY_DECK_SEARCH",
    "FLASHCARDS_TAGS",
    "FLASHCARDS_REVIEW",
    "FLASHCARDS_AI_GENERATE",

    "DECKS_BASE",
    "DECKS_CREATE",
    "DECKS_LIST",
    "DECKS_GET",
    "DECKS_UPDATE",
    "DECKS_DELETE",
    "DECKS_SEARCH",
    "DECKS_GENERATE",
    "DECKS_GENERATE_WITH_AI",
    "DECKS_SUGGEST_TOPICS",
    "DECKS_CLONE",
    "DECKS_TAGS",

    "TAGS_BASE",
    "TAGS_CREATE",
    "TAGS_LIST",
    "TAGS_GET",
    "TAGS_UPDATE",
    "TAGS_DELETE",
    "TAGS_SEARCH",
    "TAGS_BULK",

    "AUTH_BASE",
    "AUTH_REGISTER",
    "AUTH_LOGIN",

    "SYNC_BASE",
    "SYNC_ANKI_STATUS",
    "SYNC_ANKI_SYNC",
    "SYNC_ANKI_SYNC_DECK",
    "SYNC_ANKI_IMPORT",
    "SYNC_ANKI_EXPORT",

    "LOGGING_BASE",
    "LOGGING_RESET_STATS",
    "LOGGING_HEALTH",

    "HEALTH",
    "HEALTH_DETAILED",
    "VERSION",

    "FLASHCARD_ENDPOINTS",
    "DECK_ENDPOINTS",
    "TAG_ENDPOINTS",

    "format_endpoint",
    "get_all_endpoints",
]
