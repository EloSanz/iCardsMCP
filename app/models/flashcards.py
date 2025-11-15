"""
Flashcard models for iCards API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from .common import (
    APIResponse, TimestampedModel, IDModel, DifficultyLevel,
    BulkOperationResult, PaginationParams
)


class TagReference(BaseModel):
    """Tag reference in flashcard."""
    id: int = Field(..., gt=0, description="Tag ID")
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")


class Flashcard(IDModel, TimestampedModel):
    """Flashcard model."""
    front: str = Field(..., min_length=1, max_length=5000, description="Front content of the flashcard")
    back: str = Field(..., min_length=1, max_length=5000, description="Back content of the flashcard")
    difficulty: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Difficulty level")
    deckId: int = Field(..., gt=0, description="Parent deck ID")
    tagId: Optional[int] = Field(None, gt=0, description="Associated tag ID (deprecated)")
    tag: Optional[TagReference] = Field(None, description="Associated tag details")
    lastReviewed: Optional[datetime] = Field(None, description="Last review timestamp")
    nextReview: Optional[datetime] = Field(None, description="Next scheduled review")
    reviewCount: int = Field(0, ge=0, description="Number of times reviewed")
    isActive: bool = Field(True, description="Whether the flashcard is active")

    model_config = ConfigDict(from_attributes=True)


class FlashcardCreate(BaseModel):
    """Flashcard creation request."""
    front: str = Field(..., min_length=1, max_length=5000, description="Front content")
    back: str = Field(..., min_length=1, max_length=5000, description="Back content")
    deckId: int = Field(..., gt=0, description="Parent deck ID")
    difficulty: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Difficulty level")

    @field_validator('front', 'back')
    @classmethod
    def validate_content(cls, v):
        """Validate flashcard content."""
        if not v.strip():
            raise ValueError('Flashcard content cannot be empty or whitespace only')
        return v.strip()


class FlashcardUpdate(BaseModel):
    """Flashcard update request."""
    front: Optional[str] = Field(None, min_length=1, max_length=5000, description="New front content")
    back: Optional[str] = Field(None, min_length=1, max_length=5000, description="New back content")
    difficulty: Optional[DifficultyLevel] = Field(None, description="New difficulty level")

    @field_validator('front', 'back')
    @classmethod
    def validate_content(cls, v):
        """Validate flashcard content."""
        if v is not None and not v.strip():
            raise ValueError('Flashcard content cannot be empty or whitespace only')
        return v.strip() if v else v


class FlashcardReview(BaseModel):
    """Flashcard review request."""
    difficulty: DifficultyLevel = Field(..., description="Difficulty level selected during review")


class FlashcardBulkCreate(BaseModel):
    """Bulk flashcard creation request."""
    deck_name: str = Field(..., min_length=1, max_length=255, description="Target deck name")
    flashcards: List[FlashcardCreate] = Field(..., min_length=1, max_length=100, description="List of flashcards to create")

    @field_validator('flashcards')
    @classmethod
    def validate_flashcards(cls, v):
        """Validate flashcard list."""
        if len(v) > 100:
            raise ValueError('Cannot create more than 100 flashcards at once')
        return v


class FlashcardListResponse(APIResponse):
    """Response for flashcard listing endpoints."""
    data: List[Flashcard] = Field(..., description="List of flashcards")
    count: int = Field(..., ge=0, description="Total number of flashcards")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination information")


class FlashcardSearchParams(PaginationParams):
    """Parameters for flashcard search."""
    q: str = Field(..., min_length=1, max_length=100, description="Search query")
    deck_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Filter by deck name")
    tags: Optional[List[str]] = Field(None, description="Filter by tag names")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    reviewed_after: Optional[datetime] = Field(None, description="Filter by last review date")
    reviewed_before: Optional[datetime] = Field(None, description="Filter by review date range")


class FlashcardFilterParams(BaseModel):
    """Parameters for flashcard filtering."""
    deck_id: Optional[int] = Field(None, gt=0, description="Filter by deck ID")
    deck_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Filter by deck name")
    tags: Optional[List[str]] = Field(None, description="Filter by tag names")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    has_tags: Optional[bool] = Field(None, description="Filter by tagged/untagged status")
    reviewed_after: Optional[datetime] = Field(None, description="Filter by last review date")
    reviewed_before: Optional[datetime] = Field(None, description="Filter by review date range")
    limit: int = Field(50, ge=1, le=1000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort_by: str = Field("createdAt", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    all: bool = Field(False, description="Get all results without pagination")


class FlashcardAIGenerateRequest(BaseModel):
    """AI flashcard generation request."""
    deckId: int = Field(..., gt=0, description="Target deck ID")
    topic: str = Field(..., min_length=1, max_length=200, description="Topic for generation")
    count: int = Field(5, ge=1, le=50, description="Number of flashcards to generate")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Target difficulty level")
    language: str = Field("english", min_length=2, max_length=50, description="Language for content")


class FlashcardBulkOperationResult(BulkOperationResult):
    """Result of bulk flashcard operations."""
    created_flashcards: List[Flashcard] = Field(default_factory=list, description="Successfully created flashcards")
    failed_flashcards: List[Dict[str, Any]] = Field(default_factory=list, description="Failed flashcard creations with error details")


class FlashcardStats(BaseModel):
    """Flashcard statistics."""
    totalCount: int = Field(..., ge=0, description="Total number of flashcards")
    activeCount: int = Field(..., ge=0, description="Number of active flashcards")
    reviewedCount: int = Field(..., ge=0, description="Number of reviewed flashcards")
    dueForReview: int = Field(..., ge=0, description="Number of flashcards due for review")
    newCount: int = Field(..., ge=0, description="Number of new flashcards")
    masteredCount: int = Field(..., ge=0, description="Number of mastered flashcards")
    averageDifficulty: float = Field(..., ge=1, le=5, description="Average difficulty")
    difficultyDistribution: Dict[str, int] = Field(..., description="Difficulty distribution")


class FlashcardDueResponse(APIResponse):
    """Response for due flashcards endpoint."""
    data: List[Flashcard] = Field(..., description="Due flashcards")
    count: int = Field(..., ge=0, description="Number of due flashcards")
    nextReviewIn: Optional[int] = Field(None, ge=0, description="Minutes until next review")
