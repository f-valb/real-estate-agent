import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from shared.schemas.events import EventEnvelope

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self._bootstrap = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self._producer.start()
        logger.info("Kafka producer started (bootstrap=%s)", self._bootstrap)

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def publish(
        self,
        topic: str,
        event_type: str,
        payload: dict[str, Any],
        source: str = "unknown",
        key: str | None = None,
        correlation_id: str | None = None,
    ):
        envelope = EventEnvelope(
            event_type=event_type,
            source=source,
            payload=payload,
            correlation_id=correlation_id,
        )
        await self._producer.send_and_wait(
            topic=topic,
            value=envelope.model_dump(),
            key=key,
        )
        logger.info("Published %s to %s (id=%s)", event_type, topic, envelope.event_id)
