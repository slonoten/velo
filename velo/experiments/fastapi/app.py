"""Сервис простановки ссылок в документе
Получает на вход текст документа,
на выходе координаты фрагментов и координаты целей ссылок
"""
import os
from typing import List, Optional, Dict, Any, Union
import asyncio
import logging
from logging.config import dictConfig
import uuid
import json
import itertools

from fastapi import FastAPI
import aio_pika
from itsdangerous import json

# pylint: disable=no-name-in-module
from pydantic import BaseModel

from logger_config import log_config

dictConfig(log_config)

logger = logging.getLogger("velo-logger")


def create_app() -> FastAPI:
    return FastAPI(debug=True)

app = create_app()

jobs_channel = None
jobs_queue_name = "jobs"
results_queue_name = f"results_{uuid.uuid4()}"

job_counter = itertools.count()
job_id_to_event = {}
job_id_to_result = {}


@app.on_event("startup")
def startup():
    loop = asyncio.new_event_loop()
    asyncio.ensure_future(result_processor(loop))


@app.post("/transform")
async def resolve(text: Union[List, Dict, Any]) -> List[float]:
    """
    На входе текст (не json), на выходе json
    """
    if not isinstance(text, str):
        raise TypeError("Ожидается строка")
    logger.debug('Request: "%s..." (%d symbols).', text[:100], len(text))
    # Put job to queue
    job_id = next(job_counter)
    job = {"id": job_id, "text": text, "queue": results_queue_name}
    logger.debug("Sending job to queue: %s", repr(job))
    await jobs_channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(job).encode("ascii")),
            routing_key=jobs_queue_name,
        )
    # Wait for job result received
    result_received_event = asyncio.Event()
    job_id_to_event[job_id] = result_received_event
    await result_received_event.wait()
    # Get result from dict by job id
    result = job_id_to_result[job_id]
    logger.debug("Got result: %s", repr(result))
    del job_id_to_result[job_id]
    return result

async def result_processor(loop: asyncio.AbstractEventLoop) -> None:
    global jobs_channel

    connection = await aio_pika.connect_robust(host="localhost")

    async with connection:
        jobs_channel = await connection.channel()
        await jobs_channel.declare_queue(jobs_queue_name)

        results_channel = await connection.channel()
        await results_channel.set_qos(prefetch_count=10)
        results_queue = await results_channel.declare_queue(results_queue_name, auto_delete=True)
        

        async with results_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = message.body.decode("ascii")
                    logger.debug("Incoming message: %s", body)
                    result = json.loads(body)
                    job_id = result["id"]
                    job_id_to_result[job_id] = result["embedding"]
                    job_id_to_event[job_id].set()
                    del job_id_to_event[job_id]
                    


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=5042, reload=True, debug=True)
