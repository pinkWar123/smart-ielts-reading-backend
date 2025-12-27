import bcrypt

from app.application.services.password_service import PasswordService


class PasswordHasher(PasswordService):
    @staticmethod
    def hash(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
