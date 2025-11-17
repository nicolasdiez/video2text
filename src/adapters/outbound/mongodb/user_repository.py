# adapters/outbound/mongo/user_repository.py

from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.user import User, UserTwitterCredentials, TweetFetchSortOrder
from domain.ports.outbound.mongodb.user_repository_port import UserRepositoryPort
from infrastructure.mongodb import db

from infrastructure.security.encription import encrypt_value, decrypt_value


class MongoUserRepository(UserRepositoryPort):
    def __init__(self, database: AsyncIOMotorDatabase = db):
        self._coll = database.get_collection("users")

    async def save(self, user: User) -> str:
        doc = self._entity_to_doc(user)
        result = await self._coll.insert_one(doc)
        return str(result.inserted_id)

    async def find_by_id(self, user_id: str) -> Optional[User]:
        doc = await self._coll.find_one({"_id": ObjectId(user_id)})
        return self._doc_to_entity(doc) if doc else None
    
    async def find_all(self) -> List[User]:
        cursor = self._coll.find({})
        docs = await cursor.to_list(length=None)
        return [self._doc_to_entity(doc) for doc in docs]

    async def find_by_username(self, username: str) -> Optional[User]:
        doc = await self._coll.find_one({"username": username})
        return self._doc_to_entity(doc) if doc else None

    async def update(self, user: User) -> None:
        doc = self._entity_to_doc(user)
        await self._coll.update_one(
            {"_id": ObjectId(user.id)},
            {"$set": doc}
        )

    async def delete(self, user_id: str) -> None:
        await self._coll.delete_one({"_id": ObjectId(user_id)})

    async def delete_all(self) -> int:
        res = await self._coll.delete_many({})
        return res.deleted_count

    async def update_twitter_credentials(self, user_id: str, creds: UserTwitterCredentials) -> None:
        await self._coll.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "UserTwitterCredentials": {
                    "oauth1AccessToken": encrypt_value(creds.oauth1_access_token),
                    "oauth1AccessTokenSecret": encrypt_value(creds.oauth1_access_token_secret),
                    "oauth2AccessToken": encrypt_value(creds.oauth2_access_token),
                    "oauth2AccessTokenExpiresAt": encrypt_value(creds.oauth2_access_token_expires_at),
                    "oauth2RefreshToken": encrypt_value(creds.oauth2_refresh_token),
                    "oauth2RefreshTokenExpiresAt": encrypt_value(creds.oauth2_refresh_token_expires_at),
                    "screenName": creds.screen_name,
                },
                "updatedAt": datetime.utcnow()
            }}
        )

    def _doc_to_entity(self, doc: dict) -> User:
        creds = doc.get("UserTwitterCredentials")
        twitter = None
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

        return User(
      id=str(doc["_id"]),
            username=doc["username"],
            openai_api_key=doc.get("openaiApiKey"),
            twitter_credentials=twitter_creds,
            ingestion_polling_interval=doc.get("ingestionPollingInterval"),
            publishing_polling_interval=doc.get("publishingPollingInterval"),
            max_tweets_to_fetch_from_db=doc.get("maxTweetsToFetchFromDB"),
            max_tweets_to_publish=doc.get("maxTweetsToPublish"),
            tweet_fetch_sort_order=TweetFetchSortOrder(doc["tweetFetchSortOrder"]) if doc.get("tweetFetchSortOrder") else None,
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _entity_to_doc(self, user: User) -> dict:
        doc = {
            "username": user.username,
            "openaiApiKey": user.openai_api_key,
                "UserTwitterCredentials": {
                "oauth1AccessToken": encrypt_value(user.twitter_credentials.oauth1_access_token) if user.twitter_credentials.oauth1_access_token else None,
                "oauth1AccessTokenSecret": encrypt_value(user.twitter_credentials.oauth1_access_token_secret) if user.twitter_credentials.oauth1_access_token_secret else None,
                "oauth2AccessToken": encrypt_value(user.twitter_credentials.oauth2_access_token) if user.twitter_credentials.oauth2_access_token else None,
                "oauth2AccessTokenExpiresAt": encrypt_value(user.twitter_credentials.oauth2_access_token_expires_at) if user.twitter_credentials.oauth2_access_token_expires_at else None,
                "oauth2RefreshToken": encrypt_value(user.twitter_credentials.oauth2_refresh_token) if user.twitter_credentials.oauth2_refresh_token else None,
                "oauth2RefreshTokenExpiresAt": encrypt_value(user.twitter_credentials.oauth2_refresh_token_expires_at) if user.twitter_credentials.oauth2_refresh_token_expires_at else None,
                "screenName": user.twitter_credentials.screen_name,
            } if user.twitter_credentials else None,
            "ingestionPollingInterval": user.ingestion_polling_interval,
            "publishingPollingInterval": user.publishing_polling_interval,
            "maxTweetsToFetchFromDB": user.max_tweets_to_fetch_from_db,
            "maxTweetsToPublish": user.max_tweets_to_publish,
            "tweetFetchSortOrder": user.tweet_fetch_sort_order.value if user.tweet_fetch_sort_order else None,
            "createdAt": user.created_at,
            "updatedAt": user.updated_at,
        }
        return {k: v for k, v in doc.items() if v is not None}
