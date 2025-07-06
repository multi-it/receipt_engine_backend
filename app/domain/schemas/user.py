"""User schemas."""
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """User registration schema."""
    
    full_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    """User login schema."""
    
    username: str
    password: str


class UserResponse(BaseModel):
    """User response schema."""
    
    id: int
    full_name: str
    username: str
    email: str
    is_active: bool
