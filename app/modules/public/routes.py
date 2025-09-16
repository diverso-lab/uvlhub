import logging

from flask import render_template

from app.modules.dataset.services import DataSetService
from app.modules.featuremodel.services import FeatureModelService
from app.modules.public import public_bp
from app.modules.statistics.services import StatisticsService

logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    logger.info("Access index")
    dataset_service = DataSetService()
    feature_model_service = FeatureModelService()
    statistics_service = StatisticsService()

    # Statistics: total datasets and feature models
    datasets_counter = dataset_service.count_synchronized_datasets()
    feature_models_counter = feature_model_service.count_feature_models()

    # Statistics: total downloads
    total_dataset_downloads = statistics_service.get_datasets_downloaded()
    total_feature_model_downloads = statistics_service.get_feature_models_downloaded()

    # Statistics: total views
    total_dataset_views = statistics_service.get_datasets_viewed()
    total_feature_model_views = statistics_service.get_feature_models_viewed()

    return render_template(
        "public/index.html",
        datasets=dataset_service.get_top_5_datasets_by_feature_model_count(),
        datasets_counter=datasets_counter,
        feature_models_counter=feature_models_counter,
        total_dataset_downloads=total_dataset_downloads,
        total_feature_model_downloads=total_feature_model_downloads,
        total_dataset_views=total_dataset_views,
        total_feature_model_views=total_feature_model_views,
    )
