from app.features.factlabel.models import Factlabel
from splent_framework.repositories.BaseRepository import BaseRepository


class FactlabelRepository(BaseRepository):
    def __init__(self):
        super().__init__(Factlabel)
