from functools import lru_cache

from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings

from backend.config import get_settings
from backend.services.email_service import EmailService, MockEmailProvider
from backend.services.llm_service import LLMService
from backend.services.summary_service import SummaryService
from teams_bot.bot import FlowMateBot


@lru_cache
def get_summary_service() -> SummaryService:
    settings = get_settings()
    return SummaryService(
        email_service=EmailService(MockEmailProvider()),
        llm_service=LLMService(settings),
        settings=settings,
    )


@lru_cache
def get_bot() -> FlowMateBot:
    return FlowMateBot(get_summary_service())


@lru_cache
def get_bot_adapter() -> BotFrameworkAdapter:
    settings = get_settings()
    adapter_settings = BotFrameworkAdapterSettings(
        app_id=settings.microsoft_app_id,
        app_password=settings.microsoft_app_password,
        channel_auth_tenant=settings.microsoft_app_tenant_id or None,
    )
    return BotFrameworkAdapter(adapter_settings)

