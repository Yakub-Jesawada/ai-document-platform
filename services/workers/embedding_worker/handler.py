import logging
from sqlmodel import select

from shared.events.document_chunked import DocumentChunked
from workers.common.database import get_kafka_db_session
from workers.common.helper import get_document_id
from workers.common.model import Document, ProcessingStatus, DocumentChunk
from services.shared.embeddings.provider import EmbeddingProvider

logger = logging.getLogger(__name__)

EMBEDDING_BATCH_SIZE = 32

async def handle_document_embedding(
    event: DocumentChunked,
    provider: EmbeddingProvider,
):
    document_uuid = event.document_uuid
    document_id = await get_document_id(document_uuid)

    try:
        logger.info("Starting embedding for document %s", document_uuid)

        async with get_kafka_db_session() as session:
            result = await session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()

            if not chunks:
                logger.warning("No chunks found for %s", document_uuid)
                return

            texts = [chunk.text for chunk in chunks]

            embeddings: list[list[float]] = []
            for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
                batch = texts[i:i + EMBEDDING_BATCH_SIZE]
                embeddings.extend(await provider.embed(batch))

            # 🔥 SAME SESSION → ORM tracks changes
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding

            document = (
                await session.execute(
                    select(Document).where(Document.id == document_id)
                )
            ).scalar_one_or_none()

            if document:
                document.status = ProcessingStatus.EMBEDDING_DONE
                document.embedding_completed = True

            await session.commit()

        logger.info("Embedding completed for %s", document_uuid)

    except Exception:
        async with get_kafka_db_session() as session:
            document = (
                await session.execute(
                    select(Document).where(Document.uuid == document_uuid)
                )
            ).scalar_one_or_none()

            if document:
                document.status = ProcessingStatus.EMBEDDING_FAILED
                document.embedding_completed = False
                await session.commit()
        raise