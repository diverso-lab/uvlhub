from splent_framework.repositories.BaseRepository import BaseRepository

from app.features.profile.models import UserProfile


class UserProfileRepository(BaseRepository):
    def __init__(self):
        super().__init__(UserProfile)
