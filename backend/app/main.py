import asyncio
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from sqlalchemy import text
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import api_router
from app.config import get_settings
from app.logging import setup_logging

logger = structlog.get_logger(__name__)

# Track app start time for uptime calculation
_app_start_time: float = 0.0

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _app_start_time
    _app_start_time = time.time()

    setup_logging()

    # Sentry SDK init
    settings = get_settings()
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    # Start monitoring WebSocket pubsub subscriber
    from app.api.websocket_monitoring import monitoring_pubsub_subscriber
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

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — tightened
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    max_age=600,
)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# Request ID + logging middleware
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start) * 1000, 1)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response


app.add_middleware(RequestIdMiddleware)


# Routes
app.include_router(api_router, prefix="/api")

from app.api.websocket_monitoring import ws_monitoring_router
app.include_router(ws_monitoring_router)


# Enhanced health check
@app.get("/health")
async def health_check():
    global _app_start_time
    services = {}

    # Database check
    try:
        from app.database import get_async_engine
        engine = get_async_engine()
        start = time.time()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = round((time.time() - start) * 1000, 1)
        services["database"] = {"status": "ok", "latency_ms": latency}
    except Exception as e:
        services["database"] = {"status": "error", "error": str(e)[:100]}

    # Redis check
    try:
        import redis as sync_redis
        start = time.time()
        r = sync_redis.from_url(settings.redis_url)
        r.ping()
        latency = round((time.time() - start) * 1000, 1)
        services["redis"] = {"status": "ok", "latency_ms": latency}
    except Exception as e:
        services["redis"] = {"status": "error", "error": str(e)[:100]}

    overall = "ok" if all(s.get("status") == "ok" for s in services.values()) else "degraded"
    uptime = round(time.time() - _app_start_time) if _app_start_time else 0

    return {
        "status": overall,
        "services": services,
        "version": "1.0.0",
        "uptime_seconds": uptime,
    }
