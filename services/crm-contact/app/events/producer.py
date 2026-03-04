from shared.kafka import KafkaProducer

TOPIC = "re.contacts"
SOURCE = "crm-contact-service"


async def emit_contact_event(
    producer: KafkaProducer,
    event_type: str,
    payload: dict,
    key: str | None = None,
) -> None:
    await producer.publish(
        topic=TOPIC,
        event_type=event_type,
        payload=payload,
        source=SOURCE,
        key=key,
    )
