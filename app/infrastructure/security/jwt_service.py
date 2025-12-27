import datetime
import secrets
from abc import ABC
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

import jose
from jose import jwt

from app.application.services.token_service import TokenService
from app.domain.entities.refresh_token import RefreshToken


class JwtService(TokenService):

    def create_token_pair(self, user_id: str, additional_claims: Optional[Dict] = None) -> Tuple[str, RefreshToken]:
        payload = {"user_id": user_id}
        if additional_claims:
            payload.update(additional_claims)

        access_token = self.encode(payload)
        refresh_token = self.create_refresh_token(user_id)

        return access_token, refresh_token

    def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        refresh_token_model = self.refresh_token_repo.find(token)

        if not refresh_token_model:
            return None

        return RefreshToken(
            token=refresh_token_model.token,
            user_id=refresh_token_model.user_id,
            issued_at=refresh_token_model.issued_at,
            expires_at=refresh_token_model.expires_at,
            revoked=refresh_token_model.revoked
        )

    def validate_refresh_token(self, token: str) -> bool:
        refresh_token = self.get_refresh_token(token)

        if not refresh_token:
            return False

        if refresh_token.revoked:
            return False

        if datetime.datetime.now() > refresh_token.expires_at:
            return False

        return True

    def revoke_refresh_token(self, token: str) -> Optional[RefreshToken]:
        token_after_revoke = self.refresh_token_repo.revoke(token)
        return token_after_revoke

    def regenerate_tokens(self, token: str, additional_claims: Optional[Dict]) -> Optional[Tuple[str, RefreshToken]]:
        if not self.validate_refresh_token(token):
            return None

        refresh_token = self.revoke_refresh_token(token)
        if not refresh_token:
            return None

        self.revoke_refresh_token(token)

        return self.create_token_pair(refresh_token.user_id, additional_claims)

    def log_secret(self):
        return (
            self.settings.jwt_secret
            + self.settings.jwt_algorithm
            + str(self.settings.jwt_access_token_expire_minutes)
        )

    def encode(self, payload: dict) -> str:
        # Dummy implementation for illustration
        expire = datetime.datetime.now() + timedelta(
            minutes=self.settings.jwt_access_token_expire_minutes
        )
        payload.update({"exp": expire})
        token = jwt.encode(
            payload, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm
        )
        return token

    def decode(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            decoded = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm],
            )

            return decoded

        except jose.ExpiredSignatureError:
            return None

        except jose.JWTError:
            return None

    def create_refresh_token(self, user_id: str) -> RefreshToken:
        refresh_token = RefreshToken(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            issued_at=datetime.datetime.utcnow(),
            expires_at=datetime.datetime.utcnow()
            + timedelta(minutes=self.settings.jwt_refresh_token_expire_minutes),
            revoked=False,
        )
        self.refresh_token_repo.create(refresh_token)

        return refresh_token

