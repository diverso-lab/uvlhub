from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.reset.models import ResetToken


class ResetRepository(BaseRepository):
    def __init__(self):
        super().__init__(ResetToken)

    def get_by_token(self, token: str) -> ResetToken | None:
        return self.model.query.filter_by(token=token).first()
