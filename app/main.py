from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.review import router as review_router

load_dotenv()

app = FastAPI(
    title="AI Code Reviewer",
    description="AI-powered code review and code analysis API",
    version="0.1.0",
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