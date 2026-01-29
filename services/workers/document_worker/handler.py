from shared.events.document_uploaded import DocumentUploaded
from sqlmodel import select
from workers.database import get_kafka_db_session
from workers.model import Document, ProcessingStatus
from document_processor_registry import PROCESSOR_REGISTRY
import logging
import json
from pathlib import Path

# Directory of the current file
current_dir = Path(__file__).resolve().parent

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

    except Exception:
        async with get_kafka_db_session() as session:
            stmt = select(Document).where(Document.uuid == document_uuid)
            result = await session.execute(stmt)
            document = result.scalar_one_or_none()

            if document:
                document.status = ProcessingStatus.OCR_FAILED
                document.ocr_completed = False
                await session.commit()
        raise