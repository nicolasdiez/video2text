# src/domain/value_objects/embedding_type.py

from enum import Enum

class EmbeddingType(str, Enum):
    TWEET_TEXT = "tweet_text"
    VIDEO_TRANSCRIPT = "video_transcript"
