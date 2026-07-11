from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Email(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    sender: str = Field(alias="from")
    subject: str
    body: str


class SummaryItem(BaseModel):
    subject: str
    summary: str
    action: str = ""


class EmailSummary(BaseModel):
    important: list[SummaryItem] = Field(default_factory=list)
    normal: list[SummaryItem] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    summary: EmailSummary
    generated_by: str


class TeamsMessageRequest(BaseModel):
    text: str


class AdaptiveCardResponse(BaseModel):
    type: str = "message"
    attachments: list[dict[str, Any]]

