"""Random feature-model generator core.

Every knob the wizard exposes is wired here:

* Boolean level — connectives (PROB_AND/OR_CT/IMPLICATION/EQUIVALENCE), NOT.
* Arithmetic level — operator mix (+/-/*/÷) and comparison mix (=/</>/≤/≥)
  over numeric attributes, gated by ARITHMETIC_LEVEL.
* Aggregate functions — sum()/avg() over attribute collections, gated by
  ARITHMETIC_LEVEL ∧ AGGREGATE_FUNCTIONS.
* Type level — String attributes + len() constraints, gated by TYPE_LEVEL ∧
  STRING_CONSTRAINTS.
* Relation distribution (DIST_*) including GROUP_CARDINALITY toggle.
* Feature cardinality (FEATURE_CARDINALITY + MIN/MAX_FEATURE_CARDINALITY +
  PROB_FEATURE_CARDINALITY).
* Attribute generation: random mode honours DIST_BOOLEAN/INTEGER/REAL/STRING
  gated by the enabled levels; manual mode respects ATTRIBUTE_ATTACH_PROBS
  and ATTRIBUTE_IN_CONSTRAINTS.
"""

import random

from flamapy.core.models.ast import AST, ASTOperation, Node
from flamapy.metamodels.fm_metamodel.models.feature_model import (
    Attribute,
    Cardinality,
    Constraint,
    Domain,
    Feature,
    FeatureModel,
    Range,
    Relation,
)

from fm_generator.FMGenerator.models.config import Params


# ─── Attribute generation ──────────────────────────────────────────────


def _enabled_attr_kinds(params: Params):
    """Return (kinds, weights) lists for the attribute-type distribution,
    filtered by enabled levels. Boolean is always on; Integer/Real require
    ARITHMETIC_LEVEL; String requires TYPE_LEVEL."""
    kinds, weights = ["boolean"], [max(float(params.DIST_BOOLEAN), 0.0)]
    if params.ARITHMETIC_LEVEL:
        kinds.append("integer")
        weights.append(max(float(params.DIST_INTEGER), 0.0))
        kinds.append("real")
        weights.append(max(float(params.DIST_REAL), 0.0))
    if params.TYPE_LEVEL:
        kinds.append("string")
        weights.append(max(float(params.DIST_STRING), 0.0))
    return kinds, weights


def _pick_attr_kind(params: Params) -> str:
    kinds, weights = _enabled_attr_kinds(params)
    if sum(weights) <= 0:
        return kinds[0]
    return random.choices(kinds, weights=weights, k=1)[0]


def _build_attribute(name: str, kind: str) -> Attribute:
    if kind == "boolean":
        return Attribute(
            name=name,
            domain=Domain(ranges=None, elements=[True, False]),
            default_value=random.choice([True, False]),
        )
    if kind == "integer":
        lo, hi = random.randint(0, 50), random.randint(51, 100)
        return Attribute(
            name=name,
            domain=Domain(ranges=[Range(lo, hi)], elements=None),
            default_value=random.randint(lo, hi),
        )
    if kind == "real":
        lo, hi = random.randint(0, 50), random.randint(51, 100)
        return Attribute(
            name=name,
            domain=Domain(ranges=[Range(lo, hi)], elements=None),
            default_value=round(random.uniform(lo, hi), 2),
        )
    options = ["low", "medium", "high"]
    return Attribute(
        name=name,
        domain=Domain(ranges=None, elements=options),
        default_value=random.choice(options),
    )


def _attach(attr: Attribute, feat: Feature) -> None:
    attr.set_parent(feat)
    feat.add_attribute(attr)


def _record_can_use(kind: str, params: Params, flag: bool = True) -> bool:
    if not flag:
        return False
    if kind == "boolean":
        return True
    if kind in ("integer", "real"):
        return bool(params.ARITHMETIC_LEVEL)
    if kind == "string":
        return bool(params.TYPE_LEVEL and params.STRING_CONSTRAINTS)
    return False


def generate_random_attributes(params: Params, features: list[Feature]) -> list[tuple]:
    """Random mode: create randint(MIN, MAX) attributes, each attached to a
    random feature, typed per the enabled distribution. Returns a list of
    (attr, feature, kind, can_use_in_ctc) records for constraint building."""
    if not features:
        return []
    lo = int(params.MIN_ATTRIBUTES or 0)
    hi = int(params.MAX_ATTRIBUTES or lo)
    if hi < lo:
        hi = lo
    count = random.randint(lo, hi) if hi > 0 else 0
    records = []
    for i in range(count):
        kind = _pick_attr_kind(params)
        attr = _build_attribute(f"Attr{i}", kind)
        feat = random.choice(features)
        _attach(attr, feat)
        records.append((attr, feat, kind, _record_can_use(kind, params, True)))
    return records


