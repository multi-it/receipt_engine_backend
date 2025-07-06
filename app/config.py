"""Application configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    app_name: str = Field(default="Receipt Management API")
    debug: bool = Field(default=False)
    version: str = Field(default="0.1.0")
    secret_key: str = Field(min_length=10)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
