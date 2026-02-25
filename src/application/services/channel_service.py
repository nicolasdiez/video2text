# src/application/services/channel_service.py

# Important Reminder:
# - Si un servicio A necesita otro servicio B, inyectar B en A por constructor desde el composition root (main.py) (A recibe B). Evitar que A importe y construya B por su cuenta (previene acoplamiento y ciclos).

from datetime import datetime
from typing import Optional, Any
import inspect
import logging

from domain.ports.inbound.channel_service_port import ChannelServicePort
from domain.ports.outbound.mongodb.channel_repository_port import ChannelRepositoryPort
from domain.ports.outbound.mongodb.user_prompt_repository_port import PromptRepositoryPort
from domain.ports.outbound.mongodb.master_prompt_repository_port import MasterPromptRepositoryPort

from domain.entities.channel import Channel

logger = logging.getLogger(__name__)

class ChannelService(ChannelServicePort):
    """
    Application-level service responsible for channel-related operations.
    Enforces business rules around prompt selection and delegates persistence
    to the channel repository.
    Note: This service now depends on:
      - channel_repo: ChannelRepositoryPort
      - prompt_repo: PromptRepositoryPort (user prompts)
      - master_prompt_repo: MasterPromptRepositoryPort (master prompts)
    These dependencies should be injected from the composition root.
    """

    def __init__(self, channel_repo: ChannelRepositoryPort, prompt_repo: PromptRepositoryPort, master_prompt_repo: MasterPromptRepositoryPort):
        self.channel_repo = channel_repo
        self.prompt_repo = prompt_repo
        self.master_prompt_repo = master_prompt_repo

    async def update_channel_prompt(self, channel_id: str, selected_prompt_id: Optional[str] = None, selected_master_prompt_id: Optional[str] = None) -> None:
        """
        Update the selected prompt for a channel while enforcing business rules:
        - A channel cannot select both a user prompt and a master prompt.
        - A channel must select at least one of them.
        """

        # Business rule: mutually exclusive
        if selected_prompt_id and selected_master_prompt_id:
            raise ValueError("A channel cannot select both a user prompt and a master prompt.")
        
        # Business rule: require at least one
        if not selected_prompt_id and not selected_master_prompt_id:
            raise ValueError("A channel must select either a user prompt or a master prompt.")
        
        # Persist changes
        await self.channel_repo.update_by_id(channel_id, {"selectedPromptId": selected_prompt_id, "selectedMasterPromptId": selected_master_prompt_id, "updatedAt": datetime.utcnow(),})
    
    
    async def get_channel_prompt(self, channel: Channel, user_id: str) -> Optional[Any]:
        """
        Retrieve the effective prompt for a channel following business rules:
        1. If the channel has a selected_master_prompt_id -> return that MasterPrompt.
           (Master prompt takes precedence over any user prompt.)
        2. Otherwise, follow the existing prompt resolution logic:
           - If channel.selected_prompt_id is empty -> try to find any prompt for user+channel.
           - If channel.selected_prompt_id is present -> fetch it; if missing, fall back to any prompt for user+channel.
           - In all cases, ensure the resolved user prompt belongs to the same channel.user_id.
        3. Returns:
           - MasterPrompt or Prompt entity if found and valid.
           - None if no suitable prompt exists or ownership validation fails.
        The method logs informative messages but does not raise for "not found" cases; callers should handle a None return (e.g., skip processing).
        """
        
        # 1) Master prompt (collection: "master_prompts") takes priority over the user prompt (collection: "prompts")
        if getattr(channel, "selected_master_prompt_id", None):
            
            master_prompt_id = channel.selected_master_prompt_id
            
            try:
                master_prompt = await self.master_prompt_repo.find_by_id(master_prompt_id)
            except Exception as exc:
                logger.exception("Error fetching master prompt %s for channel %s: %s", master_prompt_id, channel.id, exc, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return None
            if not master_prompt:
                # fall through to user-prompt resolution
                logger.info("Selected master prompt %s not found for channel %s; falling back to user prompts (if any)", master_prompt_id, channel.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            else:
                logger.info("Using master prompt %s for channel %s (master prompt takes priority over user prompt).", master_prompt_id, channel.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return master_prompt
        
        # 2) User prompt resolution (fallback if master prompt not available)
        user_prompt = None
        
        # If channel has no selected_prompt_id, try to find any prompt for this user+channel
        if not channel.selected_prompt_id:
            try:
                prompts = await self.prompt_repo.find_by_user_and_channel(user_id=user_id, channel_id=channel.id)
            except Exception as exc:
                logger.exception("Error fetching fallback prompt for user %s and channel %s: %s", user_id, channel.id, exc, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return None
            if not prompts:
                logger.info("Channel %s has no selected_prompt_id and no prompts exist for user %s, skipping video %s", channel.id, user_id, None, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return None
            
            # Use the first prompt when multiple exist
            user_prompt = prompts[0]
           
            # validate that the fallback prompt belongs to the same user
            if user_prompt.user_id != channel.user_id:
                logger.info("Fallback user prompt %s does not belong to user %s (channel user_id=%s), skipping", user_prompt.id, user_id, channel.user_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return None
            # log that we are using a fallback prompt
            logger.info("Channel %s has no selected_prompt_id; using fallback prompt %s for user %s and channel %s", channel.id, user_prompt.id, user_id, channel.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return user_prompt
        
        # Normal path: channel.selected_prompt_id exists
        try:
            user_prompt = await self.prompt_repo.find_by_id(channel.selected_prompt_id)
        except Exception as exc:
            logger.exception("Error fetching selected prompt %s for channel %s: %s", channel.selected_prompt_id, channel.id, exc, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None
        
        # If the selected prompt does not exist, fall back to any available prompt
        if not user_prompt:
            logger.info("Selected prompt %s not found for channel %s; falling back to any available prompt for user %s", channel.selected_prompt_id, channel.id, user_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            try:
                prompts = await self.prompt_repo.find_by_user_and_channel(user_id=user_id, channel_id=channel.id)
            except Exception as exc:
                logger.exception("Error fetching fallback prompt for user %s and channel %s: %s", user_id, channel.id, exc, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return None
            if not prompts:
                logger.info("No fallback prompts exist for user %s and channel %s, skipping", user_id, channel.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return None
            # Use the first prompt when multiple exist
            user_prompt = prompts[0]
        
        # validate that the selected or fallback prompt belongs to the same user
        if user_prompt.user_id != channel.user_id:
            logger.info("Selected prompt %s does not belong to user %s (channel user_id=%s), skipping", getattr(user_prompt, "id", None), user_id, channel.user_id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return None
        
        # log that the selected prompt was retrieved successfully
        logger.info("Selected prompt %s successfully retrieved for user %s and channel %s", user_prompt.id, user_id, channel.id, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        
        return user_prompt
