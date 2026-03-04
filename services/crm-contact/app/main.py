import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.config import ServiceConfig
from shared.database import Base, get_engine, get_session_factory
from shared.kafka import KafkaProducer
from shared.middleware.error_handling import global_exception_handler
from shared.middleware.logging import setup_logging

from app.api.routes import router
from app.models.contact import Contact, ContactTag, Interaction  # noqa: F401

config = ServiceConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(config.SERVICE_NAME)

    engine = get_engine(config.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.session_factory = get_session_factory(engine)

    producer: KafkaProducer | None = KafkaProducer(config.KAFKA_BOOTSTRAP)
    try:
        await producer.start()
    except Exception:
        logging.getLogger(__name__).warning("Kafka unavailable, events will not be published")
        producer = None
    app.state.kafka_producer = producer

    yield

    if producer:
        await producer.stop()
    await engine.dispose()


app = FastAPI(title="CRM Contact Service", lifespan=lifespan)
app.add_exception_handler(Exception, global_exception_handler)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": config.SERVICE_NAME}
