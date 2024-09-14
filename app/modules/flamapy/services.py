from typing import Any
import logging
from app.modules.flamapy.repositories import FlamapyRepository
from core.services.BaseService import BaseService

from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.operations import FMMetrics
from flamapy.metamodels.bdd_metamodel.operations import BDDMetrics
from flamapy.metamodels.pysat_metamodel.operations import PySATMetrics # noqa
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat # noqa
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD # noqa

logger = logging.getLogger(__name__)


class FlamapyService(BaseService):
    def __init__(self):
        super().__init__(FlamapyRepository())

    def get_metrics(self, fm_model: FeatureModel) -> list[dict[str, Any]]:

        logger.info(f"feature model: {fm_model}")

        fm_metrics = FMMetrics().execute(fm_model)
        logger.info(f"fm_metrics: {fm_metrics}")
        result = fm_metrics.get_result()
        return result

    def get_analysis_results(self, fm_model: FeatureModel) -> list[dict[str, Any]]:
        fm_results = BDDMetrics().execute(fm_model).get_result()
        return fm_results