def assign_manual_attributes(params: Params, features: list[Feature]) -> list[tuple]:
    """Manual mode: for each configured attribute, roll against its attach
    probability on every feature. ATTRIBUTE_IN_CONSTRAINTS gates whether the
    attribute is eligible for constraint generation."""
    assert params.MIN_ATTRIBUTES is None and params.MAX_ATTRIBUTES is None, (
        "MIN_ATTRIBUTES and MAX_ATTRIBUTES must be None in manual mode."
    )
    attrs = list(params.ATTRIBUTES_LIST)
    probs = list(params.ATTRIBUTE_ATTACH_PROBS) + [0.0] * max(0, len(attrs) - len(params.ATTRIBUTE_ATTACH_PROBS))
    flags = list(params.ATTRIBUTE_IN_CONSTRAINTS) + [False] * max(
        0, len(attrs) - len(params.ATTRIBUTE_IN_CONSTRAINTS)
    )
    records = []
    for attr, prob, in_ctc in zip(attrs, probs, flags):
        kind = _infer_kind(attr)
        for feat in features:
            if random.random() < prob:
                new_attr = Attribute(name=attr.name, domain=attr.domain, default_value=attr.default_value)
                _attach(new_attr, feat)
                records.append((new_attr, feat, kind, _record_can_use(kind, params, bool(in_ctc))))
    return records


def _infer_kind(attr: Attribute) -> str:
    """Reverse-engineer the UVL type of a manually-specified attribute from
    its Domain. flamapy stores range/element lists under the *_list names;
    Domain(ranges=..., elements=...) is the constructor vocabulary."""
    dom = attr.domain
    if dom is None:
        return "boolean"
    ranges = getattr(dom, "range_list", None) or getattr(dom, "ranges", None) or []
    elements = getattr(dom, "element_list", None) or getattr(dom, "elements", None) or []
    if ranges:
        return "integer" if isinstance(attr.default_value, int) else "real"
    if elements and all(isinstance(e, bool) for e in elements):
        return "boolean"
    return "string"


# ─── Tree generation ──────────────────────────────────────────────────


def select_relation_types(params: Params, total: int) -> list[str]:
    """Pick `total` relation kinds weighted by DIST_MANDATORY/OPTIONAL/
    ALTERNATIVE/OR. Include 'group' only if GROUP_CARDINALITY is on AND its
    weight > 0."""
    pop = ["mand", "opt", "alt", "or"]
    weights = [
        max(float(params.DIST_MANDATORY), 0.0),
        max(float(params.DIST_OPTIONAL), 0.0),
        max(float(params.DIST_ALTERNATIVE), 0.0),
        max(float(params.DIST_OR), 0.0),
    ]
    if params.GROUP_CARDINALITY and float(params.DIST_GROUP_CARDINALITY) > 0:
        pop.append("group")
        weights.append(float(params.DIST_GROUP_CARDINALITY))
    if sum(weights) <= 0:
        return ["opt"] * total
    return random.choices(pop, weights=weights, k=total)


def _determine_group_size(pool_size: int, rel_kind: str, params: Params) -> int:
    """Group size per relation kind:
    - mand/opt: 1 child each (so each child gets its own relation)
    - alt/or: 2..min(5, pool)
    - group: min..max from GROUP_CARDINALITY_MIN/MAX (capped by pool)
    """
    if rel_kind in ("mand", "opt"):
        return 1
    if rel_kind in ("alt", "or"):
        upper = min(5, pool_size)
        return random.randint(2, upper) if upper >= 2 else 1
    cap = min(max(int(params.GROUP_CARDINALITY_MAX), 1), pool_size)
    lo = max(1, min(int(params.GROUP_CARDINALITY_MIN), cap))
    return random.randint(lo, cap)


