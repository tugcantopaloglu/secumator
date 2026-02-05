from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from secumator.core import settings, get_logger, scan_queue
from secumator.core.database import init_db
from secumator.core.rate_limiter import RateLimiter, RateLimitExceeded
from .routes import scans, reports, health, queue, templates, correlation, websocket, github, ai, stats


logger = get_logger("api")
rate_limiter = RateLimiter(requests_per_minute=settings.api_rate_limit_per_minute, burst=settings.api_rate_limit_burst)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_api", version=settings.app_version)
    await init_db()
    await scan_queue.start_processing()
    yield
    await scan_queue.stop_processing()
    logger.info("shutting_down_api")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Professional security audit report generator with AI-powered analysis",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "Health check endpoints"},
        {"name": "Scans", "description": "Security scan operations"},
        {"name": "Reports", "description": "Report generation and download"},
        {"name": "Queue", "description": "Scan queue management"},
        {"name": "Templates", "description": "Scan template management"},
        {"name": "Correlation", "description": "Vulnerability correlation and CVE lookup"},
        {"name": "GitHub", "description": "GitHub integration"},
        {"name": "AI", "description": "AI-powered analysis"},
        {"name": "Stats", "description": "Dashboard statistics"},
        {"name": "WebSocket", "description": "Real-time updates"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(scans.router, prefix=settings.api_prefix, tags=["Scans"])
app.include_router(reports.router, prefix=settings.api_prefix, tags=["Reports"])
app.include_router(queue.router, prefix=settings.api_prefix, tags=["Queue"])
app.include_router(templates.router, prefix=settings.api_prefix, tags=["Templates"])
app.include_router(correlation.router, prefix=settings.api_prefix, tags=["Correlation"])
app.include_router(github.router, prefix=settings.api_prefix, tags=["GitHub"])
app.include_router(ai.router, prefix=settings.api_prefix, tags=["AI"])
app.include_router(stats.router, prefix=settings.api_prefix, tags=["Stats"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())[:8]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/ws"):
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key")
    identifier = api_key or client_ip
    
    if not await rate_limiter.is_allowed(identifier):
        raise RateLimitExceeded(retry_after=60)
    
    return await call_next(request)
