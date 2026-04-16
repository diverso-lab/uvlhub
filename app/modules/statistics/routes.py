from collections import defaultdict
from datetime import datetime, timedelta

from flask import render_template
from sqlalchemy import func

from app import db
from app.modules.statistics import statistics_bp


@statistics_bp.route("/statistics", methods=["GET"])
def index():
    from app.modules.dataset.models import Author, DataSet, DSMetaData, DSMetrics
    from app.modules.featuremodel.models import FeatureModel
    from app.modules.statistics.services import StatisticsService

    statistics_service = StatisticsService()

    # --- Summary counters ---
    total_datasets = (
        db.session.query(DataSet)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .count()
    )
    total_feature_models = (
        db.session.query(FeatureModel)
        .join(DataSet, DataSet.id == FeatureModel.dataset_id)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .count()
    )
    total_authors = db.session.query(Author).count()
    total_views = statistics_service.get_datasets_viewed()
    total_downloads = statistics_service.get_datasets_downloaded()

    avg_models_per_dataset = round(total_feature_models / total_datasets, 2) if total_datasets else 0

    # --- Top 5 datasets with most feature models ---
    top_datasets_by_models = (
        db.session.query(DataSet, func.count(FeatureModel.id).label("fm_count"))
        .join(FeatureModel, DataSet.id == FeatureModel.dataset_id)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .group_by(DataSet.id)
        .order_by(func.count(FeatureModel.id).desc())
        .limit(5)
        .all()
    )

    # --- Top 5 datasets with most features (DSMetrics) ---
    top_datasets_by_features = (
        db.session.query(DataSet, DSMetrics.number_of_features)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .join(DSMetrics, DSMetaData.ds_metrics_id == DSMetrics.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .filter(DSMetrics.number_of_features.isnot(None))
        .order_by(DSMetrics.number_of_features.desc())
        .limit(5)
        .all()
    )

    # --- Datasets by publication type ---
    datasets_by_type = (
        db.session.query(DSMetaData.publication_type, func.count(DataSet.id).label("count"))
        .join(DataSet, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .filter(DSMetaData.publication_type.isnot(None))
        .group_by(DSMetaData.publication_type)
        .order_by(func.count(DataSet.id).desc())
        .all()
    )

    # --- Timeline: uploads per month (last 12 months) ---
    twelve_months_ago = datetime.now() - timedelta(days=365)
    recent_datasets = (
        db.session.query(DataSet)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .filter(DataSet.created_at >= twelve_months_ago)
        .all()
    )
    timeline = defaultdict(int)
    for ds in recent_datasets:
        timeline[ds.created_at.strftime("%Y-%m")] += 1
    timeline_labels = sorted(timeline.keys())
    timeline_data = [timeline[k] for k in timeline_labels]

    # --- 5 most recently uploaded datasets ---
    latest_datasets = (
        db.session.query(DataSet)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .order_by(DataSet.created_at.desc())
        .limit(5)
        .all()
    )

    # --- Top 5 most viewed datasets ---
    from app.modules.dataset.models import DSDownloadRecord, DSViewRecord

    top_datasets_by_views = (
        db.session.query(DataSet, func.count(DSViewRecord.id).label("view_count"))
        .join(DSViewRecord, DataSet.id == DSViewRecord.dataset_id)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .group_by(DataSet.id)
        .order_by(func.count(DSViewRecord.id).desc())
        .limit(5)
        .all()
    )

    # --- Top 5 most downloaded datasets ---
    top_datasets_by_downloads = (
        db.session.query(DataSet, func.count(DSDownloadRecord.id).label("download_count"))
        .join(DSDownloadRecord, DataSet.id == DSDownloadRecord.dataset_id)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .group_by(DataSet.id)
        .order_by(func.count(DSDownloadRecord.id).desc())
        .limit(5)
        .all()
    )

    # --- Top 5 datasets with most configurations (number_of_models, closest to restrictions) ---
    top_datasets_by_configurations = (
        db.session.query(DataSet, DSMetrics.number_of_models)
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .join(DSMetrics, DSMetaData.ds_metrics_id == DSMetrics.id)
        .filter(DSMetaData.dataset_doi.isnot(None))
        .filter(DSMetrics.number_of_models.isnot(None))
        .order_by(DSMetrics.number_of_models.desc())
        .limit(5)
        .all()
    )

    # --- Downloads per month (last 12 months) ---
    recent_downloads = (
        db.session.query(DSDownloadRecord).filter(DSDownloadRecord.download_date >= twelve_months_ago).all()
    )
    downloads_by_month = defaultdict(int)
    for record in recent_downloads:
        downloads_by_month[record.download_date.strftime("%Y-%m")] += 1

    # --- Views per month (last 12 months) ---
    recent_views = db.session.query(DSViewRecord).filter(DSViewRecord.view_date >= twelve_months_ago).all()
    views_by_month = defaultdict(int)
    for record in recent_views:
        views_by_month[record.view_date.strftime("%Y-%m")] += 1

    # Merge all months for a unified x-axis
    all_months = sorted(set(timeline_labels) | set(downloads_by_month.keys()) | set(views_by_month.keys()))
    activity_downloads = [downloads_by_month.get(m, 0) for m in all_months]
    activity_views = [views_by_month.get(m, 0) for m in all_months]

    return render_template(
        "statistics/index.html",
        total_datasets=total_datasets,
        total_feature_models=total_feature_models,
        total_authors=total_authors,
        total_views=total_views,
        total_downloads=total_downloads,
        avg_models_per_dataset=avg_models_per_dataset,
        top_datasets_by_models=top_datasets_by_models,
        top_datasets_by_features=top_datasets_by_features,
        top_datasets_by_views=top_datasets_by_views,
        top_datasets_by_downloads=top_datasets_by_downloads,
        top_datasets_by_configurations=top_datasets_by_configurations,
        datasets_by_type=datasets_by_type,
        timeline_labels=timeline_labels,
        timeline_data=timeline_data,
        all_months=all_months,
        activity_downloads=activity_downloads,
        activity_views=activity_views,
        latest_datasets=latest_datasets,
    )
