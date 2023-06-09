"""
This module contains functions to interact with Zenodo and perform operations related to depositions
"""

import os
import requests

from dotenv import load_dotenv
from flask_login import current_user

import app
from app.dataset.models import DataSet, FeatureModel

load_dotenv()

ZENODO_API_URL = 'https://sandbox.zenodo.org/api/deposit/depositions'
ZENODO_ACCESS_TOKEN = os.getenv('ZENODO_ACCESS_TOKEN')


def test_zenodo_connection() -> bool:
    """
    Test the connection with Zenodo.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    headers = {"Content-Type": "application/json"}
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.get(ZENODO_API_URL, params=params, headers=headers)
    return response.status_code == 200


def get_all_depositions() -> dict:
    """
    Get all depositions from Zenodo.

    Returns:
        dict: The response in JSON format with the depositions.
    """
    headers = {"Content-Type": "application/json"}
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.get(ZENODO_API_URL, params=params, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get depositions')
    return response.json()


def zenodo_create_new_deposition(dataset: DataSet) -> dict:
    """
    Create a new deposition in Zenodo.

    Args:
        dataset (DataSet): The DataSet object containing the metadata of the deposition.

    Returns:
        dict: The response in JSON format with the details of the created deposition.
    """
    metadata = {
        'title': dataset.ds_meta_data.title,
        'upload_type': 'dataset' if dataset.ds_meta_data.publication_type.value == "none" else 'publication',
        'publication_type': dataset.ds_meta_data.publication_type.value if
        dataset.ds_meta_data.publication_type.value != "none" else None,
        'description': dataset.ds_meta_data.description,
        'creators': [{
            'name': author.name,
            'affiliation': author.affiliation,
            'orcid': '0000-0002-1694-233X'} for author in dataset.ds_meta_data.authors],
        'keywords': dataset.ds_meta_data.tags.split(", "),
        'access_right': 'open',
        'license': 'CC-BY-4.0'
    }

    data = {
        'metadata': metadata
    }

    headers = {"Content-Type": "application/json"}
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.post(ZENODO_API_URL, params=params, json=data, headers=headers)
    if response.status_code != 201:
        error_message = 'Failed to create deposition. Error details: {}'.format(response.json())
        raise Exception(error_message)
    return response.json()


def zenodo_upload_file(deposition_id: int, feature_model: FeatureModel) -> dict:
    """
    Upload a file to a deposition in Zenodo.

    Args:
        deposition_id (int): The ID of the deposition in Zenodo.
        feature_model (FeatureModel): The FeatureModel object representing the feature model.

    Returns:
        dict: The response in JSON format with the details of the uploaded file.
    """
    uvl_filename = feature_model.fm_meta_data.uvl_filename
    data = {'name': uvl_filename}
    user_id = current_user.id
    file_path = os.path.join(app.upload_folder_name(), 'temp', str(user_id), uvl_filename)
    files = {'file': open(file_path, 'rb')}

    publish_url = f'{ZENODO_API_URL}/{deposition_id}/files'
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.post(publish_url, params=params, data=data, files=files)
    if response.status_code != 201:
        error_message = 'Failed to upload files. Error details: {}'.format(response.json())
        raise Exception(error_message)
    return response.json()


def zenodo_publish_deposition(deposition_id: int) -> dict:
    """
    Publish a deposition in Zenodo.

    Args:
        deposition_id (int): The ID of the deposition in Zenodo.

    Returns:
        dict: The response in JSON format with the details of the published deposition.
    """
    headers = {"Content-Type": "application/json"}
    publish_url = f'{ZENODO_API_URL}/{deposition_id}/actions/publish'
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.post(publish_url, params=params, headers=headers)
    if response.status_code != 202:
        raise Exception('Failed to publish deposition')
    return response.json()


def zenodo_get_deposition(deposition_id: int) -> dict:
    """
    Get a deposition from Zenodo.

    Args:
        deposition_id (int): The ID of the deposition in Zenodo.

    Returns:
        dict: The response in JSON format with the details of the deposition.
    """
    headers = {"Content-Type": "application/json"}
    deposition_url = f'{ZENODO_API_URL}/{deposition_id}'
    params = {'access_token': ZENODO_ACCESS_TOKEN}
    response = requests.get(deposition_url, params=params, headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to get deposition')
    return response.json()


def zenodo_get_doi(deposition_id: int) -> str:
    """
    Get the DOI of a deposition from Zenodo.

    Args:
        deposition_id (int): The ID of the deposition in Zenodo.

    Returns:
        str: The DOI of the deposition.
    """
    return zenodo_get_deposition(deposition_id).get('doi')
