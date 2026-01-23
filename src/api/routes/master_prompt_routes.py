# src/api/routes/master_prompt_routes.py

# Important Reminder:
# consumo: Routes → Application Services (business logic) → Repositorios (puertos de salida) → Mongo / Infraestructura

# Important Keep in Mind:
# Routes no deben llamar repos directamente (te saltarias la capa business)
# Routes solo orquestan: 1-validan entrada (DTOs) 2-llaman application services 3-devuelven DTOs de salida

from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from api.dtos.master_prompt_dtos import (
    MasterPromptCreateDTO,
    MasterPromptUpdateDTO,
    MasterPromptResponseDTO,
    PromptContentDTO,
    TweetLengthPolicyDTO,
)
from application.services.master_prompt_service import MasterPromptService
from domain.entities.master_prompt import MasterPrompt
from domain.entities.prompt import PromptContent, TweetLengthPolicy

from main import master_prompt_service


router = APIRouter(prefix="/master-prompts", tags=["Master Prompts"])


# -------------------------
# Mappers DTO ↔ Domain
# -------------------------
def dto_to_entity_create(dto: MasterPromptCreateDTO) -> MasterPrompt:
    return MasterPrompt(
        category=dto.category,
        subcategory=dto.subcategory,
        prompt_content=PromptContent(
            system_message=dto.prompt_content.system_message,
            user_message=dto.prompt_content.user_message,
        ),
        language_of_the_prompt=dto.language_of_the_prompt,
        language_to_generate_tweets=dto.language_to_generate_tweets,
        max_tweets_to_generate_per_video=dto.max_tweets_to_generate_per_video,
        tweet_length_policy=(
            TweetLengthPolicy(
                mode=dto.tweet_length_policy.mode,
                min_length=dto.tweet_length_policy.min_length,
                max_length=dto.tweet_length_policy.max_length,
                target_length=dto.tweet_length_policy.target_length,
                tolerance_percent=dto.tweet_length_policy.tolerance_percent,
                unit=dto.tweet_length_policy.unit,
            )
            if dto.tweet_length_policy
            else None
        ),
    )


def entity_to_response_dto(entity: MasterPrompt) -> MasterPromptResponseDTO:
    return MasterPromptResponseDTO(
        id=entity.id,
        category=entity.category,
        subcategory=entity.subcategory,
        prompt_content=PromptContentDTO(
            system_message=entity.prompt_content.system_message,
            user_message=entity.prompt_content.user_message,
        ),
        language_of_the_prompt=entity.language_of_the_prompt,
        language_to_generate_tweets=entity.language_to_generate_tweets,
        max_tweets_to_generate_per_video=entity.max_tweets_to_generate_per_video,
        tweet_length_policy=(
            TweetLengthPolicyDTO(
                mode=entity.tweet_length_policy.mode,
                min_length=entity.tweet_length_policy.min_length,
                max_length=entity.tweet_length_policy.max_length,
                target_length=entity.tweet_length_policy.target_length,
                tolerance_percent=entity.tweet_length_policy.tolerance_percent,
                unit=entity.tweet_length_policy.unit,
            )
            if entity.tweet_length_policy
            else None
        ),
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


# -------------------------
# Dependency wiring
# -------------------------
def get_master_prompt_service() -> MasterPromptService:
    # This function wires the service with its MongoDB repository.
    # This dependency shall be injected from main.py.
    return master_prompt_service


# -------------------------
# Routes
# -------------------------

# Create a new master prompt
# This endpoint allows clients to create a global prompt template
# that can be used by any user/channel in the system.
@router.post(
    "/",
    response_model=MasterPromptResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_master_prompt(
    payload: MasterPromptCreateDTO,
    service: MasterPromptService = Depends(get_master_prompt_service),
):
    entity = dto_to_entity_create(payload)
    created = await service.create_master_prompt(entity)
    return entity_to_response_dto(created)


# List all master prompts
# Returns every master prompt stored in the system.
# Useful for UI dropdowns, admin panels, or browsing available templates.
@router.get(
    "/",
    response_model=List[MasterPromptResponseDTO],
)
async def list_master_prompts(
    service: MasterPromptService = Depends(get_master_prompt_service),
):
    items = await service.list_master_prompts()
    return [entity_to_response_dto(mp) for mp in items]


# Get a single master prompt by ID
# Used when editing, previewing, or selecting a specific master prompt.
@router.get(
    "/{master_prompt_id}",
    response_model=MasterPromptResponseDTO,
)
async def get_master_prompt(
    master_prompt_id: str,
    service: MasterPromptService = Depends(get_master_prompt_service),
):
    try:
        oid = ObjectId(master_prompt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid master_prompt_id")

    entity = await service.get_master_prompt(oid)
    if not entity:
        raise HTTPException(status_code=404, detail="Master prompt not found")

    return entity_to_response_dto(entity)


# List master prompts filtered by category
# Useful for grouping prompts (e.g., Finance, Sports, Food).
@router.get(
    "/by-category/{category}",
    response_model=List[MasterPromptResponseDTO],
)
async def list_master_prompts_by_category(
    category: str,
    service: MasterPromptService = Depends(get_master_prompt_service),
):
    items = await service.list_master_prompts_by_category(category)
    return [entity_to_response_dto(mp) for mp in items]


# Update an existing master prompt
# Allows partial updates (PATCH) to modify only the fields provided.
@router.patch(
    "/{master_prompt_id}",
    response_model=MasterPromptResponseDTO,
)
async def update_master_prompt(
    master_prompt_id: str,
    payload: MasterPromptUpdateDTO,
    service: MasterPromptService = Depends(get_master_prompt_service),
):
    try:
        oid = ObjectId(master_prompt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid master_prompt_id")

    update_data = payload.model_dump(exclude_unset=True)

    # Map nested DTOs to Mongo structure
    if "prompt_content" in update_data:
        pc = update_data.pop("prompt_content")
        update_data["promptContent"] = {
            "systemMessage": pc["system_message"],
            "userMessage": pc["user_message"],
        }

    if "tweet_length_policy" in update_data:
        tlp = update_data.pop("tweet_length_policy")
        update_data["tweetLengthPolicy"] = tlp

    updated = await service.update_master_prompt(oid, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Master prompt not found")

    return entity_to_response_dto(updated)


# Delete a master prompt
# Removes a master prompt permanently from the system.
# Typically used by admins or during cleanup.
@router.delete(
    "/{master_prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_master_prompt(
    master_prompt_id: str,
    service: MasterPromptService = Depends(get_master_prompt_service),
):
    try:
        oid = ObjectId(master_prompt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid master_prompt_id")

    deleted = await service.delete_master_prompt(oid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Master prompt not found")

    return None
