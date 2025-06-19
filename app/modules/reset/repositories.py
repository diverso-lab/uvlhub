from app.modules.reset.models import ResetToken
from core.repositories.BaseRepository import BaseRepository


class ResetRepository(BaseRepository):
    def __init__(self):
        super().__init__(ResetToken)
