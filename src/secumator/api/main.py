from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from secumator.core import settings, get_logger, scan_queue
from secumator.core.database import init_db
from .routes import scans, reports, health, queue, templates, correlation


logger = get_logger("api")


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())[:8]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
