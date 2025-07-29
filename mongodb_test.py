import sys
import asyncio
import threading

from infrastructure.mongodb import ping_mongo, db, _sync_client, _motor_client

def test_sync_ping():
    """
    Prueba síncrona usando PyMongo.
    Lanza excepción si algo falla.
    """
    ping_mongo()

async def test_async_list_collections():
    """
    Prueba asíncrona usando Motor.
    Lista las colecciones existentes.
    """
    names = await db.list_collection_names()
    print("✅ Colecciones encontradas:", names)

def main():
    try:
        # 1) Ping síncrono
        test_sync_ping()

        # 2) Ping asíncrono + listado
        asyncio.run(test_async_list_collections())

        print("🎉 Todas las pruebas de MongoDB pasaron correctamente.")
    except Exception as e:
        print("❌ Error en la prueba de MongoDB:", e)
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
