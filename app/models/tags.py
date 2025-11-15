"""
Tag models for iCards API.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime

from .common import (
    APIResponse, TimestampedModel, IDModel, NamedModel, DescribedModel,
    ColorModel, BulkOperationResult
)


class Tag(IDModel, NamedModel, DescribedModel, ColorModel, TimestampedModel):
    """Tag model."""
    deckId: int = Field(..., gt=0, description="Parent deck ID")
    flashcardCount: int = Field(0, ge=0, description="Number of associated flashcards")
    isActive: bool = Field(True, description="Whether the tag is active")

    model_config = ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    """Tag creation request."""
    name: str = Field(..., min_length=1, max_length=100, description="Tag name")
    color: Optional[str] = Field("#6366f1", description="Tag color (hex)")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name."""
        if not v.strip():
            raise ValueError('Tag name cannot be empty or whitespace only')
        if len(v.strip()) > 100:
            raise ValueError('Tag name cannot exceed 100 characters')
        return v.strip()

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate color format."""
        if v and not v.startswith('#'):
            return f"#{v}"
        return v


class TagUpdate(BaseModel):
    """Tag update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="New tag name")
    color: Optional[str] = Field(None, description="New tag color")
    description: Optional[str] = Field(None, max_length=500, description="New description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name."""
        if v is not None and not v.strip():
            raise ValueError('Tag name cannot be empty or whitespace only')
        return v.strip() if v else v


class TagListResponse(APIResponse):
    """Response for tag listing endpoints."""
    data: List[Tag] = Field(..., description="List of tags")
    count: int = Field(..., ge=0, description="Total number of tags")


class TagSearchParams(BaseModel):
    """Parameters for tag search."""
    q: str = Field(..., min_length=1, max_length=100, description="Search query")
    deck_id: Optional[int] = Field(None, gt=0, description="Filter by deck ID")
    limit: int = Field(50, ge=1, le=100, description="Maximum results")
    sort_by: str = Field("name", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class TagBulkOperation(BaseModel):
    """Bulk tag operation request."""
    operation: str = Field(..., pattern="^(add|remove)$", description="Operation type")
    resource_type: str = Field(..., pattern="^(flashcard|deck)$", description="Resource type")
    resource_ids: List[int] = Field(..., min_length=1, max_length=100, description="Resource IDs")
    tag_ids: List[int] = Field(..., min_length=1, max_length=50, description="Tag IDs to operate on")

    @field_validator('resource_ids', 'tag_ids')
    @classmethod
    def validate_ids(cls, v):
        """Validate ID lists."""
        if not v:
            raise ValueError('ID list cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot operate on more than 100 resources at once')
        return v


class TagBulkOperationResult(BulkOperationResult):
    """Result of bulk tag operations."""
    operation: str = Field(..., description="Operation performed")
    resource_type: str = Field(..., description="Type of resources operated on")
    successful_operations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Successful operations with details"
    )


class FlashcardTagOperation(BaseModel):
    """Tag operation on flashcards."""
    flashcard_id: int = Field(..., gt=0, description="Flashcard ID")
    tag_ids: List[int] = Field(..., min_length=1, description="Tag IDs to assign/remove")

    @field_validator('tag_ids')
    @classmethod
    def validate_tag_ids(cls, v):
        """Validate tag IDs."""
        if not v:
            raise ValueError('At least one tag ID must be provided')
        return v


class DeckTagOperation(BaseModel):
    """Tag operation on decks."""
    deck_id: int = Field(..., gt=0, description="Deck ID")
    tag_ids: List[int] = Field(..., min_length=1, description="Tag IDs to assign/remove")

    @field_validator('tag_ids')
    @classmethod
    def validate_tag_ids(cls, v):
        """Validate tag IDs."""
        if not v:
            raise ValueError('At least one tag ID must be provided')
        return v


class TagFlashcardAssociation(BaseModel):
    """Association between tag and flashcard."""
    tag_id: int = Field(..., gt=0, description="Tag ID")
    flashcard_id: int = Field(..., gt=0, description="Flashcard ID")
    created_at: datetime = Field(..., description="Association creation timestamp")


class TagStats(BaseModel):
    """Tag usage statistics."""
    total_tags: int = Field(..., ge=0, description="Total number of tags")
    active_tags: int = Field(..., ge=0, description="Number of active tags")
    average_flashcards_per_tag: float = Field(..., ge=0, description="Average flashcards per tag")
    most_used_tags: List[Dict[str, Any]] = Field(..., description="Most frequently used tags")
    unused_tags: List[Tag] = Field(..., description="Tags with no associated flashcards")
