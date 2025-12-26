
from app.common.settings import Settings


class JwtService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def log_secret(self):
        return self.settings.jwt_secret + self.settings.jwt_algorithm + str(self.settings.jwt_access_token_expire_minutes)