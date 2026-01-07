from abc import ABCMeta, abstractmethod
from typing import Dict, Optional, Tuple

from app.common.settings import Settings
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.domain.repositories.refresh_token_repository import (
    RefreshTokenRepositoryInterface,
)


class TokenService(metaclass=ABCMeta):
    """
    Abstract base class for token management services.

    This service handles the creation, validation, revocation, and regeneration of access
    and refresh tokens. Implementations should support token encoding/decoding and manage
    token lifecycle, including expiration and revocation.
    """

    def __init__(
        self, settings: Settings, refresh_token_repo: RefreshTokenRepositoryInterface
    ):
        """
        Initialize the TokenService with configuration settings and repository.

        Args:
            settings: Application settings containing token configuration (expiration times, secrets, etc.)
            refresh_token_repo: Repository for persisting and retrieving refresh tokens from the database
        """
        self.settings = settings
        self.refresh_token_repo = refresh_token_repo

    @abstractmethod
    def encode(self, payload):
        """
        Encode a payload into a token.

        Converts a dictionary payload into a token string, typically with expiration claims.

        Args:
            payload: Dictionary containing claims to encode into the token

        Returns:
            Encoded token string
        """
        pass

    @abstractmethod
    def decode(self, token):
        """
        Decode a token into its payload.

        Validates and decodes a token string back into a dictionary of claims.

        Args:
            token: The token string to decode

        Returns:
            Dictionary of decoded claims, or None if the token is invalid/expired
        """
        pass

    @abstractmethod
    async def create_refresh_token(self, user_id):
        """
        Create a new refresh token for a user.

        Generates a new refresh token, sets its expiration, and persists it to the database.

        Args:
            user_id: The user ID to associate with the refresh token

        Returns:
            RefreshToken entity containing token, user_id, issued_at, expires_at, and revoked status
        """
        pass

    @abstractmethod
    async def create_token_pair(
        self, user: User, additional_claims: Optional[Dict] = None
    ) -> Tuple[str, RefreshToken]:
        """
        Create both an access token and a refresh token for a user.

        Generates a complete token pair for authentication. The access token is typically
        short-lived and used for API requests, while the refresh token is long-lived and
        used to get new access tokens.

        Args:
            user: The user for whom to create tokens
            additional_claims: Optional dictionary of extra claims to include in the access token

        Returns:
            Tuple of (access_token_string, RefreshToken_entity)
        """
        pass

    @abstractmethod
    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """
        Retrieve a refresh token from the database by its value.

        Args:
            token: The refresh token string to look up

        Returns:
            RefreshToken entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def validate_refresh_token(self, token: str):
        """
        Validate whether a refresh token is valid and usable.

        Checks that the token exists, is not revoked, and has not expired.

        Args:
            token: The refresh token string to validate

        Returns:
            True if the token is valid and can be used, False otherwise
        """
        pass

    @abstractmethod
    async def revoke_refresh_token(self, token: str):
        """
        Mark a refresh token as revoked in the database.

        Prevents further use of the token while maintaining the revocation record for audit purposes.

        Args:
            token: The refresh token string to revoke

        Returns:
            The revoked RefreshToken entity if successful, None otherwise
        """
        pass

    @abstractmethod
    async def regenerate_tokens(
        self, token: str, additional_claims: Optional[Dict]
    ) -> Optional[Tuple[str, RefreshToken]]:
        """
        Regenerate both access and refresh tokens using a valid refresh token.

        Validates the provided refresh token, revokes it, and issues a new token pair.
        This is the typical flow when an access token expires, but the user wants to stay logged in.

        Args:
            token: The refresh token to use for regeneration
            additional_claims: Optional extra claims to include in the new access token

        Returns:
            Tuple of (new_access_token_string, new_RefreshToken_entity) if validation succeeds,
            None if the refresh token is invalid or expired
        """
        pass
