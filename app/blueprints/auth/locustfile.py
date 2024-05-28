from locust import HttpUser, TaskSet, task, between
import re
import json
from faker import Faker

fake = Faker()

class UserBehavior(TaskSet):
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.client.verify = False
        self.token = None
        self.signup()
        self.login()

    def get_token(self, response):
        # Extraer el token CSRF del HTML de la respuesta usando una expresión regular
        match = re.search('name="csrf_token" .* value="(.+?)"', response.text)
        if match:
            self.csrftoken = match.group(1)
            print(f"DEBUG: self.csrftoken = {self.csrftoken}")
        else:
            self.csrftoken = None
            print("DEBUG: CSRF token not found")
    @task
    def signup(self):
        response = self.client.get("/signup/")
        self.get_token(f"response: {response.text}")
        if not self.csrftoken:
            print("DEBUG: CSRF token not found during signup")
            return
        signup_data = {
            'name': fake.first_name(),
            'surname': fake.last_name(),
            'email': fake.email(),
            'password': 'password123',
            'csrf_token': self.csrftoken
        }
        headers = {
            'X-CSRFToken': self.csrftoken,
            'content-type': 'application/x-www-form-urlencoded'
        }
        response = self.client.post("/signup/", data=signup_data, headers=headers)
        print(f"DEBUG: signup response.status_code = {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        print(response)
        self.get_token(response)
        if not self.csrftoken:
            print("DEBUG: CSRF token not found during login")
            return
        login_data = {
            'email': fake.email(),
            'password': 'password123',
            'csrf_token': self.csrftoken
        }
        headers = {
            'X-CSRFToken': self.csrftoken,
            'content-type': 'application/x-www-form-urlencoded'
        }
        response = self.client.post("/login", data=login_data, headers=headers)
        if response.status_code == 200:
            self.token = response.cookies.get('session')
        print(f"DEBUG: login response.status_code = {response.status_code}")

    @task
    def logout(self):
        headers = {
            'Authorization': 'Token ' + self.token if self.token else '',
        }
        response = self.client.get("/logout", headers=headers)
        print(f"DEBUG: logout response.status_code = {response.status_code}")


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(5, 9)
    host = "http://localhost"
