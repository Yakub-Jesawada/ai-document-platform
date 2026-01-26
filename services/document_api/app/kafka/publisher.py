# app/kafka/publish.py
from uuid import uuid4
from datetime import datetime, timezone
from shared.events.document_uploaded import DocumentUploaded
from config import settings
import kafka.producer as producer_module


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
        settings.KAFKA_TOPIC,
        value=event.model_dump(mode="json"),  # 🔑 serializes UUID & datetime
    )
