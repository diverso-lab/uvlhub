from typing import Any, Optional

from flamapy.core.operations import Metrics

from app import db


class Factlabel(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f"Factlabel<{self.id}>"


class FMMetadata:

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        author: Optional[str] = None,
        year: Optional[int] = None,
        reference: Optional[str] = None,
        tags: Optional[str] = None,
        domains: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.author = author
        self.year = year
        self.reference = reference
        self.tags = tags
        self.domains = domains

    def get_metadata(self) -> list[dict[str, Any]]:
        result = []
        result.append(self.fm_name(self.name))
        result.append(self.fm_description(self.description))
        result.append(self.fm_author(self.author))
        result.append(self.fm_year(self.year))
        result.append(self.fm_reference(self.reference))
        result.append(self.fm_tags(self.tags))
        result.append(self.fm_domains(self.domains))
        return result

    def fm_name(self, value: Optional[str] = None) -> dict[str, Any]:
        """Name of the feature model."""
        return Metrics.construct_result(name="Name", doc=self.fm_name.__doc__, result=value)

    def fm_description(self, value: Optional[str] = None) -> dict[str, Any]:
        """Description of the feature model."""
        return Metrics.construct_result(name="Description", doc=self.fm_name.__doc__, result=value)

    def fm_author(self, value: Optional[str] = None) -> dict[str, Any]:
        """Author of the feature model."""
        return Metrics.construct_result(name="Author", doc=self.fm_name.__doc__, result=value)

    def fm_year(self, value: Optional[str] = None) -> dict[str, Any]:
        """Year of creation of the feature model."""
        return Metrics.construct_result(name="Year", doc=self.fm_name.__doc__, result=value)

    def fm_reference(self, value: Optional[str] = None) -> dict[str, Any]:
        """Main paper for reference or DOI of the feature model."""
        return Metrics.construct_result(name="Reference", doc=self.fm_name.__doc__, result=value)

    def fm_tags(self, value: Optional[str] = None) -> dict[str, Any]:
        """Tags or keywords that identify the feature model."""
        return Metrics.construct_result(name="Tags", doc=self.fm_name.__doc__, result=value)

    def fm_domains(self, value: Optional[str] = None) -> dict[str, Any]:
        """Domain of the feature model."""
        return Metrics.construct_result(name="Domain", doc=self.fm_name.__doc__, result=value)


METRICS_ORDER = [
    "Features",
    "Abstract features",
    "Abstract compound features",
    "Abstract leaf features",
    "Concrete features",
    "Concrete compound features",
    "Concrete leaf features",
    "Compound features",
    "Leaf features",
    "Root feature",
    "Top features",
    "Solitary features",
    "Grouped features",
    "Tree relationships",
    "Mandatory features",
    "Optional features",
    "Feature groups",
    "Alternative groups",
    "Or groups",
    "Mutex groups",
    "Cardinality groups",
    "Depth of tree",
    "Max depth of tree",
    "Mean depth of tree",
    "Median depth of tree",
    "Branching factor",
    "Avg children per feature",
    "Min children per feature",
    "Max children per feature",
    "Cross-tree constraints",
    "Simple constraints",
    "Requires constraints",
    "Excludes constraints",
    "Complex constraints",
    "Pseudo-complex constraints",
    "Strict-complex constraints",
    "Features in constraints",
    "Avg constraints per feature",
    "Min constraints per feature",
    "Max constraints per feature",
]


ANALYSIS_ORDER = [
    "Satisfiable",
    "Core features",
    "Variant features",
    "Dead features",
    "Unique features",
    "Pure optional features",
    "False-optional features",
    "Configurations number",
    # 'Homogeneity',
    # 'Total variability',
    # 'Partial variability',
]
