# /src/main_simplified.py

import asyncio
import logging
import os
import threading
from datetime import datetime
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnostic")

# ============================================================
# LIFESPAN
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LIFESPAN START: PID=%s THREAD=%s", os.getpid(), threading.get_ident())

    loop = asyncio.get_running_loop()
    logger.info("LIFESPAN: Using event loop %s", loop)

    scheduler = AsyncIOScheduler(event_loop=loop)

    async def test_job():
        logger.info("JOB EXECUTED: PID=%s THREAD=%s TIME=%s",
                    os.getpid(), threading.get_ident(), datetime.utcnow().isoformat())

    logger.info("ADDING JOB…")
    scheduler.add_job(test_job, "interval", seconds=5, id="test_job")

    logger.info("STARTING SCHEDULER…")
    scheduler.start()

    logger.info("SCHEDULER STARTED OK")

    yield

    logger.info("LIFESPAN SHUTDOWN: leaving scheduler running intentionally")
    # scheduler.shutdown()  # NO shutdown here


# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "pid": os.getpid(), "thread": threading.get_ident()}


if __name__ == "__main__":
    # wrap ASGI server start-up under if __name__ == "__main__":, so the run doesnt double-execute
    uvicorn.run("main:app", host="0.0.0.0", port=8081)       # En PRO --> reload=False
