import logging

logger = logging.getLogger(__name__)


def init_search_index():
    try:
        from app.features.elasticsearch.services import ElasticsearchService

        search = ElasticsearchService()

        search.create_index_if_not_exists()
    except Exception as e:
        logger.exception("init_search_index failed: %s", e)
        raise


def index_dataset(dataset):

    from app.features.elasticsearch.services import ElasticsearchService
    from app.features.factlabel.models import HubfileMetrics

    search = ElasticsearchService()

    if not dataset.ds_meta_data.dataset_doi:
        logger.info("[SKIP] Dataset %s has no dataset_doi. Skipping indexing.", dataset.id)
        return

    authors_text = (
        " ".join(a.name for a in dataset.ds_meta_data.authors) if not dataset.ds_meta_data.dataset_anonymous else ""
    )
    content = (
        f"{dataset.ds_meta_data.title} "
        f"{dataset.ds_meta_data.description} "
        f"{dataset.ds_meta_data.publication_doi} "
        f"{authors_text} "
    )

    # Calcular total de features: suma de features de todos los hubfiles del dataset
    from app.features.hubfile.models import Hubfile

    total_features = 0
    hubfiles = Hubfile.query.filter_by(dataset_id=dataset.id).all()
    for hubfile in hubfiles:
        hubfile_metrics = HubfileMetrics.query.filter_by(hubfile_id=hubfile.id).first()
        if hubfile_metrics and hubfile_metrics.features:
            total_features += hubfile_metrics.features

    doc = {
        "type": "dataset",
        "id": dataset.id,
        "dataset_id": dataset.id,
        "title": dataset.ds_meta_data.title,
        "description": dataset.ds_meta_data.description,
        "publication_doi": dataset.ds_meta_data.publication_doi,
        "dataset_doi": dataset.ds_meta_data.dataset_doi,
        "url": dataset.get_uvlhub_doi(),
        "authors": (
            [
                {
                    "name": a.name,
                    "affiliation": getattr(a, "affiliation", None),
                    "orcid": getattr(a, "orcid", None),
                }
                for a in dataset.ds_meta_data.authors
            ]
            if not dataset.ds_meta_data.dataset_anonymous
            else []
        ),
        "authors_is_anonymous": dataset.ds_meta_data.dataset_anonymous,
        "tags": ([t.strip() for t in dataset.ds_meta_data.tags.split(",")] if dataset.ds_meta_data.tags else []),
        "publication_type": (
            dataset.ds_meta_data.publication_type.value if dataset.ds_meta_data.publication_type else None
        ),
        "publication_type_label": dataset.get_cleaned_publication_type(),
        "content": content,
        "created_at": dataset.created_at.isoformat(),
        "total_size_in_bytes": dataset.get_file_total_size(),
        "files_count": dataset.get_files_count(),
        "number_of_features": total_features,  # Suma de features de todos los hubfiles
        "number_of_models": len(hubfiles),  # Cantidad de hubfiles/modelos
    }

    search.index_document(doc_id=f"dataset-{dataset.id}", data=doc)

    logger.info(f"[SEARCH] Dataset {dataset.id} indexed with DOI: {dataset.ds_meta_data.dataset_doi}")


def index_hubfile(hubfile):

    from app.features.elasticsearch.services import ElasticsearchService
    from app.features.factlabel.models import HubfileMetrics

    search = ElasticsearchService()

    dataset = hubfile.feature_model.dataset if hubfile.feature_model else None

    if not dataset or not dataset.ds_meta_data.dataset_doi:
        logger.info("[SKIP] Hubfile %s skipped (no dataset or dataset has no DOI).", hubfile.id)
        return

    # Obtener número de features del hubfile desde HubfileMetrics
    hubfile_metrics = HubfileMetrics.query.filter_by(hubfile_id=hubfile.id).first()
    number_of_features = hubfile_metrics.features if hubfile_metrics else 0

    doc = {
        "type": "hubfile",
        "id": hubfile.id,
        "filename": hubfile.name,
        "content": hubfile.name,
        "feature_model_id": hubfile.feature_model_id,
        "dataset_id": dataset.id,
        "dataset_doi": dataset.get_uvlhub_doi(),
        "dataset_title": dataset.ds_meta_data.title,
        "checksum": hubfile.checksum,
        "url": hubfile.get_url(),
        "size_in_bytes": hubfile.size,
        "size_in_human_format": hubfile.get_formatted_size(),
        "number_of_features": number_of_features,
    }

    search.index_document(doc_id=f"hubfile-{hubfile.id}", data=doc)

    logger.info(f"[SEARCH] Hubfile {hubfile.id} indexed in dataset: {dataset.id}")


def reindex_all():
    from app.features.dataset.models import DataSet
    from app.features.hubfile.models import Hubfile

    datasets = DataSet.query.all()
    hubfiles = Hubfile.query.all()

    logger.info("[REINDEX] Reindexing %s datasets and %s hubfiles...", len(datasets), len(hubfiles))

    for dataset in datasets:
        index_dataset(dataset)

    for hubfile in hubfiles:
        index_hubfile(hubfile)

    logger.info("[REINDEX] Reindexing completed.")
