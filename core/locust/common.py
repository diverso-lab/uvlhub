from bs4 import BeautifulSoup
from faker import Faker

fake = Faker()


def get_csrf_token(response):
    soup = BeautifulSoup(response.text, "html.parser")
    token_tag = soup.find("input", {"name": "csrf_token"})
    if token_tag:
        return token_tag["value"]
    else:
        print("Response HTML:", response.text)
        raise ValueError("CSRF token not found in the response")
