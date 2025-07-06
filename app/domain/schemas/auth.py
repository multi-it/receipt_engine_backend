"""Authentication schemas."""
from pydantic import BaseModel


class Token(BaseModel):
    """Token schema."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    
    user_id: int
    username: str
