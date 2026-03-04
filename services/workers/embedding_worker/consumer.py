import json
import logging
from aiokafka import AIOKafkaConsumer

from shared.events.document_chunked import DocumentChunked
from shared.constant import DOCUMENT_CHUNKED
from workers.common.env import KAFKA_BROKER_URL, EMBEDDING_WORKER_TOPIC
from workers.embedding_worker.handler import handle_document_embedding
from services.shared.embeddings.provider import get_embedding_provider

logger = logging.getLogger(__name__)

async def consume():
    consumer = AIOKafkaConsumer(
        EMBEDDING_WORKER_TOPIC,
        bootstrap_servers=KAFKA_BROKER_URL,
        group_id="document-workers",
        client_id="embedding-worker",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    provider = get_embedding_provider()
    await provider.start()   # ✅ model loads once

    await consumer.start()
    logger.info("Embedding worker started")

    try:
        async for msg in consumer:
            payload = msg.value

            if payload.get("event_type") == DOCUMENT_CHUNKED:
                event = DocumentChunked(**payload)
                await handle_document_embedding(event, provider)

    finally:
        await consumer.stop()
        await provider.close()   # ✅ clean shutdown