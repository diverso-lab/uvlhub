from flamapy.metamodels.fm_metamodel.models.feature_model import (
    Attribute,
    Feature,
)

from fm_generator.FMGenerator.models.config import Params
from fm_generator.FMGenerator.operations.hierarchy import feature_constraint_bucket

RANDOM_ATTR_CONSTRAINT_PROB = 0.8


def constraints_must_be_boolean_only(params: Params) -> bool:
    return bool(getattr(params, "ENSURE_SATISFIABLE", False))


def infer_attribute_type(attr: Attribute) -> str:
    raw_attr_type = getattr(attr, "attribute_type", None)

    if raw_attr_type is not None:
        return getattr(raw_attr_type, "value", str(raw_attr_type)).lower()

    domain = getattr(attr, "domain", None)
    elements = getattr(domain, "elements", None) or []
    ranges = getattr(domain, "ranges", None) or []

    if elements:
        return "boolean"

    if ranges:
        range_ = ranges[0]
        range_min = getattr(range_, "min_value", None)
        range_max = getattr(range_, "max_value", None)

        if isinstance(range_min, int) and isinstance(range_max, int):
            return "integer"

        if isinstance(range_min, float) or isinstance(range_max, float):
            return "real"

        return "string"

    return "string"


def get_manual_attribute_config(
    attr: Attribute,
    feature: Feature,
    params: Params,
) -> tuple[str | None, bool, float, bool]:
    if not hasattr(params, "ATTRIBUTES_LIST"):
        return None, False, 1.0, False

    for attr_dict in params.ATTRIBUTES_LIST:
        if attr_dict.get("name") == attr.name and feature.name and attr.name:
            attr_type = (attr_dict.get("type", "") or "").lower()
            use_in_constraints = attr_dict.get("use_in_constraints", False)
            constraint_probability = float(attr_dict.get("attach_probability", 1.0))
            return attr_type, use_in_constraints, constraint_probability, True

    return None, False, 1.0, False


def should_include_attribute_in_pool(
    attr_type: str,
    is_manual_attribute: bool,
    params: Params,
) -> bool:
    if attr_type in ("integer", "real"):
        return bool(getattr(params, "ARITHMETIC_LEVEL", False))

    if attr_type == "string":
        if is_manual_attribute:
            return True

        return bool(getattr(params, "TYPE_LEVEL", False)) and bool(getattr(params, "STRING_CONSTRAINTS", False))

    return attr_type == "boolean"


def build_attribute_pools(
    features: list[Feature],
    params: Params,
) -> tuple[
    list[tuple[Feature, Attribute, float]],
    list[tuple[Feature, Attribute, float]],
    list[tuple[Feature, Attribute, float]],
]:
    attrs_bool: list[tuple[Feature, Attribute, float]] = []
    attrs_num: list[tuple[Feature, Attribute, float]] = []
    attrs_str: list[tuple[Feature, Attribute, float]] = []

    if constraints_must_be_boolean_only(params):
        return attrs_bool, attrs_num, attrs_str

    for feature in features:
        for attr in getattr(feature, "attributes", []):
            (
                attr_type,
                use_in_constraints,
                constraint_probability,
                is_manual_attribute,
            ) = get_manual_attribute_config(attr, feature, params)

            if attr_type is None:
                attr_type = infer_attribute_type(attr)
                use_in_constraints = True
                constraint_probability = RANDOM_ATTR_CONSTRAINT_PROB

            if not use_in_constraints:
                continue

            if not should_include_attribute_in_pool(
                attr_type,
                is_manual_attribute,
                params,
            ):
                continue

            constraint_probability = max(0.0, min(float(constraint_probability), 1.0))
            attr_tuple = (feature, attr, constraint_probability)

            if attr_type == "boolean":
                attrs_bool.append(attr_tuple)
            elif attr_type in ("integer", "real"):
                attrs_num.append(attr_tuple)
            elif attr_type == "string":
                attrs_str.append(attr_tuple)

    return attrs_bool, attrs_num, attrs_str


def build_feature_pools(
    features: list[Feature],
    params: Params,
) -> tuple[list[Feature], list[Feature], list[Feature]]:
    feats_bool = [feature for feature in features if feature_constraint_bucket(feature, params) == "bool"]

    if constraints_must_be_boolean_only(params):
        return feats_bool, [], []

    feats_num = [feature for feature in features if feature_constraint_bucket(feature, params) == "num"]
    feats_str = [feature for feature in features if feature_constraint_bucket(feature, params) == "string"]

    return feats_bool, feats_num, feats_str


def build_constraint_pools(
    features: list[Feature],
    params: Params,
) -> tuple[
    list[Feature],
    list[Feature],
    list[Feature],
    list[tuple[Feature, Attribute, float]],
    list[tuple[Feature, Attribute, float]],
    list[tuple[Feature, Attribute, float]],
]:
    feats_bool, feats_num, feats_str = build_feature_pools(features, params)
    attrs_bool, attrs_num, attrs_str = build_attribute_pools(features, params)

    return feats_bool, feats_num, feats_str, attrs_bool, attrs_num, attrs_str
