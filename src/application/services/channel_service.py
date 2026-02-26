# src/application/services/channel_service.py

# TODO: llamar desde aqui a PromptResolverService para q devuelva el FinalPrompt a usar en el ingestion pipeline

# Important Reminder:
# - Si un servicio A necesita otro servicio B, inyectar B en A por constructor desde el composition root (main.py) (A recibe B). Evitar que A importe y construya B por su cuenta (previene acoplamiento y ciclos).

from datetime import datetime
from typing import Optional, Any
import inspect
import logging

from domain.ports.inbound.channel_service_port import ChannelServicePort
from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from domain.ports.outbound.mongodb.user_prompt_repository_port import UserPromptRepositoryPort
from domain.ports.outbound.mongodb.master_prompt_repository_port import MasterPromptRepositoryPort

from domain.entities.channel import Channel

logger = logging.getLogger(__name__)


class ChannelService(ChannelServicePort):
    """
    Application-level service responsible for channel-related operations.
    After the refactor:
      - Channels only reference a UserPrompt (selected_prompt_id)
      - UserPrompt may optionally reference a MasterPrompt
      - MasterPrompt is never selected directly by a channel
    """

    def __init__(
        self,
        channel_repo: ChannelRepositoryPort,
        user_prompt_repo: UserPromptRepositoryPort,
        master_prompt_repo: MasterPromptRepositoryPort,
    ):
        self.channel_repo = channel_repo
        self.user_prompt_repo = user_prompt_repo
        self.master_prompt_repo = master_prompt_repo

    # -------------------------------------------------------------------------
    # UPDATE CHANNEL PROMPT
    # -------------------------------------------------------------------------
    async def update_channel_prompt(self, channel_id: str, selected_prompt_id: Optional[str] = None) -> None:
        """
        Update the selected prompt for a channel.
        After the refactor:
          - Channels can ONLY select a UserPrompt.
          - Master prompts are no longer directly selectable.
        """
        # TODO: validar que el selected_prompt_id corresponde efectivamente a un prompt de user_prompt_repo

        if not selected_prompt_id:
            raise ValueError("A channel must select a user prompt (selected_prompt_id cannot be None).")

        await self.channel_repo.update_by_id(
            channel_id,
            {
                "selectedPromptId": selected_prompt_id,
                "updatedAt": datetime.utcnow(),
            },
        )

    # -------------------------------------------------------------------------
    # GET EFFECTIVE PROMPT FOR A CHANNEL
    # -------------------------------------------------------------------------
    async def get_channel_prompt(self, channel: Channel, user_id: str) -> Optional[Any]:
        """
        Retrieve the effective prompt for a channel.

        New logic after refactor:
        1. Channels only store selected_prompt_id → UserPrompt
        2. UserPrompt may optionally reference a MasterPrompt
        3. The effective prompt is:
              - UserPrompt (base)
              - If user_prompt.master_prompt_id exists → load MasterPrompt and merge
        4. If selected_prompt_id is missing or invalid → return None
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

        # Validate ownership
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
        # 3. If UserPrompt references a MasterPrompt → load it
        # ---------------------------------------------------------------------
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
                return user_prompt  # fallback: use user prompt only

            if master_prompt:
                logger.info(
                    "UserPrompt %s references MasterPrompt %s; returning both.",
                    user_prompt.id,
                    user_prompt.master_prompt_id,
                    extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
                )
                return {
                    "user_prompt": user_prompt,
                    "master_prompt": master_prompt,
                }

            logger.info(
                "MasterPrompt %s referenced by UserPrompt %s not found; using only UserPrompt.",
                user_prompt.master_prompt_id,
                user_prompt.id,
                extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
            )

        # ---------------------------------------------------------------------
        # 4. Return only the UserPrompt
        # ---------------------------------------------------------------------
        logger.info(
            "Selected UserPrompt %s successfully retrieved for channel %s.",
            user_prompt.id,
            channel.id,
            extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name},
        )

        return user_prompt

