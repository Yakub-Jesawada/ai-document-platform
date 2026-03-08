import logging
from workers.common.model import Document, ProcessingStatus
from workers.common.database import get_kafka_db_session
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def get_document_id(document_uuid: str) -> int:
    async with get_kafka_db_session() as session:
        document = await session.scalar(
            select(Document).where(Document.uuid == document_uuid)
        )

        if not document:
            raise ValueError(f"Document not found for uuid: {document_uuid}")

        return document.id


async def mark_document_failed(
    document_uuid, failed_status: ProcessingStatus, **flag_updates
):
    async with get_kafka_db_session() as session:
        result = await session.execute(
            select(Document).where(Document.uuid == document_uuid)
        )
        document = result.scalar_one_or_none()
        if document:
            document.status = failed_status
            for attr, value in flag_updates.items():
                setattr(document, attr, value)
            await session.commit()
            logger.info("Marked document %s as %s", document_uuid, failed_status.value)
