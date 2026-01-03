from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int = 15
    claude_api_key: str
    claude_model: str = "claude-instant-1"
    max_retry_attempts: int = 3

    # CORS Configuration
    environment: str = "dev"  # dev or production
    cors_origins: str = "*"  # Comma-separated list or "*"

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str, info) -> list[str]:
        """Parse CORS origins from comma-separated string to list"""
        env = info.data.get("environment", "dev")

        # In dev, if set to "*", allow common dev origins
        if env == "dev" and v == "*":
            return ["*"]

        # If "*" in production (not recommended but allowed)
        if v == "*":
            return ["*"]

        # Parse comma-separated origins
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
