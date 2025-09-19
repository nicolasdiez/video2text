# adapters/outbound/twitter_client.py

import os
import asyncio
import tweepy
import inspect  # para trazas logging con print

from domain.ports.outbound.twitter_port import TwitterPort
from functools import wraps

DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"

def skip_if_debug(fn):
    @wraps(fn)
    async def wrapper(self, *args, **kwargs):
        if DEBUG:
            print(f"[DEBUG] Se omitió TwitterClient publish con args={args}, kwargs={kwargs}")
            return None
        return await fn(self, *args, **kwargs)
    return wrapper


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
        if not all([
            api_key,
            api_secret,
            access_token,
            access_token_secret,
            bearer_token
        ]):
            raise RuntimeError("Twitter (X) credentials not defined.")
        
        # load credentials
        self.api_key            = api_key
        self.api_secret         = api_secret
        self.access_token       = access_token
        self.access_token_secret= access_token_secret
        self.bearer_token       = bearer_token
        
        # Instanciamos el cliente tweepy
        self.client = tweepy.Client(
            consumer_key        = self.api_key,
            consumer_secret     = self.api_secret,
            access_token        = self.access_token,
            access_token_secret = self.access_token_secret,
            bearer_token        = self.bearer_token
        )

        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")


    @skip_if_debug
    async def publish(self, text: str) -> str:
        """
        Publica un tweet de forma asíncrona delegando la llamada bloqueante a un hilo aparte.
        """

        tweet_id = await asyncio.to_thread(self._publish_sync, text)

        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")

        return tweet_id


    def _publish_sync(self, text: str) -> str:

        # Llamar al método bloqueante create_tweet() de tweepy --> al haberlo wrappeado con await asyncio.to_thread() no bloquea el event loop
        resp = self.client.create_tweet(text=text)
        tweet_id = resp.data["id"]
        print(f"[TwitterClient] Tweet published with ID: {tweet_id}")

        # Logging
        print(f"[{self.__class__.__name__}][{inspect.currentframe().f_code.co_name}] Finished OK")

        return tweet_id