def _create_relation(parent: Feature, children: list[Feature], rel_kind: str, params: Params) -> Relation:
    size = len(children)
    if rel_kind == "mand":
        return Relation(parent=parent, children=children, card_min=size, card_max=size)
    if rel_kind == "opt":
        return Relation(parent=parent, children=children, card_min=0, card_max=1 if size == 1 else size)
    if rel_kind == "alt":
        return Relation(parent=parent, children=children, card_min=1, card_max=1)
    if rel_kind == "or":
        return Relation(parent=parent, children=children, card_min=1, card_max=size)
    # group cardinality
    lo = max(1, min(int(params.GROUP_CARDINALITY_MIN), size))
    card_min = random.randint(lo, size)
    card_max = random.randint(card_min, size)
    return Relation(parent=parent, children=children, card_min=card_min, card_max=card_max)


def _apply_feature_cardinality(params: Params, features: list[Feature]) -> None:
    """Assign [n..m] cardinality to non-root features with probability
    PROB_FEATURE_CARDINALITY. The bounds come from MIN/MAX_FEATURE_CARDINALITY
    (first list element; list-shape is a legacy of the vendor dataclass)."""
    if not params.FEATURE_CARDINALITY:
        return
    prob = float(params.PROB_FEATURE_CARDINALITY or 0)
    if prob <= 0:
        return
    mins = list(params.MIN_FEATURE_CARDINALITY or [2])
    maxs = list(params.MAX_FEATURE_CARDINALITY or [5])
    lo = int(mins[0])
    hi = int(maxs[0] if maxs else lo)
    if hi < lo:
        hi = lo
    for f in features:
        # Feature.is_root is a method in flamapy, not a property — call it.
        if f.is_root():
            continue
        if random.random() < prob:
            fmin = random.randint(max(1, lo), max(lo, hi))
            fmax = random.randint(fmin, max(fmin, hi))
            f.feature_cardinality = Cardinality(fmin, fmax)


def _add_relations_to_level(parents: list[Feature], children: list[Feature], params: Params) -> None:
    total = len(children)
    rel_types = select_relation_types(params, total)
    random.shuffle(rel_types)
    pool = list(children)
    parent_idx = 0
    while pool:
        kind = rel_types.pop() if rel_types else "opt"
        parent = parents[parent_idx % len(parents)]
        parent_idx += 1
        size = max(1, min(_determine_group_size(len(pool), kind, params), len(pool)))
        group = [pool.pop() for _ in range(size)]
        parent.add_relation(_create_relation(parent, group, kind, params))
        for c in group:
            c.parent = parent


