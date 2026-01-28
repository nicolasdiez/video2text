# adapters/outbound/mongo/user_repository.py

from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.user import User, UserTwitterCredentials, TweetFetchSortOrder
from domain.value_objects.scheduler_config import SchedulerConfig
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from infrastructure.mongodb import db

from infrastructure.security.encription import encrypt_value, decrypt_value


class MongoUserRepository(UserRepositoryPort):
    """
    MongoDB implementation of the UserRepositoryPort.
    Handles persistence and retrieval of User entities.
    """

    def __init__(self, database: AsyncIOMotorDatabase = db):
        self._coll = database.get_collection("users")

    # ---------------------------------------------------------
    # Basic CRUD
    # ---------------------------------------------------------

    async def save(self, user: User) -> str:
        """
        Insert a new User document.
        """
        doc = self._entity_to_doc(user)
        result = await self._coll.insert_one(doc)
        return str(result.inserted_id)

    async def update(self, user: User) -> None:
        """
        Update all fields of an existing User.
        """
        doc = self._entity_to_doc(user)
        await self._coll.update_one(
            {"_id": ObjectId(user.id)},
            {"$set": doc}
        )

    async def delete(self, user_id: str) -> None:
        """
        Delete a User by ID.
        """
        await self._coll.delete_one({"_id": ObjectId(user_id)})

    async def delete_all(self) -> int:
        """
        Delete all User documents.
        """
        res = await self._coll.delete_many({})
        return res.deleted_count

    # ---------------------------------------------------------
    # Retrieval operations
    # ---------------------------------------------------------

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve a User by its MongoDB _id.
        """
        doc = await self._coll.find_one({"_id": ObjectId(user_id)})
        return self._doc_to_entity(doc) if doc else None

    async def find_all(self) -> List[User]:
        """
        Retrieve all Users.
        """
        cursor = self._coll.find({})
        docs = await cursor.to_list(length=None)
        return [self._doc_to_entity(doc) for doc in docs]

    async def find_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a User by username.
        """
        doc = await self._coll.find_one({"username": username})
        return self._doc_to_entity(doc) if doc else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a User by email.
        Required for authentication.
        """
        doc = await self._coll.find_one({"email": email})
        return self._doc_to_entity(doc) if doc else None

    # ---------------------------------------------------------
    # Password operations
    # ---------------------------------------------------------

    async def update_password(self, user_id: str, hashed_password: str) -> None:
        """
        Update only the hashed password of a User.
        The repository NEVER hashes passwords; it only stores the hashed value.
        """
        await self._coll.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "hashedPassword": hashed_password,
                "updatedAt": datetime.utcnow()
            }}
        )

    # ---------------------------------------------------------
    # Twitter credentials
    # ---------------------------------------------------------

    async def update_twitter_credentials(self, user_id: str, creds: UserTwitterCredentials) -> None:
        """
        Update encrypted Twitter credentials for a User.
        """
        await self._coll.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "userTwitterCredentials": {
                    "oauth1AccessToken": encrypt_value(creds.oauth1_access_token) if creds.oauth1_access_token else None,
                    "oauth1AccessTokenSecret": encrypt_value(creds.oauth1_access_token_secret) if creds.oauth1_access_token_secret else None,
                    "oauth2AccessToken": encrypt_value(creds.oauth2_access_token) if creds.oauth2_access_token else None,
                    "oauth2AccessTokenExpiresAt": encrypt_value(creds.oauth2_access_token_expires_at) if creds.oauth2_access_token_expires_at else None,
                    "oauth2RefreshToken": encrypt_value(creds.oauth2_refresh_token) if creds.oauth2_refresh_token else None,
                    "oauth2RefreshTokenExpiresAt": encrypt_value(creds.oauth2_refresh_token_expires_at) if creds.oauth2_refresh_token_expires_at else None,
                    "screenName": creds.screen_name,
                },
                "updatedAt": datetime.utcnow()
            }}
        )

    # ---------------------------------------------------------
    # Mapping helpers
    # ---------------------------------------------------------

    def _doc_to_entity(self, doc: dict) -> User:
        """
        Convert a MongoDB document into a User domain entity.
        Handles decryption of Twitter credentials and nested structures.
        """

        creds = doc.get("userTwitterCredentials")
        twitter_creds = None
        if creds:
            twitter_creds = UserTwitterCredentials(
                oauth1_access_token=decrypt_value(creds.get("oauth1AccessToken")) if creds.get("oauth1AccessToken") else None,
                oauth1_access_token_secret=decrypt_value(creds.get("oauth1AccessTokenSecret")) if creds.get("oauth1AccessTokenSecret") else None,
                oauth2_access_token=decrypt_value(creds.get("oauth2AccessToken")) if creds.get("oauth2AccessToken") else None,
                oauth2_access_token_expires_at=decrypt_value(creds.get("oauth2AccessTokenExpiresAt")) if creds.get("oauth2AccessTokenExpiresAt") else None,
                oauth2_refresh_token=decrypt_value(creds.get("oauth2RefreshToken")) if creds.get("oauth2RefreshToken") else None,
                oauth2_refresh_token_expires_at=decrypt_value(creds.get("oauth2RefreshTokenExpiresAt")) if creds.get("oauth2RefreshTokenExpiresAt") else None,
                screen_name=creds.get("screenName"),
            )

        sc_doc = doc.get("schedulerConfig")
        scheduler_config = None
        if sc_doc:
            scheduler_config = SchedulerConfig(
                ingestion_pipeline_frequency_minutes=int(sc_doc.get("ingestionPipelineFrequencyMinutes", 1)),
                publishing_pipeline_frequency_minutes=int(sc_doc.get("publishingPipelineFrequencyMinutes", 10)),
                is_ingestion_pipeline_enabled=bool(sc_doc.get("isIngestionPipelineEnabled", True)),
                is_publishing_pipeline_enabled=bool(sc_doc.get("isPublishingPipelineEnabled", True)),
            )

        return User(
            id=str(doc["_id"]),
            username=doc["username"],
            email=doc.get("email"),
            hashed_password=doc.get("hashedPassword"),
            is_active=doc.get("isActive", True),
            openai_api_key=doc.get("openaiApiKey"),
            twitter_credentials=twitter_creds,
            scheduler_config=scheduler_config,
            max_tweets_to_fetch_from_db=doc.get("maxTweetsToFetchFromDB", 10),
            max_tweets_to_publish=doc.get("maxTweetsToPublish", 5),
            tweet_fetch_sort_order=TweetFetchSortOrder(doc["tweetFetchSortOrder"]) if doc.get("tweetFetchSortOrder") else None,
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _entity_to_doc(self, user: User) -> dict:
        """
        Convert a User domain entity into a MongoDB document.
        Handles encryption of Twitter credentials and nested structures.
        """
        doc: Dict[str, Any] = {
            "username": user.username,
            "email": user.email,
            "hashedPassword": user.hashed_password,
            "isActive": user.is_active,
            "openaiApiKey": user.openai_api_key,
            "userTwitterCredentials": {
                "oauth1AccessToken": encrypt_value(user.twitter_credentials.oauth1_access_token) if user.twitter_credentials and user.twitter_credentials.oauth1_access_token else None,
                "oauth1AccessTokenSecret": encrypt_value(user.twitter_credentials.oauth1_access_token_secret) if user.twitter_credentials and user.twitter_credentials.oauth1_access_token_secret else None,
                "oauth2AccessToken": encrypt_value(user.twitter_credentials.oauth2_access_token) if user.twitter_credentials and user.twitter_credentials.oauth2_access_token else None,
                "oauth2AccessTokenExpiresAt": encrypt_value(user.twitter_credentials.oauth2_access_token_expires_at) if user.twitter_credentials and user.twitter_credentials.oauth2_access_token_expires_at else None,
                "oauth2RefreshToken": encrypt_value(user.twitter_credentials.oauth2_refresh_token) if user.twitter_credentials and user.twitter_credentials.oauth2_refresh_token else None,
                "oauth2RefreshTokenExpiresAt": encrypt_value(user.twitter_credentials.oauth2_refresh_token_expires_at) if user.twitter_credentials and user.twitter_credentials.oauth2_refresh_token_expires_at else None,
                "screenName": user.twitter_credentials.screen_name if user.twitter_credentials else None,
            } if user.twitter_credentials else None,
            "schedulerConfig": {
                "ingestionPipelineFrequencyMinutes": user.scheduler_config.ingestion_pipeline_frequency_minutes,
                "publishingPipelineFrequencyMinutes": user.scheduler_config.publishing_pipeline_frequency_minutes,
                "isIngestionPipelineEnabled": user.scheduler_config.is_ingestion_pipeline_enabled,
                "isPublishingPipelineEnabled": user.scheduler_config.is_publishing_pipeline_enabled,
            } if user.scheduler_config else None,
            "maxTweetsToFetchFromDB": user.max_tweets_to_fetch_from_db,
            "maxTweetsToPublish": user.max_tweets_to_publish,
            "tweetFetchSortOrder": user.tweet_fetch_sort_order.value if user.tweet_fetch_sort_order else None,
            "createdAt": user.created_at,
            "updatedAt": user.updated_at,
        }

        # Remove None values to avoid storing nulls
        return {k: v for k, v in doc.items() if v is not None}
