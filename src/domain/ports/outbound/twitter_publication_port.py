# src/domain/ports/outbound/twitter_publication_port.py

from abc import ABC, abstractmethod

class TwitterPublicationPort(ABC):
    """
    Abstraction for publishing tweets (X) on behalf of a user.
    Implementations may use OAuth1 or OAuth2, but the domain does not care.
    """

    @abstractmethod
    async def publish(self, user, text: str) -> str:
        """
        Publishes a tweet on behalf of the given user.

        :param user: Domain User object, containing twitter_credentials
        :param text: Tweet content
        :return: ID of the published tweet
        """
        raise NotImplementedError
