from locust import HttpUser, TaskSet, task

from app.environment.host import get_host_for_locust_testing


class GithubBehavior(TaskSet):
    def on_start(self):
        self.index()

    @task
    def index(self):
        response = self.client.get("/github")

        if response.status_code != 200:
            print(f"Github index failed: {response.status_code}")


class GithubUser(HttpUser):
    tasks = [GithubBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
