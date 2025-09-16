from enum import Enum
from typing import Any, Optional


class FMProperty:
    """It defines a property of the feature model.

    Each property has a name, a description, and maybe a property parent.
    The property parent is used to organize the properties in a hierarchy.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        parent: Optional["FMProperty"] = None,
    ):
        self.name = name
        self.description = description
        self.parent = parent

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parent": self.parent.name if self.parent is not None else None,
            "level": self.level(),
        }

    def level(self) -> int:
        """Return the level of parents."""
        if self.parent is None:
            return 0
        return 1 + self.parent.level()


class FMPropertyMeasure:
    """It represent the measure of a property.

    It has the value of the measure, it can also have a size and a ratio.
    Example:
        property: Abstract Features.
        value: the list of abstract features.
        size: the length of the list.
        ratio: the percentage of abstract features with regards the total number of features.
    """

    def __init__(
        self,
        property: FMProperty,
        value: Optional[Any] = None,  # Example: the list of abstract features
        size: Optional[Any] = None,  # Example: number of abstract features
        ratio: Optional[Any] = None,
    ):  # Example: percentage of abstract features from the total number of features
        self.property = property
        self.value = value
        self.size = size
        self.ratio = ratio

    def to_dict(self) -> dict[str, Any]:
        result = {"value": self.value, "size": self.size, "ratio": self.ratio}
        return self.property.to_dict() | result


class FMProperties(Enum):
    # METADATA
    NAME = FMProperty("Name", "Name of the feature model.", None)
    DESCRIPTION = FMProperty("Description", "Description of the feature model.", None)
    AUTHOR = FMProperty("Author", "Author of the feature model", None)
    YEAR = FMProperty("Year", "Year of creation of the feature model", None)
    REFERENCE = FMProperty("Reference", "Main paper for reference or DOI of the feature model", None)
    TAGS = FMProperty("Tags", "Tags or keywords that identify the feature model.", None)
    DOMAIN = FMProperty("Domain", "Domain of the feature model.", None)

    # METRICS
    FEATURES = FMProperty("Features", "Set of features in the feature model.", None)
    ABSTRACT_FEATURES = FMProperty(
        "Abstract features",
        "Features used to structure the feature model that, however, do not have any impact at implementation level.",
        FEATURES,
    )
    CONCRETE_FEATURES = FMProperty(
        "Concrete features",
        "Features that are mapped to at least one implementation artifact.",
        FEATURES,
    )
    LEAF_FEATURES = FMProperty(
        "Leaf features",
        "Features that have not subfeatures (aka 'primitive features' or 'terminal features').",
        FEATURES,
    )
    COMPOUND_FEATURES = FMProperty("Compound features", "Features that have subfeatures.", FEATURES)
    CONCRETE_COMPOUND_FEATURES = FMProperty(
        "Concrete compound features",
        "Concrete and compound features.",
        CONCRETE_FEATURES,
    )
    CONCRETE_LEAF_FEATURES = FMProperty("Concrete leaf features", "Concrete and leaf features.", CONCRETE_FEATURES)
    ABSTRACT_COMPOUND_FEATURES = FMProperty(
        "Abstract compound features",
        "Abstract and compound features.",
        ABSTRACT_FEATURES,
    )
    ABSTRACT_LEAF_FEATURES = FMProperty("Abstract leaf features", "Abstract and leaf features.", ABSTRACT_FEATURES)
    TREE_RELATIONSHIPS = FMProperty(
        "Tree relationships",
        "Number of relationships (edges) of the feature model.",
        None,
    )
    ROOT_FEATURE = FMProperty("Root feature", "The root of the feature model.", FEATURES)
    TOP_FEATURES = FMProperty("Top features", "Features that are first descendants of the root.", ROOT_FEATURE)
    SOLITARY_FEATURES = FMProperty(
        "Solitary features",
        "Features that are not grouped in a feature group.",
        FEATURES,
    )
    GROUPED_FEATURES = FMProperty("Grouped features", "Features that occurs in a feature group.", FEATURES)
    MANDATORY_FEATURES = FMProperty(
        "Mandatory features",
        ("Features marked as mandatory that need to be selected " "if its parent is selected."),
        TREE_RELATIONSHIPS,
    )
    OPTIONAL_FEATURES = FMProperty("Optional features", "Feature marked as optional.", TREE_RELATIONSHIPS)
    FEATURE_GROUPS = FMProperty(
        "Feature groups",
        "Features that express a choice over the grouped features in a group.",
        TREE_RELATIONSHIPS,
    )
    ALTERNATIVE_GROUPS = FMProperty(
        "Alternative groups",
        "Feature groups that require the selection of just one child (i.e., [1..1] cardinality).",
        FEATURE_GROUPS,
    )
    OR_GROUPS = FMProperty(
        "Or groups",
        "Feature groups that require the selection of at least one child (i.e., [1..*] cardinality).",
        FEATURE_GROUPS,
    )
    MUTEX_GROUPS = FMProperty(
        "Mutex groups",
        "Feature groups that require the selection of zero or just one child (i.e., [0..1] cardinality).",
        FEATURE_GROUPS,
    )
    CARDINALITY_GROUPS = FMProperty(
        "Cardinality groups",
        (
            "Feature groups with arbitrary cardinality [a..b] that require the "
            "selection of a minimum and a maximum number of children."
        ),
        FEATURE_GROUPS,
    )
    BRANCHING_FACTOR = FMProperty(
        "Branching factor",
        "Average number of children per non-leaf feature (aka 'Ratio of Variability').",
        None,
    )  # Also 'Avg children per feature'
    MIN_CHILDREN_PER_FEATURE = FMProperty(
        "Min children per feature",
        "Minimal number of children per non-leaf feature.",
        BRANCHING_FACTOR,
    )
    MAX_CHILDREN_PER_FEATURE = FMProperty(
        "Max children per feature",
        "Maximal number of children per feature.",
        BRANCHING_FACTOR,
    )
    AVG_CHILDREN_PER_FEATURE = FMProperty(
        "Avg children per feature",
        "Average number of children per feature.",
        BRANCHING_FACTOR,
    )
    DEPTH_TREE = FMProperty(
        "Depth of tree",
        "Number of features of the longest path from the root to the leaf features.",
        None,
    )
    MAX_DEPTH_TREE = FMProperty(
        "Max depth of tree",
        "Number of features of the longest path from the root to the leaf features.",
        DEPTH_TREE,
    )
    MEAN_DEPTH_TREE = FMProperty(
        "Mean depth of tree",
        "Number of features of the mean path from the root to the leaf features.",
        DEPTH_TREE,
    )
    MEDIAN_DEPTH_TREE = FMProperty(
        "Median depth of tree",
        "Number of features of the median path from the root to the leaf features.",
        DEPTH_TREE,
    )

    CROSS_TREE_CONSTRAINTS = FMProperty("Cross-tree constraints", "Textual cross-tree constraints.", None)
    SIMPLE_CONSTRAINTS = FMProperty(
        "Simple constraints",
        "Requires and Excludes constraints.",
        CROSS_TREE_CONSTRAINTS,
    )  # Requires and excludes
    REQUIRES_CONSTRAINTS = FMProperty(
        "Requires constraints",
        "Constraints modeling that the activation of a feature f1 implies the activation of a feature f2.",
        SIMPLE_CONSTRAINTS,
    )
    EXCLUDES_CONSTRAINTS = FMProperty(
        "Excludes constraints",
        "Constraints modeling that two features are mutually exclusive and cannot be activated together.",
        SIMPLE_CONSTRAINTS,
    )
    COMPLEX_CONSTRAINTS = FMProperty(
        "Complex constraints",
        "Constraints in arbitrary propositional logic formulae.",
        CROSS_TREE_CONSTRAINTS,
    )  # Prop logic constraints (aka advanced constraints)
    PSEUDO_COMPLEX_CONSTRAINTS = FMProperty(
        "Pseudo-complex constraints",
        "Constraints that are convertible to a set of simple constraints.",
        COMPLEX_CONSTRAINTS,
    )
    STRICT_COMPLEX_CONSTRAINTS = FMProperty(
        "Strict-complex constraints",
        "Constraints that cannot be converted to a set of simple constraints.",
        COMPLEX_CONSTRAINTS,
    )
    MIN_CONSTRAINTS_PER_FEATURE = FMProperty(
        "Min constraints per feature",
        "The minimal number of constraints per feature.",
        CROSS_TREE_CONSTRAINTS,
    )
    MAX_CONSTRAINTS_PER_FEATURE = FMProperty(
        "Max constraints per feature",
        "The maximal number of constraints per feature.",
        CROSS_TREE_CONSTRAINTS,
    )
    AVG_CONSTRAINTS_PER_FEATURE = FMProperty(
        "Avg constraints per feature",
        "The average number of constraints per feature.",
        CROSS_TREE_CONSTRAINTS,
    )
    EXTRA_CONSTRAINT_REPRESENTATIVENESS = FMProperty(
        "Features in constraints",
        (
            "Features involved in cross-tree constraints. The ratio to the total "
            "number of features is called 'Extra constraint representativeness (ECR)'."
        ),
        CROSS_TREE_CONSTRAINTS,
    )
    VALID = FMProperty(
        "Valid (not void)",
        "A feature model is valid if it represents at least one configuration.",
        None,
    )
    CORE_FEATURES = FMProperty(
        "Core features",
        "Features that are part of all the configurations (aka 'common features').",
        None,
    )  # Also 'Common features'
    VARIANT_FEATURES = FMProperty(
        "Variant features",
        "Features that do not appear in all the configurations.",
        None,
    )  # Also 'Real optional features'
    DEAD_FEATURES = FMProperty("Dead features", "Features that cannot appear in any configuration.", None)
    UNIQUE_FEATURES = FMProperty("Unique features", "Features that appear in exactly one configuration.", None)
    FALSE_OPTIONAL_FEATURES = FMProperty(
        "False-optional features",
        "Features defined as optionals the selection of their parents make the feature itself selected as well.",
        None,
    )
    CONFIGURATIONS = FMProperty(
        "Configurations",
        (
            "Number of configurations represented by the feature model. "
            "If <= is shown, the number represents an upper estimation bound."
        ),
        None,
    )
    # ATOMIC_SETS = FMProperty('Atomic sets', '', None)  # Atomic sets need to be fixed in FLAMA.
