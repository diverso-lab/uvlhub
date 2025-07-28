from app.modules.elasticsearch.services import ElasticsearchService

search = ElasticsearchService()

def init_search_index():
    try:
        search.create_index_if_not_exists()
    except Exception as e:
        print(f"[ERROR init_search_index] {e}")
        raise

def index_dataset(dataset):
    doc = {
        "type": "dataset",
        "title": dataset.ds_meta_data.title,
        "description": dataset.ds_meta_data.description,
        "doi": dataset.ds_meta_data.publication_doi,
        "authors": [a.name for a in dataset.ds_meta_data.authors],
        "tags": dataset.ds_meta_data.tags,
        "publication_type": dataset.ds_meta_data.publication_type.name,
        "content": f"{dataset.ds_meta_data.title} {dataset.ds_meta_data.description} {dataset.ds_meta_data.publication_doi} {' '.join(a.name for a in dataset.ds_meta_data.authors)}",
        "dataset_id": dataset.id,
        "created_at": dataset.created_at.isoformat(),
        "total_size_in_bytes": dataset.get_file_total_size(),
        "files_count": dataset.get_files_count(),
    }
    search.index_document(doc_id=f"dataset-{dataset.id}", data=doc)


def index_hubfile(hubfile):
    doc = {
        "type": "hubfile",
        "filename": hubfile.name,
        "content": hubfile.name,
        "feature_model_id": hubfile.feature_model_id,
        "dataset_id": hubfile.feature_model.dataset_id,
        "checksum": hubfile.checksum,
        "size_in_bytes": hubfile.size,
    }
    search.index_document(doc_id=f"hubfile-{hubfile.id}", data=doc)


def reindex_all():
    from app.modules.dataset.models import DataSet
    from app.modules.hubfile.models import Hubfile

    datasets = DataSet.query.all()
    hubfiles = Hubfile.query.all()

    print(f"[REINDEX] Reindexing {len(datasets)} datasets and {len(hubfiles)} hubfiles...")

    for dataset in datasets:
        index_dataset(dataset)

    for hubfile in hubfiles:
        index_hubfile(hubfile)

    print("[REINDEX] Reindexing completed.")
