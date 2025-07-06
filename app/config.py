from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Receipt Management API")
    debug: bool = Field(default=False)
    version: str = Field(default="0.1.0")
    secret_key: str = Field(min_length=10)
    database_url: str = Field(description="Database connection URL")
    
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    postgres_host: str = Field(default="localhost")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="password")
    postgres_db: str = Field(default="mydb")
    pg_host_port: int = Field(default=5432)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
