"""
MCP Tool validation models.

These models define the input validation for FastMCP tools,
ensuring type safety and proper validation for user inputs.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from .common import DifficultyLevel
from .flashcards import FlashcardCreate


class DeckNameParam(BaseModel):
    """Parameter for deck name input."""
    deck_name: str = Field(..., min_length=1, max_length=255, description="Name of the deck")

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()


class FlashcardIdParam(BaseModel):
    """Parameter for flashcard ID input."""
    flashcard_id: int = Field(..., gt=0, description="ID of the flashcard")


class TagIdParam(BaseModel):
    """Parameter for tag ID input."""
    tag_id: int = Field(..., gt=0, description="ID of the tag")


class DeckIdParam(BaseModel):
    """Parameter for deck ID input."""
    deck_id: int = Field(..., gt=0, description="ID of the deck")


# Tool: list_decks
class ListDecksParams(BaseModel):
    """Parameters for list_decks tool."""
    pass  # No parameters needed


# Tool: get_deck_info
class GetDeckInfoParams(DeckNameParam):
    """Parameters for get_deck_info tool."""
    pass  # Inherits deck_name validation


# Tool: get_deck_stats
class GetDeckStatsParams(DeckNameParam):
    """Parameters for get_deck_stats tool."""
    pass  # Inherits deck_name validation


# Tool: create_deck
class CreateDeckParams(BaseModel):
    """Parameters for create_deck tool."""
    name: str = Field(..., min_length=1, max_length=255, description="Name for the new deck")
    description: Optional[str] = Field("", max_length=1000, description="Description of the deck")
    generate_cover: Optional[bool] = Field(None, description="Whether to generate a cover image (None triggers elicitation)")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()

    @field_validator('generate_cover', mode='before')
    @classmethod
    def validate_generate_cover(cls, v):
        """Validate and convert generate_cover to boolean or None."""
        if isinstance(v, str):
            if v.lower() in ('true', 'yes', '1', 'si', 'sí'):
                return True
            elif v.lower() in ('false', 'no', '0'):
                return False
            else:
                # Invalid string, keep as None to trigger elicitation
                return None
        # Keep None as None to trigger elicitation
        return v


# Tool: add_flashcard
class AddFlashcardParams(BaseModel):
    """Parameters for add_flashcard tool."""
    front: str = Field(..., min_length=1, max_length=5000, description="Front content of the flashcard")
    back: str = Field(..., min_length=1, max_length=5000, description="Back content of the flashcard")
    deck_name: str = Field(..., min_length=1, max_length=255, description="Name of the target deck")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Difficulty level (1-5)")

    @field_validator('front', 'back')
    @classmethod
    def validate_content(cls, v):
        """Validate flashcard content."""
        if not v.strip():
            raise ValueError('Flashcard content cannot be empty')
        return v.strip()

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()


# Tool: bulk_create_flashcards
class BulkCreateFlashcardsParams(BaseModel):
    """Parameters for bulk_create_flashcards tool."""
    deck_name: str = Field(..., min_length=1, max_length=255, description="Name of the target deck")
    flashcards: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of flashcards to create"
    )

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()

    @field_validator('flashcards')
    @classmethod
    def validate_flashcards(cls, v):
        """Validate flashcard list."""
        if len(v) > 50:
            raise ValueError('Cannot create more than 50 flashcards at once')

        for i, card in enumerate(v):
            if not isinstance(card, dict):
                raise ValueError(f'Flashcard {i} must be a dictionary')
            if 'front' not in card or 'back' not in card:
                raise ValueError(f'Flashcard {i} must have front and back fields')
            if not card.get('front', '').strip():
                raise ValueError(f'Flashcard {i} front content cannot be empty')
            if not card.get('back', '').strip():
                raise ValueError(f'Flashcard {i} back content cannot be empty')

        return v


# Tool: list_flashcards
class ListFlashcardsParams(BaseModel):
    """Parameters for list_flashcards tool."""
    deck_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Filter by deck name")
    limit: int = Field(50, ge=1, le=1000, description="Maximum number of flashcards to return")
    include_tags: bool = Field(True, description="Whether to include tag information")

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if v is not None and not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip() if v else v


# Tool: update_flashcard
class UpdateFlashcardParams(BaseModel):
    """Parameters for update_flashcard tool."""
    flashcard_id: int = Field(..., gt=0, description="ID of the flashcard to update")
    front: Optional[str] = Field(None, min_length=1, max_length=5000, description="New front content")
    back: Optional[str] = Field(None, min_length=1, max_length=5000, description="New back content")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="New difficulty level")

    @field_validator('front', 'back')
    @classmethod
    def validate_content(cls, v):
        """Validate flashcard content."""
        if v is not None and not v.strip():
            raise ValueError('Flashcard content cannot be empty')
        return v.strip() if v else v


# Tool: delete_flashcard
class DeleteFlashcardParams(FlashcardIdParam):
    """Parameters for delete_flashcard tool."""
    pass  # Inherits flashcard_id validation


# Tool: list_untagged_flashcards
class ListUntaggedFlashcardsParams(BaseModel):
    """Parameters for list_untagged_flashcards tool."""
    deck_name: str = Field(..., min_length=1, max_length=255, description="Name of the deck")
    all_cards: bool = Field(False, description="Whether to return all untagged cards without pagination")

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()


# Tool: assign_tags_to_flashcards
class AssignTagsToFlashcardsParams(BaseModel):
    """Parameters for assign_tags_to_flashcards tool."""
    deck_name: str = Field(..., min_length=1, max_length=255, description="Name of the deck")
    tag_name: str = Field(..., min_length=1, max_length=100, description="Name of the tag to assign")
    filter_criteria: str | None = Field(
        None,
        description="Auto-select flashcards by criteria: 'untagged' (flashcards without tags), 'all' (all flashcards in deck), or None to specify manual IDs"
    )
    flashcard_ids: List[int] | None = Field(
        None,
        description="Manual list of flashcard IDs to tag (ignored if filter_criteria is specified). Maximum 100 IDs."
    )
    max_flashcards: int | None = Field(
        None,
        ge=1,
        le=100,
        description="Maximum number of flashcards to tag when using filter_criteria (default: all matching)"
    )

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()

    @field_validator('tag_name')
    @classmethod
    def validate_tag_name(cls, v):
        """Validate tag name."""
        if not v.strip():
            raise ValueError('Tag name cannot be empty')
        return v.strip()

    @field_validator('filter_criteria')
    @classmethod
    def validate_filter_criteria(cls, v):
        """Validate filter criteria."""
        if v is not None and v not in ['untagged', 'all']:
            raise ValueError('Filter criteria must be "untagged", "all", or None')
        return v

    @field_validator('flashcard_ids')
    @classmethod
    def validate_flashcard_ids(cls, v):
        """Validate flashcard IDs."""
        if v is not None and len(v) > 100:
            raise ValueError('Maximum 100 flashcard IDs allowed')
        return v
        if not v:
            raise ValueError('At least one flashcard ID must be provided')
        if len(set(v)) != len(v):
            raise ValueError('Duplicate flashcard IDs are not allowed')
        return v


# Tool: create_tag
class CreateTagParams(BaseModel):
    """Parameters for create_tag tool."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for the new tag")
    deck_name: str = Field(..., min_length=1, max_length=255, description="Name of the parent deck")
    color: Optional[str] = Field("#6366f1", description="Tag color (hex format)")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name."""
        if not v.strip():
            raise ValueError('Tag name cannot be empty')
        return v.strip()

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip()


# Tool: list_tags
class ListTagsParams(BaseModel):
    """Parameters for list_tags tool."""
    deck_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Filter by deck name")

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if v is not None and not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip() if v else v


# Tool: update_tag
class UpdateTagParams(BaseModel):
    """Parameters for update_tag tool."""
    tag_id: int = Field(..., gt=0, description="ID of the tag to update")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="New tag name")
    color: Optional[str] = Field(None, description="New tag color")
    description: Optional[str] = Field(None, max_length=500, description="New description")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tag name."""
        if v is not None and not v.strip():
            raise ValueError('Tag name cannot be empty')
        return v.strip() if v else v


# Tool: delete_tag
class DeleteTagParams(TagIdParam):
    """Parameters for delete_tag tool."""
    pass  # Inherits tag_id validation


# Tool: count_flashcards
class CountFlashcardsParams(BaseModel):
    """Parameters for count_flashcards tool."""
    deck_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Filter by deck name")

    @field_validator('deck_name')
    @classmethod
    def validate_deck_name(cls, v):
        """Validate deck name."""
        if v is not None and not v.strip():
            raise ValueError('Deck name cannot be empty')
        return v.strip() if v else v


# Tool: create_flashcard_template
class CreateFlashcardTemplateParams(BaseModel):
    """Parameters for create_flashcard_template tool."""
    template_name: str = Field(..., min_length=1, max_length=100, description="Name for the template")
    front_template: str = Field(..., min_length=1, max_length=1000, description="Template for front content")
    back_template: str = Field(..., min_length=1, max_length=1000, description="Template for back content")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Default difficulty level")

    @field_validator('template_name')
    @classmethod
    def validate_template_name(cls, v):
        """Validate template name."""
        if not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()
