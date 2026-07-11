from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from botbuilder.core import BotFrameworkAdapter
from botbuilder.schema import Activity

from backend.dependencies import get_bot, get_bot_adapter, get_summary_service
from backend.models.schemas import AdaptiveCardResponse, TeamsMessageRequest
from backend.services.llm_service import LLMServiceError
from backend.services.summary_service import SummaryService
from teams_bot.bot import FlowMateBot
from teams_bot.cards.email_summary import build_email_summary_card

router = APIRouter(prefix="/api", tags=["teams"])


@router.post("/messages")
async def bot_messages(
    request: Request,
    adapter: BotFrameworkAdapter = Depends(get_bot_adapter),
    bot: FlowMateBot = Depends(get_bot),
):
    """Authenticated Bot Framework endpoint configured in Azure Bot."""
    if "application/json" not in request.headers.get("content-type", ""):
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")

    activity = Activity().deserialize(await request.json())
    auth_header = request.headers.get("authorization", "")
    invoke_response = await adapter.process_activity(activity, auth_header, bot.on_turn)
    if invoke_response:
        return JSONResponse(content=invoke_response.body, status_code=invoke_response.status)
    return Response(status_code=201)


@router.post("/teams/message", response_model=AdaptiveCardResponse)
async def simulate_teams_message(
    payload: TeamsMessageRequest,
    service: SummaryService = Depends(get_summary_service),
) -> AdaptiveCardResponse:
    """Local integration endpoint; the real Teams channel uses /api/messages."""
    text = payload.text.strip().lower()
    if "summar" not in text or ("email" not in text and "mail" not in text):
        raise HTTPException(status_code=400, detail="Supported command: summarize my emails")
    try:
        result = await service.generate_daily_summary()
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AdaptiveCardResponse(
        attachments=[
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": build_email_summary_card(result.summary, result.generated_by),
            }
        ]
    )
