import json
from aiokafka import AIOKafkaConsumer
from shared.events.document_uploaded import DocumentUploaded
from shared.constant import DOCUMENT_UPLOAD_EVENT
from shared.kafka.producer import start_producer, stop_producer
from handler import handle_document_upload

async def consume():
    await start_producer() 
    consumer = AIOKafkaConsumer(
        "document-ocr",
        bootstrap_servers="localhost:9092",
        group_id="document-workers",
        client_id="document-worker-1",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    await consumer.start()
    print("📥 Document worker started")

    try:
        async for msg in consumer:
            payload = msg.value

            if payload.get("event_type") == DOCUMENT_UPLOAD_EVENT:
                event = DocumentUploaded(**payload)
                await handle_document_upload(event)

    finally:
        await consumer.stop()
        await stop_producer()   # cleanup

