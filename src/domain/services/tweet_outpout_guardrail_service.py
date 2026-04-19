# src/application/services/tweet_output_guardrail_service.py

# valorar moverlo a domain/services

import logging
import inspect
from typing import Dict, Any, Tuple, Optional
from domain.ports.inbound.tweet_output_guardrail_service_port import TweetOutputGuardrailPort
from domain.entities.user_prompt import TweetLengthPolicy, TweetLengthMode, TweetLengthUnit

logger = logging.getLogger(__name__)


class TweetOutputGuardrailService(TweetOutputGuardrailPort):
    """
    Concrete implementation of tweet guardrail validation logic.
    """

    def is_count_valid(self, json_response: Dict, expected_count: int) -> bool:
        # Extract tweets array
        tweets = json_response.get("tweets", [])

        # Validate count
        is_valid = len(tweets) == expected_count

        # Logging
        logger.info("Count validation result: %s (expected=%s, actual=%s)", is_valid, expected_count, len(tweets), extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})

        return is_valid

    def is_length_valid(self, json_response: Dict, policy: TweetLengthPolicy) -> bool:
        # Extract tweets
        tweets = json_response.get("tweets", [])

        # Only character-based validation supported for now
        if policy.unit != TweetLengthUnit.CHARS:
            logger.info("Length validation skipped: unsupported unit '%s'", policy.unit, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
            return True

        # Validate each tweet according to the policy
        for t in tweets:
            text = t.get("text", "")
            length = len(text)

            if policy.mode == TweetLengthMode.FIXED:
                # Compute tolerance window
                if policy.target_length:
                    tolerance = int(policy.target_length * (policy.tolerance_percent / 100))
                    min_len = policy.target_length - tolerance
                    max_len = policy.target_length + tolerance
                else:
                    # Fallback to min/max if target_length is not provided 
                    min_len = policy.min_length or 0
                    max_len = policy.max_length or 9999

            elif policy.mode == TweetLengthMode.RANGE:
                min_len = policy.min_length or 0
                max_len = int(policy.max_length * 1.5) if policy.max_length else 9999  # added 50% margin in max length

            else:
                logger.error("Unknown TweetLengthMode '%s'", policy.mode, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return False

            # Check length boundaries
            if not (min_len <= length <= max_len):
                logger.info("Length validation failed for tweet='%s' (len=%s, min=%s, max=%s)", text, length, min_len, max_len, extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
                return False

        # All tweets passed
        logger.info("Length validation result: True", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        return True

    def is_json_structure_valid(self, json_response: Any) -> Tuple[bool, Optional[str]]:
        """
        Pure JSON format validator for LLM output.
        - Returns (True, None) when payload is a dict with a 'tweets' list that contains
          at least one plausible text candidate (string or dict with text-like key).
        - Returns (False, reason) otherwise.
        - Logs a concise info line with the validation result (same style as other methods).
        """
        method_name = inspect.currentframe().f_code.co_name

        # Basic type check
        if not isinstance(json_response, dict):
            logger.info("JSON structure validation result: False (payload not a dict)", extra={"class": self.__class__.__name__, "method": method_name})
            return False, "payload-not-dict"

        tweets = json_response.get("tweets")
        if not isinstance(tweets, list):
            logger.info("JSON structure validation result: False (missing or non-list 'tweets')", extra={"class": self.__class__.__name__, "method": method_name})
            return False, "missing-or-nonlist-tweets"

        # Quick scan for at least one plausible text candidate
        found_candidate = False
        for item in tweets:
            if isinstance(item, str):
                if item.strip():
                    found_candidate = True
                    break
                else:
                    continue
            if isinstance(item, dict):
                # accept common text-like keys without extracting/normalizing
                for key in ("text", "tweet", "content"):
                    if key in item:
                        val = item.get(key)
                        if isinstance(val, str) and val.strip():
                            found_candidate = True
                            break
                if found_candidate:
                    break

        if not found_candidate:
            logger.info("JSON structure validation result: False (no text candidates in 'tweets' list)", extra={"class": self.__class__.__name__, "method": method_name})
            return False, "no-text-candidates-in-tweets-list"

        # Passed minimal structural checks
        logger.info("JSON structure validation result: True", extra={"class": self.__class__.__name__, "method": method_name})
        return True, None

    def is_semantically_valid(self, json_response: Dict) -> bool:
        # Placeholder for future LLM-based semantic validation
        logger.info("Semantic validation skipped (stub)", extra={"class": self.__class__.__name__, "method": inspect.currentframe().f_code.co_name})
        return True

