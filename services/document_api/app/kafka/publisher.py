# app/kafka/publish.py
from uuid import uuid4
from datetime import datetime, timezone
from shared.events.document_uploaded import DocumentUploaded
from shared.events.document_textracted import DocumentTextracted
from shared.events.document_chunked import DocumentChunked
from config import settings
import shared.kafka.producer as producer_module


async def publish_document_uploaded(document, user):
    now = datetime.now(timezone.utc)

    event = DocumentUploaded(
        event_id=uuid4(),
        document_uuid=document.uuid,
        occurred_at=now,
        uploaded_at=now,
        uploader_uuid=user.uuid,
    )
    producer = producer_module.require_producer()
    await producer.send_and_wait(
        settings.OCR_WORKER_TOPIC,
        value=event.model_dump(mode="json"),
    )


async def publish_document_textracted(document):
    now = datetime.now(timezone.utc)

    event = DocumentTextracted(
        event_id=uuid4(),
        document_uuid=document.uuid,
        occurred_at=now,
    )
    producer = producer_module.require_producer()
    await producer.send_and_wait(
        settings.CHUNK_WORKER_TOPIC,
        value=event.model_dump(mode="json"),
    )


async def publish_document_chunked(document):
    now = datetime.now(timezone.utc)

    event = DocumentChunked(
        event_id=uuid4(),
        document_uuid=document.uuid,
        occurred_at=now,
    )
    producer = producer_module.require_producer()
    await producer.send_and_wait(
        settings.EMBEDDING_WORKER_TOPIC,
        value=event.model_dump(mode="json"),
    )
