"""API for model predictions"""

from typing import List, Dict, Any, Union, Tuple, Optional
import asyncio
import logging
from logging.config import dictConfig
import uuid
import json
import itertools
from timeit import default_timer
import os
import time

from fastapi import FastAPI, logger, HTTPException
import aio_pika

from logger_config import log_config
from app_stat import ModelStatStore, ModelStat

JOBS_QUEUE_NAME = "jobs"
RETRY_COUNT = 2
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

dictConfig(log_config)

logger = logging.getLogger("velo-logger")

logging.getLogger("uvicorn").setLevel(LOG_LEVEL)

rabbitmq_url = os.environ.get("RABBITMQ_URL", "amqp://localhost")


def create_app() -> FastAPI:
    return FastAPI(debug=True)


app = create_app()

jobs_channel = None
results_queue_name = f"results-{uuid.uuid4()}"

job_counter = itertools.count()
job_id_to_event = {}
job_id_to_result = {}

stat_store = ModelStatStore()

connected = asyncio.Event()


@app.on_event("startup")
def startup():
    time.sleep(10)  # dirty hack
    loop = asyncio.new_event_loop()
    asyncio.ensure_future(result_processor(loop))


async def predict(text: str) -> Optional[Dict[str, Any]]:
    """Sends data to worker and waits for result
    Args:
        text (str): model input

    Returns:
        Optional[Dict[str, Any]]: Dict from worker or None if timeout excided
    """
    # Put job to queue
    job_id = next(job_counter)
    job = {"id": job_id, "text": text, "queue": results_queue_name}
    logger.debug("Sending job to queue: %s", repr(job))
    await jobs_channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(job).encode("ascii")),
        routing_key=JOBS_QUEUE_NAME,
    )
    # Wait for job result received
    result_received_event = asyncio.Event()
    job_id_to_event[job_id] = result_received_event
    try:
        await asyncio.wait_for(result_received_event.wait(), 1.0)
        # Get result from dict by job id
        result = job_id_to_result[job_id]
        del job_id_to_result[job_id]
        return result
    except asyncio.TimeoutError:
        return None


@app.post("/transform", response_model=List[float])
async def transform(text: Union[List, Dict, Any]) -> List[float]:
    if not isinstance(text, str):
        raise TypeError(f"Got {type(text)}. Expected str.")
    start = default_timer()
    logger.debug('Request: "%s..." (%d symbols).', text[:100], len(text))
    for _ in range(RETRY_COUNT):
        result = await predict(text)
        if result:
            break
    else:
        raise HTTPException(408)
    logger.debug("Got result: %s", repr(result))
    stop = default_timer()
    stat_store.update(result=result, response_time=stop - start)
    return result["embedding"]


@app.get("/stat", response_model=ModelStat)
async def stat() -> ModelStat:
    return ModelStat(
        workers={
            id_: store.get_worker_stat() for id_, store in stat_store.workers.items()
        },
        queue_lenght=len(job_id_to_event),
        response_time=stat_store.mean_response_time,
    )


async def result_processor(loop: asyncio.AbstractEventLoop) -> None:
    global jobs_channel

    logger.debug('Connecting to RabbitMQ "%s"', rabbitmq_url)

    for _ in range(5):
        logger.debug('Trying to connect RabbitMQ "%s"', rabbitmq_url)
        try:
            connection = await aio_pika.connect_robust(url=rabbitmq_url)
            break
        except ConnectionError:
            await asyncio.sleep(5)
    else:
        connection = await aio_pika.connect_robust(url=rabbitmq_url)

    connected.set()

    async with connection:
        jobs_channel = await connection.channel()
        # Если реализовывать устройчивость к падению ноды через подтверждение приёма сообщения
        # то одно сообщение с данными вызывающими падение ноды приведет к падению всех нод по очереди
        # поэтому auto_delete=True
        await jobs_channel.declare_queue(JOBS_QUEUE_NAME, auto_delete=True)

        results_channel = await connection.channel()
        await results_channel.set_qos(prefetch_count=10)
        results_queue = await results_channel.declare_queue(
            results_queue_name, auto_delete=True
        )

        async with results_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = message.body.decode("ascii")
                    logger.debug("Incoming message: %s", body)
                    result = json.loads(body)
                    job_id = result["id"]
                    job_id_to_result[job_id] = result
                    job_id_to_event[job_id].set()
                    del job_id_to_event[job_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8877, reload=True, debug=True)
