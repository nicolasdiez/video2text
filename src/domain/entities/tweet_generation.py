# domain/entities/tweet_generation.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class OpenAIRequest:
    prompt: str
    model: str
    temperature: float
    max_tokens: int

@dataclass
class TweetGeneration:
    """
    Domain entity representing a tweet generation process (i.e. a call to OpenAI API to retrieve generated tweets=sentences)
    """
    id: Optional[str] = None
    user_id: str
    video_id: str                       # FK → videos._id
    openai_request: OpenAIRequest
    generated_at: datetime = field(default_factory=datetime.utcnow)
