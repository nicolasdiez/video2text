# src/domain/entities/prompt.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(kw_only=True)
class PromptContent:
    """
    Nested content for the Prompt entity holding the system and user messages.
    """
    system_message: str
    user_message: str

@dataclass(kw_only=True)
class Prompt:
    """
    Domain entity representing a prompt configuration for tweet generation.
    """
    id: Optional[str] = None                # maps to _id / ObjectId
    user_id: str                            # FK → users._id
    channel_id: str                         # FK → channels._id
    prompt_content: PromptContent           # nested system + user messages
    language_of_the_prompt: str             # ISO 639-2 code
    language_to_generate_tweets: str        # ISO 639-2 code
    max_tweets_to_generate_per_video: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)