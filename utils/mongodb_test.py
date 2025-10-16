# IMPORTANT!!!:
# this is a snippet code, NOT part of the application code base.
# What´s this script used for? --> to validate that mongoDB works properly

import sys
import asyncio
import threading

# logging
import logging 
import inspect  

from src.infrastructure.mongodb import ping_mongo, db, _sync_client, _motor_client

# Specific logger for this module
logger = logging.getLogger(__name__)

def test_sync_ping():
    """
    Prueba síncrona usando PyMongo. Lanza excepción si algo falla.
    """
    ping_mongo()

async def test_async_list_collections():
    """
    Prueba asíncrona usando Motor. Lista las colecciones existentes.
    """
    names = await db.list_collection_names()
    # print("✅ Colecciones encontradas:", names)
    logger.info("✅ Collections found: %s", names, extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})


def main():
    try:
        # 1) Ping síncrono
        test_sync_ping()

        # 2) Ping asíncrono + listado
        asyncio.run(test_async_list_collections())

        logger.info("🎉 All MongoDB tests passed successfully!", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    except Exception as e:
        logger.info("❌ Error ni MongoDB test: %s", e, extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
        sys.exit(1)
    finally:
        # 3) Cerramos clientes para evitar hilos colgando
        _sync_client.close()
        _motor_client.close()
         # Limpiar hilos dummy antes del teardown de Python
        try:
            threading._shutdown()
        except Exception:
            pass

    sys.exit(0)

if __name__ == "__main__":
    main()
