from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from backend.api.email import router as email_router
from backend.api.teams import router as teams_router
from backend.config import get_settings

app = FastAPI(
    title="FlowMate AI Prototype",
    description="Microsoft Teams bot backed by an OpenAI-compatible model API.",
    version="0.1.0",
)
app.include_router(email_router)
app.include_router(teams_router)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "teams_configured": str(bool(settings.microsoft_app_id)).lower(),
    }


@app.get("/privacy", response_class=PlainTextResponse, include_in_schema=False)
async def privacy() -> str:
    return "FlowMate Prototype uses messages only to generate the requested email summary."


@app.get("/terms", response_class=PlainTextResponse, include_in_schema=False)
async def terms() -> str:
    return "FlowMate Prototype is provided for internal demonstration purposes."
