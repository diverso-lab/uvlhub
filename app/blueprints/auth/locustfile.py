from locust import HttpUser, TaskSet, task, between
from faker import Faker
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

fake = Faker()

# Load environment variables
load_dotenv()

def get_host():
    working_dir = os.getenv('WORKING_DIR', "")
    
    if working_dir == "":
        return "http://localhost:5000"
    elif working_dir == "/app/":
        return "http://nginx_web_server"
    elif working_dir == "/vagrant/":
        return "http://localhost:5000"
    else:
        raise ValueError("Unknown WORKING_DIR value")
    
def get_csrf_token(response):
        soup = BeautifulSoup(response.text, 'html.parser')
        token_tag = soup.find('input', {'name': 'csrf_token'})
        if token_tag:
            return token_tag['value']
        else:
            print("Response HTML:", response.text)
            raise ValueError("CSRF token not found in the response")

class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)
        print(f"csrf_token signup: {csrf_token}")

        response = self.client.post("/signup", data={
            "email": fake.email(),
            "password": fake.password(),
            "csrf_token": csrf_token
        })
        if response.status_code != 200:
            print(f"Signup failed: {response.status_code}")

class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        response = self.client.get("/logout")
        if response.status_code != 200:
            print(f"Logout failed or no active session: {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            print("Already logged in or unexpected response, redirecting to logout")
            self.ensure_logged_out()
            response = self.client.get("/login")
        
        csrf_token = get_csrf_token(response)
        print(f"csrf_token login: {csrf_token}")

        email = fake.email()
        password = fake.password()

        response = self.client.post("/login", data={
            "email": 'user1@example.com',
            "password": '1234',
            "csrf_token": csrf_token
        })
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")

class WebsiteUser(HttpUser):
    tasks = [SignupBehavior, LoginBehavior]
    wait_time = between(5, 9)
    host = get_host()
