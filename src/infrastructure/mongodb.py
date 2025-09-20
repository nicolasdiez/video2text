# infrastructure/mongodb.py

import os
from datetime import datetime
import config

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi

# Build URIs
_BASE = f"mongodb+srv://{config.MONGO_USER}:{config.MONGO_PASSWORD}@{config.MONGO_HOST}/{config.MONGO_DB}"
URI_ASYNC = _BASE + "?retryWrites=true&w=majority"
URI_SYNC  = _BASE + "?retryWrites=true&w=majority"

# Async client (Motor)
_motor_client: AsyncIOMotorClient = AsyncIOMotorClient(URI_ASYNC)
db: AsyncIOMotorDatabase = _motor_client[config.MONGO_DB]

# Sync client for ping testing (PyMongo)
_sync_client = MongoClient(URI_SYNC, server_api=ServerApi("1"))

def ping_mongo() -> None:
    """
    Executes sync pinc to validate credentials and network connection. 
    Exception thrown if failure.
    """
    try:
        _sync_client.admin.command("ping")
        print("✅ Successfull ping to MongoDB Atlas")
    except errors.PyMongoError as e:
        print(f"❌ Ping failed: {e}")
        raise

# Uncomment following line to test ping when importing module:
# ping_mongo()