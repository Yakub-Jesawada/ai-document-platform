from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingProvider:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: SentenceTransformer | None = None

    async def start(self):
        # Called ONCE at worker startup
        self.model = SentenceTransformer(self.model_name)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not self.model:
            raise RuntimeError("EmbeddingProvider not started")

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    async def close(self):
        # Nothing to cleanup now, but future-proof
        self.model = None


def get_embedding_provider() -> EmbeddingProvider:
    return EmbeddingProvider()
