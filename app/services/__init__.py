"""Services for iCards MCP server."""

# Import all services for easy access
from .flashcard_service import FlashcardService
from .deck_service import DeckService
from .tag_service import TagService

__all__ = [
    "FlashcardService",
    "DeckService",
    "TagService"
]
