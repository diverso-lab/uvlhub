import logging
import os
import requests

from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.zenodo.repositories import ZenodoRepository

from core.configuration.configuration import uploads_folder_name
from dotenv import load_dotenv
from flask import jsonify, Response
from flask_login import current_user


from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()


class ZenodoService(BaseService):

    def __init__(self):
        super().__init__(ZenodoRepository())
        self.ZENODO_ACCESS_TOKEN = self.get_zenodo_access_token()
        self.ZENODO_API_URL = self.get_zenodo_url()
        self.headers = {"Content-Type": "application/json"}
        self.params = {"access_token": self.ZENODO_ACCESS_TOKEN}

    def get_zenodo_url(self):

        FLASK_ENV = os.getenv("FLASK_ENV", "development")
        ZENODO_API_URL = ""

        if FLASK_ENV == "development":
            ZENODO_API_URL = os.getenv(
                "ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions"
            )
        elif FLASK_ENV == "production":
            ZENODO_API_URL = os.getenv(
                "ZENODO_API_URL", "https://zenodo.org/api/deposit/depositions"
            )
        else:
            ZENODO_API_URL = os.getenv(
                "ZENODO_API_URL", "https://sandbox.zenodo.org/api/deposit/depositions"
            )

        return ZENODO_API_URL

    def get_zenodo_access_token(self):
        return os.getenv("ZENODO_ACCESS_TOKEN")

    def test_connection(self) -> bool:
        """
        Test the connection with Zenodo.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        response = requests.get(
            self.ZENODO_API_URL, params=self.params, headers=self.headers
        )
        return response.status_code == 200

    def test_full_connection(self) -> Response:
        """
        Test the connection with Zenodo by creating a deposition, uploading an empty test file, and deleting the
        deposition.

        Returns:
            bool: True if the connection, upload, and deletion are successful, False otherwise.
        """

        success = True

        # Create a test file
        working_dir = os.getenv("WORKING_DIR", "")
        file_path = os.path.join(working_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("This is a test file with some content.")

        messages = []  # List to store messages

        # Step 1: Create a deposition on Zenodo
        data = {
            "metadata": {
                "title": "Test Deposition",
                "upload_type": "dataset",
                "description": "This is a test deposition created via Zenodo API",
                "creators": [{"name": "John Doe"}],
            }
        }

        response = requests.post(
            self.ZENODO_API_URL, json=data, params=self.params, headers=self.headers
        )

        if response.status_code != 201:
            return jsonify(
                {
                    "success": False,
                    "messages": (
                        f"Failed to create test deposition on Zenodo. "
                        f"Response code: {response.status_code}, {response.json()}"
                    ),
                }
            )

        deposition_id = response.json()["id"]

        # Step 2: Upload an empty file to the deposition
        data = {"name": "test_file.txt"}
        files = {"file": open(file_path, "rb")}
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(
            publish_url, params=self.params, data=data, files=files
        )
        files["file"].close()  # Close the file after uploading

        logger.info(f"Publish URL: {publish_url}")
        logger.info(f"Params: {self.params}")
        logger.info(f"Data: {data}")
        logger.info(f"Files: {files}")
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.content}")

        if response.status_code != 201:
            messages.append(
                f"Failed to upload test file to Zenodo. Response code: {response.status_code}"
            )
            success = False

        # Step 3: Delete the deposition
        response = requests.delete(
            f"{self.ZENODO_API_URL}/{deposition_id}", params=self.params
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": success, "messages": messages})

    def get_all_depositions(self) -> dict:
        """
        Get all depositions from Zenodo.

        Returns:
            dict: The response in JSON format with the depositions.
        """
        response = requests.get(
            self.ZENODO_API_URL, params=self.params, headers=self.headers
        )
        if response.status_code != 200:
            raise Exception("Failed to get depositions")
        return response.json()

    def create_new_deposition(self, dataset: DataSet, anonymous: bool = False) -> dict:
        """
        Create a new deposition in Zenodo.

        Args:
            dataset (DataSet): The DataSet object containing the metadata of the deposition.
            anonymous (bool): Whether to anonymize the creators metadata.

        Returns:
            dict: The response in JSON format with the details of the created deposition.
        """

        logger.info("Dataset sending to Zenodo...")
        logger.info(f"Publication type... {dataset.ds_meta_data.publication_type.value}")
        logger.info(f"Anonymous upload: {anonymous}")

        upload_type = (
            "dataset"
            if dataset.ds_meta_data.publication_type.value == "none"
            else "publication"
        )
        publication_type = (
            dataset.ds_meta_data.publication_type.value
            if dataset.ds_meta_data.publication_type.value != "none"
            else None
        )

        if anonymous or not dataset.ds_meta_data.authors:
            creators = [{"name": "Anonymous"}]
        else:
            creators = [
                {
                    "name": author.name,
                    **({"affiliation": author.affiliation} if author.affiliation else {}),
                    **({"orcid": author.orcid} if author.orcid else {}),
                }
                for author in dataset.ds_meta_data.authors
            ]

        keywords = (
            ["uvlhub"]
            if not dataset.ds_meta_data.tags
            else dataset.ds_meta_data.tags.replace(", ", ",").split(",") + ["uvlhub"]
        )

        metadata = {
            "title": dataset.ds_meta_data.title,
            "upload_type": upload_type,
            "publication_type": publication_type,
            "description": dataset.ds_meta_data.description,
            "creators": creators,
            "keywords": keywords,
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        data = {"metadata": metadata}

        response = requests.post(
            self.ZENODO_API_URL, params=self.params, json=data, headers=self.headers
        )
        if response.status_code != 201:
            error_message = f"Failed to create deposition. Error details: {response.json()}"
            raise Exception(error_message)

        return response.json()

    def upload_file(
        self,
        dataset: DataSet,
        deposition_id: int,
        feature_model: FeatureModel,
        user=None,
    ) -> dict:
        """
        Upload a file to a deposition in Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.
            feature_model (FeatureModel): The FeatureModel object representing the feature model.
            user (FeatureModel): The User object representing the file owner.

        Returns:
            dict: The response in JSON format with the details of the uploaded file.
        """
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        data = {"name": uvl_filename}
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(
            uploads_folder_name(),
            f"user_{str(user_id)}",
            f"dataset_{dataset.id}",
            "uvl",
            uvl_filename,
        )

        files = {"file": open(file_path, "rb")}

        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(
            publish_url, params=self.params, data=data, files=files
        )
        if response.status_code != 201:
            error_message = f"Failed to upload files. Error details: {response.json()}"
            raise Exception(error_message)
        return response.json()

    def upload_zip(self, dataset: DataSet, deposition_id: int, zip_path: str) -> dict:
        """
        Upload a ZIP file containing all UVL models to a Zenodo deposition.
        """
        file_name = os.path.basename(zip_path)
        data = {"name": file_name}
        with open(zip_path, "rb") as file_obj:
            files = {"file": file_obj}
            upload_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
            response = requests.post(
                upload_url, params=self.params, data=data, files=files
            )

        if response.status_code != 201:
            logger.error(f"Failed to upload ZIP: {response.content}")
            raise Exception(f"Error uploading ZIP to Zenodo: {response.json()}")

        return response.json()

    def publish_deposition(self, deposition_id: int):
        """
        Publish a deposition on Zenodo.

        Args:
            deposition_id (int): The ID of the deposition to be published.
        """
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/actions/publish"
        logger.info(f"Publishing deposition {deposition_id} at {publish_url}")

        response = requests.post(
            publish_url,
            params=self.params,
            headers=self.headers,
        )

        logger.info(f"Zenodo publish response code: {response.status_code}")
        logger.info(f"Zenodo publish response body: {response.text}")

        if response.status_code != 202:
            raise Exception("Failed to publish deposition")


    def update_deposition(self, deposition_id: int, metadata: dict) -> dict:
        """
        Update a deposition in Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.
            metadata (dict): The metadata to update the deposition with.

        Returns:
            dict: The response in JSON format with the details of the updated deposition.
        """

        # Step 1: Change the deposition to an editable draft
        edit_url = f"{self.ZENODO_API_URL}/{deposition_id}/actions/edit"
        logger.info(f"Zenodo edit URL: {edit_url}")
        edit_response = requests.post(
            edit_url, params=self.params, headers=self.headers
        )

        if edit_response.status_code != 201:
            error_message = (
                f"Failed to change deposition to editable draft. "
                f"Status code: {edit_response.status_code}. "
                f"Error details: {edit_response.json()}"
            )
            raise Exception(error_message)

        # Step 2: Update the deposition metadata
        data = {"metadata": metadata}
        update_url = f"{self.ZENODO_API_URL}/{deposition_id}"
        logger.info(f"Zenodo update URL: {update_url}")
        update_response = requests.put(
            update_url, params=self.params, json=data, headers=self.headers
        )

        if update_response.status_code != 200:
            error_message = (
                f"Failed to update deposition. "
                f"Status code: {update_response.status_code}. "
                f"Error details: {update_response.json()}"
            )
            raise Exception(error_message)

        # Step 3: Re-publish deposition
        self.publish_deposition(deposition_id=deposition_id)

        return update_response.json()

    def get_deposition(self, deposition_id: int) -> dict:
        """
        Get a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            dict: The response in JSON format with the details of the deposition.
        """
        deposition_url = f"{self.ZENODO_API_URL}/{deposition_id}"
        response = requests.get(
            deposition_url, params=self.params, headers=self.headers
        )
        if response.status_code != 200:
            raise Exception("Failed to get deposition")
        return response.json()

    def get_doi(self, deposition_id: int) -> str:
        """
        Get the DOI of a deposition from Zenodo.

        Args:
            deposition_id (int): The ID of the deposition in Zenodo.

        Returns:
            str: The DOI of the deposition.
        """
        return self.get_deposition(deposition_id).get("doi")

