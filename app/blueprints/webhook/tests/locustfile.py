from locust import HttpUser, TaskSet, task
from core.environment.host import get_host_for_locust_testing


class WebhookBehavior(TaskSet):
    def on_start(self):
        self.index()

    @task
    def index(self):
        response = self.client.get("/webhook")

        if response.status_code != 200:
            print(f"Webhook index failed: {response.status_code}")


class WebhookUser(HttpUser):
    tasks = [WebhookBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
