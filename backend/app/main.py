"""FastAPI application assembly for IssuePilot."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import initialize_database
from app.routes.issues import router as issues_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize local persistence before serving requests."""

    initialize_database()
    yield


app = FastAPI(title="IssuePilot API", version="0.1.0", lifespan=lifespan)
app.include_router(issues_router)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    """Hide internal details while preserving a useful server-side log."""

    logger.exception(
        "Unhandled error while processing %s", request.url.path, exc_info=error
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
