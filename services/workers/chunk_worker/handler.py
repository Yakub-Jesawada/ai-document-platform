import logging
from uuid import uuid4
from datetime import datetime, timezone

from shared.events.document_textracted import DocumentTextracted
from shared.events.document_chunked import DocumentChunked
from workers.common.helper import get_document_id, mark_document_failed
from workers.common.model import ProcessingStatus
from workers.common.document_processor_registry import PROCESSOR_REGISTRY
from workers.common.env import EMBEDDING_WORKER_TOPIC
from shared.kafka.producer import require_producer

logger = logging.getLogger(__name__)


async def handle_document_chunking(event: DocumentTextracted):
    document_uuid = event.document_uuid

    processor = PROCESSOR_REGISTRY.get('chunk')

    try:
        document_id = await get_document_id(document_uuid)
        logger.info("Starting chunking for document uuid: %s", document_uuid)
        chunks = await processor.create_chunks(document_id)
        logger.info("Chunks created, saving to db for document uuid: %s", document_uuid)
        await processor.persist_chunks(document_id, chunks)
        logger.info("Chunking completed for document uuid: %s", document_uuid)

        now = datetime.now(timezone.utc)
        chunked_event = DocumentChunked(
            event_id=uuid4(),
            document_uuid=document_uuid,
            occurred_at=now,
        )
        producer = require_producer()
        await producer.send_and_wait(
            EMBEDDING_WORKER_TOPIC,
            value=chunked_event.model_dump(mode="json"),
        )
        logger.info("DocumentChunked event published for document uuid: %s", document_uuid)

    except Exception:
        logger.exception("Chunking failed for document %s", document_uuid)
        await mark_document_failed(
            document_uuid, ProcessingStatus.CHUNKING_FAILED, chunk_completed=False
        )
        raise
