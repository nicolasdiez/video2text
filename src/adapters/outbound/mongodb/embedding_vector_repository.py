# src/adapters/outbound/mongodb/embedding_vector_repository.py

from datetime import datetime
from typing import Optional
from bson import ObjectId

from src.domain.value_objects.embedding_vector import EmbeddingVector
from src.domain.value_objects.embedding_type import EmbeddingType
from src.domain.ports.outbound.mongodb.embedding_vector_repository_port import EmbeddingVectorRepositoryPort

class MongoEmbeddingVectorRepository(EmbeddingVectorRepositoryPort):
    """
    MongoDB implementation of the EmbeddingVectorRepositoryPort.
    Stores and retrieves embedding vectors in a single collection.
    """

    def __init__(self, db):
        self.collection = db["embeddings"]   # Single collection for all embeddings

    def _to_entity(self, doc) -> EmbeddingVector:
        return EmbeddingVector(
            id=str(doc["_id"]),
            tweet_id=doc["tweet_id"],
            type=EmbeddingType(doc["type"]),            
            vector=doc["vector"],
            created_at=doc["created_at"],
        )

    async def save(self, embedding: EmbeddingVector) -> str:
        doc = {
            "tweet_id": embedding.tweet_id,
            "type": embedding.type.value,
            "vector": embedding.vector,
            "created_at": embedding.created_at or datetime.utcnow(),
        }

        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_tweet_and_type(self, tweet_id: str, type: EmbeddingType) -> Optional[EmbeddingVector]:
        doc = await self.collection.find_one({
            "tweet_id": tweet_id,
            "type": type.value
        })

        return self._to_entity(doc) if doc else None

    async def delete_by_tweet(self, tweet_id: str) -> None:
        await self.collection.delete_many({"tweet_id": tweet_id})
