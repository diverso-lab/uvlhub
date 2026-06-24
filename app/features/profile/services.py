from splent_framework.services.BaseService import BaseService

from app.features.profile.repositories import UserProfileRepository


class UserProfileService(BaseService):
    def __init__(self):
        super().__init__(UserProfileRepository())

    def update_profile(self, user_profile_id, form):
        if not form.validate():
            return None, form.errors

        # Only the user-editable fields are written; ORCID stays under the OAuth flow.
        profile = self.repository.update(
            user_profile_id,
            name=form.name.data,
            surname=form.surname.data,
            affiliation=form.affiliation.data,
        )
        return profile, None

    def paginate_user_datasets(self, user_id, page: int = 1, per_page: int = 5):
        # Imported lazily to avoid a hard import cycle with the dataset feature.
        from app.features.dataset.models import DataSet

        return (
            DataSet.query.filter_by(user_id=user_id)
            .order_by(DataSet.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
