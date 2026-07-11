from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_summary_service
from backend.models.schemas import SummaryResponse
from backend.services.llm_service import LLMServiceError
from backend.services.summary_service import SummaryService

router = APIRouter(prefix="/api/email", tags=["email"])


@router.post("/summary", response_model=SummaryResponse)
async def summarize_email(
    service: SummaryService = Depends(get_summary_service),
) -> SummaryResponse:
    try:
        return await service.generate_daily_summary()
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

