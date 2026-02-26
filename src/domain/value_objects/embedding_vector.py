# src/domain/value_objects/embedding_vector.py

# TODO: valorar convertir este VO en un Entity xq finalmente tiene id y se persiste en una indexed vectorDB ("embeddings")

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from src.domain.value_objects.embedding_type import EmbeddingType

@dataclass
class EmbeddingVector:
    """
    Value object representing a stored embedding vector in the vector database.
    """
    id: Optional[str]           # MongoDB document ID
    tweet_id: str               # Tweet this embedding belongs to (is the mongo/entity _id, NOT the ID of the tweet in X)
    type: EmbeddingType         # "tweet_text" | "video_transcript"
    vector: List[float]         # The embedding vector itself
    created_at: datetime        # Timestamp of creation
