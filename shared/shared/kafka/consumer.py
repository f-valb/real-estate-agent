import json
import logging
from collections.abc import Callable, Awaitable
from typing import Any

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str]):
        self._bootstrap = bootstrap_servers
        self._group_id = group_id
        self._topics = topics
        self._consumer: AIOKafkaConsumer | None = None

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._bootstrap,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        logger.info("Kafka consumer started (group=%s, topics=%s)", self._group_id, self._topics)

    async def stop(self):
        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume(self, handler: Callable[[dict[str, Any]], Awaitable[None]]):
        async for msg in self._consumer:
            try:
                await handler(msg.value)
            except Exception:
                logger.exception("Error handling message from %s", msg.topic)
