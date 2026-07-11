import json
import re

import httpx
from pydantic import ValidationError

from backend.config import Settings
from backend.models.schemas import Email, EmailSummary


class LLMServiceError(RuntimeError):
    pass


SYSTEM_PROMPT = """You are FlowMate AI, an enterprise workflow assistant.
Analyze the supplied emails and generate a concise daily summary.
Classify urgent, blocking, deadline-driven, or decision-related messages as important.
Put informational messages in normal.
Return JSON only, using this exact shape:
{
  "important": [{"subject": "", "summary": "", "action": ""}],
  "normal": [{"subject": "", "summary": "", "action": ""}]
}
Do not invent facts. Keep each summary and action to one sentence."""


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def summarize_emails(self, emails: list[Email]) -> EmailSummary:
        if not emails:
            return EmailSummary()

        headers = {"Content-Type": "application/json"}
        if self._settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self._settings.llm_api_key}"

        payload = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "Emails:\n" + json.dumps(
                        [email.model_dump(by_alias=True) for email in emails],
                        ensure_ascii=False,
                    ),
                },
            ],
            "temperature": self._settings.llm_temperature,
            "max_tokens": self._settings.llm_max_tokens,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.llm_timeout_seconds,
                verify=self._settings.llm_verify_tls,
                trust_env=self._settings.llm_trust_env_proxy,
            ) as client:
                response = await client.post(
                    self._settings.llm_chat_completions_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
            content = body["choices"][0]["message"]["content"]
            return EmailSummary.model_validate(self._parse_json(content))
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
            raise LLMServiceError(
                f"{self._settings.llm_display_name} request failed: {exc}"
            ) from exc

    @staticmethod
    def _parse_json(content: str | dict) -> dict:
        if isinstance(content, dict):
            return content
        cleaned = content.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
        if fenced:
            cleaned = fenced.group(1)
        return json.loads(cleaned)
