from app.modules.elasticsearch.repositories import ElasticsearchRepository
from core.services.BaseService import BaseService
from elasticsearch import Elasticsearch, NotFoundError


class ElasticsearchService(BaseService):
    def __init__(self):
        super().__init__(ElasticsearchRepository())

    def __init__(self, host="http://elasticsearch:9200", index_name="search_index"):
        self.es = Elasticsearch(hosts=[host])
        self.index_name = index_name

    def create_index_if_not_exists(self):
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(index=self.index_name, body={
                "mappings": {
                    "properties": {
                        "type": {"type": "keyword"},
                        "title": {"type": "text"},
                        "filename": {"type": "text"},
                        "doi": {"type": "keyword"},
                        "authors": {"type": "text"},
                        "content": {"type": "text"},
                        "dataset_id": {"type": "integer"},
                        "feature_model_id": {"type": "integer"}
                    }
                }
            })

    def index_document(self, doc_id: str, data: dict):
        self.es.index(index=self.index_name, id=doc_id, document=data)

    def delete_document(self, doc_id: str):
        try:
            self.es.delete(index=self.index_name, id=doc_id)
        except NotFoundError:
            pass

    def search(self, query: str, size=10):
        result = self.es.search(index=self.index_name, query={
            "multi_match": {
                "query": query,
                "fields": ["title^3", "authors", "filename^2", "content"],
                "fuzziness": "AUTO"
            }
        }, size=size)
        return [hit["_source"] for hit in result["hits"]["hits"]]
