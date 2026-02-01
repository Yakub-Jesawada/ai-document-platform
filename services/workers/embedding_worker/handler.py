from shared.events.document_textracted import DocumentTextracted
from sqlmodel import select
from workers.common.database import get_kafka_db_session
from workers.common.helper import get_document_id
from workers.common.model import Document, ProcessingStatus
from workers.common.document_processor_registry import PROCESSOR_REGISTRY
import logging
from pathlib import Path

# Directory of the current file
current_dir = Path(__file__).resolve().parent

logger = logging.getLogger(__name__)


async def handle_document_chunking(event: DocumentTextracted):
    document_uuid = event.document_uuid

   
    processor = PROCESSOR_REGISTRY.get('chunk')

    try:
        document_id = await get_document_id(document_uuid)
        logger.info(f'starting chunking for document uuid: {document_uuid}')
        chunks = await processor.create_chunks(document_id)
        logger.info(f'chunks created saving chunks in db for document uuid: {document_uuid}')
        await processor.persist_chunks(document_id, chunks)
        logger.info(f'Chunking completed for document uuid: {document_uuid}')

    except Exception:
        async with get_kafka_db_session() as session:
            stmt = select(Document).where(Document.uuid == document_uuid)
            result = await session.execute(stmt)
            document = result.scalar_one_or_none()

            if document:
                document.status = ProcessingStatus.CHUNKING_FAILED
                document.ocr_completed = False
                await session.commit()
        raise