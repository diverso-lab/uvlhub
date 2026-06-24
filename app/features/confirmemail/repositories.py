from app.features.confirmemail.models import Confirmemail
from splent_framework.repositories.BaseRepository import BaseRepository


class ConfirmemailRepository(BaseRepository):
    def __init__(self):
        super().__init__(Confirmemail)
