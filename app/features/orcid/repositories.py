from app.features.orcid.models import Orcid
from splent_framework.repositories.BaseRepository import BaseRepository


class OrcidRepository(BaseRepository):
    def __init__(self):
        super().__init__(Orcid)
