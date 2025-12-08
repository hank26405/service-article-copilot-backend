"""Prompt models for the API."""

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    """Prompt model for update requests."""
    content: str = Field(..., min_length=1, description="The new content of the prompt")
