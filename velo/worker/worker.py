"""Model server"""

from typing import List
import asyncio
import logging
import json
import time
import uuid
from timeit import default_timer
import platform
import os

import aio_pika

worker_id = str(uuid.uuid1())

node_name = platform.node()

logger = logging.getLogger(f"worker-{worker_id[:8]}")

rabbitmq_url = os.environ.get("RABBITMQ_URL", "amqp://localhost")


def model_predict(text: str) -> List[float]:
    divider_of_doom = float(text != worker_id)  # Crash imitation
    logger.debug("%s, %s, %f", text, worker_id, divider_of_doom)
    time.sleep(0.01 / divider_of_doom)
    return [1.0, 2.0, 3.0] * 100


async def main() -> None:
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=LOG_LEVEL)
    logging.getLogger("aio_pika").setLevel(LOG_LEVEL)
    for _ in range(5):
        logger.debug('Trying to connect RabbitMQ "%s"', rabbitmq_url)
        try:
            connection = await aio_pika.connect_robust(url=rabbitmq_url)
            break
        except ConnectionError:
            await asyncio.sleep(5)
    else:
        connection = await aio_pika.connect_robust(url=rabbitmq_url)

    queue_name = "jobs"

    async with connection:
        # Creating channel
        channel = await connection.channel()

        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(queue_name, auto_delete=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = message.body.decode("ascii")
                    logger.debug("Received: %s", body)
                    job = json.loads(body)
                    # Имитация модели
                    start = default_timer()
                    prediction = model_predict(job["text"])
                    stop = default_timer()
                    result = {
                        "id": job["id"],
                        "embedding": prediction,
                        "model_time": stop - start,
                        "worker_id": worker_id,
                        "model_version": "1.0.0",
                        "node_name": node_name,
                    }
                    await channel.default_exchange.publish(
                        aio_pika.Message(body=json.dumps(result).encode("ascii")),
                        routing_key=job["queue"],
                    )


if __name__ == "__main__":
    asyncio.run(main())
