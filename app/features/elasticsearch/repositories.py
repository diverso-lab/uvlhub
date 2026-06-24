from app.features.elasticsearch.models import Elasticsearch
from splent_framework.repositories.BaseRepository import BaseRepository


class ElasticsearchRepository(BaseRepository):
    def __init__(self):
        super().__init__(Elasticsearch)
