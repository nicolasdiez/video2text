# src/adapters/outbound/twitter_publication_client_oauth1.py

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
    """Decorator that bypasses real publishing when APP_DEBUG=True."""
    @wraps(fn)
    async def wrapper(self, *args, **kwargs):
        if DEBUG:
            logger.info(
                "[DEBUG] Se omitió TwitterPublicationClientOAuth1 publish con args=%s, kwargs=%s",
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

# src/adapters/outbound/twitter_publication_client_oauth1.py

import asyncio
import tweepy
import logging
import inspect
import random
import config

from domain.ports.outbound.twitter_publication_port import TwitterPublicationPort

logger = logging.getLogger(__name__)
DEBUG = bool(config.APP_DEBUG)


def _generate_fake_tweet_id() -> str:
    """Generates a valid-looking Twitter Snowflake ID."""
    return str(random.randint(10**18, 10**19 - 1))


def skip_if_debug(fn):
    """Decorator that bypasses real publishing when APP_DEBUG=True."""
    async def wrapper(self, *args, **kwargs):
        if DEBUG:
            logger.info("[DEBUG] Skipping real OAuth1 publish")
            return "2023032187466183103"
        return await fn(self, *args, **kwargs)
    return wrapper


class TwitterPublicationClientOAuth1(TwitterPublicationPort):
    """
    OAuth1 implementation of TwitterPublicationPort.
    Uses Tweepy v2 client with user access tokens.

    OAuth1 →    The App interacts with Twitter using both App credentials and User credentials.
                The App signs every request and performs the publish operation.
    """

    def __init__(self, oauth1_api_key: str, oauth1_api_secret: str):
        if not all([oauth1_api_key, oauth1_api_secret]):
            raise RuntimeError("Twitter OAuth1 app credentials missing")

        self.oauth1_api_key = oauth1_api_key
        self.oauth1_api_secret = oauth1_api_secret

        logger.info("TwitterPublicationClientOAuth1 initialized")
        self.validate_app_credentials()

    # ---------------------------------------------------------
    # APP CREDENTIALS VALIDATION
    # ---------------------------------------------------------
    def validate_app_credentials(self) -> None:
        """
        Validates OAuth1 app credentials by attempting to build a handler.
        """
        try:
            tweepy.OAuth1UserHandler(
                consumer_key=self.oauth1_api_key,
                consumer_secret=self.oauth1_api_secret,
                access_token="dummy",
                access_token_secret="dummy"
            )
        except Exception as e:
            logger.error("Invalid OAuth1 App credentials: %s", e)
            raise RuntimeError("Invalid OAuth1 App credentials") from e

        logger.info("OAuth1 App credentials validated OK")

    # ---------------------------------------------------------
    # USER CREDENTIALS VALIDATION
    # ---------------------------------------------------------
    def _validate_user_credentials(self, user_creds) -> bool:
        """
        Validates user OAuth1 credentials using get_me().
        """
        try:
            client = tweepy.Client(
                consumer_key=self.oauth1_api_key,
                consumer_secret=self.oauth1_api_secret,
                user_access_token=user_creds.oauth1_access_token,
                user_access_token_secret=user_creds.oauth1_access_token_secret,
            )
            resp = client.get_me()
            return bool(resp and resp.data)
        except Exception:
            return False

    # ---------------------------------------------------------
    # PUBLISH
    # ---------------------------------------------------------
    @skip_if_debug
    async def publish(self, user, text: str) -> str:
        """
        Publishes a tweet using OAuth1 user credentials.
        """
        user_creds = user.twitter_credentials

        if not user_creds or not user_creds.oauth1_access_token or not user_creds.oauth1_access_token_secret:
            raise RuntimeError("User has no valid OAuth1 credentials")

        if not self._validate_user_credentials(user_creds):
            raise RuntimeError("Invalid OAuth1 user credentials")

        # wrap create_tweet() with asyncio.to_thread() because Tweepy is natively sync, 
        # so wrapping it with asyncio ensures we don't block the event loop.
        tweet_id = await asyncio.to_thread(
            self._publish_sync,
            text,
            user_creds.oauth1_access_token,
            user_creds.oauth1_access_token_secret
        )

        logger.info(
            f"Tweet published OK (tweet_id={tweet_id}) (text: {text})",
            extra={"user_id": user.id, "class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return tweet_id

    def _publish_sync(self, text, user_access_token, user_access_token_secret):
        """
        Synchronous Tweepy call executed in a thread.
        """
        client = tweepy.Client(
            consumer_key=self.oauth1_api_key,
            consumer_secret=self.oauth1_api_secret,
            user_access_token=user_access_token,
            user_access_token_secret=user_access_token_secret,
        )
        resp = client.create_tweet(text=text)
        return resp.data["id"]