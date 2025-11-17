# utils/seed_master_data_mongodb.py

# Usage: 
# cd /d/software_projects/video2text
# PYTHONPATH="$PWD/src" SEED_CLEAN_USERS=true SEED_CLEAN_CHANNELS=true SEED_CLEAN_PROMPTS=true SEED_CLEAN_CONFIG=false python src/utils/seed_master_data_mongodb.py

import asyncio
import os
from datetime import datetime
from bson import ObjectId

# reuse existing async db instance
from infrastructure.mongodb import db  # AsyncIOMotorDatabase

# IMPORTA repos/adapters solo para app_config fallback
from adapters.outbound.mongodb.app_config_repository import MongoAppConfigRepository

# Flags (env vars "1"/"true" to enable)
CLEAN_USERS = os.getenv("SEED_CLEAN_USERS", "false").lower() in ("1", "true", "yes")
CLEAN_CHANNELS = os.getenv("SEED_CLEAN_CHANNELS", "false").lower() in ("1", "true", "yes")
CLEAN_PROMPTS = os.getenv("SEED_CLEAN_PROMPTS", "false").lower() in ("1", "true", "yes")
CLEAN_CONFIG = os.getenv("SEED_CLEAN_CONFIG", "false").lower() in ("1", "true", "yes")

# Import domain entities for AppConfig usage
from domain.entities.app_config import AppConfig, SchedulerConfig

def ms_to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000.0)

async def seed():
    print("Seeding data to MongoDB starting.")

    # Optional cleaning using direct collection clears (we operate directly here)
    if CLEAN_USERS:
        await db.get_collection("users").delete_many({})
        print("[ok] cleaned users")
    if CLEAN_CHANNELS:
        await db.get_collection("channels").delete_many({})
        print("[ok] cleaned channels")
    if CLEAN_PROMPTS:
        await db.get_collection("prompts").delete_many({})
        print("[ok] cleaned prompts")
    if CLEAN_CONFIG:
        await db.get_collection("app_config").delete_many({})
        print("[ok] cleaned app_config")

    # -----------------------
    # 1) User with _id = 1 (integer)
    # -----------------------
    user_doc = {
        "_id": 1,
        "username": "nico_seed@ejemplo.com",
        "openaiApiKey": "",
        "UserTwitterCredentials": {
            "oauth1AccessToken": "",
            "oauth1AccessTokenSecret": "",
            "oauth2AccessToken": "",
            "oauth2AccessTokenExpiresAt": "",
            "oauth2RefreshToken": "",
            "oauth2RefreshTokenExpiresAt": "",
            "screenName": "nicolai"
        },
        "ingestionPollingInterval": 1,
        "publishingPollingInterval": 2,
        "maxTweetsToFetchFromDB": 4,
        "maxTweetsToPublish": 2,
        "tweetFetchSortOrder": "random",
        "createdAt": ms_to_dt(1756412100000),
        "updatedAt": ms_to_dt(1763205251652)
    }
    await db.get_collection("users").replace_one({"_id": user_doc["_id"]}, user_doc, upsert=True)
    print("[ok] user upserted with _id=1")

    # -----------------------
    # 2) Channel referencing userId = 1
    # -----------------------
    channel_id = ObjectId("68c42891474831a97800f02f")
    channel_doc = {
        "_id": channel_id,
        "userId": 1,  # reference to master user with _id = 1
        "youtubeChannelId": "UCvSXMi2LebwJEM1s4bz5IBA",
        "title": "@NewMoneyYouTube",
        "pollingInterval": 18,
        "maxVideosToFetchFromChannel": 1,
        "lastPolledAt": None,
        "createdAt": ms_to_dt(1756157820000),
        "updatedAt": ms_to_dt(1756157820000)
    }
    await db.get_collection("channels").replace_one({"_id": channel_doc["_id"]}, channel_doc, upsert=True)
    print(f"[ok] channel upserted with _id={channel_id}")

    # -----------------------
    # 3) Prompt referencing userId = 1 and channelId above
    # -----------------------
    prompt_doc = {
        # let Mongo generate _id if you prefer; or set one explicitly:
        "_id": ObjectId(), 
        "userId": 1,  # reference to master user
        "channelId": channel_id,
        "prompt": {
            "systemMessage": "",
            "userMessage": ""
        },
        "languageOfThePrompt": "",
        "languageToGenerateTweets": "",
        "maxTweetsToGeneratePerVideo": 0,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    await db.get_collection("prompts").replace_one(
        {"userId": prompt_doc["userId"], "channelId": prompt_doc["channelId"]},
        prompt_doc,
        upsert=True
    )
    print(f"[ok] prompt upserted referencing userId=1 and channelId={channel_id}")

    # -----------------------
    # 4) App config document (root) - via repo if available, fallback to direct upsert
    # -----------------------
    scheduler = SchedulerConfig(ingestion_minutes=4, publishing_minutes=10)
    app_config = AppConfig(scheduler=scheduler)
    app_config_repo = MongoAppConfigRepository(db)
    try:
        await app_config_repo.update_config(app_config)
        print("[ok] app config updated via repo")
    except AttributeError:
        # fallback direct write
        await db.get_collection("app_config").replace_one(
            {"_id": "global"},
            {"_id": "global", "scheduler": {"ingestionMinutes": 4, "publishingMinutes": 10}},
            upsert=True
        )
        print("[ok] app config upserted directly")

    print("Seeding data to MongoDB finished.")

if __name__ == "__main__":
    asyncio.run(seed())
