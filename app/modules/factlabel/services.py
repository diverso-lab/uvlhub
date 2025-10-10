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

        # Generate the characterization (factlabel)
        characterization = FMCharacterization.from_path(hubfile.get_path(), light_fact_label=light_fact_label)

        # === Metadata ===
        characterization.metadata.name = hubfile.name

        # 🔧 DESCRIPTION CLEANUP (fix for broken line rendering)
        html = dataset_metadata.get("description") or ""
        soup = BeautifulSoup(html, "html.parser")

        # Option 1 — Flatten all line breaks and extra spaces
        description = " ".join(soup.get_text().split())

        # Option 2 — Keep <p> paragraphs (if you prefer some structure)
        # description = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))

        characterization.metadata.description = description

        # Other metadata fields
        characterization.metadata.author = dataset_metadata.get("authors")
        characterization.metadata.year = dataset_metadata.get("year")
        characterization.metadata.tags = dataset_metadata.get("tags")
        characterization.metadata.reference = dataset_metadata.get("doi")
        characterization.metadata.domains = dataset_metadata.get("domain")

        return characterization.to_json()
