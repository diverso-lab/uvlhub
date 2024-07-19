from app.modules.orcid.models import Orcid
from core.repositories.BaseRepository import BaseRepository


class OrcidRepository(BaseRepository):
    def __init__(self):
        super().__init__(Orcid)
