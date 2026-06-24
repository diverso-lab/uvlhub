from flask_login import current_user
from splent_framework.decorators.decorators import pass_or_abort

from app.features.dataset.services import DataSetService

dataset_service = DataSetService()


def guest_required(f):

    def condition(**kwargs):
        return not current_user.is_authenticated

    return pass_or_abort(condition)(f)
