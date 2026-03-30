# src/domain/entities/tweet_generation.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from domain.entities.user_prompt import PromptContent

@dataclass
class OpenAIRequest:
    """
    Represents the payload sent to OpenAI. Uses PromptContent but the field is named
    prompy_content to match the renamed attribute in the Prompt entity and avoid confusion.
    """
    prompt_content: PromptContent
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

@dataclass(kw_only=True)
class TweetGeneration:
    """
    Domain entity representing a tweet generation process (i.e. a call to OpenAI API to retrieve generated tweets/ sentences)
    """
    id: Optional[str] = None
    user_id: str
    video_id: str                       # FK → videos._id
    openai_request: OpenAIRequest
    generated_at: datetime = field(default_factory=datetime.utcnow)