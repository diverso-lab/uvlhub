import logging
from typing import Any

from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from app.modules.factlabel.models import ANALYSIS_ORDER, METRICS_ORDER, FMMetadata
from app.modules.factlabel.repositories import FactlabelRepository
from app.modules.flamapy.services import FlamapyService
from app.modules.hubfile.models import Hubfile
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


class FactlabelService(BaseService):
    def __init__(self):
        super().__init__(FactlabelRepository())

    def get_characterization(self, hubfile: Hubfile) -> Any:
        fm = UVLReader(hubfile.get_path()).transform()

        # Obtain characterization
        dataset_metadata = hubfile.get_dataset().get_zenodo_metadata()
        logger.info(f"dataset_metadata: {dataset_metadata}")

        metadata = FMMetadata(
            name=hubfile.name,
            description=dataset_metadata.get("description", None),
            tags=",".join(dataset_metadata.get("tags", None)),
        ).get_metadata()

        metrics = FlamapyService().get_metrics(fm)

        analysis_results = FlamapyService().get_analysis_results(fm)

        logger.info(f"Expected  metrics: {len(METRICS_ORDER)} :: metrics obtained: {len(metrics)}")
        logger.info(f"Expected  analysis: {len(ANALYSIS_ORDER)} :: analysis obtained: {len(analysis_results)}")
        logger.info(f"Equals? {metrics == analysis_results}")
        # for m in metrics:
        #     print(m)
        # Sort metrics according to the Fact Label order
        metrics_dict = {item["name"]: item for item in metrics}
        ordered_metrics = [metrics_dict[name] for name in METRICS_ORDER if name in metrics_dict]

        analysis_dict = {item["name"]: item for item in analysis_results}
        # Update Satisfiable result for human-readability
        satisfiable = analysis_dict["Satisfiable"]["result"]
        analysis_dict["Satisfiable"]["result"] = "Yes" if satisfiable else "No"
        # Sort analysis results according to the Fact Label order
        ordered_analysis = [analysis_dict[name] for name in ANALYSIS_ORDER if name in analysis_dict]

        result = {}
        result["metadata"] = metadata
        result["metrics"] = ordered_metrics
        result["analysis"] = ordered_analysis
        return result


def order_metrics_list(Y, X):
    # Create a dictionary from list Y for quick lookup
    Y_dict = {item["name"]: item for item in Y}

    # Create the ordered list based on X
    ordered_Y = [Y_dict[name] for name in X if name in Y_dict]

    return ordered_Y
