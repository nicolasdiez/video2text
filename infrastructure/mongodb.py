# infrastructure/mongodb.py

import os
from datetime import datetime
from dotenv import load_dotenv

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient, errors
from pymongo.server_api import ServerApi

# 1) Cargar variables de entorno
load_dotenv()  
MONGO_USER     = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST     = os.getenv("MONGO_HOST")
MONGO_DB       = os.getenv("MONGO_DB")

if not (MONGO_USER and MONGO_PASSWORD and MONGO_DB):
    raise RuntimeError("Faltan credenciales de Mongo en variables de entorno")

# 2) Construir URIs
_BASE = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/{MONGO_DB}"
URI_ASYNC = _BASE + "?retryWrites=true&w=majority"
URI_SYNC  = _BASE + "?retryWrites=true&w=majority"

# 3) Cliente async (Motor)
_motor_client: AsyncIOMotorClient = AsyncIOMotorClient(URI_ASYNC)
db: AsyncIOMotorDatabase = _motor_client[MONGO_DB]

# 4) Cliente sync para ping de prueba (PyMongo)
_sync_client = MongoClient(URI_SYNC, server_api=ServerApi("1"))

def ping_mongo() -> None:
    """
    Ejecuta un ping sincrónico para verificar credenciales y red.
    Lanza excepción si falla.
    """
    try:
        _sync_client.admin.command("ping")
        print("✅ Ping exitoso a MongoDB Atlas")
    except errors.PyMongoError as e:
        print(f"❌ Ping fallido: {e}")
        raise

# descomentar la siguiente línea para testear al importar:
# ping_mongo()