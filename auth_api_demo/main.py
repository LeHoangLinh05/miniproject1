import logging
import time
import os

# Manual .env file loader
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("auth_api_demo")

# Import database engine and base
from .database import engine, Base
# Import models to ensure they are registered before create_all
from .models.user_model import User

# Initialize database tables
logger.info("Initializing database tables...")
Base.metadata.create_all(bind=engine)
logger.info("Database tables initialized successfully.")

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Auth & Activity Tracking API",
    description="A secure Web API with JWT Auth, SQLite, and online/offline status tracking.",
    version="1.0.0"
)

# Enable CORS for frontend integrations (e.g. Next.js in future weeks)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handlers for standard REST Responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "success": False}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation failure on {request.method} {request.url.path}")
    errors = [{"field": ".".join(map(str, err["loc"][1:])), "message": err["msg"]} for err in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed.",
            "errors": errors,
            "success": False
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "success": False
        }
    )

# Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Duration: {duration:.4f}s"
    )
    return response

# Import routers
from .routers import auth, users

# Register routers
app.include_router(auth.router)
app.include_router(users.router)

# Health Check Route
@app.get("/ping", response_class=PlainTextResponse)
def ping():
    """
    Simple health check route to verify environment.
    """
    return "pong"
