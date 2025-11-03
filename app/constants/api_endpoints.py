"""
API Endpoints Constants
Centralized constants for all iCards API endpoints.

This module contains all API endpoint paths used across the application.
All endpoints are defined as constants to ensure consistency and easy maintenance.
"""

# ===== BASE API PATHS =====
API_BASE = "/api"

# ===== FLASHCARD ENDPOINTS =====
FLASHCARDS_BASE = f"{API_BASE}/flashcards"

# CRUD operations
FLASHCARDS_CREATE = FLASHCARDS_BASE
FLASHCARDS_LIST = FLASHCARDS_BASE
FLASHCARDS_GET = f"{FLASHCARDS_BASE}/{{flashcard_id}}"
FLASHCARDS_UPDATE = f"{FLASHCARDS_BASE}/{{flashcard_id}}"
FLASHCARDS_DELETE = f"{FLASHCARDS_BASE}/{{flashcard_id}}"

# Bulk operations
FLASHCARDS_BULK_CREATE = f"{FLASHCARDS_BASE}/bulk"

# Search and filtering
FLASHCARDS_SEARCH = f"{FLASHCARDS_BASE}/search"
FLASHCARDS_DUE = f"{FLASHCARDS_BASE}/due"
FLASHCARDS_DUE_BY_DECK = f"{FLASHCARDS_BASE}/due/{{deck_id}}"

# Deck-specific flashcard operations
FLASHCARDS_BY_DECK = f"{FLASHCARDS_BASE}/deck/{{deck_id}}"
FLASHCARDS_BY_DECK_SEARCH = f"{FLASHCARDS_BASE}/deck/{{deck_id}}/search"

# Tag operations on flashcards
FLASHCARDS_TAGS = f"{FLASHCARDS_BASE}/{{flashcard_id}}/tags"

# Review operations
FLASHCARDS_REVIEW = f"{FLASHCARDS_BASE}/{{flashcard_id}}/review"

# AI generation
FLASHCARDS_AI_GENERATE = f"{FLASHCARDS_BASE}/ai-generate"


# ===== DECK ENDPOINTS =====
DECKS_BASE = f"{API_BASE}/decks"

# CRUD operations
DECKS_CREATE = DECKS_BASE
DECKS_LIST = DECKS_BASE
DECKS_LIST_MCP = f"{DECKS_BASE}/mcp"  # Optimized endpoint without coverUrl for MCP
DECKS_GET = f"{DECKS_BASE}/{{deck_id}}"
DECKS_UPDATE = f"{DECKS_BASE}/{{deck_id}}"
DECKS_DELETE = f"{DECKS_BASE}/{{deck_id}}"

# MCP-specific endpoints (lightweight, without cover images)

# Search operations
DECKS_SEARCH = f"{DECKS_BASE}/search"


# AI and generation operations
DECKS_GENERATE = f"{DECKS_BASE}/generate"
DECKS_GENERATE_WITH_AI = f"{DECKS_BASE}/generate-with-ai"
DECKS_SUGGEST_TOPICS = f"{DECKS_BASE}/suggest-topics"

# Clone operations
DECKS_CLONE = f"{DECKS_BASE}/{{deck_id}}/clone"

# Tag operations on decks
DECKS_TAGS = f"{DECKS_BASE}/{{deck_id}}/tags"

# ===== TAG ENDPOINTS =====
TAGS_BASE = f"{API_BASE}/tags"

# CRUD operations
TAGS_CREATE = TAGS_BASE
TAGS_LIST = TAGS_BASE
TAGS_GET = f"{TAGS_BASE}/{{tag_id}}"
TAGS_UPDATE = f"{TAGS_BASE}/{{tag_id}}"
TAGS_DELETE = f"{TAGS_BASE}/{{tag_id}}"

# Search operations
TAGS_SEARCH = f"{TAGS_BASE}/search"

# Bulk operations
TAGS_BULK = f"{TAGS_BASE}/bulk"


# ===== AUTHENTICATION ENDPOINTS =====
AUTH_BASE = f"{API_BASE}/auth"

