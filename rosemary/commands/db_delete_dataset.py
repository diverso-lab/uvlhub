import os
import shutil

import click
from dotenv import load_dotenv

from app import create_app, db
from app.modules.dataset.models import (
    Author,
    DataSet,
    DSDownloadRecord,
    DSMetaData,
    DSViewRecord,
)
from app.modules.elasticsearch.services import ElasticsearchService


def delete_dataset_uploads(dataset, uploads_root="uploads"):
    """
    Deletes uploads/user_<user_id>/dataset_<dataset_id>/ recursively.
    """
    dataset_dir = os.path.join(
        uploads_root,
        f"user_{dataset.user_id}",
        f"dataset_{dataset.id}",
    )

    if os.path.exists(dataset_dir):
        shutil.rmtree(dataset_dir)
        return dataset_dir

    return None


@click.command("db:delete-dataset", help="Deletes a dataset and ALL related data given its DOI.")
@click.argument("doi")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def delete_dataset(doi, yes):
    load_dotenv()

    app = create_app()
    with app.app_context():

        # 1. localizar dataset por DOI
        dataset = db.session.query(DataSet).join(DSMetaData).filter(DSMetaData.dataset_doi == doi).one_or_none()

        if dataset is None:
            click.echo(f"No dataset found with DOI: {doi}")
            return

        ds_meta_data = dataset.ds_meta_data

        uploads_dir = os.path.join(
            "uploads",
            f"user_{dataset.user_id}",
            f"dataset_{dataset.id}",
        )

        # --- INFO PREVIA ---
        click.echo("")
        click.echo("Dataset to be deleted:")
        click.echo(f"  Dataset ID: {dataset.id}")
        click.echo(f"  Title: {ds_meta_data.title}")
        click.echo(f"  DOI: {ds_meta_data.dataset_doi}")
        click.echo(f"  Owner user_id: {dataset.user_id}")
        click.echo(f"  Feature models: {len(dataset.feature_models)}")
        click.echo(f"  Uploads dir: {uploads_dir}")
        click.echo("")

        if not yes:
            if not click.confirm(
                "This will PERMANENTLY delete the dataset, metadata, authors, views, downloads, files "
                "AND Elasticsearch documents. Continue?",
                default=False,
            ):
                click.echo("Aborted.")
                return

        # --- 2. BORRADO DE FICHEROS ---
        try:
            deleted_path = delete_dataset_uploads(dataset)
            if deleted_path:
                click.echo(f"Deleted files in: {deleted_path}")
            else:
                click.echo("No uploads directory found to delete.")
        except Exception as e:
            click.echo(f"Error deleting files: {e}")
            click.echo("Nothing else was modified.")
            return

        # --- 3. BORRADO EN ELASTICSEARCH ---
        try:
            es_service = ElasticsearchService()
            es_service.delete_document(f"dataset-{dataset.id}")
            es_service.delete_by_dataset_id(dataset.id)
        except Exception as e:
            click.echo(f"Elasticsearch error: {e}")
            click.echo("Database was NOT modified.")
            return

        # --- 4. BORRADO EN BASE DE DATOS ---
        try:
            # borrar vistas
            db.session.query(DSViewRecord).filter(DSViewRecord.dataset_id == dataset.id).delete(
                synchronize_session=False
            )

            # borrar descargas
            db.session.query(DSDownloadRecord).filter(DSDownloadRecord.dataset_id == dataset.id).delete(
                synchronize_session=False
            )

            # borrar autores
            db.session.query(Author).filter(Author.ds_meta_data_id == ds_meta_data.id).delete(synchronize_session=False)

            # borrar dataset (borra feature_models por cascade)
            db.session.delete(dataset)

            # borrar metadata (borra metrics por cascade)
            db.session.delete(ds_meta_data)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            click.echo(f"Database error: {e}")
            click.echo("Files and Elasticsearch were cleaned, but DB delete failed.")
            return

        click.echo("Dataset and ALL related data deleted successfully.")
