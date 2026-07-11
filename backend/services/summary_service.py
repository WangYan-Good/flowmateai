from backend.config import Settings
from backend.models.schemas import EmailSummary, SummaryItem, SummaryResponse
from backend.services.email_service import EmailService
from backend.services.llm_service import LLMService, LLMServiceError


class SummaryService:
    def __init__(
        self,
        email_service: EmailService,
        llm_service: LLMService,
        settings: Settings,
    ) -> None:
        self._email_service = email_service
        self._llm_service = llm_service
        self._settings = settings

    async def generate_daily_summary(self) -> SummaryResponse:
        emails = await self._email_service.get_unread_emails()
        try:
            summary = await self._llm_service.summarize_emails(emails)
            generated_by = self._settings.llm_display_name
        except LLMServiceError:
            if not self._settings.allow_demo_fallback:
                raise
            summary = self._fallback_summary(emails)
            generated_by = "demo-fallback"
        return SummaryResponse(summary=summary, generated_by=generated_by)

    @staticmethod
    def _fallback_summary(emails) -> EmailSummary:
        items = [
            SummaryItem(subject=email.subject, summary=email.body, action="Review this email.")
            for email in emails
        ]
        return EmailSummary(important=items, normal=[])
