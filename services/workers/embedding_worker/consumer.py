import json
from aiokafka import AIOKafkaConsumer
from shared.events.document_textracted import DocumentTextracted
from shared.constant import DOCUMENT_TEXTRACTED
from handler import handle_document_chunking

async def consume():
    consumer = AIOKafkaConsumer(
        "document-chunk",
        bootstrap_servers="localhost:9092",
        group_id="document-workers",
        client_id="document-worker-2",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    await consumer.start()
    print("📥 Document worker started")

    try:
        async for msg in consumer:
            payload = msg.value

            if payload.get("event_type") == DOCUMENT_TEXTRACTED:
                event = DocumentTextracted(**payload)
                await handle_document_chunking(event)

    finally:
        await consumer.stop()
