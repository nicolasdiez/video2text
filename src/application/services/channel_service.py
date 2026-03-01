# src/application/services/channel_service.py

# TODO: llamar desde aqui a PromptResolverService para q devuelva el FinalPrompt a usar en el ingestion pipeline

# Dependency Injection Reminder:
# - Si un servicio A necesita otro servicio B, inyectar B en A por constructor desde el composition root (main.py) (A recibe B). Evitar que A importe y construya B por su cuenta (previene acoplamiento y ciclos).

from datetime import datetime
from typing import Optional
import inspect
import logging

from domain.ports.inbound.channel_port import ChannelPort
from domain.ports.inbound.prompt_resolver_port import PromptResolverPort

from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from domain.ports.outbound.mongodb.user_prompt_repository_port import UserPromptRepositoryPort
from domain.ports.outbound.mongodb.master_prompt_repository_port import MasterPromptRepositoryPort

from domain.entities.channel import Channel
from domain.value_objects.final_prompt import FinalPrompt

logger = logging.getLogger(__name__)


class ChannelService(ChannelPort):
    """
    Application-level service responsible for channel-related operations.

    After the refactor:
      - Channels only reference a UserPrompt (selected_prompt_id)
      - UserPrompt may optionally reference a MasterPrompt
      - MasterPrompt is never selected directly by a channel
      - This service returns a FinalPrompt already resolved via PromptResolverService
    """

    def __init__(
        self,
        channel_repo: ChannelRepositoryPort,
        user_prompt_repo: UserPromptRepositoryPort,
        master_prompt_repo: MasterPromptRepositoryPort,
        prompt_resolver: PromptResolverPort,
    ):
        self.channel_repo = channel_repo
        self.user_prompt_repo = user_prompt_repo
        self.master_prompt_repo = master_prompt_repo
        self.prompt_resolver = prompt_resolver

    # -------------------------------------------------------------------------
    # UPDATE CHANNEL PROMPT
    # -------------------------------------------------------------------------
    async def update_channel_prompt(self, channel_id: str, selected_prompt_id: Optional[str] = None) -> None:
        """
        Update the selected prompt for a channel.
        After the refactor:
          - Channels can ONLY select a UserPrompt.
          - Master prompts are no longer directly selectable.

        This version includes optional validation:
          - The selected prompt must exist.
          - The selected prompt must belong to the same user as the channel.
        """

        if not selected_prompt_id:
            raise ValueError("A channel must select a user prompt (selected_prompt_id cannot be None).")

        # ---------------------------------------------------------------------
        # Fetch channel to validate ownership
        # ---------------------------------------------------------------------
        try:
            channel = await self.channel_repo.find_by_id(channel_id)
        except Exception as exc:
            logger.exception(
                "Error fetching channel %s during update_channel_prompt(): %s",
                channel_id,
                exc,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            raise

        if not channel:
            raise ValueError(f"Channel {channel_id} does not exist.")

        # ---------------------------------------------------------------------
        # Validation: ensure the prompt exists and belongs to the channel's user
        # ---------------------------------------------------------------------
        try:
            user_prompt = await self.user_prompt_repo.find_by_id(selected_prompt_id)
        except Exception as exc:
            logger.exception(
                "Error fetching user prompt %s during update_channel_prompt(): %s",
                selected_prompt_id,
                exc,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            raise

        if not user_prompt:
            raise ValueError(f"UserPrompt {selected_prompt_id} does not exist.")

        if user_prompt.user_id != channel.user_id:
            raise ValueError(
                f"UserPrompt {selected_prompt_id} does not belong to the same user as channel {channel_id}."
            )

        # ---------------------------------------------------------------------
        # Persist the update
        # ---------------------------------------------------------------------
        await self.channel_repo.update_by_id(
            channel_id,
            {
                "selectedPromptId": selected_prompt_id,
                "updatedAt": datetime.utcnow(),
            },
        )

        logger.info(
            "Channel %s updated to use UserPrompt %s.",
            channel_id,
            selected_prompt_id,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

    # -------------------------------------------------------------------------
    # GET FINAL PROMPT FOR A CHANNEL
    # -------------------------------------------------------------------------
    async def get_channel_prompt(self, channel: Channel, user_id: str) -> Optional[FinalPrompt]:
        """
        Retrieve the fully resolved FinalPrompt for a channel.

        Steps:
        1. Validate that the channel has a selected_prompt_id.
        2. Load the UserPrompt.
        3. Validate ownership.
        4. If UserPrompt references a MasterPrompt, load it.
        5. Use PromptResolverService to combine them.
        6. Return a FinalPrompt ready for tweet generation.
        """

        # ---------------------------------------------------------------------
        # 1. Validate selected_prompt_id exists
        # ---------------------------------------------------------------------
        if not channel.selected_prompt_id:
            logger.info(
                "Channel %s has no selected_prompt_id; cannot resolve prompt.",
                channel.id,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        # ---------------------------------------------------------------------
        # 2. Fetch the UserPrompt
        # ---------------------------------------------------------------------
        try:
            user_prompt = await self.user_prompt_repo.find_by_id(channel.selected_prompt_id)
        except Exception as exc:
            logger.exception(
                "Error fetching user prompt %s for channel %s: %s",
                channel.selected_prompt_id,
                channel.id,
                exc,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        if not user_prompt:
            logger.info(
                "Selected user prompt %s not found for channel %s.",
                channel.selected_prompt_id,
                channel.id,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        # ---------------------------------------------------------------------
        # 3. Validate ownership
        # ---------------------------------------------------------------------
        if user_prompt.user_id != channel.user_id:
            logger.info(
                "UserPrompt %s does not belong to user %s (channel user_id=%s), skipping.",
                user_prompt.id,
                user_id,
                channel.user_id,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        # ---------------------------------------------------------------------
        # 4. Load MasterPrompt if referenced
        # ---------------------------------------------------------------------
        master_prompt = None

        if user_prompt.master_prompt_id:
            try:
                master_prompt = await self.master_prompt_repo.find_by_id(user_prompt.master_prompt_id)
            except Exception as exc:
                logger.exception(
                    "Error fetching master prompt %s referenced by user prompt %s: %s",
                    user_prompt.master_prompt_id,
                    user_prompt.id,
                    exc,
                    extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
                )
                master_prompt = None  # fallback: ignore master prompt

            if not master_prompt:
                logger.info(
                    "MasterPrompt %s referenced by UserPrompt %s not found; using only UserPrompt.",
                    user_prompt.master_prompt_id,
                    user_prompt.id,
                    extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
                )

        # ---------------------------------------------------------------------
        # 5. Resolve final prompt using PromptResolverService
        # ---------------------------------------------------------------------
        try:
            final_prompt = await self.prompt_resolver.resolve_final_prompt(
                user_prompt=user_prompt,
                master_prompt=master_prompt,
            )
        except Exception as exc:
            logger.exception(
                "Error resolving final prompt for channel %s using UserPrompt %s: %s",
                channel.id,
                user_prompt.id,
                exc,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )
            return None

        # ---------------------------------------------------------------------
        # 6. Return FinalPrompt
        # ---------------------------------------------------------------------
        logger.info(
            "FinalPrompt successfully resolved for channel %s using UserPrompt %s.",
            channel.id,
            user_prompt.id,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

        return final_prompt

