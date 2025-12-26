from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
