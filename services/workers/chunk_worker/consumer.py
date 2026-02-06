import json
from aiokafka import AIOKafkaConsumer
from shared.events.document_textracted import DocumentTextracted
from shared.constant import DOCUMENT_TEXTRACTED
from shared.kafka.producer import start_producer, stop_producer
from workers.common.env import KAFKA_BROKER_URL, CHUNK_WORKER_TOPIC
from handler import handle_document_chunking
import logging

logger = logging.getLogger(__name__)

async def consume():
    await start_producer()
    consumer = AIOKafkaConsumer(
        CHUNK_WORKER_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL,
        group_id="document-workers",
        client_id="chunk-worker",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    await consumer.start()
    logger.info("Chunk worker started, consuming from topic: %s", CHUNK_WORKER_TOPIC)

    try:
        async for msg in consumer:
            payload = msg.value

            if payload.get("event_type") == DOCUMENT_TEXTRACTED:
                event = DocumentTextracted(**payload)
                await handle_document_chunking(event)

    finally:
        await consumer.stop()
        await stop_producer()
