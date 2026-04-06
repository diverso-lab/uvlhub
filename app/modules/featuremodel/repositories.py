from sqlalchemy import func

from app.modules.dataset.models import DataSet, DSMetaData
from app.modules.featuremodel.models import FeatureModel
from core.repositories.BaseRepository import BaseRepository


class FeatureModelRepository(BaseRepository):
    def __init__(self):
        super().__init__(FeatureModel)

    def count_feature_models(self) -> int:
        return (
            self.session.query(func.count(self.model.id))
            .join(DataSet, self.model.dataset_id == DataSet.id)
            .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
            .filter(DSMetaData.dataset_doi.isnot(None))
            .scalar()
            or 0
        )
