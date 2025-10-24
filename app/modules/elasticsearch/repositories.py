from app.modules.elasticsearch.models import Elasticsearch
from core.repositories.BaseRepository import BaseRepository


class ElasticsearchRepository(BaseRepository):
    def __init__(self):
        super().__init__(Elasticsearch)
