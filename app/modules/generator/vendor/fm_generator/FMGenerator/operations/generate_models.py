import random
from enum import Enum
from dataclasses import dataclass, field
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    FeatureModel, Feature, Relation, Constraint, Attribute, Domain, Range
)
from flamapy.core.models.ast import AST, ASTOperation, Node
from fm_generator.FMGenerator.models.config import Params

def generate_random_attributes(params: Params, features: list[Feature]) -> None:
    num_attributes = random.randint(params.MIN_ATTRIBUTES, params.MAX_ATTRIBUTES)
    for i in range(num_attributes):
        feature = random.choice(features)
        attr_name = f"Attr{i}"
        attr_type = random.choice(['boolean', 'integer', 'real', 'string'])

        if attr_type == 'boolean':
            domain = Domain(ranges=None, elements=[True, False])
            default = random.choice([True, False])
        elif attr_type == 'integer':
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = random.randint(min_val, max_val)
        elif attr_type == 'real':
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = round(random.uniform(min_val, max_val), 2)
        else:
            options = ["low", "medium", "high"]
            domain = Domain(ranges=None, elements=options)
            default = random.choice(options)

        attribute = Attribute(name=attr_name, domain=domain, default_value=default)
        attribute.set_parent(feature)
        feature.add_attribute(attribute)

def assign_manual_attributes(params: Params, features: list[Feature]) -> None:
    assert params.MIN_ATTRIBUTES is None and params.MAX_ATTRIBUTES is None, (
        "MIN_ATTRIBUTES and MAX_ATTRIBUTES must be None when using manual attributes."
    )
    for attr, prob in zip(params.ATTRIBUTES_LIST, params.ATTRIBUTE_ATTACH_PROBS):
        for feature in features:
            if random.random() < prob:
                new_attr = Attribute(name=attr.name, domain=attr.domain, default_value=attr.default_value)
                new_attr.set_parent(feature)
                feature.add_attribute(new_attr)

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

def create_relation(parent: Feature, children: list[Feature], rel_kind: str, params: Params) -> Relation:
    size = len(children)
    if rel_kind == 'mand': # Revisar
        return Relation(parent=parent, children=children, card_min=size, card_max=size)
    if rel_kind == 'opt':
        if size == 1: # Revisar
            return Relation(parent=parent, children=children, card_min=0, card_max=1)
        else:
            return Relation(parent=parent, children=children, card_min=0, card_max=size)
    if rel_kind == 'alt':
        return Relation(parent=parent, children=children, card_min=1, card_max=1)
    if rel_kind == 'or':
        return Relation(parent=parent, children=children, card_min=1, card_max=size)

    # group cardinality
    min_bound = max(params.GROUP_CARDINALITY_MIN, 1)
    max_bound = size
    if min_bound > max_bound:
        min_bound = max_bound
    card_min = random.randint(min_bound, max_bound)
    card_max = random.randint(card_min, max_bound)

    return Relation(parent=parent, children=children, card_min=card_min, card_max=card_max)

def add_relations_to_level(parents: list[Feature], children: list[Feature], params: Params) -> None:
    total = len(children)
    rel_types = select_relation_types(params, total)
    random.shuffle(rel_types)
    pool = children[:]
    parent_idx = 0
    for rel_kind in rel_types:
        if not pool:
            break
        parent = parents[parent_idx % len(parents)]
        parent_idx += 1
        size = determine_group_size(len(pool), params)
        group = [pool.pop() for _ in range(size)]
        rel = create_relation(parent, group, rel_kind, params)
        parent.add_relation(rel)
        for child in group:
            child.parent = parent

def generate_hierarchy(params: Params) -> tuple[FeatureModel, list[Feature]]:
    root = Feature(name="F0")
    fm = FeatureModel(root=root)
    numFeats = random.randint(params.MIN_FEATURES, params.MAX_FEATURES)
    names = [f"F{i+1}" for i in range(numFeats)]
    features = [Feature(name=n) for n in names]
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

def add_constraints(fm: FeatureModel, features: list[Feature], params: Params) -> None:
    count = random.randint(params.MIN_CONSTRAINTS, params.MAX_CONSTRAINTS)
    for i in range(count):
        if len(features) < 2:
            break
        a, b = random.sample(features, 2)
        op = random.choices(
            [ASTOperation.IMPLIES, ASTOperation.AND, ASTOperation.OR, ASTOperation.EQUIVALENCE],
            weights=[
                params.PROB_IMPLICATION,
                params.PROB_AND,
                params.PROB_OR_CT,
                params.PROB_EQUIVALENCE
            ],
            k=1
        )[0]

        left = Node(a.name)
        right = Node(b.name)

        if random.random() < params.PROB_NOT:
            left = Node(ASTOperation.NOT, left)
        if random.random() < params.PROB_NOT:
            right = Node(ASTOperation.NOT, right)

        root = Node(op, left, right)
        fm.ctcs.append(Constraint(name=f"ctc{i}", ast=AST(root)))

def generate_single_model(params: Params, index: int) -> FeatureModel:
    random.seed(params.SEED + index)
    fm, feats = generate_hierarchy(params)
    if params.RANDOM_ATTRIBUTES:
        generate_random_attributes(params, feats)
    else:
        assign_manual_attributes(params, feats)
    add_constraints(fm, feats, params)
    return fm
