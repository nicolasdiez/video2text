# src/infrastructure/mongodb.py

import os
from datetime import datetime
import config

# logging
import inspect
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi

# Specific logger for this module
logger = logging.getLogger(__name__)

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
        logger.info("✅ Successfull ping to MongoDB Atlas", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    except errors.PyMongoError as e:
        logger.info("❌ Ping failed: %s", e, extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
        raise

# Uncomment following line to test ping when importing module:
ping_mongo()

# Log database name and existing collections (synchronous call via pymongo client)
try:
    _sync_db = _sync_client[config.MONGO_DB]
    collections = _sync_db.list_collection_names()
    logger.info("Database name: %s", config.MONGO_DB, extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    logger.info("Collections found: %s", ", ".join(collections) if collections else "(none)", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
except Exception as e:
    logger.warning("Could not list collections: %s", e, extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
