import json
import logging
from aiokafka import AIOKafkaConsumer
from shared.events.document_uploaded import DocumentUploaded
from shared.constant import DOCUMENT_UPLOAD_EVENT
from shared.kafka.producer import start_producer, stop_producer
from workers.common.env import KAFKA_BROKER_URL
from handler import handle_document_upload

logger = logging.getLogger(__name__)

OCR_WORKER_TOPIC = "document-ocr"

async def consume():
    await start_producer()
    consumer = AIOKafkaConsumer(
        OCR_WORKER_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL,
        group_id="document-workers",
        client_id="ocr-worker",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    await consumer.start()
    logger.info("OCR worker started, consuming from topic: %s", OCR_WORKER_TOPIC)

    try:
        async for msg in consumer:
            try:
                payload = msg.value
                if payload.get("event_type") == DOCUMENT_UPLOAD_EVENT:
                    event = DocumentUploaded(**payload)
                    await handle_document_upload(event)
            except Exception:
                logger.exception("Failed to process message at offset %s", msg.offset)
    finally:
        await consumer.stop()
        await stop_producer()
