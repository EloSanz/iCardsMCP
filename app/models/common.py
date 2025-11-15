"""
Common models and types used across the iCards API.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class DifficultyLevel(int, Enum):
    """Flashcard difficulty levels."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4
    MASTER = 5


class Visibility(str, Enum):
    """Deck visibility options."""
    PRIVATE = "private"
    PUBLIC = "public"


class APIResponse(BaseModel):
    """Base API response model."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: Optional[datetime] = Field(None, description="Response timestamp")
    count: Optional[int] = Field(None, description="Number of items returned")


class PaginationParams(BaseModel):
    """Parameters for paginated requests."""
    page: int = Field(1, ge=1, description="Page number")
    pageSize: int = Field(50, ge=1, le=100, description="Items per page")
    offset: Optional[int] = Field(None, ge=0, description="Offset for pagination")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class SearchParams(BaseModel):
    """Parameters for search requests."""
    q: str = Field(..., min_length=1, max_length=100, description="Search query")
    limit: int = Field(50, ge=1, le=100, description="Maximum results")
    exact_match: bool = Field(False, description="Whether to require exact matches")


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""
    successful: int = Field(..., ge=0, description="Number of successful operations")
    failed: int = Field(..., ge=0, description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")


class TimestampedModel(BaseModel):
    """Base model with timestamp fields."""
    createdAt: Optional[datetime] = Field(None, description="Creation timestamp")
    updatedAt: Optional[datetime] = Field(None, description="Last update timestamp")


class IDModel(BaseModel):
    """Base model with ID field."""
    id: int = Field(..., gt=0, description="Unique identifier")


class NamedModel(BaseModel):
    """Base model with name field."""
    name: str = Field(..., min_length=1, max_length=255, description="Name")


class DescribedModel(BaseModel):
    """Base model with description field."""
    description: Optional[str] = Field(None, max_length=1000, description="Description")


class ColorModel(BaseModel):
    """Base model with color field."""
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")

    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        """Validate hex color format."""
        if v and not v.startswith('#'):
            return f"#{v}"
        return v
