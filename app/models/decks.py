"""
Deck models for iCards API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from .common import (
    APIResponse, TimestampedModel, IDModel, NamedModel, DescribedModel,
    Visibility, DifficultyLevel, BulkOperationResult
)


class DeckStats(BaseModel):
    """Deck statistics model."""
    flashcardsCount: int = Field(..., ge=0, description="Total number of flashcards")
    newFlashcardsCount: int = Field(..., ge=0, description="Number of new flashcards")
    reviewsCount: int = Field(..., ge=0, description="Number of flashcards due for review")
    studiedFlashcardsCount: Optional[int] = Field(None, ge=0, description="Number of studied flashcards")
    masteredFlashcardsCount: Optional[int] = Field(None, ge=0, description="Number of mastered flashcards")
    organizationPercentage: Optional[float] = Field(None, ge=0, le=100, description="Percentage of tagged flashcards")
    untaggedFlashcardsCount: Optional[int] = Field(None, ge=0, description="Number of untagged flashcards")
    totalTags: Optional[int] = Field(None, ge=0, description="Total number of tags in deck")
    averageDifficulty: Optional[float] = Field(None, ge=1, le=5, description="Average difficulty of flashcards")
    difficultyDistribution: Dict[str, int] = Field(default_factory=dict, description="Difficulty level distribution")
    studyStreak: Optional[int] = Field(None, ge=0, description="Current study streak in days")
    lastStudiedAt: Optional[datetime] = Field(None, description="Last study session timestamp")
    totalStudyTime: Optional[int] = Field(None, ge=0, description="Total study time in minutes")


class TagSummary(BaseModel):
    """Tag summary for deck listing."""
    id: int = Field(..., gt=0, description="Tag ID")
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    flashcardCount: int = Field(..., ge=0, description="Number of flashcards with this tag")


class Deck(IDModel, NamedModel, DescribedModel, TimestampedModel):
    """Deck model."""
    coverUrl: Optional[str] = Field(None, description="Cover image URL")
    visibility: Visibility = Field(Visibility.PRIVATE, description="Deck visibility")
    isActive: bool = Field(True, description="Whether the deck is active")
    clonesCount: int = Field(0, ge=0, description="Number of times this deck has been cloned")
    userId: int = Field(..., gt=0, description="Owner user ID")
    cardCount: Optional[int] = Field(None, ge=0, description="Total number of flashcards")
    tagCount: Optional[int] = Field(None, ge=0, description="Total number of tags")
    stats: Optional[DeckStats] = Field(None, description="Deck statistics")
    tags: Optional[List[TagSummary]] = Field(None, description="Deck tags summary")
    difficultyDistribution: Optional[Dict[str, int]] = Field(None, description="Difficulty distribution")
    studyStreak: Optional[int] = Field(None, ge=0, description="Study streak")
    lastStudied: Optional[datetime] = Field(None, description="Last studied timestamp")

    model_config = ConfigDict(from_attributes=True)


class DeckCreate(BaseModel):
    """Deck creation request."""
    name: str = Field(..., min_length=1, max_length=255, description="Deck name")
    description: Optional[str] = Field(None, max_length=1000, description="Deck description")
    generateCover: bool = Field(False, description="Whether to generate a cover image")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty or whitespace only')
        return v.strip()


class DeckCreateResponse(BaseModel):
    """Response from deck creation API."""
    success: bool = Field(..., description="Whether the creation was successful")
    message: str = Field(..., description="Response message")
    deck: Optional[Deck] = Field(None, description="Created deck data")
    createdAt: Optional[datetime] = Field(None, description="Creation timestamp")
    tags: Optional[List[Dict[str, Any]]] = Field(None, description="Initial tags")

    model_config = ConfigDict(from_attributes=True)


class DeckUpdate(BaseModel):
    """Deck update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New deck name")
    description: Optional[str] = Field(None, max_length=1000, description="New description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate deck name."""
        if v is not None and not v.strip():
            raise ValueError('Deck name cannot be empty or whitespace only')
        return v.strip() if v else v


class DeckVisibilityUpdate(BaseModel):
    """Deck visibility update request."""
    visibility: Visibility = Field(..., description="New visibility setting")


class DeckCloneRequest(BaseModel):
    """Deck cloning request."""
    name: str = Field(..., min_length=1, max_length=255, description="Name for the cloned deck")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate clone name."""
        if not v.strip():
            raise ValueError('Clone name cannot be empty or whitespace only')
        return v.strip()


class DeckGenerateRequest(BaseModel):
    """AI deck generation request."""
    mode: str = Field(..., pattern="^(free|guided)$", description="Generation mode")
    topic: str = Field(..., min_length=1, max_length=200, description="Topic for generation")
    flashcardCount: int = Field(10, ge=5, le=50, description="Number of flashcards to generate")
    generateCover: bool = Field(False, description="Whether to generate a cover image")


class DeckSuggestTopicsRequest(BaseModel):
    """Topic suggestion request."""
    count: int = Field(3, ge=1, le=10, description="Number of topics to suggest")


class DeckListResponse(APIResponse):
    """Response for deck listing endpoints."""
    data: List[Deck] = Field(..., description="List of decks")
    count: int = Field(..., ge=0, description="Total number of decks")
    totalCards: int = Field(..., ge=0, description="Total flashcards across all decks")


class DeckMCPResponse(APIResponse):
    """Response for MCP-optimized deck listing."""
    data: List[Deck] = Field(..., description="List of decks (without cover images)")
    count: int = Field(..., ge=0, description="Total number of decks")
    totalCards: int = Field(..., ge=0, description="Total flashcards across all decks")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class DeckStatsResponse(APIResponse):
    """Response for deck statistics endpoint."""
    data: DeckStats = Field(..., description="Detailed deck statistics")


class DeckFlashcardsCountResponse(APIResponse):
    """Response for deck flashcards count endpoint."""
    data: Dict[str, int] = Field(..., description="Flashcard count data")


class DeckUntaggedFlashcardsCountResponse(APIResponse):
    """Response for untagged flashcards count endpoint."""
    count: int = Field(..., ge=0, description="Number of untagged flashcards")


class DeckFlashcardsByTagResponse(APIResponse):
    """Response for flashcards grouped by tag."""
    data: Dict[str, List[Dict[str, Any]]] = Field(..., description="Flashcards grouped by tag")


class TopicSuggestion(BaseModel):
    """Topic suggestion model."""
    topic: str = Field(..., min_length=1, description="Suggested topic")
    description: str = Field(..., min_length=1, description="Topic description")
    estimatedFlashcards: int = Field(..., ge=1, description="Estimated number of flashcards")


class DeckSuggestTopicsResponse(APIResponse):
    """Response for topic suggestions."""
    data: List[TopicSuggestion] = Field(..., description="List of topic suggestions")
