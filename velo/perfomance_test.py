import json
from locust import HttpUser, task, between


class PerformanceTests(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def testFastApi(self):
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.client.post("/transform", data=json.dumps("Тест!"), headers=headers)
