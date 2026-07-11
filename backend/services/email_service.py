import json
from abc import ABC, abstractmethod
from pathlib import Path

from backend.models.schemas import Email


class EmailProvider(ABC):
    @abstractmethod
    async def get_unread_emails(self) -> list[Email]:
        """Return unread emails from the provider."""


class MockEmailProvider(EmailProvider):
    def __init__(self, data_path: Path | None = None) -> None:
        self._data_path = data_path or Path(__file__).parents[1] / "data" / "emails.json"

    async def get_unread_emails(self) -> list[Email]:
        raw = json.loads(self._data_path.read_text(encoding="utf-8"))
        return [Email.model_validate(item) for item in raw]


class EmailService:
    def __init__(self, provider: EmailProvider) -> None:
        self._provider = provider

    async def get_unread_emails(self) -> list[Email]:
        return await self._provider.get_unread_emails()

