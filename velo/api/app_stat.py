"""Собираем статистику"""
from typing import Dict, Any
from collections import defaultdict
from datetime import datetime
from collections import deque


N_LAST_TIMES_LENGTH = 1000

# pylint: disable=no-name-in-module
from pydantic import BaseModel


class WorkerStat(BaseModel):
    last_seen: datetime
    model_version: str
    node_name: str
    model_time: float


class ModelStat(BaseModel):
    workers: Dict[str, WorkerStat]
    queue_lenght: int
    response_time: float


class WorkerStatStore:
    def __init__(self):
        self.model_times = deque()
        self.first_seen = datetime.now()

    def update(self, result) -> None:
        self.last_seen = datetime.now()
        self.model_version = result["model_version"]
        self.model_times.append(result["model_time"])
        if len(self.model_times) > N_LAST_TIMES_LENGTH:
            self.model_times.popleft()
        self.node_name = result["node_name"]

    def get_worker_stat(self) -> WorkerStat:
        return WorkerStat(
            last_seen=self.last_seen,
            model_version=self.model_version,
            node_name=self.node_name,
            model_time=sum(self.model_times)
            / len(self.model_times),  # divsion by zero is impossible
        )


class ModelStatStore:
    def __init__(self):
        self.workers = defaultdict(WorkerStatStore)
        self.response_times = deque()

    def update(self, result: Dict[str, Any], response_time: float) -> None:
        worker_id = result["worker_id"]
        worker = self.workers[worker_id]
        worker.update(result)
        self.response_times.append(response_time)
        if len(self.response_times) > N_LAST_TIMES_LENGTH:
            self.response_times.popleft()

    @property
    def mean_response_time(self):
        if self.response_times:
            return sum(self.response_times) / len(self.response_times)
        else:
            return 0.0
