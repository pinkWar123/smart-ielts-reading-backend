from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int = 15
    claude_api_key: str
    claude_model: str = "claude-instant-1"
    max_retry_attempts: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
