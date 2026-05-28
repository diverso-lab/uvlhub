import random

from flamapy.metamodels.fm_metamodel.models.feature_model import (
    FeatureModel,
    Feature,
    Relation,
    Cardinality,
    FeatureType,
)

from fm_generator.FMGenerator.models.config import Params

def maybe_apply_feature_type(feature: Feature, params: Params) -> None:
    """Assign a type-level type to the feature according to independent probabilities.

    If no type is selected, the feature remains semantically Boolean without explicit type.
    If several probabilities succeed at once, one of the matched types is chosen randomly.
    """
    if not getattr(params, "TYPE_LEVEL", False):
        feature.feature_type = FeatureType.BOOLEAN
        setattr(feature, "is_type_level_typed", False)
        return

    candidates: list[FeatureType] = []

    if random.random() < float(getattr(params, "DIST_BOOLEAN", 0.0)):
        candidates.append(FeatureType.BOOLEAN)
    if random.random() < float(getattr(params, "DIST_INTEGER", 0.0)):
        candidates.append(FeatureType.INTEGER)
    if random.random() < float(getattr(params, "DIST_REAL", 0.0)):
        candidates.append(FeatureType.REAL)
    if random.random() < float(getattr(params, "DIST_STRING", 0.0)):
        candidates.append(FeatureType.STRING)

    if candidates:
        feature.feature_type = random.choice(candidates)
        setattr(feature, "is_type_level_typed", True)
    else:
        # Untyped feature: semantically equivalent to Boolean
        feature.feature_type = FeatureType.BOOLEAN
        setattr(feature, "is_type_level_typed", False)


def feature_constraint_bucket(feature: Feature, params: Params) -> str:
    """Return the constraint bucket where the feature must participate.

    Rules agreed with you:
    - untyped feature or Boolean feature -> bool
    - Integer / Real feature -> num
    - String feature -> string
    """
    if not getattr(params, "TYPE_LEVEL", False):
        return "bool"

    ftype = getattr(feature, "feature_type", FeatureType.BOOLEAN)

    if ftype in (FeatureType.INTEGER, FeatureType.REAL):
        return "num"
    if ftype == FeatureType.STRING:
        return "string"
    return "bool"


def select_relation_types(params: Params, total: int) -> list[str]:
    return random.choices(
        population=['mand', 'opt', 'alt', 'or', 'group'],
        weights=[
            params.DIST_MANDATORY,
            params.DIST_OPTIONAL,
            params.DIST_ALTERNATIVE,
            params.DIST_OR,
            params.DIST_GROUP_CARDINALITY
        ],
        k=total
    )


def determine_group_size(pool_size: int, params: Params) -> int:
    return random.randint(1, min(params.GROUP_CARDINALITY_MAX, pool_size))


def maybe_apply_feature_cardinality(feature: Feature, params: Params) -> None:
    if not getattr(params, "FEATURE_CARDINALITY", False):
        return

    prob = float(getattr(params, "PROB_FEATURE_CARDINALITY", 0.0))
    if random.random() >= prob:
        return

    fc_min_cfg = int(getattr(params, "MIN_FEATURE_CARDINALITY", 2))
    fc_max_cfg = int(getattr(params, "MAX_FEATURE_CARDINALITY", 5))

    if fc_min_cfg > fc_max_cfg:
        fc_min_cfg = fc_max_cfg

    fc_min = random.randint(fc_min_cfg, fc_max_cfg)
    fc_max = random.randint(fc_min, fc_max_cfg)

    feature.feature_cardinality = Cardinality(fc_min, fc_max)


def maybe_set_feature_cardinality(feature: Feature, params: Params) -> None:
    if not getattr(params, "FEATURE_CARDINALITY", False):
        return

    prob = float(getattr(params, "PROB_FEATURE_CARDINALITY", 0.0))
    if random.random() >= prob:
        return

    fc_min_cfg = int(getattr(params, "MIN_FEATURE_CARDINALITY", 2))
    fc_max_cfg = int(getattr(params, "MAX_FEATURE_CARDINALITY", 5))

    if fc_min_cfg > fc_max_cfg:
        fc_min_cfg = fc_max_cfg

    fc_min = random.randint(fc_min_cfg, fc_max_cfg)
    fc_max = random.randint(fc_min, fc_max_cfg)

    feature.cardinality_min = fc_min
    feature.cardinality_max = fc_max


def create_relation(
        parent: Feature,
        children: list[Feature],
        rel_kind: str,
        params: Params) -> list[Relation]:
    size = len(children)
    relations = []

    if rel_kind == 'mand':
        for child in children:
            rel = Relation(
                parent=parent,
                children=[child],
                card_min=1,
                card_max=1)
            relations.append(rel)

    elif rel_kind == 'opt':
        for child in children:
            rel = Relation(
                parent=parent,
                children=[child],
                card_min=0,
                card_max=1)
            relations.append(rel)

    elif rel_kind == 'alt':
        rel = Relation(
            parent=parent,
            children=children,
            card_min=1,
            card_max=1)
        relations.append(rel)

    elif rel_kind == 'or':
        rel = Relation(
            parent=parent,
            children=children,
            card_min=1,
            card_max=size)
        relations.append(rel)

    else:
        min_bound = max(params.GROUP_CARDINALITY_MIN, 1)
        max_bound = size
        if min_bound > max_bound:
            min_bound = max_bound
        card_min = random.randint(min_bound, max_bound)
        card_max = random.randint(card_min, max_bound)
        rel = Relation(
            parent=parent,
            children=children,
            card_min=card_min,
            card_max=card_max)
        relations.append(rel)

    return relations


def add_relations_to_level(
        parents: list[Feature],
        children: list[Feature],
        params: Params) -> None:
    total = len(children)
    rel_types = select_relation_types(params, total)
    random.shuffle(rel_types)
    pool = children[:]
    parent_idx = 0
    while pool:
        rel_kind = rel_types[parent_idx % len(rel_types)]
        parent = parents[parent_idx % len(parents)]
        parent_idx += 1
        size = determine_group_size(len(pool), params)
        group = [pool.pop() for _ in range(size)]
        relations = create_relation(parent, group, rel_kind, params)
        for rel in relations:
            parent.add_relation(rel)
            for child in rel.children:
                child.parent = parent
                maybe_apply_feature_cardinality(child, params)


def generate_hierarchy(params: Params) -> tuple[FeatureModel, list[Feature]]:
    root = Feature(name="F0")
    fm = FeatureModel(root=root)
    numFeats = random.randint(params.MIN_FEATURES, params.MAX_FEATURES)
    names = [f"F{i + 1}" for i in range(numFeats)]
    features = [Feature(name=n) for n in names]
    for feature in features:
        maybe_apply_feature_type(feature, params)
    levels = {0: [root]}
    idx = 0
    total = 0
    max_depth = params.MAX_TREE_DEPTH

    for depth in range(1, max_depth + 1):
        remaining = numFeats - total
        if remaining <= 0:
            break
        parents = levels.get(depth - 1, [])
        if not parents:
            break
        levels_left = max_depth - depth + 1
        level_count = max(1, remaining // levels_left)
        if depth == max_depth:
            level_count = remaining
        level_feats = features[idx: idx + level_count]
        levels[depth] = level_feats
        idx += level_count
        total += level_count
        add_relations_to_level(parents, level_feats, params)

    connected = {f.name for f in fm.get_features()}
    return fm, [f for f in features if f.name in connected]