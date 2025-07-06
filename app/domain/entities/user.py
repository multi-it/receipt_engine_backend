from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass
import re

@dataclass
class User:
    id: Optional[int] = None
    fullname: str = ""
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def validate(self) -> None:
        if not self.fullname or len(self.fullname.strip()) < 2:
            raise ValueError("Full name must contain at least 2 characters")
        
        if not self.username or len(self.username.strip()) < 3:
            raise ValueError("Username must contain at least 3 characters")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email address")
        
        if not self.password_hash:
            raise ValueError("Password cannot be empty")
    
    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
