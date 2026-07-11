import re

from botbuilder.core import ActivityHandler, CardFactory, MessageFactory, TurnContext

from backend.services.llm_service import LLMServiceError
from backend.services.summary_service import SummaryService
from teams_bot.cards.email_summary import build_email_summary_card


class FlowMateBot(ActivityHandler):
    def __init__(self, summary_service: SummaryService) -> None:
        self._summary_service = summary_service

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        TurnContext.remove_recipient_mention(turn_context.activity)
        text = re.sub(r"\s+", " ", turn_context.activity.text or "").strip().lower()

        if not self._is_summary_command(text):
            await turn_context.send_activity(
                MessageFactory.text(
                    "Try **summarize my emails** to generate today's AI email summary."
                )
            )
            return

        await turn_context.send_activity({"type": "typing"})
        try:
            result = await self._summary_service.generate_daily_summary()
        except LLMServiceError:
            await turn_context.send_activity(
                MessageFactory.text(
                    "I couldn't reach the configured AI model. Check the API endpoint, API key, "
                    "model name, and account balance, then try again."
                )
            )
            return

        card = build_email_summary_card(result.summary, result.generated_by)
        await turn_context.send_activity(
            MessageFactory.attachment(CardFactory.adaptive_card(card))
        )

    @staticmethod
    def _is_summary_command(text: str) -> bool:
        return "summar" in text and ("email" in text or "mail" in text)

    async def on_members_added_activity(self, members_added, turn_context: TurnContext) -> None:
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "Hi, I'm FlowMate. Ask me to **summarize my emails**."
                )
