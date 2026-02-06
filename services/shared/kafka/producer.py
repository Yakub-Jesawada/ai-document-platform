import json
from aiokafka import AIOKafkaProducer
from shared.constant import KAFKA_BROKER_URL, KAFKA_FASTAPI_PRODUCER_CLIENT_ID

producer = None


def require_producer():
    if producer is None:
        raise RuntimeError(
            "Kafka producer not initialized. "
            "Did you forget to start the app?"
        )
    return producer


async def start_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER_URL,
        client_id=KAFKA_FASTAPI_PRODUCER_CLIENT_ID,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()

async def stop_producer():
    if producer:
        await producer.stop()
