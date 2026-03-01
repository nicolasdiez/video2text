# src/api/schemas/master_prompt_dtos.py

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# -------------------------
# Nested DTOs
# -------------------------
class PromptContentDTO(BaseModel):
    system_message: str = Field(..., min_length=1)
    user_message: str = Field(..., min_length=1)


# -------------------------
# Main DTOs
# -------------------------
class MasterPromptCreateDTO(BaseModel):
    category: str
    subcategory: str
    prompt_content: PromptContentDTO
    language_of_the_prompt: str


class MasterPromptUpdateDTO(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    prompt_content: Optional[PromptContentDTO] = None
    language_of_the_prompt: Optional[str] = None


class MasterPromptResponseDTO(BaseModel):
    id: str
    category: str
    subcategory: str
    prompt_content: PromptContentDTO
    language_of_the_prompt: str
    created_at: datetime
    updated_at: datetime
