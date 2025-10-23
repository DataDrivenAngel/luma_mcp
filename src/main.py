"""
LUMA MCP Server - FastAPI application for managing LUMA events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.config import settings, validate_api_key
from src.luma_client import LumaAPIError
from src.routes.events import router as events_router
from src.routes.templates import router as templates_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    if not validate_api_key():
        raise ValueError(
            "LUMA_API_KEY environment variable is required. "
            "Please set it in your environment or .env file."
        )

    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title="LUMA MCP Server",
    description="Model Context Protocol server for LUMA event management",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # No CORS in production - server should be accessed directly
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(events_router)
app.include_router(templates_router)


@app.get("/health", summary="Health Check")
async def health_check():
    """Check if the service is healthy and can connect to LUMA API."""
    try:
        # Test API connectivity by getting user info
        from src.luma_client import LumaClient
        client = LumaClient()
        await client.get_user_self()
        return {"status": "healthy", "message": "LUMA API connection successful"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.exception_handler(LumaAPIError)
async def luma_api_exception_handler(request: Request, exc: LumaAPIError):
    """Handle LUMA API errors."""
    return JSONResponse(
        status_code=exc.status_code or 500,
        content={
            "error": str(exc),
            "code": str(exc.status_code),
            "details": exc.response_data
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    # Don't expose internal error details in production
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


def main():
    """Main entry point for the LUMA MCP server."""
    # Validate configuration before starting
    if not validate_api_key():
        print("ERROR: LUMA_API_KEY environment variable is required.")
        print("Please set it in your environment or .env file.")
        exit(1)

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()