"""
Authentication models for iCards API.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import datetime

from .common import TimestampedModel, IDModel


class User(IDModel, TimestampedModel):
    """User model."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="User email address")
    isActive: bool = Field(True, description="Whether the user account is active")
    lastLoginAt: Optional[datetime] = Field(None, description="Last login timestamp")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50, description="Desired username")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    email: EmailStr = Field(..., description="User email address")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class UserLogin(BaseModel):
    """User login request."""
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=1, description="User password")


class TokenResponse(BaseModel):
    """Authentication token response."""
    token: str = Field(..., description="JWT authentication token")
    expiresAt: datetime = Field(..., description="Token expiration timestamp")
    user: User = Field(..., description="Authenticated user data")


class AuthResponse(BaseModel):
    """Authentication response."""
    success: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Response message")
    data: TokenResponse = Field(..., description="Authentication data")

    model_config = ConfigDict(from_attributes=True)
