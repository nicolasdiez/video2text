# adapters/outbound/twitter_client.py

import os
import asyncio
import tweepy
import inspect  # para trazas logging con print

from domain.ports.twitter_port import TwitterPort

class TwitterClient(TwitterPort):
    """
    Implementación de TwitterPort usando tweepy.Client v2.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        access_token: str | None = None,
        access_token_secret: str | None = None,
        bearer_token: str | None = None
    ):
        # Carga credenciales desde parámetros o variables de entorno
        self.api_key            = api_key            or os.getenv("X_API_KEY")
        self.api_secret         = api_secret         or os.getenv("X_API_SECRET")
        self.access_token       = access_token       or os.getenv("X_API_ACCESS_TOKEN")
        self.access_token_secret= access_token_secret or os.getenv("X_API_ACCESS_TOKEN_SECRET")
        self.bearer_token       = bearer_token       or os.getenv("X_API_BEARER_TOKEN")

        if not all([
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret,
            self.bearer_token
        ]):
            raise RuntimeError("Faltan credenciales de Twitter (X).")

        # Instanciamos el cliente tweepy
        self.client = tweepy.Client(
            consumer_key        = self.api_key,
            consumer_secret     = self.api_secret,
            access_token        = self.access_token,
            access_token_secret = self.access_token_secret,
            bearer_token        = self.bearer_token
        )

        # Logging
        print(f"[{self.__class__.__name__}] __init__ finished OK")


    async def publish(self, text: str) -> str:
        """
        Publica un tweet de forma asíncrona delegando la llamada bloqueante
        a un hilo aparte.
        """
        tweet_id = await asyncio.to_thread(self._publish_sync, text)

        # Logging
        print(f"[{inspect.currentframe().f_code.co_name}] finished OK")

        return tweet_id

    def _publish_sync(self, text: str) -> str:
        # Aquí se llama al método bloqueante de tweepy
        resp = self.client.create_tweet(text=text)
        tweet_id = resp.data["id"]
        print(f"[TwitterClient] Tweet published with ID: {tweet_id}")

        # Logging
        print(f"[{inspect.currentframe().f_code.co_name}] finished OK")

        return tweet_id
