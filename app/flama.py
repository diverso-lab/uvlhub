import os

import requests
from flask_login import current_user

import app

FLAMAPY_API_URL = "http://flamapyapi:8000"
FLAMAPY_API_VERSION = "api/v1/operations"


def flamapy_valid_model(uvl_filename: str, user=None) -> bool:
    user_id = current_user.id if user is None else user.id
    file_path = os.path.join(app.upload_folder_name(), 'temp', str(user_id), uvl_filename)
    files = {'model': open(file_path, 'rb')}

    publish_url = f'{FLAMAPY_API_URL}/{FLAMAPY_API_VERSION}/valid'

    response = requests.post(publish_url, files=files)
    if response.status_code != 200:
        error_message = 'FlamaPy Error! Failed to send UVL file. Error details: {}'.format(response.json())
        raise Exception(error_message)
    return response.json()
