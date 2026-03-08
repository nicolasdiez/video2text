# src/adapters/outbound/twitter_publication_client_oauth2.py

import aiohttp
import logging
import inspect
from datetime import datetime

from domain.ports.outbound.twitter_publication_port import TwitterPublicationPort
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from infrastructure.auth.twitter_oauth2_service import TwitterOAuth2Service

logger = logging.getLogger(__name__)


class TwitterPublicationClientOAuth2(TwitterPublicationPort):
    """
    Implementación moderna del puerto TwitterPublicationPort usando OAuth2 User Context.
    Publica tweets en nombre de un usuario usando su access_token almacenado en DB.
    """

    TWEET_URL = "https://api.twitter.com/2/tweets"

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        oauth2_service: TwitterOAuth2Service,
    ):
        self.user_repo = user_repo
        self.oauth2_service = oauth2_service

        logger.info(
            "TwitterPublicationClient initialized (OAuth2 User Context)",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    # ---------------------------------------------------------
    # PUBLICACIÓN DE TWEETS (OAuth2)
    # ---------------------------------------------------------
    async def publish(self, user_id: str, text: str) -> str:
        """
        Publica un tweet en nombre de un usuario usando OAuth2 User Context.
        - Recupera tokens del usuario
        - Refresca tokens si han expirado
        - Publica el tweet con Bearer Token
        """

        user = await self.user_repo.find_by_id(user_id)
        if not user or not user.twitter_credentials:
            raise RuntimeError("User has no Twitter credentials configured.")

        creds = user.twitter_credentials

        # 1) Refrescar tokens si han expirado
        if not creds.oauth2_access_token or not creds.oauth2_access_token_expires_at:
            raise RuntimeError("User has no OAuth2 access token stored.")

        if creds.oauth2_access_token_expires_at <= datetime.utcnow():
            logger.info(
                f"Access token expired for user {user_id}, refreshing...",
                extra={"user_id": user_id, "module": __name__, "method": "publish"},
            )
            access_token = await self.oauth2_service.refresh_tokens(user_id)
        else:
            access_token = creds.oauth2_access_token

        # 2) Publicar el tweet
        payload = {"text": text}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.TWEET_URL, json=payload, headers=headers) as resp:
                body = await resp.text()

                if resp.status != 201:
                    logger.error(
                        f"Failed to publish tweet: {resp.status} - {body}",
                        extra={"user_id": user_id, "module": __name__, "method": "publish"},
                    )
                    raise RuntimeError(f"Twitter publish failed: {resp.status}")

                data = await resp.json()

        tweet_id = data["data"]["id"]

        logger.info(
            f"Tweet published OK (tweet_id={tweet_id})",
            extra={"user_id": user_id, "class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

        return tweet_id
