"""Утилита для нагрузочного тестирования"""
from asyncio.log import logger
from typing import List, Optional
import logging
import json

import asyncio

import aiohttp
import typer


logger = logging.getLogger()

async def send_request(url: str, string : str) -> Optional[List[float]]:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json = string) as response:
            if response.status == 200:
                result = await response.json()
                return result
            logger.error("Got %d status on request \"%s\"", response.status, url)
            return None


async def load_test(url: str, file_name: str, n_repeats: int) -> None:
    with open(file_name, "rt") as text_file:
        lines = [l for l in text_file if l]
    n_lines = len(lines)
    if n_lines == 0:
        raise Exception(f"Input file \"{file_name}\" is empty.")
    if n_repeats == 0:
        n_repeats = n_lines
    tasks = [asyncio.create_task(send_request(url, lines[i % n_lines])) for i in range(n_repeats)]
    results = await asyncio.gather(*tasks)

    
def main(url: str, file_name: str, n_repeats: int = typer.Argument(0)) -> None:
    asyncio.run(load_test(url, file_name, n_repeats))

if __name__=="__main__":
    typer.run(main)