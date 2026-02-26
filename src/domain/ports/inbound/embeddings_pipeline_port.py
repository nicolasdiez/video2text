from abc import ABC, abstractmethod

class EmbeddingsPipelinePort(ABC):
    """
    Inbound port for the embeddings pipeline.
    Defines the contract to compute and persist embedding vectors
    for all tweets belonging to a given user.
    """

    @abstractmethod
    async def run_for_user(self, user_id: str) -> None:
        """
        Execute the embeddings pipeline for the given user_id:
          1) retrieve all tweets belonging to the user
          2) extract tweet text and video transcript
          3) generate embedding vectors via the embedding provider
          4) persist embeddings in the vector database
          5) update Tweet.embedding_refs accordingly
        """
        raise NotImplementedError
