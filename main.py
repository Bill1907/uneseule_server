"""
Uneseule Backend - Main Application Entry Point

FastAPI application for AI Voice Agent smart toy backend.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.events import lifespan

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
)

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI Voice Agent Backend for Smart Toy System",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # Mount GraphQL endpoint
    from app.graphql.schema import create_graphql_router

    graphql_router = create_graphql_router()
    app.include_router(graphql_router, prefix="/graphql")

    # Register REST API routers
    from app.api.v1.device.router import router as device_router
    from app.api.v1.webhooks.elevenlabs import router as elevenlabs_webhook_router
    from app.api.v1.webhooks.payment import router as payment_webhook_router

    app.include_router(device_router, prefix="/api/v1")
    app.include_router(elevenlabs_webhook_router)
    app.include_router(payment_webhook_router)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return JSONResponse(
            content={
                "status": "healthy",
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
            }
        )

    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return JSONResponse(
            content={
                "message": f"Welcome to {settings.APP_NAME}",
                "version": settings.APP_VERSION,
                "docs": "/docs" if settings.DEBUG else "Documentation disabled",
            }
        )

    return app


# Create FastAPI application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
