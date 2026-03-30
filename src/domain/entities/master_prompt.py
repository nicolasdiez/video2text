# src/domain/entities/master_prompt.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .user_prompt import PromptContent, TweetLengthPolicy


@dataclass(kw_only=True)
class MasterPrompt:
    """
    Domain entity representing a global (master) prompt configuration shared across all users.

    Mirrors the structure of the MongoDB collection master_prompts.
    
    It is not a complete usable prompt, because it lacks the language_to_generate_tweets and the tweet_length_policy, 
    which are mandatory fields of a valid and usable prompt.
    """

    id: Optional[str] = None                     # maps to _id / ObjectId
    category: str                                # e.g. "Finance", "Sports"
    subcategory: str                             # e.g. "Investing", "Futbol"

    prompt_content: PromptContent                # nested system + user messages

    language_of_the_prompt: str                  # ISO 639 language code
    # language_to_generate_tweets: str             # english + native name

    # tweet_length_policy: Optional[TweetLengthPolicy] = None  # optional

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
