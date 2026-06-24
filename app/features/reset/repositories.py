from app.features.reset.models import ResetToken
from splent_framework.repositories.BaseRepository import BaseRepository


class ResetRepository(BaseRepository):
    def __init__(self):
        super().__init__(ResetToken)
