from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.review import router as review_router
from app.database import Base, engine

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on startup (no-op if they already exist).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Code Reviewer",
    description="AI-powered code review and code analysis API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Auth"],
)
app.include_router(
    review_router,
    prefix="/api/v1/reviews",
    tags=["Reviews"],
)



@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-code-reviewer",
    }