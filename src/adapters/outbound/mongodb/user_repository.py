# adapters/outbound/mongo/user_repository.py

from datetime import datetime
from typing import Optional, List, Dict, Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.user import User, TwitterCredentials, TweetFetchSortOrder
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
    
    async def find_all(self) -> List[Dict[str, Any]]:
        cursor = self._coll.find({})
        return await cursor.to_list(length=None)

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

    async def update_twitter_credentials(self, user_id: str, creds: TwitterCredentials) -> None:
        await self._coll.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "twitterCredentials": {
                    "apiKey": encrypt_value(creds.api_key),
                    "apiSecret": encrypt_value(creds.api_secret),
                    "accessToken": encrypt_value(creds.access_token),
                    "accessTokenSecret": encrypt_value(creds.access_token_secret),
                    "bearerToken": encrypt_value(creds.bearer_token),
                    "oauth2ClientId": encrypt_value(creds.oauth2_client_id),
                    "oauth2ClientSecret": encrypt_value(creds.oauth2_client_secret),
                    "screenName": creds.screen_name,
                },
                "updatedAt": datetime.utcnow()
            }}
        )

    def _doc_to_entity(self, doc: dict) -> User:
        creds = doc.get("twitterCredentials")
        twitter = None
        if creds:
            twitter = TwitterCredentials(
                api_key=decrypt_value(creds.get("apiKey")) if creds.get("apiKey") else "",
                api_secret=decrypt_value(creds.get("apiSecret")) if creds.get("apiSecret") else "",
                access_token=decrypt_value(creds.get("accessToken")) if creds.get("accessToken") else "",
                access_token_secret=decrypt_value(creds.get("accessTokenSecret")) if creds.get("accessTokenSecret") else "",
                bearer_token=decrypt_value(creds.get("bearerToken")) if creds.get("bearerToken") else "",
                oauth2_client_id=decrypt_value(creds.get("oauth2ClientId")) if creds.get("oauth2ClientId") else "",
                oauth2_client_secret=decrypt_value(creds.get("oauth2ClientSecret")) if creds.get("oauth2ClientSecret") else "",
                refresh_token=decrypt_value(creds.get("refreshToken")) if creds.get("refreshToken") else None,      # For future OAuth2.0
                refresh_token_expires_at=creds.get("refreshTokenExpiresAt"),                                        # For future OAuth2.0
                screen_name=creds.get("screenName")
            )

        return User(
      id=str(doc["_id"]),
            username=doc["username"],
            openai_api_key=doc.get("openaiApiKey"),
            twitter_credentials=twitter,
            ingestion_polling_interval=doc.get("ingestionPollingInterval"),
            publishing_polling_interval=doc.get("publishingPollingInterval"),
            max_tweets_to_fetch=doc.get("maxTweetsToFetch"),
            max_tweets_to_publish=doc.get("maxTweetsToPublish"),
            tweet_fetch_sort_order=TweetFetchSortOrder(doc["tweetFetchSortOrder"]) if doc.get("tweetFetchSortOrder") else None,
            created_at=doc.get("createdAt", datetime.utcnow()),
            updated_at=doc.get("updatedAt", datetime.utcnow())
        )

    def _entity_to_doc(self, user: User) -> dict:
        doc = {
            "username": user.username,
            "openaiApiKey": user.openai_api_key,
            "twitterCredentials": {
                "apiKey": encrypt_value(user.twitter_credentials.api_key),
                "apiSecret": encrypt_value(user.twitter_credentials.api_secret),
                "accessToken": encrypt_value(user.twitter_credentials.access_token),
                "accessTokenSecret": encrypt_value(user.twitter_credentials.access_token_secret),
                "bearerToken": encrypt_value(user.twitter_credentials.bearer_token),
                "oauth2ClientId": encrypt_value(user.twitter_credentials.oauth2_client_id),
                "oauth2ClientSecret": encrypt_value(user.twitter_credentials.oauth2_client_secret),
                "refreshToken": encrypt_value(user.twitter_credentials.refresh_token) if user.twitter_credentials.refresh_token else None,  # For future OAuth2.0
                "refreshTokenExpiresAt": user.twitter_credentials.refresh_token_expires_at,                                                 # For future OAuth2.0
                "screenName": user.twitter_credentials.screen_name,
            } if user.twitter_credentials else None,
            "ingestionPollingInterval": user.ingestion_polling_interval,
            "publishingPollingInterval": user.publishing_polling_interval,
            "maxTweetsToFetch": user.max_tweets_to_fetch,
            "maxTweetsToPublish": user.max_tweets_to_publish,
            "tweetFetchSortOrder": user.tweet_fetch_sort_order.value if user.tweet_fetch_sort_order else None,
            "createdAt": user.created_at,
            "updatedAt": user.updated_at,
        }
        return {k: v for k, v in doc.items() if v is not None}
