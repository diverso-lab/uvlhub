from app.modules.factlabel.models import Factlabel
from core.repositories.BaseRepository import BaseRepository


class FactlabelRepository(BaseRepository):
    def __init__(self):
        super().__init__(Factlabel)
