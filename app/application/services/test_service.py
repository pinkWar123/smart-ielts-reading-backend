from app.infrastructure.security.jwt_service import JwtService


class TestService:
    def __init__(self, jwt_service: JwtService):
        self.jwt_service = jwt_service

    def get_jwt_secret(self):
        return self.jwt_service.log_secret()
