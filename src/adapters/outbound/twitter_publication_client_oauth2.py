# src/adapters/outbound/twitter_publication_client_oauth2.py

import aiohttp
import logging
import inspect
from datetime import datetime, timedelta

from domain.ports.outbound.twitter_publication_port import TwitterPublicationPort
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from infrastructure.auth.twitter_oauth2_service import TwitterOAuth2Service

logger = logging.getLogger(__name__)


class TwitterPublicationClientOAuth2(TwitterPublicationPort):
    """
    OAuth2 User Context implementation of TwitterPublicationPort.
    Publishes tweets using the user's OAuth2 access token.
    
    OAuth2 →    The User authorizes the App, and the App interacts with Twitter using the User's access token.
                The App still performs the publish operation, but only with user-level credentials.    
    """

    TWEET_URL = "https://api.twitter.com/2/tweets"

    def __init__(self, user_repo: UserRepositoryPort, oauth2_service: TwitterOAuth2Service):
        self.user_repo = user_repo
        self.oauth2_service = oauth2_service

        logger.info(
            "TwitterPublicationClientOAuth2 initialized (User Context)",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    # ---------------------------------------------------------
    # OPTIONAL: App credentials validation (not required)
    # ---------------------------------------------------------
    async def validate_app_credentials(self) -> None:
        """
        Optional method. OAuth2 User Context does not require app-level
        credentials to publish tweets, so this method is only provided for symmetry with OAuth1.
        """
        logger.info(
            "validate_app_credentials() called, but OAuth2 User Context does not require app validation.",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    # ---------------------------------------------------------
    # PUBLISH
    # ---------------------------------------------------------
    async def publish(self, user, text: str) -> str:
        """
        Publishes a tweet using the user's OAuth2 access token.
        Automatically refreshes tokens if expired.
        """

        creds = user.twitter_credentials
        if not creds or not creds.oauth2_access_token:
            raise RuntimeError("User has no OAuth2 credentials configured.")

        # Refresh user access token if expired
        REFRESH_BUFFER = timedelta(seconds=60)
        expires_at = creds.oauth2_access_token_expires_at
        now = datetime.utcnow()

        if (expires_at is None) or (expires_at <= now + REFRESH_BUFFER):
            logger.info("Access token missing or near expiry for user %s (expires_at=%s), refreshing...",
                user.id,
                expires_at,
                extra={"user_id": user.id, "module_name": __name__, "method": "publish"},)
            access_token = await self.oauth2_service.refresh_tokens(user.id)
        else:
            access_token = creds.oauth2_access_token

        payload = {"text": text}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # there is no need to wrap with asyncio.to_thread() because aiohttp is natively async
        async with aiohttp.ClientSession() as session:
            async with session.post(self.TWEET_URL, json=payload, headers=headers) as resp:
                body = await resp.text()

                if resp.status != 201:
                    logger.error(
                        f"Failed to publish tweet: {resp.status} - {body}",
                        extra={"user_id": user.id, "module_name": __name__, "method": "publish"},
                    )
                    raise RuntimeError(f"Twitter publish failed: {resp.status}")

                data = await resp.json()

        tweet_id = data["data"]["id"]

        logger.info(
            f"Tweet published OK (tweet_id={tweet_id}) (text: {text})",
            extra={"user_id": user.id, "class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return tweet_id
