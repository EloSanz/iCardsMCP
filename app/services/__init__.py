"""Services for iCards MCP server."""

# Import all services for easy access
from .deck_service import DeckService
from .flashcard_service import FlashcardService
from .tag_service import TagService

__all__ = ["FlashcardService", "DeckService", "TagService"]
