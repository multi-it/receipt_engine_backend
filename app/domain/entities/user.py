"""User domain entities."""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    """User domain entity."""
    
    id: Optional[int] = None
    full_name: str = ""
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize after creation."""
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def validate(self) -> None:
        """Validate user data."""
        if not self.full_name or len(self.full_name.strip()) < 2:
            raise ValueError("Full name must contain at least 2 characters")
        
        if not self.username or len(self.username.strip()) < 3:
            raise ValueError("Username must contain at least 3 characters")
        
        if "@" not in self.email:
            raise ValueError("Invalid email address")
        
        if not self.password_hash:
            raise ValueError("Password cannot be empty")
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
