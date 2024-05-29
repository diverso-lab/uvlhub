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
