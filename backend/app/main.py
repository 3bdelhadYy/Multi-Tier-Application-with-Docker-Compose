import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import wait_for_db, init_db
from app.routes import router

logger = logging.getLogger("course_reg_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    # Do not wait for Postgres if explicitly running standalone unit tests
    if not os.getenv("SKIP_DB_INIT", "").lower() in ("true", "1", "yes"):
        try:
            wait_for_db()
            init_db()
        except Exception as e:
            logger.error("Startup database initialization failed: %s", e)
            # Re-raise to prevent starting an unhealthy backend
            raise e
    yield
    logger.info("Application shutting down...")

app = FastAPI(
    title="Student Course Registration API",
    description="Backend API for Lab 4 Part 2 - Student Course Registration System",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "message": "Student Course Registration API is running.",
        "documentation": "/docs",
        "health": "/api/health"
    }