def generate_hierarchy(params: Params) -> tuple[FeatureModel, list[Feature]]:
    root = Feature(name="F0")
    fm = FeatureModel(root=root)
    num_feats = random.randint(int(params.MIN_FEATURES), int(params.MAX_FEATURES))
    names = [f"F{i + 1}" for i in range(num_feats)]
    features = [Feature(name=n) for n in names]
    max_depth = max(1, int(params.MAX_TREE_DEPTH))

    levels = {0: [root]}
    idx = 0
    placed = 0
    for depth in range(1, max_depth + 1):
        remaining = num_feats - placed
        if remaining <= 0:
            break
        parents = levels.get(depth - 1, [])
        if not parents:
            break
        levels_left = max_depth - depth + 1
        level_count = max(1, remaining // levels_left)
        if depth == max_depth:
            level_count = remaining
        level_feats = features[idx : idx + level_count]
        levels[depth] = level_feats
        idx += level_count
        placed += level_count
        _add_relations_to_level(parents, level_feats, params)

    connected = {f.name for f in fm.get_features()}
    used = [root] + [f for f in features if f.name in connected]
    _apply_feature_cardinality(params, used)
    return fm, used


# ─── Constraint generation ────────────────────────────────────────────


_BOOL_OPS = {
    "and": ASTOperation.AND,
    "or": ASTOperation.OR,
    "implies": ASTOperation.IMPLIES,
    "equiv": ASTOperation.EQUIVALENCE,
}


def _weighted_choice(options, weights):
    pairs = [(o, max(float(w), 0.0)) for o, w in zip(options, weights)]
    positive = [(o, w) for o, w in pairs if w > 0]
    if not positive:
        return options[0] if options else None
    os_, ws = zip(*positive)
    return random.choices(os_, weights=ws, k=1)[0]


def _pick_features_for_ctc(features, params):
    lo = max(1, int(params.MIN_VARS_PER_CONSTRAINT or 1))
    hi = max(lo, int(params.MAX_VARS_PER_CONSTRAINT or lo))
    upper = min(hi, len(features))
    lower = min(lo, upper)
    n = random.randint(max(1, lower), max(1, upper))
    return random.sample(features, k=n) if n <= len(features) else list(features)


def _maybe_negate(node, params):
    return Node(ASTOperation.NOT, node) if random.random() < float(params.PROB_NOT or 0) else node


def _apply_extra_representativeness(chosen, params, pool):
    """EXTRA_CONSTRAINT_REPRESENTATIVENESS = how many extra mentions of a
    hot feature to inject (feature reuse bias). A value of 1 means "normal",
    higher values add N-1 extra duplicates of a randomly-chosen feature."""
    extra = int(float(params.EXTRA_CONSTRAINT_REPRESENTATIVENESS or 1)) - 1
    if extra <= 0 or not chosen or not pool:
        return chosen
    hot = random.choice(chosen)
    return chosen + [hot] * min(extra, max(0, len(pool) - len(chosen)))


def _make_boolean_ctc(features, params):
    conn_name = _weighted_choice(
        ["and", "or", "implies", "equiv"],
        [params.PROB_AND, params.PROB_OR_CT, params.PROB_IMPLICATION, params.PROB_EQUIVALENCE],
    )
    conn_op = _BOOL_OPS[conn_name or "implies"]
    chosen = _pick_features_for_ctc(features, params)
    if len(chosen) < 2:
        chosen = random.sample(features, k=min(2, len(features)))
    chosen = _apply_extra_representativeness(chosen, params, features)
    nodes = [_maybe_negate(Node(f.name), params) for f in chosen]
    # Left-deep fold: (((n0 op n1) op n2) op n3)
    while len(nodes) > 1:
        nodes = [Node(conn_op, nodes[0], nodes[1])] + nodes[2:]
    return nodes[0]


def _ref_attr_node(attr_rec) -> Node:
    attr, feat, _, _ = attr_rec
    return Node(f"{feat.name}.{attr.name}")


def _make_arith_ctc(numeric_records, params):
    if not numeric_records:
        return None
    op = _weighted_choice(
        [ASTOperation.ADD, ASTOperation.SUB, ASTOperation.MUL, ASTOperation.DIV],
        [params.PROB_SUM, params.PROB_SUBSTRACT, params.PROB_MULTIPLY, params.PROB_DIVIDE],
    ) or ASTOperation.ADD
    cmp_op = _weighted_choice(
        [
            ASTOperation.EQUALS,
            ASTOperation.LOWER,
            ASTOperation.GREATER,
            ASTOperation.LOWER_EQUALS,
            ASTOperation.GREATER_EQUALS,
        ],
        [
            params.PROB_EQUALS,
            params.PROB_LESS,
            params.PROB_GREATER,
            params.PROB_LESS_EQUALS,
            params.PROB_GREATER_EQUALS,
        ],
    ) or ASTOperation.GREATER
    left = _ref_attr_node(random.choice(numeric_records))
    if random.random() < 0.5 and len(numeric_records) > 1:
        right = _ref_attr_node(random.choice(numeric_records))
    else:
        right = Node(random.randint(1, 20))
    expr = Node(op, left, right)
    return Node(cmp_op, expr, Node(random.randint(0, 100)))


def _make_aggregate_ctc(numeric_records, params):
    if not numeric_records:
        return None
    op = _weighted_choice(
        [ASTOperation.SUM, ASTOperation.AVG],
        [params.PROB_SUM_FUNCTION, params.PROB_AVG_FUNCTION],
    ) or ASTOperation.SUM
    cmp_op = _weighted_choice(
        [
            ASTOperation.EQUALS,
            ASTOperation.LOWER,
            ASTOperation.GREATER,
            ASTOperation.LOWER_EQUALS,
            ASTOperation.GREATER_EQUALS,
        ],
        [
            params.PROB_EQUALS,
            params.PROB_LESS,
            params.PROB_GREATER,
            params.PROB_LESS_EQUALS,
            params.PROB_GREATER_EQUALS,
        ],
    ) or ASTOperation.LOWER
    attr, _feat, _, _ = random.choice(numeric_records)
    agg = Node(op, Node(attr.name))
    return Node(cmp_op, agg, Node(random.randint(10, 200)))


def _make_string_ctc(string_records, params):
    """Two forms of string constraint:

    * ``len(F.X) <op> N`` — when the len() variant wins the PROB_LEN_FUNCTION
      coin flip. Uses the configured comparison-operator distribution.
    * ``F.X == 'literal'`` — the fallback equality-on-string form. Picks a
      value from the attribute's own string domain so the constraint is
      actually satisfiable.
    """
    if not string_records:
        return None
    cmp_op = _weighted_choice(
        [
            ASTOperation.EQUALS,
            ASTOperation.LOWER,
            ASTOperation.GREATER,
            ASTOperation.LOWER_EQUALS,
            ASTOperation.GREATER_EQUALS,
        ],
        [
            params.PROB_EQUALS,
            params.PROB_LESS,
            params.PROB_GREATER,
            params.PROB_LESS_EQUALS,
            params.PROB_GREATER_EQUALS,
        ],
    ) or ASTOperation.GREATER
    attr, feat, _, _ = random.choice(string_records)
    if random.random() < float(params.PROB_LEN_FUNCTION or 0):
        lenf = Node(ASTOperation.LEN, Node(f"{feat.name}.{attr.name}"))
        return Node(cmp_op, lenf, Node(random.randint(1, 10)))
    # Equality-to-literal form. Prefer a value from the attribute's own domain
    # so the generated constraint is at least sometimes satisfiable.
    elements = (
        getattr(attr.domain, "element_list", None)
        or getattr(attr.domain, "elements", None)
        or ["x"]
    )
    literal = random.choice(list(elements))
    return Node(ASTOperation.EQUALS, Node(f"{feat.name}.{attr.name}"), Node(str(literal)))


def _enabled_ctc_families(params, numeric, string):
    """Return (families, weights) for constraint-family selection.

    Families:
      - boolean    — weight = CTC_DIST_BOOLEAN
      - arithmetic — weight = CTC_DIST_INTEGER + CTC_DIST_REAL (split from
        the aggregate share when aggregates are also on).
      - aggregate  — derived from the arithmetic slice when
        AGGREGATE_FUNCTIONS is on (half of the arithmetic budget).
      - string     — weight = CTC_DIST_STRING

    A family with weight 0 but still "enabled" will fall back to a tiny
    positive weight so that a user who turned on a level but left the
    weight at 0 still sees the occasional constraint from it.
    """
    families, weights = ["boolean"], [max(float(params.CTC_DIST_BOOLEAN or 0), 0.0) or 0.01]
    if params.ARITHMETIC_LEVEL and numeric:
        arith_w = max(float(params.CTC_DIST_INTEGER or 0) + float(params.CTC_DIST_REAL or 0), 0.0) or 0.01
        if params.AGGREGATE_FUNCTIONS:
            # Half of the arithmetic budget goes to aggregates so both
            # families are represented when enabled.
            families.append("arithmetic")
            weights.append(arith_w * 0.5)
            families.append("aggregate")
            weights.append(arith_w * 0.5)
        else:
            families.append("arithmetic")
            weights.append(arith_w)
    if params.TYPE_LEVEL and params.STRING_CONSTRAINTS and string:
        families.append("string")
        weights.append(max(float(params.CTC_DIST_STRING or 0), 0.0) or 0.01)
    return families, weights


def add_constraints(fm: FeatureModel, features: list[Feature], attr_records: list[tuple], params: Params) -> None:
    count = random.randint(int(params.MIN_CONSTRAINTS), int(params.MAX_CONSTRAINTS))
    numeric = [r for r in attr_records if r[3] and r[2] in ("integer", "real")]
    string = [r for r in attr_records if r[3] and r[2] == "string"]
    families, weights = _enabled_ctc_families(params, numeric, string)

    builders = {
        "boolean": lambda: _make_boolean_ctc(features, params),
        "arithmetic": lambda: _make_arith_ctc(numeric, params),
        "aggregate": lambda: _make_aggregate_ctc(numeric, params),
        "string": lambda: _make_string_ctc(string, params),
    }

    emitted = 0
    for _ in range(count):
        if len(features) < 2:
            break
        fam = random.choices(families, weights=weights, k=1)[0]
        node = builders[fam]() or builders["boolean"]()
        fm.ctcs.append(Constraint(name=f"ctc{emitted}", ast=AST(node)))
        emitted += 1


# ─── Public entry point ───────────────────────────────────────────────


def generate_single_model(params: Params, index: int) -> FeatureModel:
    """Deterministic per (SEED, index): seeding at the top makes every
    run reproducible, including attribute and constraint choices."""
    random.seed(int(params.SEED or 1) + int(index))
    fm, features = generate_hierarchy(params)
    if params.RANDOM_ATTRIBUTES:
        attr_records = generate_random_attributes(params, features)
    else:
        attr_records = assign_manual_attributes(params, features)
    add_constraints(fm, features, attr_records, params)
    return fm
