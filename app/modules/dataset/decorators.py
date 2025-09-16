from flask_login import current_user

from app.modules.dataset.services import DataSetService
from core.decorators.decorators import pass_or_abort

dataset_service = DataSetService()


def is_dataset_owner(f):

    def condition(**kwargs):
        dataset_id = kwargs.get("dataset_id")
        dataset = dataset_service.get_or_404(dataset_id)
        return dataset.user_id == current_user.id

    return pass_or_abort(condition)(f)
