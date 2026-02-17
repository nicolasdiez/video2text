import os
import asyncio
import tweepy
import random

# logging
import inspect
import logging

import config

from domain.ports.outbound.twitter_publication_port import TwitterPublicationPort
from functools import wraps

DEBUG = bool(config.APP_DEBUG)

# Specific logger for this module
logger = logging.getLogger(__name__)


def _generate_fake_tweet_id() -> str:
    """
    Generates a valid-looking Twitter Snowflake ID (18-19 digits).
    Example: 2020243890524078182
    """
    # Twitter snowflakes are 64-bit integers. Range approx: 2^63 → 9.22e18
    return str(random.randint(10**18, 10**19 - 1))


def skip_if_debug(fn):
    @wraps(fn)
    async def wrapper(self, *args, **kwargs):
        if DEBUG:
            logger.info(
                "[DEBUG] Se omitió TwitterPublicationClient publish con args=%s, kwargs=%s",
                args,
                kwargs,
                extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name}
            )
            # ID of an existing valid dummy tweet
            return "2023032187466183103" #"2019141630763073856"
        
            # Returns a fake tweet_id so the consumers behaves normally
            # fake_id = _generate_fake_tweet_id()
            # logger.info(
            #    "[DEBUG] Returning fake tweet_id=%s",
            #    fake_id,
            #    extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name}
            # )
            #return fake_id

        return await fn(self, *args, **kwargs)
    return wrapper


class TwitterPublicationClient(TwitterPublicationPort):
    """
    Implementación de TwitterPublicationPort usando tweepy.Client v2.
    Se inicializa con credenciales de aplicación (OAuth1 API key/secret).
    Las credenciales de usuario (access_token, access_token_secret) se pasan en cada publish().
    """

    def __init__(self, oauth1_api_key: str, oauth1_api_secret: str):
        if not all([oauth1_api_key, oauth1_api_secret]):
            raise RuntimeError("Twitter (X) application credentials not defined.")
        
        # application credentials
        self.oauth1_api_key = oauth1_api_key
        self.oauth1_api_secret = oauth1_api_secret
        
        logger.info(
            "TwitterPublicationClient initialized with app credentials",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
        )
        logger.info(
            "Finished OK",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
        )


    @skip_if_debug
    async def publish(self, text: str, oauth1_access_token: str, oauth1_access_token_secret: str) -> str:
        """
        Publica un tweet en nombre de un usuario.
        Se construye un cliente tweepy con las credenciales de app + usuario.
        """
        tweet_id = await asyncio.to_thread(
            self._publish_sync,
            text,
            oauth1_access_token,
            oauth1_access_token_secret
        )

        logger.info(
            "Publish finished OK",
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
        )

        return tweet_id


    def _publish_sync(self, text: str, oauth1_access_token: str, oauth1_access_token_secret: str) -> str:
        """
        Método síncrono que llama a Tweepy para publicar un tweet.
        """
        client = tweepy.Client(
            consumer_key=self.oauth1_api_key,
            consumer_secret=self.oauth1_api_secret,
            access_token=oauth1_access_token,
            access_token_secret=oauth1_access_token_secret,
        )

        resp = client.create_tweet(text=text)
        tweet_id = resp.data["id"]

        logger.info(
            "Tweet published with ID: %s (tweet text: '%s')",
            tweet_id,
            text,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name}
        )

        return tweet_id
