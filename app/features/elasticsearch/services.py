import time
from datetime import datetime

from elasticsearch import ApiError, BadRequestError, ConnectionError, Elasticsearch, NotFoundError

from app.features.elasticsearch.repositories import ElasticsearchRepository
from splent_framework.services.BaseService import BaseService


class ElasticsearchService(BaseService):
    def __init__(self, host="http://elasticsearch:9200", index_name="search_index"):
        print("[INIT] Initializing ElasticsearchService...")
        print(f"[INIT] Host: {host}")
        print(f"[INIT] Index name: '{index_name}'")

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

        super().__init__(ElasticsearchRepository())

        self.es = Elasticsearch(hosts=[host])
        self.index_name = index_name

        if not self.wait_for_elasticsearch():
            print("[ERROR] Elasticsearch is not responding after several attempts. Continuing, but may fail later.")

        print("[INIT] ElasticsearchService initialized successfully.\n")

    def wait_for_elasticsearch(self, retries=5, delay=2):
        print("[WAIT] Waiting for Elasticsearch to become available...")
        for attempt in range(retries):
            if self.es.ping():
                print(f"[WAIT] Elasticsearch responded to ping on attempt {attempt + 1}.")
                return True
            print(f"[WAIT] Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        return False

    def create_index_if_not_exists(self):
        print(f"[DEBUG] Checking whether index '{self.index_name}' exists...")
        try:
            exists = self.es.indices.exists(index=self.index_name)
            print(f"[DEBUG] Does index '{self.index_name}' exist? {exists}")

            if not exists:
                print(f"[DEBUG] Creating index '{self.index_name}'...")

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
                                "title": {
                                    "type": "text",
                                    "analyzer": "custom_text_analyzer",
                                },
                                "filename": {
                                    "type": "text",
                                    "analyzer": "custom_filename_analyzer",
                                },
                                "created_at": {"type": "date"},
                                "doi": {"type": "keyword"},
                                "authors": {
                                    "type": "nested",  # or "object" if you won't query internal fields
                                    "properties": {
                                        "name": {
                                            "type": "text",
                                            "analyzer": "custom_text_analyzer",
                                        },
                                        "affiliation": {
                                            "type": "text",
                                            "analyzer": "custom_text_analyzer",
                                        },
                                        "orcid": {"type": "keyword"},
                                    },
                                },
                                "content": {
                                    "type": "text",
                                    "analyzer": "custom_text_analyzer",
                                },
                                "dataset_id": {"type": "integer"},
                                "feature_model_id": {"type": "integer"},
                                "dataset_title": {
                                    "type": "text",
                                    "analyzer": "custom_text_analyzer",
                                },
                            }
                        },
                    },
                )

                print(f"[SUCCESS] Index '{self.index_name}' created successfully.")
            else:
                print(f"[INFO] Index '{self.index_name}' already exists.")
        except BadRequestError as e:
            print(f"[ERROR] BadRequestError while checking/creating index: {e}")
            print(f"[DETAIL] Error body: {getattr(e, 'body', 'no body')}")
            raise
        except ConnectionError as e:
            print(f"[ERROR] Could not connect to Elasticsearch: {e}")
            raise
        except ApiError as e:
            print(f"[ERROR] API error while creating index: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Unexpected error while creating index: {e}")
            raise

    def index_document(self, doc_id: str, data: dict):
        try:
            print(f"[DEBUG] Indexing document with ID '{doc_id}' in '{self.index_name}'")
            self.es.index(index=self.index_name, id=doc_id, document=data)
            print(f"[SUCCESS] Document '{doc_id}' indexed successfully.")
        except Exception as e:
            print(f"[ERROR] Could not index document '{doc_id}': {e}")
            raise

    def delete_document(self, doc_id: str):
        try:
            print(f"[DEBUG] Deleting document with ID '{doc_id}' from '{self.index_name}'")
            self.es.delete(index=self.index_name, id=doc_id)
            print(f"[SUCCESS] Document '{doc_id}' deleted.")
        except NotFoundError:
            print(f"[INFO] Document '{doc_id}' not found. Nothing to delete.")
        except Exception as e:
            print(f"[ERROR] Could not delete document '{doc_id}': {e}")
            raise

    def delete_by_dataset_id(self, dataset_id: int):
        try:
            print(f"[DEBUG] Deleting Elasticsearch docs for dataset_id={dataset_id}")
            self.es.delete_by_query(
                index=self.index_name,
                body={"query": {"term": {"dataset_id": dataset_id}}},
                conflicts="proceed",  # KEY
                refresh=True,  # optional but recommended
            )
            print(f"[SUCCESS] Elasticsearch docs deleted for dataset_id={dataset_id}")
        except Exception as e:
            print(f"[ERROR] Failed to delete ES docs for dataset_id={dataset_id}: {e}")
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
            print(
                f"[DEBUG] Searching in '{self.index_name}' "
                f"with query: '{query}', "
                f"type: {publication_type}, "
                f"tags: {tags}, "
                f"order: {sorting}, "
                f"page: {page}, size: {size}"
            )

            must_clauses = []
            filter_clauses = []

            # Free text
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

            # Filter by publication type
            if publication_type:
                filter_clauses.append({"term": {"publication_type.keyword": publication_type}})

            # Filter by tags
            if tags:
                filter_clauses.append({"terms": {"tags.keyword": tags}})

            # Filter by dates
            if date_from or date_to:
                try:
                    range_query = {"range": {"created_at": {}}}

                    if date_from:
                        # Normalize and validate format
                        dt_from = datetime.strptime(date_from, "%Y-%m-%d")
                        range_query["range"]["created_at"]["gte"] = dt_from.strftime("%Y-%m-%dT00:00:00Z")

                    if date_to:
                        dt_to = datetime.strptime(date_to, "%Y-%m-%d")
                        range_query["range"]["created_at"]["lte"] = dt_to.strftime("%Y-%m-%dT23:59:59Z")

                    if "gte" in range_query["range"]["created_at"] or "lte" in range_query["range"]["created_at"]:
                        filter_clauses.append(range_query)

                except ValueError as e:
                    print(f"[WARN] Invalid date format received: from={date_from}, to={date_to}. Error: {e}")

            # Sorting
            sort_clause = [
                {"created_at": {"order": "desc"}} if sorting == "newest" else {"created_at": {"order": "asc"}}
            ]

            # Compute offset
            from_ = (page - 1) * size

            body = {
                "query": {
                    "bool": {
                        "must": must_clauses if must_clauses else [{"match_all": {}}],
                        "filter": filter_clauses,
                    }
                },
                "sort": sort_clause,
            }

            result = self.es.search(index=self.index_name, body=body, from_=from_, size=size)
            hits = result["hits"]["hits"]
            total = result["hits"]["total"]["value"]

            print(f"[SUCCESS] Search completed. Page {page}, results: {len(hits)}, total: {total}")

            return [self._format_hit(hit) for hit in hits], total

        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            raise

    def _format_hit(self, hit):
        """Formats an Elasticsearch hit with human-readable dates and sizes."""
        from datetime import datetime

        source = hit["_source"]

        # Date format
        if "created_at" in source:
            try:
                dt = datetime.fromisoformat(source["created_at"])
                source["created_at"] = dt.strftime("%d %b %Y, %H:%M")
            except Exception:
                pass

        # Human-readable size
        if "total_size_in_bytes" in source:
            source["total_size_in_human_format"] = self._human_readable_size(source["total_size_in_bytes"])

        return source

    def _human_readable_size(self, size_bytes):
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
    """
    Encapsulates Elasticsearch indexing logic.
    """

    def __init__(self, index_dataset_fn, index_hubfile_fn, logger):
        self.index_dataset = index_dataset_fn
        self.index_hubfile = index_hubfile_fn
        self.logger = logger

    def index_dataset_and_hubfiles(self, dataset, created_fms):
        try:
            # Re-fetch the updated dataset
            self.index_dataset(dataset)
            self.logger.info(f"[INDEX] Dataset {dataset.id} indexed")

            for fm in created_fms:
                for hubfile in fm.hubfiles:
                    self.index_hubfile(hubfile)
                    self.logger.info(f"[INDEX] Hubfile {hubfile.id} indexed")

        except Exception as exc:
            self.logger.exception(f"[INDEX ERROR] Failed to index dataset {dataset.id}: {exc}")
            raise
