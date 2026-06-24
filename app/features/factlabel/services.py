import json
import logging
from typing import Any

from bs4 import BeautifulSoup
from fmfactlabel import FMCharacterization

from app.features.hubfile.models import Hubfile
from app.features.hubfile.repositories import HubfileViewRecordRepository

logger = logging.getLogger(__name__)


class FactlabelNotReady(Exception):
    """The fact label for a hubfile has not been generated yet."""


class InvalidFactlabel(Exception):
    """The stored fact label JSON is corrupted."""


class FactlabelService:
    """Owns no entity of its own: it reads the fact label stored on a hubfile and
    delegates view bookkeeping to the hubfile domain."""

    def __init__(self):
        self.view_record_repository = HubfileViewRecordRepository()

    def parse_factlabel(self, hubfile: Hubfile) -> dict:
        factlabel = hubfile.factlabel
        if not factlabel or not factlabel.factlabel_json:
            raise FactlabelNotReady("FactLabel not ready yet")
        try:
            return json.loads(factlabel.factlabel_json)
        except (ValueError, TypeError):
            raise InvalidFactlabel("Invalid FactLabel JSON in DB")

    def record_view(self, hubfile: Hubfile, user_cookie: str) -> None:
        if not self.view_record_repository.the_record_exists(hubfile, user_cookie):
            self.view_record_repository.create_new_record(hubfile, user_cookie)

    def get_characterization(self, hubfile: Hubfile, light_fact_label: bool = False) -> Any:
        dataset_metadata = hubfile.get_dataset().get_zenodo_metadata()
        logger.info(f"dataset_metadata: {dataset_metadata}")

        characterization = FMCharacterization.from_path(hubfile.get_path(), light_fact_label=light_fact_label)
        characterization.metadata.name = hubfile.name

        # Flatten the HTML description into a single clean line.
        html = dataset_metadata.get("description") or ""
        characterization.metadata.description = " ".join(BeautifulSoup(html, "html.parser").get_text().split())

        characterization.metadata.author = dataset_metadata.get("authors")
        characterization.metadata.year = dataset_metadata.get("year")
        characterization.metadata.tags = dataset_metadata.get("tags")
        characterization.metadata.reference = dataset_metadata.get("doi")
        characterization.metadata.domains = dataset_metadata.get("domain")

        return characterization.to_json()
