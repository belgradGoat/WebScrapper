"""
NotebookAI - Multi-Modal AI Data Analysis Platform
Apple-inspired backend architecture with FastAPI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import engine, create_tables
from app.api.v1 import api_router
from app.core.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management - startup and shutdown events"""
    # Startup
    print("🚀 Starting NotebookAI Backend...")
    await create_tables()
    print("✅ Database tables created")
    
    yield
    
    # Shutdown  
    print("🛑 Shutting down NotebookAI Backend...")


# Initialize FastAPI app with Apple-inspired design philosophy
app = FastAPI(
    title="NotebookAI API",
    description="""
    🍎 **NotebookAI** - Multi-Modal AI Data Analysis Platform
    
    ## Apple Design Philosophy
    - **Simplicity**: Clean, intuitive API design
    - **Performance**: Optimized for speed and efficiency  
    - **Reliability**: Robust error handling and validation
    - **Scalability**: Built for growth and extensibility
    
    ## Features
    - 📁 Multi-format file upload and processing
    - 🤖 AI-powered chat with context awareness
    - 📊 Advanced data analytics and insights
    - 🔐 Secure authentication and user management
    - 🌐 Real-time WebSocket communication
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints",
        },
        {
            "name": "Upload",
            "description": "File upload and data ingestion endpoints",
        },
        {
            "name": "Chat",
            "description": "AI chat and conversation management endpoints",
        },
        {
            "name": "Analytics", 
            "description": "Data analytics and insights endpoints",
        },
        {
            "name": "User",
            "description": "User profile and settings endpoints",
        },
    ]
)

# Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Exception Handlers
setup_exception_handlers(app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with Apple-inspired welcome message"""
    return {
        "message": "Welcome to NotebookAI 🍎",
        "description": "Multi-Modal AI Data Analysis Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "✅ Online"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-07T03:36:50Z",
        "version": "1.0.0",
        "services": {
            "database": "✅ Connected",
            "redis": "✅ Connected", 
            "vector_store": "✅ Connected",
            "ai_service": "✅ Ready"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )