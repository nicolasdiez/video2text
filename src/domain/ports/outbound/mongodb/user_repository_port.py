# domain/ports/outbound/mongodb/user_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from domain.entities.user import User, TwitterCredentials

class UserRepositoryPort(ABC):
    """
    Outbound port for User persistence in MongoDB.
    Handles CRUD operations for the User entity.
    """

    @abstractmethod
    async def save(self, user: User) -> str:
        """
        Persiste un User y devuelve el nuevo _id como cadena.
        """
        ...

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Recupera un User por su _id.
        """
        ...

    @abstractmethod
    async def find_all(self) -> List[Dict[str, Any]]:
        """Devuelve todos los usuarios"""
        ...

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """
        Recupera un User por su username.
        """
        ...

    @abstractmethod
    async def update(self, user: User) -> None:
        """
        Actualiza un User existente.
        """
        ...

    @abstractmethod
    async def delete(self, user_id: str) -> None:
        """
        Elimina un User por su _id.
        """
        ...

    @abstractmethod
    async def update_twitter_credentials(self, user_id: str, creds: TwitterCredentials) -> None:
        """
        Actualiza las credenciales de Twitter de un usuario.
        """
        ...