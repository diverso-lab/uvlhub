from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.orcid.models import Orcid


class OrcidRepository(BaseRepository):
    def __init__(self):
        super().__init__(Orcid)

    def get_by_orcid_id(self, orcid_id: str) -> Orcid | None:
        return self.model.query.filter_by(orcid_id=orcid_id).first()
