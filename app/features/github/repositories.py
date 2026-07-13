from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.github.models import Github


class GithubRepository(BaseRepository):
    def __init__(self):
        super().__init__(Github)

    def get_by_github_id(self, github_id: int) -> Github | None:
        return self.model.query.filter_by(github_id=github_id).first()
