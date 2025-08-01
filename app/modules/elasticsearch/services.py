import time
from app.modules.elasticsearch.repositories import ElasticsearchRepository
from core.services.BaseService import BaseService
from elasticsearch import (
    Elasticsearch,
    NotFoundError,
    BadRequestError,
    ApiError,
    ConnectionError,
)


class ElasticsearchService(BaseService):
    def __init__(self, host="http://elasticsearch:9200", index_name="search_index"):
        print("[INIT] Inicializando ElasticsearchService...")
        print(f"[INIT] Host: {host}")
        print(f"[INIT] Index name: '{index_name}'")

        if not isinstance(index_name, str):
            raise ValueError("El nombre del índice debe ser una cadena.")
        if not index_name:
            raise ValueError("El nombre del índice está vacío.")
        if any(c in index_name for c in r" #?/\*\"<>|,"):
            raise ValueError(f"Nombre de índice inválido: {index_name}")
        if not index_name.islower():
            raise ValueError("El nombre del índice debe estar en minúsculas.")
        if index_name.startswith(("-", "_", "+")):
            raise ValueError("El nombre del índice no puede comenzar por -, _ o +.")

        super().__init__(ElasticsearchRepository())

        self.es = Elasticsearch(hosts=[host])
        self.index_name = index_name

        if not self.wait_for_elasticsearch():
            print(
                "[ERROR] Elasticsearch no responde tras varios intentos. Continuando, pero puede fallar luego."
            )

        print("[INIT] ElasticsearchService inicializado correctamente.\n")

    def wait_for_elasticsearch(self, retries=5, delay=2):
        print("[WAIT] Esperando a que Elasticsearch esté disponible...")
        for attempt in range(retries):
            if self.es.ping():
                print(
                    f"[WAIT] Elasticsearch respondió al ping en intento {attempt + 1}."
                )
                return True
            print(
                f"[WAIT] Intento {attempt + 1} fallido. Reintentando en {delay} segundos..."
            )
            time.sleep(delay)
        return False

    def create_index_if_not_exists(self):
        print(f"[DEBUG] Verificando si el índice '{self.index_name}' existe...")
        try:
            exists = self.es.indices.exists(index=self.index_name)
            print(f"[DEBUG] ¿Existe el índice '{self.index_name}'? {exists}")

            if not exists:
                print(f"[DEBUG] Creando índice '{self.index_name}'...")

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
                                "doi": {"type": "keyword"},
                                "authors": {
                                    "type": "nested",  # o "object" si no vas a hacer queries sobre campos internos
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

                print(f"[SUCCESS] Índice '{self.index_name}' creado correctamente.")
            else:
                print(f"[INFO] El índice '{self.index_name}' ya existe.")
        except BadRequestError as e:
            print(f"[ERROR] BadRequestError al comprobar/crear índice: {e}")
            print(f"[DETAIL] Cuerpo del error: {getattr(e, 'body', 'sin cuerpo')}")
            raise
        except ConnectionError as e:
            print(f"[ERROR] No se pudo conectar a Elasticsearch: {e}")
            raise
        except ApiError as e:
            print(f"[ERROR] Error de API al crear índice: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Error inesperado al crear índice: {e}")
            raise

    def index_document(self, doc_id: str, data: dict):
        try:
            print(
                f"[DEBUG] Indexando documento con ID '{doc_id}' en '{self.index_name}'"
            )
            self.es.index(index=self.index_name, id=doc_id, document=data)
            print(f"[SUCCESS] Documento '{doc_id}' indexado correctamente.")
        except Exception as e:
            print(f"[ERROR] No se pudo indexar documento '{doc_id}': {e}")
            raise

    def delete_document(self, doc_id: str):
        try:
            print(
                f"[DEBUG] Eliminando documento con ID '{doc_id}' de '{self.index_name}'"
            )
            self.es.delete(index=self.index_name, id=doc_id)
            print(f"[SUCCESS] Documento '{doc_id}' eliminado.")
        except NotFoundError:
            print(f"[INFO] Documento '{doc_id}' no encontrado. Nada que eliminar.")
        except Exception as e:
            print(f"[ERROR] No se pudo eliminar documento '{doc_id}': {e}")
            raise

    def search(self, query: str, publication_type=None, sorting="newest", size=10):
        try:
            print(
                f"[DEBUG] Buscando en '{self.index_name}' "
                f"con query: '{query}', "
                f"tipo: {publication_type}, "
                f"orden: {sorting}"
            )

            must_clauses = []

            if query:
                must_clauses.append(
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "authors", "filename^2", "content"],
                            "fuzziness": "AUTO",
                        }
                    }
                )

            if publication_type:
                must_clauses.append(
                    {"term": {"publication_type.keyword": publication_type.lower()}}
                )

            sort_clause = [
                (
                    {"created_at": {"order": "desc"}}
                    if sorting == "newest"
                    else {"created_at": {"order": "asc"}}
                )
            ]

            body = {"query": {"bool": {"must": must_clauses}}, "sort": sort_clause}

            result = self.es.search(index=self.index_name, body=body, size=size)
            print(
                f"[SUCCESS] Búsqueda completada. Resultados: {len(result['hits']['hits'])}"
            )

            return [self._format_hit(hit) for hit in result["hits"]["hits"]]

        except Exception as e:
            print(f"[ERROR] Fallo en la búsqueda: {e}")
            raise

    def _format_hit(self, hit):
        """Formatea un resultado Elasticsearch con fechas y tamaños legibles."""
        from datetime import datetime

        source = hit["_source"]

        # Formato de fecha
        if "created_at" in source:
            try:
                dt = datetime.fromisoformat(source["created_at"])
                source["created_at"] = dt.strftime("%d %b %Y, %H:%M")
            except Exception:
                pass

        # Tamaño legible
        if "total_size_in_bytes" in source:
            source["total_size_in_human_format"] = self._human_readable_size(
                source["total_size_in_bytes"]
            )

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
