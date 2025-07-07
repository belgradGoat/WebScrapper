"""
API v1 package for NotebookAI
Apple-inspired REST API architecture
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .upload import router as upload_router  
from .chat import router as chat_router
from .analytics import router as analytics_router
from .user import router as user_router

# Main API router with Apple-style organization
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    upload_router,
    prefix="/upload", 
    tags=["Upload"]
)

api_router.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics"]
)

api_router.include_router(
    user_router,
    prefix="/user",
    tags=["User"]
)

# Health check endpoint for the API
@api_router.get("/health", summary="API Health Check")
async def api_health():
    """API health check with Apple-style simplicity"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api": "NotebookAI v1",
        "message": "🍎 API is running smoothly"
    }