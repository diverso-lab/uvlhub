from app.modules.confirmemail.models import Confirmemail
from core.repositories.BaseRepository import BaseRepository


class ConfirmemailRepository(BaseRepository):
    def __init__(self):
        super().__init__(Confirmemail)
