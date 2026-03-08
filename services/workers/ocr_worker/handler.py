import logging
from uuid import uuid4
from datetime import datetime, timezone

from shared.events.document_uploaded import DocumentUploaded
from shared.events.document_textracted import DocumentTextracted
from sqlmodel import select
from workers.common.database import get_kafka_db_session
from workers.common.model import Document, ProcessingStatus
from workers.common.helper import mark_document_failed
from workers.common.document_processor_registry import PROCESSOR_REGISTRY
from shared.constant import DOCUMENT_TEXTRACTED
from shared.kafka.producer import require_producer

logger = logging.getLogger(__name__)


async def handle_document_upload(event: DocumentUploaded):
    document_uuid = event.document_uuid

    async with get_kafka_db_session() as session:
        stmt = select(Document).where(Document.uuid == document_uuid)
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise ValueError(f"Document not found for uuid={document_uuid}")

        processor = PROCESSOR_REGISTRY.get(document.file_type.lower())

        if not processor:
            raise ValueError(
                f"No processor registered for file_type={document.file_type}"
            )

        storage_uri = document.storage_uri

    try:
        extracted_data = await processor.extract(document_uuid, storage_uri)
        await processor.persist(document_uuid, extracted_data)
        now = datetime.now(timezone.utc)
        event = DocumentTextracted(
            event_id=uuid4(),
            document_uuid=document.uuid,
            occurred_at=now,
            uploaded_at=now,
        )
        producer = require_producer()
        await producer.send_and_wait(DOCUMENT_TEXTRACTED, event.model_dump(mode="json"))

    except Exception:
        logger.exception("OCR failed for document %s", document_uuid)
        await mark_document_failed(
            document_uuid, ProcessingStatus.OCR_FAILED, ocr_completed=False
        )
        raise
