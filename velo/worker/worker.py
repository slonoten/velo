"""Сервис для модели"""

import asyncio
import logging
import json
import time
import uuid
from timeit import default_timer
import platform

import aio_pika

worker_id = str(uuid.uuid1())

node_name = platform.node()

logger = logging.getLogger(f"worker-{worker_id}")


async def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    connection = await aio_pika.connect_robust(host="localhost")

    queue_name = "jobs"

    async with connection:
        # Creating channel
        channel = await connection.channel()

        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = message.body.decode("ascii")
                    logger.debug("Received: %s", body)
                    job = json.loads(body)
                    # Имитация модели
                    start = default_timer()
                    time.sleep(0.01)
                    stop = default_timer()
                    result = {
                        "id": job["id"], 
                        "embedding": [1.0, 2.0, 3.0], 
                        "model_time": stop - start,
                        "worker_id": worker_id,
                        "model_version": "1.0.0",
                        "node_name": node_name
                    }
                    await channel.default_exchange.publish(
                        aio_pika.Message(body = json.dumps(result).encode("ascii")),
                        routing_key=job["queue"]
                    )


if __name__ == "__main__":
    asyncio.run(main())