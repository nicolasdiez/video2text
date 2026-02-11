# adapters/outbound/twitter_publication_client.py

import os
import asyncio
import tweepy

# logging
import inspect
import logging

import config

from domain.ports.outbound.twitter_port import TwitterPublicationPort
from functools import wraps

DEBUG = bool(config.APP_DEBUG)

# Specific logger for this module
logger = logging.getLogger(__name__)

def skip_if_debug(fn):
    @wraps(fn)
    async def wrapper(self, *args, **kwargs):
        if DEBUG:
            logger.info("[DEBUG] Se omitió TwitterPublicationClient publish con args=%s, kwargs=%s", args, kwargs, extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
            return None
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
        
        # load credentials
        self.oauth1_api_key     = oauth1_api_key
        self.oauth1_api_secret  = oauth1_api_secret
        
        # Logging
        logger.info("TwitterPublicationClient initialized with app credentials",extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        logger.info("Finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})


    @skip_if_debug
    async def publish(self, text: str, oauth1_access_token: str, oauth1_access_token_secret: str) -> str:
        """
        Publica un tweet en nombre de un usuario.
        Se construye un cliente tweepy con las credenciales de app + usuario.
        """
        tweet_id = await asyncio.to_thread(self._publish_sync, text, oauth1_access_token, oauth1_access_token_secret)

        logger.info("Publish finished OK", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

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

        logger.info("Tweet published with ID: %s (tweet text: '%s')", tweet_id, text, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return tweet_id