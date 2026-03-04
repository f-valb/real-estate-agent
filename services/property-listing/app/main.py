import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.config import ServiceConfig
from shared.database import Base, get_engine, get_session_factory
from shared.kafka import KafkaProducer
from shared.middleware.error_handling import global_exception_handler
from shared.middleware.logging import setup_logging

from app.api.routes import router
from app.models.property import Property, PropertyPhoto  # noqa: F401 -- ensure models registered for create_all

config = ServiceConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(config.SERVICE_NAME)

    # ---- Database ---------------------------------------------------------
    engine = get_engine(config.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.session_factory = get_session_factory(engine)

    # ---- Kafka ------------------------------------------------------------
    producer: KafkaProducer | None = KafkaProducer(config.KAFKA_BOOTSTRAP)
    try:
        await producer.start()
    except Exception:
        logging.getLogger(__name__).warning(
            "Kafka unavailable, events will not be published"
        )
        producer = None
    app.state.kafka_producer = producer

    yield

    # ---- Shutdown ---------------------------------------------------------
    if producer:
        await producer.stop()
    await engine.dispose()


app = FastAPI(title="Property Listing Service", lifespan=lifespan)
app.add_exception_handler(Exception, global_exception_handler)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": config.SERVICE_NAME}
