# src/api/dtos/master_prompt_dtos.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# -------------------------
# Nested DTOs
# -------------------------
class PromptContentDTO(BaseModel):
    system_message: str = Field(..., min_length=1)
    user_message: str = Field(..., min_length=1)


class TweetLengthPolicyDTO(BaseModel):
    mode: str = Field(..., pattern="^(fixed|range)$")
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    target_length: Optional[int] = None
    tolerance_percent: int = 10
    unit: str = Field(default="chars", pattern="^(chars|tokens)$")


# -------------------------
# Main DTOs
# -------------------------
class MasterPromptCreateDTO(BaseModel):
    category: str
    subcategory: str
    prompt_content: PromptContentDTO
    language_of_the_prompt: str
    language_to_generate_tweets: str
    tweet_length_policy: Optional[TweetLengthPolicyDTO] = None


class MasterPromptUpdateDTO(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    prompt_content: Optional[PromptContentDTO] = None
    language_of_the_prompt: Optional[str] = None
    language_to_generate_tweets: Optional[str] = None
    tweet_length_policy: Optional[TweetLengthPolicyDTO] = None


class MasterPromptResponseDTO(BaseModel):
    id: str
    category: str
    subcategory: str
    prompt_content: PromptContentDTO
    language_of_the_prompt: str
    language_to_generate_tweets: str
    tweet_length_policy: Optional[TweetLengthPolicyDTO]
    created_at: datetime
    updated_at: datetime
