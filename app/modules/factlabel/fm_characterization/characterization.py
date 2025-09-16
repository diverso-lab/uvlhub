import json
from typing import Any

from flamapy.metamodels.fm_metamodel.models import FeatureModel
from fm_characterization import FMAnalysis, FMMetadata, FMMetrics, FMProperty

SPACE = " "


class FMCharacterization:

    def __init__(self, model: FeatureModel) -> None:
        self.metadata = FMMetadata(model)
        self.metrics = FMMetrics(model)
        self.analysis = FMAnalysis(model)

    def __str__(self) -> str:
        lines = ["METADATA"]
        for property in self.metadata.get_metadata():
            name = property.property.name
            value = str(property.value)
            lines.append(f"{name}: {value}")

        lines.append("METRICS")
        for property in self.metrics.get_metrics():
            indentation = SPACE * get_parents_numbers(property.property)
            name = property.property.name
            value = str(property.value) if property.size is None else str(property.size)
            ratio = f" ({str(property.ratio*100)}%)" if property.ratio is not None else ""
            lines.append(f"{indentation}{name}: {value}{ratio}")

        lines.append("ANALYSIS")
        for property in self.analysis.get_analysis():
            indentation = SPACE * get_parents_numbers(property.property)
            name = property.property.name
            value = str(property.value) if property.size is None else str(property.size)
            ratio = f" ({str(property.ratio*100)}%)" if property.ratio is not None else ""
            lines.append(f"{indentation}{name}: {value}{ratio}")
        return "\n".join(lines)

    def to_json(self) -> dict[Any]:
        metadata = []
        metrics = []
        analysis = []

        for property in self.metadata.get_metadata():
            metadata.append(property.to_dict())

        for property in self.metrics.get_metrics():
            metrics.append(property.to_dict())

        for property in self.analysis.get_analysis():
            analysis.append(property.to_dict())

        result = {}
        result["metadata"] = metadata
        result["metrics"] = metrics
        result["analysis"] = analysis
        return result

    def to_json_str(self) -> str:
        result = self.to_json()
        return json.dumps(result, indent=4)

    def to_json_file(self, filepath: str = None) -> None:
        result = self.to_json()
        with open(filepath, "w") as output_file:
            json.dump(result, output_file, indent=4)


def get_parents_numbers(property: FMProperty) -> int:
    if property.parent is None:
        return 1
    return 1 + get_parents_numbers(property.parent)
