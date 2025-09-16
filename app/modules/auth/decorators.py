from flask_login import current_user

from app.modules.dataset.services import DataSetService
from core.decorators.decorators import pass_or_abort

dataset_service = DataSetService()


def guest_required(f):

    def condition(**kwargs):
        return not current_user.is_authenticated

    return pass_or_abort(condition)(f)
