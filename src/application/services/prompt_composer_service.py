# application/services/prompt_composer_service.py

# Important Reminder:
# - Si un servicio A necesita otro servicio B, inyectar B en A por constructor desde el composition root (main.py) (A recibe B). Evitae que A importe y construya B por su cuenta (previene acoplamiento y ciclos).

from enum import Enum
from typing import Optional

from domain.entities.prompt import Prompt, TweetLengthPolicy
from domain.ports.inbound.prompt_composer_service_port import PromptComposerServicePort


class InstructionPosition(str, Enum):
    BEFORE = "before"
    AFTER = "after"

class PromptComposerService(PromptComposerServicePort):
    """
    Service to compose different variations of a prompt from a Prompt entity and additional runtime data like the transcript.
    """
    
    def add_transcript(self, message: str, transcript: str, position: InstructionPosition = InstructionPosition.AFTER) -> str:
        """
        Append or prepend the transcript block to an existing message prompt.
        - Default behavior preserves current placement: transcript is appended (AFTER).
        - position: InstructionPosition.BEFORE | InstructionPosition.AFTER
        """
        transcript_block = (
            "=== TRANSCRIPT ===\n"
            f"{transcript}\n\n"
        )

        pos_val = position.value if hasattr(position, "value") else str(position)
        pos_val = pos_val.lower()

        if pos_val == InstructionPosition.BEFORE.value:
            message_with_transcript = transcript_block + message.lstrip()
        else:
            # default/AFTER
            message_body = message.rstrip()
            message_with_transcript = message_body + "\n\n" + transcript_block

        return message_with_transcript


    def add_objective(self, message: str, sentences: int = 3, position: InstructionPosition = InstructionPosition.BEFORE) -> str:
        """
        Prepend or append the objective block to an existing message prompt.
        - Default behavior preserves current placement: objective is prepended (BEFORE).
        - position: InstructionPosition.BEFORE | InstructionPosition.AFTER
        """
        objective_block = ( 
            "=== OBJECTIVE ===\n" 
            f"Based on the provided transcript, generate exactly {sentences} standalone tweets.\n" 
            "Each tweet must be crafted to maximize virality, driving the highest possible number of likes, retweets, and new followers.\n\n"
        )

        pos_val = position.value if hasattr(position, "value") else str(position)
        pos_val = pos_val.lower()

        if pos_val == InstructionPosition.AFTER.value:
            # append after
            message_with_objective = message.rstrip() + "\n\n" + objective_block
        else:
            # default/BEFORE: prepend
            message_body = message.lstrip()
            message_with_objective = objective_block + message_body

        return message_with_objective


    def add_output_language(self, message: str, output_language: str = "Spanish (ESPAÑOL)", position: InstructionPosition = InstructionPosition.AFTER) -> str:
        """
        Append or prepend the output language block to an existing message prompt.
        - Default behavior preserves current placement: output language is appended (AFTER).
        - position: InstructionPosition.BEFORE | InstructionPosition.AFTER
        """
        output_language_block = (
            f"=== OUTPUT LANGUAGE ===\n"
            f"The tweets must be generated in {output_language} language.\n\n"
        )

        pos_val = position.value if hasattr(position, "value") else str(position)
        pos_val = pos_val.lower()

        if pos_val == InstructionPosition.BEFORE.value:
            message_with_output_language = output_language_block + message.lstrip()
        else:
            # default/AFTER
            message_with_output_language = message.rstrip() + "\n\n" + output_language_block

        return message_with_output_language


    def add_output_length(
        self,
        message: str,
        tweet_length_policy: Optional["TweetLengthPolicy"],
        position: InstructionPosition = InstructionPosition.AFTER,
        ) -> str:
        """
        Prepend or append an output length instruction block based on tweet_length_policy.
        - tweet_length_policy: domain object (optional). If None, returns message unchanged.
        - position: InstructionPosition.BEFORE | InstructionPosition.AFTER (default AFTER).
        - Supports mode "fixed" and "range".
        - Uses target_length + tolerance_percent for fixed; min/max for range.
        - unit can be "chars" or "tokens" (accepts either enum or raw string).
        """

        if not tweet_length_policy:
            return message

        # Extract fields with safe defaults
        mode = getattr(tweet_length_policy, "mode", None)
        min_len = getattr(tweet_length_policy, "min_length", None)
        max_len = getattr(tweet_length_policy, "max_length", None)
        target = getattr(tweet_length_policy, "target_length", None)
        tolerance = getattr(tweet_length_policy, "tolerance_percent", 10)
        unit = getattr(tweet_length_policy, "unit", None)

        # Normalize unit to human readable label
        if unit is None:
            unit_val = "characters"
        else:
            try:
                unit_str = unit.value if hasattr(unit, "value") else str(unit)
            except Exception:
                unit_str = str(unit)
            unit_str = unit_str.lower()
            unit_val = "tokens" if "token" in unit_str else "characters"

        # Normalize mode string
        if mode is None:
            mode_str = ""
        else:
            mode_str = mode.value if hasattr(mode, "value") else str(mode)

        # Build instruction block depending on mode
        if mode_str.lower() == "fixed":
            if target is None:
                target = min_len or 120
            instruction = (
                "=== OUTPUT LENGTH ===\n"
                f"Generate tweets of approximately {target} {unit_val} (tolerance ±{tolerance}%).\n\n"
            )
        elif mode_str.lower() == "range":
            # In range mode, ignore `target` — the model should produce lengths between min and max.
            min_val = min_len if min_len is not None else 80
            max_val = max_len if max_len is not None else 240
            instruction = (
                "=== OUTPUT LENGTH ===\n"
                f"Each tweet must be between {min_val} and {max_val} {unit_val}.\n\n"
            )
        else:
            # Unknown mode: do not modify message
            return message

        # Normalize position (accept enum or raw string)
        pos_val = position.value if hasattr(position, "value") else str(position)
        pos_val = pos_val.lower()

        if pos_val == InstructionPosition.BEFORE.value:
            message_with_output_length = instruction + message.lstrip()
        else:
            # default to AFTER
            message_with_output_length = message.rstrip() + "\n\n" + instruction

        return message_with_output_length