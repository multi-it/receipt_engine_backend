from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Receipt Management API"
    debug: bool = False
    version: str = "0.1.0"
    secret_key: str = "default-secret-key-change-in-production"
    database_url: str = "sqlite+aiosqlite:///:memory:"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    postgres_host: str = "localhost"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_db: str = "mydb"
    pg_host_port: int = 5432

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

settings = Settings()
