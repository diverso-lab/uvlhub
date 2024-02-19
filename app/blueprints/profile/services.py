from app.blueprints.profile.repositories import UserProfileRepository
from app.services.BaseService import BaseService


class UserProfileService(BaseService):
    def __init__(self):
        super().__init__(UserProfileRepository())

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None
        else:
            return None, form.errors