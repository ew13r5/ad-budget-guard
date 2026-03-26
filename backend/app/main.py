import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.config import get_settings
from app.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Start monitoring WebSocket pubsub subscriber
    from app.api.websocket_monitoring import monitoring_pubsub_subscriber
    settings = get_settings()
    monitoring_task = asyncio.create_task(
        monitoring_pubsub_subscriber(settings.redis_url)
    )
    yield
    monitoring_task.cancel()
    try:
        await monitoring_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Ad Budget Guard", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

from app.api.websocket_monitoring import ws_monitoring_router
app.include_router(ws_monitoring_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
