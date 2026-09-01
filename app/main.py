from fastapi import FastAPI

app=FastAPI(
    title = "AI code Reviewer",
    description= "AI-powered code review and code analysis API",
    version="0.1.0"
)

@app.get("/health")
async def health_check():
    return{
        "status":"healthy",
        "service":"ai-code-reviewer"
    }