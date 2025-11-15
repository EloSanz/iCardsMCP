"""
Typed models for iCards API.

This module provides Pydantic models for all iCards API entities and operations.
Models are organized by domain (auth, decks, flashcards, tags) and include
validation, serialization, and type safety.
"""

from .auth import *
from .decks import *
from .flashcards import *
from .tags import *
from .common import *
from .mcp_tools import *

__all__ = [
    # Auth models
    "User",
    "UserCreate",
    "UserLogin",
    "AuthResponse",
    "TokenResponse",

    # Deck models
    "Deck",
    "DeckCreate",
    "DeckCreateResponse",
    "DeckUpdate",
    "DeckStats",
    "DeckListResponse",
    "DeckMCPResponse",

    # Flashcard models
    "Flashcard",
    "FlashcardCreate",
    "FlashcardUpdate",
    "FlashcardReview",
    "FlashcardBulkCreate",
    "FlashcardListResponse",

    # Tag models
    "Tag",
    "TagCreate",
    "TagUpdate",
    "TagBulkOperation",

    # MCP Tool models
    "CreateDeckParams",
    "AddFlashcardParams",
    "BulkCreateFlashcardsParams",
    "GetDeckInfoParams",
    "GetDeckStatsParams",
    "ListDecksParams",
    "ListFlashcardsParams",
    "ListUntaggedFlashcardsParams",
    "CreateTagParams",
    "ListTagsParams",
    "UpdateTagParams",

    # Common models
    "APIResponse",
    "PaginationParams",
    "SearchParams",
    "DifficultyLevel",
    "Visibility",
]
