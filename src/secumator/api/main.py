from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from secumator.core import settings, get_logger
from secumator.core.database import init_db
from .routes import scans, reports, health


logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_api", version=settings.app_version)
    await init_db()
    yield
    logger.info("shutting_down_api")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Professional security audit report generator with AI-powered analysis",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
