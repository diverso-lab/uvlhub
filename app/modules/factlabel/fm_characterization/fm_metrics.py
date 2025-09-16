import statistics

from flamapy.metamodels.fm_metamodel import operations as fm_operations
from flamapy.metamodels.fm_metamodel.models import Feature, FeatureModel
from fm_characterization import FMProperties, FMPropertyMeasure

from . import constraints_utils as ctcs_utils
from .fm_utils import get_ratio


class FMMetrics:

    def __init__(self, model: FeatureModel):
        self.fm = model

        # Variables for performance
        self._features = []
        self._features_by_name = {}
        self._abstract_features = {}
        self._concrete_features = {}
        self._leaf_features = {}
        for f in self.fm.get_features():
            self._features.append(f)
            self._features_by_name[f.name] = f
            if f.is_abstract:
                self._abstract_features[f.name] = f
            else:
                self._concrete_features[f.name] = f
            if len(f.get_relations()) == 0:
                self._leaf_features[f.name] = f

        self._constraints = []
        self._simple_constraints = []
        self._requires_constraints = []
        self._excludes_constraints = []
        self._complex_constraints = []
        self._strictcomplex_constraints = []
        self._pseudocomplex_constraints = []
        for ctc in self.fm.get_constraints():
            if ctcs_utils.is_requires_constraint(ctc):
                self._simple_constraints.append(str(ctc))
                self._requires_constraints.append(str(ctc))
            elif ctcs_utils.is_excludes_constraint(ctc):
                self._simple_constraints.append(str(ctc))
                self._excludes_constraints.append(str(ctc))
            else:
                self._complex_constraints.append(str(ctc))
                if ctcs_utils.is_pseudo_complex_constraint(ctc):
                    self._pseudocomplex_constraints.append(str(ctc))
                else:
                    self._strictcomplex_constraints.append(str(ctc))

        self._constraints_per_features = constraints_per_features(model, self._features)
        self._feature_ancestors = [len(get_feature_ancestors(self._features_by_name[f])) for f in self._leaf_features]

    def get_metrics(self) -> list[FMPropertyMeasure]:
        result = []
        result.append(self.fm_features())
        result.append(self.fm_abstract_features())
        result.append(self.fm_abstract_leaf_features())
        result.append(self.fm_abstract_compound_features())
        result.append(self.fm_concrete_features())
        result.append(self.fm_concrete_leaf_features())
        result.append(self.fm_concrete_compound_features())
        result.append(self.fm_compound_features())
        result.append(self.fm_leaf_features())
        result.append(self.fm_root_feature())
        result.append(self.fm_top_features())
        result.append(self.fm_solitary_features())
        result.append(self.fm_grouped_features())
        result.append(self.fm_tree_relationships())
        result.append(self.fm_mandatory_features())
        result.append(self.fm_optional_features())
        result.append(self.fm_feature_groups())
        result.append(self.fm_alternative_groups())
        result.append(self.fm_or_groups())
        result.append(self.fm_mutex_groups())
        result.append(self.fm_cardinality_groups())
        result.append(self.fm_depth_tree())
        result.append(self.fm_max_depth_tree())
        result.append(self.fm_mean_depth_tree())
        result.append(self.fm_median_depth_tree())
        result.append(self.fm_avg_branching_factor())
        result.append(self.fm_avg_children_per_feature())
        result.append(self.fm_min_children_per_feature())
        result.append(self.fm_max_children_per_feature())
        result.append(self.fm_cross_tree_constraints())
        result.append(self.fm_simple_constraints())
        result.append(self.fm_requires_constraints())
        result.append(self.fm_excludes_constraints())
        result.append(self.fm_complex_constraints())
        result.append(self.fm_pseudocomplex_constraints())
        result.append(self.fm_strictcomplex_constraints())
        result.append(self.fm_extra_constraint_representativeness())
        result.append(self.fm_avg_constraints_per_feature())
        result.append(self.fm_min_constraints_per_feature())
        result.append(self.fm_max_constraints_per_feature())
        return result

    def fm_features(self) -> FMPropertyMeasure:
        _features = list(self._features_by_name.keys())
        return FMPropertyMeasure(FMProperties.FEATURES.value, _features, len(_features))

    def fm_abstract_features(self) -> FMPropertyMeasure:
        _abstract_features = list(self._abstract_features.keys())
        return FMPropertyMeasure(
            FMProperties.ABSTRACT_FEATURES.value,
            _abstract_features,
            len(_abstract_features),
            get_ratio(_abstract_features, self._features),
        )

    def fm_concrete_features(self) -> FMPropertyMeasure:
        _concrete_features = list(self._concrete_features.keys())
        return FMPropertyMeasure(
            FMProperties.CONCRETE_FEATURES.value,
            _concrete_features,
            len(_concrete_features),
            get_ratio(_concrete_features, self._features),
        )

    def fm_root_feature(self) -> FMPropertyMeasure:
        _root_feature = self.fm.root.name
        return FMPropertyMeasure(
            FMProperties.ROOT_FEATURE.value,
            _root_feature,
            1,
            get_ratio([_root_feature], self._features),
        )

    def fm_top_features(self) -> FMPropertyMeasure:
        _top_features = [f.name for r in self.fm.root.get_relations() for f in r.children]
        return FMPropertyMeasure(
            FMProperties.TOP_FEATURES.value,
            _top_features,
            len(_top_features),
            get_ratio(_top_features, self._features),
        )

    def fm_leaf_features(self) -> FMPropertyMeasure:
        _leaf_features = list(self._leaf_features.keys())
        return FMPropertyMeasure(
            FMProperties.LEAF_FEATURES.value,
            _leaf_features,
            len(_leaf_features),
            get_ratio(_leaf_features, self._features),
        )

    def fm_compound_features(self) -> FMPropertyMeasure:
        _compound_features = [f.name for f in self._features if len(f.get_relations()) > 0]
        return FMPropertyMeasure(
            FMProperties.COMPOUND_FEATURES.value,
            _compound_features,
            len(_compound_features),
            get_ratio(_compound_features, self._features),
        )

    def fm_abstract_leaf_features(self) -> FMPropertyMeasure:
        _abstract_leaf_features = [name for name, f in self._abstract_features.items() if len(f.get_relations()) == 0]
        return FMPropertyMeasure(
            FMProperties.ABSTRACT_LEAF_FEATURES.value,
            _abstract_leaf_features,
            len(_abstract_leaf_features),
            get_ratio(_abstract_leaf_features, self._abstract_features.keys()),
        )

    def fm_abstract_compound_features(self) -> FMPropertyMeasure:
        _abstract_compound_features = [
            name for name, f in self._abstract_features.items() if len(f.get_relations()) > 0
        ]
        return FMPropertyMeasure(
            FMProperties.ABSTRACT_COMPOUND_FEATURES.value,
            _abstract_compound_features,
            len(_abstract_compound_features),
            get_ratio(_abstract_compound_features, self._abstract_features.keys()),
        )

    def fm_concrete_leaf_features(self) -> FMPropertyMeasure:
        _concrete_leaf_features = [name for name, f in self._concrete_features.items() if len(f.get_relations()) == 0]
        return FMPropertyMeasure(
            FMProperties.CONCRETE_LEAF_FEATURES.value,
            _concrete_leaf_features,
            len(_concrete_leaf_features),
            get_ratio(_concrete_leaf_features, self.fm_concrete_features().value),
        )

    def fm_concrete_compound_features(self) -> FMPropertyMeasure:
        _concrete_compound_features = [
            name for name, f in self._concrete_features.items() if len(f.get_relations()) > 0
        ]
        return FMPropertyMeasure(
            FMProperties.CONCRETE_COMPOUND_FEATURES.value,
            _concrete_compound_features,
            len(_concrete_compound_features),
            get_ratio(_concrete_compound_features, self.fm_concrete_features().value),
        )

    def fm_tree_relationships(self) -> FMPropertyMeasure:
        _tree_relationships = [str(r) for r in self.fm.get_relations()]
        return FMPropertyMeasure(
            FMProperties.TREE_RELATIONSHIPS.value,
            _tree_relationships,
            len(_tree_relationships),
        )

    def fm_solitary_features(self) -> FMPropertyMeasure:
        _solitary_features = [f.name for f in self._features if not f.is_root() and not f.parent.is_group()]
        return FMPropertyMeasure(
            FMProperties.SOLITARY_FEATURES.value,
            _solitary_features,
            len(_solitary_features),
            get_ratio(_solitary_features, self._features),
        )

    def fm_grouped_features(self) -> FMPropertyMeasure:
        _grouped_features = [f.name for f in self._features if not f.is_root() and f.parent.is_group()]
        return FMPropertyMeasure(
            FMProperties.GROUPED_FEATURES.value,
            _grouped_features,
            len(_grouped_features),
            get_ratio(_grouped_features, self._features),
        )

    def fm_mandatory_features(self) -> FMPropertyMeasure:
        _mandatory_features = [f.name for f in self.fm.get_mandatory_features()]
        return FMPropertyMeasure(
            FMProperties.MANDATORY_FEATURES.value,
            _mandatory_features,
            len(_mandatory_features),
            get_ratio(_mandatory_features, self.fm_solitary_features().value),
        )

    def fm_optional_features(self) -> FMPropertyMeasure:
        _optional_features = [f.name for f in self.fm.get_optional_features()]
        return FMPropertyMeasure(
            FMProperties.OPTIONAL_FEATURES.value,
            _optional_features,
            len(_optional_features),
            get_ratio(_optional_features, self.fm_solitary_features().value),
        )

    def fm_feature_groups(self) -> FMPropertyMeasure:
        _tree_relationships = [r for r in self.fm.get_relations()]
        _feature_groups = [f.name for f in self._features if f.is_group()]
        return FMPropertyMeasure(
            FMProperties.FEATURE_GROUPS.value,
            _feature_groups,
            len(_feature_groups),
            get_ratio(_feature_groups, _tree_relationships),
        )

    def fm_alternative_groups(self) -> FMPropertyMeasure:
        _group_features = [f.name for f in self._features if f.is_group()]
        _alternative_groups = [f.name for f in self.fm.get_alternative_group_features()]
        return FMPropertyMeasure(
            FMProperties.ALTERNATIVE_GROUPS.value,
            _alternative_groups,
            len(_alternative_groups),
            get_ratio(_alternative_groups, _group_features),
        )

    def fm_or_groups(self) -> FMPropertyMeasure:
        _group_features = [f.name for f in self._features if f.is_group()]
        _or_groups = [f.name for f in self.fm.get_or_group_features()]
        return FMPropertyMeasure(
            FMProperties.OR_GROUPS.value,
            _or_groups,
            len(_or_groups),
            get_ratio(_or_groups, _group_features),
        )

    def fm_mutex_groups(self) -> FMPropertyMeasure:
        _group_features = [f.name for f in self._features if f.is_group()]
        _mutex_groups = [f.name for f in self._features if f.is_mutex_group()]
        return FMPropertyMeasure(
            FMProperties.MUTEX_GROUPS.value,
            _mutex_groups,
            len(_mutex_groups),
            get_ratio(_mutex_groups, _group_features),
        )

    def fm_cardinality_groups(self) -> FMPropertyMeasure:
        _group_features = [f.name for f in self._features if f.is_group()]
        _cardinality_groups = [f.name for f in self._features if f.is_cardinality_group()]
        return FMPropertyMeasure(
            FMProperties.CARDINALITY_GROUPS.value,
            _cardinality_groups,
            len(_cardinality_groups),
            get_ratio(_cardinality_groups, _group_features),
        )

    def fm_depth_tree(self) -> FMPropertyMeasure:
        _max_depth_tree = max(self._feature_ancestors)
        return FMPropertyMeasure(FMProperties.DEPTH_TREE.value, _max_depth_tree)

    def fm_max_depth_tree(self) -> FMPropertyMeasure:
        _max_depth_tree = max(self._feature_ancestors)
        # _max_depth_tree = fm_operations.max_depth_tree(self.fm)
        return FMPropertyMeasure(FMProperties.MAX_DEPTH_TREE.value, _max_depth_tree)

    def fm_mean_depth_tree(self) -> FMPropertyMeasure:
        _mean_depth_tree = statistics.mean(self._feature_ancestors)
        return FMPropertyMeasure(FMProperties.MEAN_DEPTH_TREE.value, round(_mean_depth_tree, 2))

    def fm_median_depth_tree(self) -> FMPropertyMeasure:
        _median_depth_tree = statistics.median(self._feature_ancestors)
        return FMPropertyMeasure(FMProperties.MEDIAN_DEPTH_TREE.value, round(_median_depth_tree, 2))

    def fm_avg_branching_factor(self) -> FMPropertyMeasure:
        _avg_branching_factor = fm_operations.average_branching_factor(self.fm)
        return FMPropertyMeasure(FMProperties.BRANCHING_FACTOR.value, _avg_branching_factor)

    def fm_min_children_per_feature(self) -> FMPropertyMeasure:
        n_children = [
            sum(len(r.children) for r in feature.get_relations()) for feature in self._features if not feature.is_leaf()
        ]
        _min_children_per_feature = min(n_children) if len(n_children) > 0 else 0
        return FMPropertyMeasure(FMProperties.MIN_CHILDREN_PER_FEATURE.value, _min_children_per_feature)

    def fm_max_children_per_feature(self) -> FMPropertyMeasure:
        _max_children_per_feature = max(
            sum(len(r.children) for r in feature.get_relations()) for feature in self._features
        )
        return FMPropertyMeasure(FMProperties.MAX_CHILDREN_PER_FEATURE.value, _max_children_per_feature)

    def fm_avg_children_per_feature(self) -> FMPropertyMeasure:
        nof_children = sum(len(r.children) for feature in self._features for r in feature.get_relations())
        _avg_children_per_feature = round(nof_children / len(self._features), 2)
        return FMPropertyMeasure(FMProperties.AVG_CHILDREN_PER_FEATURE.value, _avg_children_per_feature)

    def fm_cross_tree_constraints(self) -> FMPropertyMeasure:
        _cross_tree_constraints = self._constraints
        return FMPropertyMeasure(
            FMProperties.CROSS_TREE_CONSTRAINTS.value,
            _cross_tree_constraints,
            len(_cross_tree_constraints),
        )

    def fm_simple_constraints(self) -> FMPropertyMeasure:
        _simple_constraints = self._simple_constraints
        return FMPropertyMeasure(
            FMProperties.SIMPLE_CONSTRAINTS.value,
            _simple_constraints,
            len(_simple_constraints),
            get_ratio(_simple_constraints, self._constraints),
        )

    def fm_requires_constraints(self) -> FMPropertyMeasure:
        _requires_constraints = self._requires_constraints
        return FMPropertyMeasure(
            FMProperties.REQUIRES_CONSTRAINTS.value,
            _requires_constraints,
            len(_requires_constraints),
            get_ratio(_requires_constraints, self._simple_constraints),
        )

    def fm_excludes_constraints(self) -> FMPropertyMeasure:
        _excludes_constraints = self._excludes_constraints
        return FMPropertyMeasure(
            FMProperties.EXCLUDES_CONSTRAINTS.value,
            _excludes_constraints,
            len(_excludes_constraints),
            get_ratio(_excludes_constraints, self._simple_constraints),
        )

    def fm_complex_constraints(self) -> FMPropertyMeasure:
        _complex_constraints = self._complex_constraints
        return FMPropertyMeasure(
            FMProperties.COMPLEX_CONSTRAINTS.value,
            _complex_constraints,
            len(_complex_constraints),
            get_ratio(_complex_constraints, self._constraints),
        )

    def fm_pseudocomplex_constraints(self) -> FMPropertyMeasure:
        _pseudocomplex_constraints = self._pseudocomplex_constraints
        return FMPropertyMeasure(
            FMProperties.PSEUDO_COMPLEX_CONSTRAINTS.value,
            _pseudocomplex_constraints,
            len(_pseudocomplex_constraints),
            get_ratio(_pseudocomplex_constraints, self._complex_constraints),
        )

    def fm_strictcomplex_constraints(self) -> FMPropertyMeasure:
        _strictcomplex_constraints = self._strictcomplex_constraints
        return FMPropertyMeasure(
            FMProperties.STRICT_COMPLEX_CONSTRAINTS.value,
            _strictcomplex_constraints,
            len(_strictcomplex_constraints),
            get_ratio(_strictcomplex_constraints, self._complex_constraints),
        )

    def fm_extra_constraint_representativeness(self) -> FMPropertyMeasure:
        _features_in_constraints = list({f for ctc in self.fm.get_constraints() for f in ctc.get_features()})
        _ecr = get_ratio(_features_in_constraints, self._features, 2)
        return FMPropertyMeasure(
            FMProperties.EXTRA_CONSTRAINT_REPRESENTATIVENESS.value,
            _features_in_constraints,
            len(_features_in_constraints),
            _ecr,
        )

    def fm_min_constraints_per_feature(self) -> FMPropertyMeasure:
        _constraints_per_feature = self._constraints_per_features
        return FMPropertyMeasure(
            FMProperties.MIN_CONSTRAINTS_PER_FEATURE.value,
            min(_constraints_per_feature),
        )

    def fm_max_constraints_per_feature(self) -> FMPropertyMeasure:
        _constraints_per_feature = self._constraints_per_features
        return FMPropertyMeasure(
            FMProperties.MAX_CONSTRAINTS_PER_FEATURE.value,
            max(_constraints_per_feature),
        )

    def fm_avg_constraints_per_feature(self) -> FMPropertyMeasure:
        _constraints_per_feature = self._constraints_per_features
        return FMPropertyMeasure(
            FMProperties.AVG_CONSTRAINTS_PER_FEATURE.value,
            round(statistics.mean(_constraints_per_feature), 2),
        )


def constraints_per_features(fm: FeatureModel, features: list[Feature]) -> list[int]:
    _features_per_constraints = []
    _constraints_per_feature = []
    for ctc in fm.get_constraints():
        _features_per_constraints.append([f for f in ctc.get_features()])

    for feature in features:
        cpf = sum(feature.name in feature_list for feature_list in _features_per_constraints)
        _constraints_per_feature.append(cpf)

    return _constraints_per_feature


def get_feature_ancestors(feature: Feature) -> list[Feature]:
    features = []
    parent = feature.get_parent()
    while parent is not None:
        features.append(parent)
        parent = parent.get_parent()
    return features
