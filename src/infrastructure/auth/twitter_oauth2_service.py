# src/infra/auth/twitter_oauth2_service.py

import aiohttp
import uuid
from datetime import datetime, timedelta
from typing import Optional

from domain.entities.user import UserTwitterCredentials
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort

from config import (
    X_OAUTH2_CLIENT_ID,
    X_OAUTH2_CLIENT_SECRET,
    X_OAUTH2_REDIRECT_URI,
)

import logging
logger = logging.getLogger(__name__)


class TwitterOAuth2Service:
    """
    Handles the full OAuth2 User Context flow for Twitter/X:
    - Generate authorization URL
    - Exchange authorization code for tokens
    - Refresh tokens
    - Persist updated tokens in UserRepositoryPort
    """

    AUTH_BASE_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

    SCOPES = [
        "tweet.write",
        "users.read",
        "offline.access",
    ]

    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo

    # ---------------------------------------------------------
    # 1) Generate authorization URL
    # ---------------------------------------------------------
    async def get_authorization_url(self, user_id: str) -> str:
        """
        Generates the URL where the user must be redirected to authorize the app.
        Stores a random OAuth2 state value for later validation.
        """
        
        # Generate state
        state = str(uuid.uuid4())
        scope_str = " ".join(self.SCOPES)

        # Load user and store state
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise RuntimeError(f"User {user_id} not found.")

        creds = user.twitter_credentials or UserTwitterCredentials(
            oauth1_access_token="",
            oauth1_access_token_secret="",
            oauth2_access_token="",
        )

        creds.oauth2_state = state
        await self.user_repo.update_twitter_credentials(user_id, creds)

        # Build authorization URL
        url = (
            f"{self.AUTH_BASE_URL}"
            f"?response_type=code"
            f"&client_id={X_OAUTH2_CLIENT_ID}"
            f"&redirect_uri={X_OAUTH2_REDIRECT_URI}"
            f"&scope={scope_str}"
            f"&state={state}"
            f"&code_challenge=challenge"
            f"&code_challenge_method=plain"
        )

        logger.info(
            f"Generated Twitter OAuth2 authorization URL for user {user_id}",
            extra={"user_id": user_id, "module": __name__, "method": "get_authorization_url"},
        )

        return url

    # ---------------------------------------------------------
    # 2) Exchange authorization code for tokens
    # ---------------------------------------------------------
    async def exchange_code_for_tokens(self, user_id: str, code: str, state: str) -> None:
        """
        Exchanges the authorization code for access_token + refresh_token.
        Validates the OAuth2 state and persists tokens in the user's credentials.
        """

        # Validate stored state
        user = await self.user_repo.find_by_id(user_id)
        if not user or not user.twitter_credentials:
            raise RuntimeError("User has no Twitter credentials to validate state.")

        stored_state = user.twitter_credentials.oauth2_state
        if not stored_state:
            raise RuntimeError("No OAuth2 state stored for this user.")

        if state != stored_state:
            logger.error(
                f"Invalid OAuth2 state for user {user_id}: expected={stored_state}, received={state}",
                extra={"user_id": user_id, "module": __name__, "method": "exchange_code_for_tokens"},
            )
            raise RuntimeError("Invalid OAuth2 state received.")

        # Prepare token exchange request
        data = {
            "grant_type": "authorization_code",
            "client_id": X_OAUTH2_CLIENT_ID,
            "redirect_uri": X_OAUTH2_REDIRECT_URI,
            "code": code,
            "code_verifier": "challenge",
        }

        # Call Twitter token endpoint
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.TOKEN_URL,
                data=data,
                auth=aiohttp.BasicAuth(
                    X_OAUTH2_CLIENT_ID,
                    X_OAUTH2_CLIENT_SECRET
                )
            ) as resp:

                if resp.status != 200:
                    body = await resp.text()
                    logger.error(
                        f"Failed to exchange code for tokens: {resp.status} - {body}",
                        extra={"user_id": user_id, "module": __name__, "method": "exchange_code_for_tokens"},
                    )
                    raise RuntimeError(f"Twitter OAuth2 token exchange failed: {resp.status}")

                payload = await resp.json()

        # Extract tokens
        access_token = payload["access_token"]
        refresh_token = payload.get("refresh_token")
        expires_in = payload.get("expires_in", 7200)
        refresh_expires_in = payload.get("refresh_token_expires_in", 30 * 24 * 3600)

        # Persist tokens
        await self._update_user_tokens(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
        )

        logger.info(
            f"Successfully exchanged code for tokens for user {user_id}",
            extra={"user_id": user_id, "module": __name__, "method": "exchange_code_for_tokens"},
        )


    # ---------------------------------------------------------
    # 3) Refresh tokens
    # ---------------------------------------------------------
    async def refresh_tokens(self, user_id: str) -> str:
        """
        Refreshes the user's access token using the stored refresh_token.
        Returns the new access_token.
        """

        user = await self.user_repo.find_by_id(user_id)
        if not user or not user.twitter_credentials:
            raise RuntimeError("User has no Twitter credentials to refresh.")

        refresh_token = user.twitter_credentials.oauth2_refresh_token
        if not refresh_token:
            raise RuntimeError("User has no refresh_token stored.")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": X_OAUTH2_CLIENT_ID,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, data=data, auth=aiohttp.BasicAuth(
                X_OAUTH2_CLIENT_ID,
                X_OAUTH2_CLIENT_SECRET
            )) as resp:

                if resp.status != 200:
                    body = await resp.text()
                    logger.error(
                        f"Failed to refresh tokens: {resp.status} - {body}",
                        extra={"user_id": user_id, "module": __name__, "method": "refresh_tokens"},
                    )
                    raise RuntimeError(f"Twitter OAuth2 refresh failed: {resp.status}")

                payload = await resp.json()

        new_access_token = payload["access_token"]
        new_refresh_token = payload.get("refresh_token", refresh_token)
        expires_in = payload.get("expires_in", 7200)
        refresh_expires_in = payload.get("refresh_token_expires_in", 30 * 24 * 3600)

        await self._update_user_tokens(
            user_id=user_id,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
        )

        logger.info(
            f"Successfully refreshed tokens for user {user_id}",
            extra={"user_id": user_id, "module": __name__, "method": "refresh_tokens"},
        )

        return new_access_token

    # ---------------------------------------------------------
    # Internal helper: persist tokens
    # ---------------------------------------------------------
    async def _update_user_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: int,
        refresh_expires_in: int,
    ) -> None:

        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        refresh_expires_at = datetime.utcnow() + timedelta(seconds=refresh_expires_in)

        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise RuntimeError(f"User {user_id} not found.")

        creds = user.twitter_credentials or UserTwitterCredentials(
            oauth1_access_token="",
            oauth1_access_token_secret="",
            oauth2_access_token="",
        )

        creds.oauth2_access_token = access_token
        creds.oauth2_access_token_expires_at = expires_at
        creds.oauth2_refresh_token = refresh_token
        creds.oauth2_refresh_token_expires_at = refresh_expires_at

        await self.user_repo.update_twitter_credentials(user_id, creds)
