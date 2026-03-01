# src/application/services/prompt_resolver_service.py

#  Es un application service (y no un domain service) porque:
#   - Necesita acceder a repositorios (para cargar MasterPrompt).
#   - Orquesta entidades y value objects.
#   - Produce un resultado listo para usar por pipelines.

from typing import Optional

from domain.ports.inbound.prompt_resolver_port import PromptResolverPort
from domain.entities.user_prompt import UserPrompt
from domain.entities.master_prompt import MasterPrompt
from domain.value_objects.final_prompt import FinalPrompt


class PromptResolverService(PromptResolverPort):
    """
    Application service responsible for combining:
      - MasterPrompt (base template)
      - UserPrompt (overrides)
    and producing a FinalPrompt ready for tweet generation.

    This service contains no persistence logic and no side effects.
    """

    async def resolve_final_prompt(
        self,
        user_prompt: UserPrompt,
        master_prompt: Optional[MasterPrompt] = None
    ) -> FinalPrompt:

        # 1. Determine system_message
        if master_prompt:
            base_system = master_prompt.prompt_content.system_message
        else:
            base_system = ""

        # UserPrompt always overrides system_message if provided
        final_system_message = user_prompt.prompt_content.system_message or base_system

        # 2. Determine user_message
        if master_prompt:
            base_user = master_prompt.prompt_content.user_message
        else:
            base_user = ""

        # UserPrompt always overrides user_message if provided
        final_user_message = user_prompt.prompt_content.user_message or base_user

        # 3. Language to generate tweets always comes from UserPrompt
        final_language = user_prompt.language_to_generate_tweets

        # 4. Tweet length policy always comes from UserPrompt
        final_length_policy = user_prompt.tweet_length_policy

        # 5. Build the FinalPrompt value object
        return FinalPrompt(
            system_message=final_system_message,
            user_message=final_user_message,
            language_to_generate_tweets=final_language,
            tweet_length_policy=final_length_policy
        )
