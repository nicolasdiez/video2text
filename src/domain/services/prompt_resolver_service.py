# src/application/services/prompt_resolver_service.py

#  Es un domain service (y no un application service) porque:
#   - No accede a repositorios.
#   - Contiene reglas del dominio que no pertenecen a una entidad concreta, sino a varias.

from typing import Optional

from domain.ports.inbound.prompt_resolver_port import PromptResolverPort
from domain.entities.user_prompt import UserPrompt
from domain.entities.master_prompt import MasterPrompt
from domain.value_objects.final_prompt import FinalPrompt


class PromptResolverService(PromptResolverPort):
    """
    Domain service that composes a FinalPrompt from two possible sources:
      - MasterPrompt: a reusable, authoritative template (takes precedence when present)
      - UserPrompt: user-specific overrides and runtime settings

    Responsibilities:
      - Resolve which source provides the system and user messages.
      - Preserve user-level settings that must always come from the UserPrompt
        (for example: language_to_generate_tweets and tweet_length_policy).
      - Perform no persistence and cause no side effects; purely a deterministic
        transformation of input domain objects into a FinalPrompt value object.

    Behavior summary:
      - If a MasterPrompt is referenced and available, the FinalPrompt's
        system_message and user_message are taken from the MasterPrompt.
      - If no MasterPrompt is present, the FinalPrompt's messages are taken
        from the UserPrompt.
      - Language and tweet length policy always come from the UserPrompt.
    """

    async def resolve_final_prompt(
            self,
            user_prompt: UserPrompt,
            master_prompt: Optional[MasterPrompt] = None
        ) -> FinalPrompt:

            # 1. Determine system_message
            # If a master_prompt is provided, use its system_message.
            # Otherwise, fall back to the user_prompt.system_message (may be empty).
            if master_prompt:
                final_system_message = master_prompt.prompt_content.system_message or ""
            else:
                final_system_message = user_prompt.prompt_content.system_message or ""

            # 2. Determine user_message
            # If a master_prompt is provided, use its user_message.
            # Otherwise, fall back to the user_prompt.user_message (may be empty).
            if master_prompt:
                final_user_message = master_prompt.prompt_content.user_message or ""
            else:
                final_user_message = user_prompt.prompt_content.user_message or ""

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

