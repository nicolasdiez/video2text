# src/domain/value_objects/embedding_vector.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class EmbeddingVector:
    """
    Value object representing a stored embedding vector in the vector database.
    """

    id: Optional[str]                     # MongoDB document ID
    tweet_id: str                         # Tweet this embedding belongs to
    user_id: str                          # Owner of the tweet
    type: str                             # "tweet_text" | "video_transcript"
    vector: List[float]                   # The embedding vector itself
    created_at: datetime                  # Timestamp of creation
