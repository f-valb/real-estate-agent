from shared.kafka import KafkaProducer

TOPIC = "re.listings"
SOURCE = "property-listing-service"


async def emit_listing_event(
    producer: KafkaProducer,
    event_type: str,
    payload: dict,
    key: str | None = None,
) -> None:
    """Publish a listing event to the Kafka topic.

    Args:
        producer: The shared KafkaProducer instance.
        event_type: Event name, e.g. ``listing.created``.
        payload: Serialisable dict with event data.
        key: Optional partition key (typically the listing ID).
    """
    await producer.publish(
        topic=TOPIC,
        event_type=event_type,
        payload=payload,
        source=SOURCE,
        key=key,
    )
