import requests
import os

from dotenv import load_dotenv

load_dotenv()


ZENODO_API_URL = 'https://zenodo.org/api/deposit/depositions'
ZENODO_ACCESS_TOKEN = {os.getenv('ZENODO_ACCESS_TOKEN')}

def test_zenodo_connection():
    headers = {"Content-Type": "application/json"}
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.get(ZENODO_API_URL, params=params, headers=headers)
    return response.status_code == 200

def get_all_depositions():
    headers = {"Content-Type": "application/json"}
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.get(ZENODO_API_URL, params=params, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get depositions')
    return response.json()

def create_new_deposition(data):
    headers = {"Content-Type": "application/json"}
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.post(ZENODO_API_URL, params=params, json=data, headers=headers)
    if response.status_code != 201:
        raise Exception('Failed to create deposition')
    return response.json()

def publish_deposition(deposition_id):
    headers = {"Content-Type": "application/json"}
    publish_url = f'{ZENODO_API_URL}/{deposition_id}/actions/publish'
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.post(publish_url, params=params, headers=headers)
    if response.status_code != 202:
        raise Exception('Failed to publish deposition')
    return response.json()

def get_doi(deposition_id):
    headers = {"Content-Type": "application/json"}
    deposition_url = f'{ZENODO_API_URL}/{deposition_id}'
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.get(deposition_url, params=params, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get deposition')
    return response.json().get('doi')
