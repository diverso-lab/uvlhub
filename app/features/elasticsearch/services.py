import logging
import time
from datetime import datetime

from elasticsearch import ApiError, BadRequestError, ConnectionError, Elasticsearch, NotFoundError

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """Thin wrapper around the Elasticsearch client. It owns no relational entity,
    so it is a plain service rather than a repository-backed one."""

    def __init__(self, host="http://elasticsearch:9200", index_name="search_index"):
        if not isinstance(index_name, str):
            raise ValueError("Index name must be a string.")
        if not index_name:
            raise ValueError("Index name is empty.")
        if any(c in index_name for c in r" #?/\*\"<>|,"):
            raise ValueError(f"Invalid index name: {index_name}")
        if not index_name.islower():
            raise ValueError("Index name must be lowercase.")
        if index_name.startswith(("-", "_", "+")):
            raise ValueError("Index name cannot start with -, _ or +.")

        self.es = Elasticsearch(hosts=[host])
        self.index_name = index_name

        logger.info("Initializing ElasticsearchService (host=%s, index='%s')", host, index_name)
        if not self.wait_for_elasticsearch():
            logger.error("Elasticsearch is not responding after several attempts; it may fail later.")

    def wait_for_elasticsearch(self, retries=5, delay=2):
        for attempt in range(retries):
            if self.es.ping():
                logger.debug("Elasticsearch responded to ping on attempt %s.", attempt + 1)
                return True
            logger.debug("Elasticsearch ping attempt %s failed; retrying in %ss.", attempt + 1, delay)
            time.sleep(delay)
        return False

    def create_index_if_not_exists(self):
        try:
            if self.es.indices.exists(index=self.index_name):
                logger.info("Index '%s' already exists.", self.index_name)
                return

            logger.info("Creating index '%s'...", self.index_name)
            self.es.indices.create(
                index=self.index_name,
                body={
                    "settings": {
                        "analysis": {
                            "analyzer": {
                                "custom_text_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": ["lowercase", "asciifolding"],
                                },
                                "custom_filename_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "custom_filename_tokenizer",
                                    "filter": ["lowercase", "asciifolding"],
                                },
                            },
                            "tokenizer": {
                                "custom_filename_tokenizer": {
                                    "type": "pattern",
                                    "pattern": "[_\\W]+",
                                }
                            },
                        },
                        "index": {"number_of_shards": 1, "number_of_replicas": 0},
                    },
                    "mappings": {
                        "properties": {
                            "type": {"type": "keyword"},
                            "title": {"type": "text", "analyzer": "custom_text_analyzer"},
                            "filename": {"type": "text", "analyzer": "custom_filename_analyzer"},
                            "created_at": {"type": "date"},
                            "doi": {"type": "keyword"},
                            "authors": {
                                "type": "nested",
                                "properties": {
                                    "name": {"type": "text", "analyzer": "custom_text_analyzer"},
                                    "affiliation": {"type": "text", "analyzer": "custom_text_analyzer"},
                                    "orcid": {"type": "keyword"},
                                },
                            },
                            "content": {"type": "text", "analyzer": "custom_text_analyzer"},
                            "dataset_id": {"type": "integer"},
                            "feature_model_id": {"type": "integer"},
                            "dataset_title": {"type": "text", "analyzer": "custom_text_analyzer"},
                        }
                    },
                },
            )
            logger.info("Index '%s' created successfully.", self.index_name)
        except BadRequestError as e:
            logger.error("BadRequestError while checking/creating index: %s (body=%s)", e, getattr(e, "body", None))
            raise
        except ConnectionError as e:
            logger.error("Could not connect to Elasticsearch: %s", e)
            raise
        except ApiError as e:
            logger.error("API error while creating index: %s", e)
            raise
        except Exception as e:
            logger.exception("Unexpected error while creating index: %s", e)
            raise

    def index_document(self, doc_id: str, data: dict):
        try:
            self.es.index(index=self.index_name, id=doc_id, document=data)
            logger.debug("Document '%s' indexed in '%s'.", doc_id, self.index_name)
        except Exception as e:
            logger.error("Could not index document '%s': %s", doc_id, e)
            raise

    def delete_document(self, doc_id: str):
        try:
            self.es.delete(index=self.index_name, id=doc_id)
            logger.debug("Document '%s' deleted from '%s'.", doc_id, self.index_name)
        except NotFoundError:
            logger.info("Document '%s' not found. Nothing to delete.", doc_id)
        except Exception as e:
            logger.error("Could not delete document '%s': %s", doc_id, e)
            raise

    def delete_by_dataset_id(self, dataset_id: int):
        try:
            self.es.delete_by_query(
                index=self.index_name,
                body={"query": {"term": {"dataset_id": dataset_id}}},
                conflicts="proceed",
                refresh=True,
            )
            logger.debug("Elasticsearch docs deleted for dataset_id=%s.", dataset_id)
        except Exception as e:
            logger.error("Failed to delete ES docs for dataset_id=%s: %s", dataset_id, e)
            raise

    def search(
        self,
        query: str,
        publication_type=None,
        sorting="newest",
        tags=None,
        date_from=None,
        date_to=None,
        page=1,
        size=10,
    ):
        try:
            must_clauses = []
            filter_clauses = []

            if query:
                must_clauses.append(
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "title^3",
                                "authors.name",
                                "authors.affiliation",
                                "filename^2",
                                "content",
                                "tags",
                            ],
                            "fuzziness": "AUTO",
                        }
                    }
                )

            if publication_type:
                filter_clauses.append({"term": {"publication_type.keyword": publication_type}})

            if tags:
                filter_clauses.append({"terms": {"tags.keyword": tags}})

            if date_from or date_to:
                filter_clauses.extend(self._date_range_filter(date_from, date_to))

            sort_clause = [
                {"created_at": {"order": "desc"}} if sorting == "newest" else {"created_at": {"order": "asc"}}
            ]

            body = {
                "query": {
                    "bool": {
                        "must": must_clauses if must_clauses else [{"match_all": {}}],
                        "filter": filter_clauses,
                    }
                },
                "sort": sort_clause,
            }

            result = self.es.search(index=self.index_name, body=body, from_=(page - 1) * size, size=size)
            hits = result["hits"]["hits"]
            total = result["hits"]["total"]["value"]

            logger.debug("Search completed (page %s, results %s, total %s).", page, len(hits), total)
            return [self._format_hit(hit) for hit in hits], total

        except Exception as e:
            logger.error("Search failed: %s", e)
            raise

    @staticmethod
    def _date_range_filter(date_from, date_to):
        try:
            created_at = {}
            if date_from:
                created_at["gte"] = datetime.strptime(date_from, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
            if date_to:
                created_at["lte"] = datetime.strptime(date_to, "%Y-%m-%d").strftime("%Y-%m-%dT23:59:59Z")
            return [{"range": {"created_at": created_at}}] if created_at else []
        except ValueError as e:
            logger.warning("Invalid date format received: from=%s, to=%s. Error: %s", date_from, date_to, e)
            return []

    @staticmethod
    def _format_hit(hit):
        """Formats an Elasticsearch hit with human-readable dates and sizes."""
        source = hit["_source"]

        if "created_at" in source:
            try:
                source["created_at"] = datetime.fromisoformat(source["created_at"]).strftime("%d %b %Y, %H:%M")
            except Exception:
                pass

        if "total_size_in_bytes" in source:
            source["total_size_in_human_format"] = ElasticsearchService._human_readable_size(
                source["total_size_in_bytes"]
            )

        return source

    @staticmethod
    def _human_readable_size(size_bytes):
        if size_bytes is None:
            return ""
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(min(len(size_name) - 1, max(0, (size_bytes.bit_length() - 1) // 10)))
        p = 1 << (i * 10)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"


class IndexingService:
    """Encapsulates Elasticsearch indexing logic."""

    def __init__(self, index_dataset_fn, index_hubfile_fn, logger):
        self.index_dataset = index_dataset_fn
        self.index_hubfile = index_hubfile_fn
        self.logger = logger

    def index_dataset_and_hubfiles(self, dataset, created_fms):
        try:
            self.index_dataset(dataset)
            self.logger.info(f"[INDEX] Dataset {dataset.id} indexed")

            for fm in created_fms:
                for hubfile in fm.hubfiles:
                    self.index_hubfile(hubfile)
                    self.logger.info(f"[INDEX] Hubfile {hubfile.id} indexed")

        except Exception as exc:
            self.logger.exception(f"[INDEX ERROR] Failed to index dataset {dataset.id}: {exc}")
            raise
