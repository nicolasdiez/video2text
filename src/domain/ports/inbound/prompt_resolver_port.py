# domain/ports/inbound/prompt_resolver_port.py

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.user_prompt import UserPrompt
from domain.entities.master_prompt import MasterPrompt
from domain.value_objects.final_prompt import FinalPrompt


class PromptResolverPort(ABC):
    """
    Defines the contract for resolving a final prompt from:
      - a UserPrompt (required)
      - an optional MasterPrompt (if referenced)
    The implementation must combine both and return a FinalPrompt.
    """

    @abstractmethod
    async def resolve_final_prompt(
        self,
        user_prompt: UserPrompt,
        master_prompt: Optional[MasterPrompt] = None
    ) -> FinalPrompt:
        raise NotImplementedError
