from typing import Any

from app.modules.flamapy.repositories import FlamapyRepository
from core.services.BaseService import BaseService

from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.operations import FMMetrics
from flamapy.metamodels.bdd_metamodel.operations import BDDMetrics
from flamapy.metamodels.pysat_metamodel.operations import PySATMetrics  # Import required to find the transformation in the metrics operation.
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat  # Import required to find the transformation in the metrics operation.
from flamapy.metamodels.bdd_metamodel.transformations import FmToBDD  # Import required to find the transformation in the metrics operation.


class FlamapyService(BaseService):
    def __init__(self):
        super().__init__(FlamapyRepository())

    def get_metrics(self, fm_model: FeatureModel) -> list[dict[str, Any]]:
        fm_metrics = FMMetrics().execute(fm_model).get_result()
        return fm_metrics

    def get_analysis_results(self, fm_model: FeatureModel) -> list[dict[str, Any]]:
        fm_results = BDDMetrics().execute(fm_model).get_result()
        return fm_results
