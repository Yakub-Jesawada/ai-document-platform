from workers.common.model import Document
from workers.common.database import get_kafka_db_session
from sqlalchemy import select

async def get_document_id(document_uuid: str) -> int:
    async with get_kafka_db_session() as session:
        document = await session.scalar(
            select(Document).where(Document.uuid == document_uuid)
        )

        if not document:
            raise ValueError(f"Document not found for uuid: {document_uuid}")

        return document.id
