from abc import ABC, abstractmethod
import aiohttp
import os
from typing import List
from workers.common.env import EMBEDDING_PROVIDER
from workers.common.model import DocumentChunk


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        pass


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str):
        self.api_url = (
            "https://api-inference.huggingface.co/"
            f"pipeline/feature-extraction/{model}"
        )
        self.headers = {
            "Authorization": f"Bearer {os.getenv('HF_API_KEY')}"
        }
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def embed(self, texts: List[str]) -> List[List[float]]:
        session = await self._get_session()

        async with session.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": texts}
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        # HF sometimes returns [[...]] per text
        embeddings = []
        for emb in data:
            if isinstance(emb[0], list):
                embeddings.append(emb[0])
            else:
                embeddings.append(emb)

        return embeddings


def get_embedding_provider():
    provider = EMBEDDING_PROVIDER

    if provider == "huggingface":
        return HuggingFaceEmbeddingProvider(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    else:
        raise ValueError("Unknown embedding provider")


from sqlmodel import select

async def fetch_chunks_for_embedding(session):
    result = await session.exec(
        select(DocumentChunk)
        .where(DocumentChunk.embedding_status == "pending")
    )
    return result.all()
