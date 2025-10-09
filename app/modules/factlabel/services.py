import logging
from typing import Any
from bs4 import BeautifulSoup
from fmfactlabel import FMCharacterization

from app.modules.factlabel.repositories import FactlabelRepository
from app.modules.hubfile.models import Hubfile
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class FactlabelService(BaseService):
    def __init__(self):
        super().__init__(FactlabelRepository())

    def get_characterization(self, hubfile: Hubfile, light_fact_label: bool = False) -> Any:
        dataset_metadata = hubfile.get_dataset().get_zenodo_metadata()
        logger.info(f"dataset_metadata: {dataset_metadata}")

        # Aquí ya usamos el flag dinámicamente
        characterization = FMCharacterization.from_path(hubfile.get_path(), light_fact_label=light_fact_label)

        # Fill metadata
        characterization.metadata.name = hubfile.name
        html = dataset_metadata.get("description") or ""
        description = BeautifulSoup(html, "html.parser").get_text().strip()
        characterization.metadata.description = description
        characterization.metadata.author = dataset_metadata.get("authors")
        characterization.metadata.year = dataset_metadata.get("year")
        characterization.metadata.tags = dataset_metadata.get("tags")
        characterization.metadata.reference = dataset_metadata.get("doi")
        characterization.metadata.domains = dataset_metadata.get("domain")

        return characterization.to_json()
