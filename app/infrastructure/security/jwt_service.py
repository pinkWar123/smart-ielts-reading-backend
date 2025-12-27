import secrets
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple

import jose
from jose import jwt

from app.application.services.token_service import TokenService
from app.common.utils.time_helper import TimeHelper
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.errors.jwt_errors import (
    JwtTokenExpiredError,
    JwtTokenInvalidError,
    RefreshTokenExpiredError,
    RefreshTokenNotFoundError,
    RefreshTokenRevokedError,
)


class JwtService(TokenService):

    async def create_token_pair(
        self, user: User, additional_claims: Optional[Dict] = None
    ) -> Tuple[str, RefreshToken]:
        payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            # Convert datetime to timestamp for JSON serialization
            "created_at": user.created_at.timestamp() if user.created_at else None,
        }
        if additional_claims:
            payload.update(additional_claims)

        access_token = self.encode(payload)
        refresh_token = await self.create_refresh_token(user.id)

        return access_token, refresh_token

    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        refresh_token_model = await self.refresh_token_repo.find(token)

        if not refresh_token_model:
            return None

        return RefreshToken(
            token=refresh_token_model.token,
            user_id=refresh_token_model.user_id,
            issued_at=refresh_token_model.issued_at,
            expires_at=refresh_token_model.expires_at,
            revoked=refresh_token_model.revoked,
        )

    async def validate_refresh_token(self, token: str, user_id: str):
        refresh_token = await self.get_refresh_token(token)

        if not refresh_token:
            raise RefreshTokenNotFoundError()

        if refresh_token.revoked:
            raise RefreshTokenRevokedError()

        current_time = TimeHelper.utc_now()
        expires_at = refresh_token.expires_at

        # If expires_at is naive, make it timezone-aware (assume UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=current_time.tzinfo)

        if current_time > expires_at:
            raise RefreshTokenExpiredError()

    async def revoke_refresh_token(self, token: str):
        token_after_revoke = await self.refresh_token_repo.revoke(token)
        return token_after_revoke

    async def regenerate_tokens(
        self, user: User, token: str, additional_claims: Optional[Dict]
    ) -> Optional[Tuple[str, RefreshToken]]:
        # TODO: Fix this method - it has a type mismatch issue
        # The create_token_pair method expects a User object, not user_id string
        # This needs to be properly implemented with user repository
        if not await self.validate_refresh_token(token):
            return None

        refresh_token = await self.revoke_refresh_token(token)
        if not refresh_token:
            return None

        # This line has a bug - refresh_token.user_id is a string but create_token_pair expects User object
        return await self.create_token_pair(user, additional_claims)
        raise NotImplementedError(
            "regenerate_tokens method needs to be properly implemented"
        )

    def log_secret(self):
        return (
            self.settings.jwt_secret
            + self.settings.jwt_algorithm
            + str(self.settings.jwt_access_token_expire_minutes)
        )

    def encode(self, payload: dict) -> str:
        # Create a copy to avoid modifying the original payload
        token_payload = payload.copy()

        # Use TimeHelper for consistent UTC timezone handling
        now_utc = TimeHelper.utc_now()
        expire_utc = now_utc + timedelta(
            minutes=self.settings.jwt_access_token_expire_minutes
        )

        # Convert to timestamps for JWT (jose expects UTC timestamps)
        exp_timestamp = int(TimeHelper.to_timestamp(expire_utc))
        iat_timestamp = int(TimeHelper.to_timestamp(now_utc))

        token_payload.update(
            {
                "exp": exp_timestamp,
                "iat": iat_timestamp,
            }
        )

        token = jwt.encode(
            token_payload,
            self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        return token

    def decode(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            # Decode the token - JWT library will automatically check expiration
            decoded = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.settings.jwt_algorithm],
            )

            return decoded

        except jose.ExpiredSignatureError:
            raise JwtTokenExpiredError()

        except jose.JWTError:
            raise JwtTokenInvalidError()

    async def create_refresh_token(self, user_id: str) -> RefreshToken:
        now = TimeHelper.utc_now()
        refresh_token = RefreshToken(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            issued_at=now,
            expires_at=now
            + timedelta(minutes=self.settings.jwt_access_token_expire_minutes),
            revoked=False,
        )
        await self.refresh_token_repo.revoke_active_tokens_by_user(user_id=user_id)
        await self.refresh_token_repo.create(refresh_token)

        return refresh_token
