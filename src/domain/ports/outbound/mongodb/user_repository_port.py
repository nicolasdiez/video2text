# domain/ports/outbound/mongodb/user_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional, List

from domain.entities.user import User, UserTwitterCredentials


class UserRepositoryPort(ABC):
    """
    Outbound port for User persistence in MongoDB.
    Defines all required operations for reading and writing User entities.
    """

    # -------------------------
    # Basic CRUD operations
    # -------------------------

    @abstractmethod
    async def save(self, user: User) -> str:
        """
        Persist a new User and return the new _id as string.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: User) -> None:
        """
        Update an existing User entity.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        """
        Delete a User by its _id.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> int:
        """
        Delete all User documents. Returns number of deleted documents.
        """
        raise NotImplementedError

    # -------------------------
    # Retrieval operations
    # -------------------------

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a User by its _id.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_all(self) -> List[User]:
        """
        Retrieve all Users.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a User by its username.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a User by email.
        Required for authentication (login).
        """
        raise NotImplementedError

    # -------------------------
    # Password operations
    # -------------------------

    @abstractmethod
    async def update_password(self, user_id: str, hashed_password: str) -> None:
        """
        Update the hashed password of a User.
        The repository NEVER hashes passwords; it only stores the hashed value.
        """
        raise NotImplementedError

    # -------------------------
    # Twitter credentials
    # -------------------------

    @abstractmethod
    async def update_twitter_credentials(self, user_id: str, creds: UserTwitterCredentials) -> None:
        """
        Update the Twitter credentials of a User.
        """
        raise NotImplementedError