AUTH_REGISTER = f"{AUTH_BASE}/register"
AUTH_LOGIN = f"{AUTH_BASE}/login"

# ===== SYNC ENDPOINTS =====
SYNC_BASE = f"{API_BASE}/sync"

# Anki sync
SYNC_ANKI_STATUS = f"{SYNC_BASE}/anki/status"
SYNC_ANKI_SYNC = f"{SYNC_BASE}/anki/sync"
SYNC_ANKI_SYNC_DECK = f"{SYNC_BASE}/anki/sync/{{deck_id}}"
SYNC_ANKI_IMPORT = f"{SYNC_BASE}/anki/import"
SYNC_ANKI_EXPORT = f"{SYNC_BASE}/anki/export"


# ===== LOGGING ENDPOINTS =====
LOGGING_BASE = f"{API_BASE}/logging"

LOGGING_RESET_STATS = f"{LOGGING_BASE}/reset-stats"
LOGGING_HEALTH = f"{LOGGING_BASE}/health"

# ===== HEALTH CHECK ENDPOINTS =====
HEALTH = f"{API_BASE}/health"
HEALTH_DETAILED = f"{API_BASE}/health/detailed"

# ===== UTILITY ENDPOINTS =====
VERSION = f"{API_BASE}/version"

# ===== ENDPOINT COLLECTIONS =====
# Collections for easy iteration and validation

FLASHCARD_ENDPOINTS = {
    "create": FLASHCARDS_CREATE,
    "list": FLASHCARDS_LIST,
    "get": FLASHCARDS_GET,
    "update": FLASHCARDS_UPDATE,
    "delete": FLASHCARDS_DELETE,
    "bulk_create": FLASHCARDS_BULK_CREATE,
    "search": FLASHCARDS_SEARCH,
    "due": FLASHCARDS_DUE,
    "due_by_deck": FLASHCARDS_DUE_BY_DECK,
    "by_deck": FLASHCARDS_BY_DECK,
    "by_deck_search": FLASHCARDS_BY_DECK_SEARCH,
    "tags": FLASHCARDS_TAGS,
    "review": FLASHCARDS_REVIEW,
    "ai_generate": FLASHCARDS_AI_GENERATE,
}

DECK_ENDPOINTS = {
    "create": DECKS_CREATE,
    "list": DECKS_LIST,
    "list_mcp": DECKS_LIST_MCP,  # Lightweight endpoint without cover images
    "get": DECKS_GET,
    "update": DECKS_UPDATE,
    "delete": DECKS_DELETE,
    "search": DECKS_SEARCH,
    "generate": DECKS_GENERATE,
    "generate_with_ai": DECKS_GENERATE_WITH_AI,
    "suggest_topics": DECKS_SUGGEST_TOPICS,
    "clone": DECKS_CLONE,
    "tags": DECKS_TAGS,
}

TAG_ENDPOINTS = {
    "create": TAGS_CREATE,
    "list": TAGS_LIST,
    "get": TAGS_GET,
    "update": TAGS_UPDATE,
    "delete": TAGS_DELETE,
    "search": TAGS_SEARCH,
    "bulk": TAGS_BULK,
}


# ===== HELPER FUNCTIONS =====


def format_endpoint(endpoint: str, **kwargs) -> str:
    """
    Format an endpoint template with provided parameters.

    Args:
        endpoint: Endpoint template with placeholders (e.g., "/api/flashcards/{flashcard_id}")
        **kwargs: Parameters to substitute in the template

    Returns:
        Formatted endpoint string

    Example:
        format_endpoint(FLASHCARDS_GET, flashcard_id=123) -> "/api/flashcards/123"
    """
    return endpoint.format(**kwargs)


def get_all_endpoints() -> dict:
    """
    Get all endpoint collections organized by category.

    Returns:
        Dictionary with all endpoint collections
    """
    return {
        "flashcards": FLASHCARD_ENDPOINTS,
        "decks": DECK_ENDPOINTS,
        "tags": TAG_ENDPOINTS,
    }
