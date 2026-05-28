import random
import string

from flamapy.metamodels.fm_metamodel.models.feature_model import (
    Feature,
    Attribute,
    Domain,
    Range,
)

from fm_generator.FMGenerator.models.config import Params


def generate_random_attributes(params: Params, features: list[Feature]) -> None:
    num_attributes = random.randint(params.MIN_ATTRIBUTES, params.MAX_ATTRIBUTES)

    arithmetic_level_enabled = bool(getattr(params, "ARITHMETIC_LEVEL", False))
    min_vars_per_constraint = int(getattr(params, "MIN_VARS_PER_CONSTRAINT", 1))
    extra_constraint_repr = max(1, int(getattr(params, "EXTRA_CONSTRAINT_REPRESENTATIVENESS", 1)))

    # Si hay nivel aritmético, necesitamos suficientes attrs numéricos
    # repartidos en features distintas para que las constraints numéricas
    # sean realmente viables.
    required_numeric_attrs = 0
    numeric_weight = float(getattr(params, "DIST_INTEGER", 0.0)) + float(getattr(params, "DIST_REAL", 0.0))

    if arithmetic_level_enabled and numeric_weight > 0.0:
        required_numeric_attrs = (min_vars_per_constraint + extra_constraint_repr - 1) // extra_constraint_repr
        required_numeric_attrs = min(
            required_numeric_attrs,
            num_attributes,
            len(features),
        )

    available_features_for_numeric = features[:]
    random.shuffle(available_features_for_numeric)

    def pick_random_attribute_type() -> str:
        attr_types = ["boolean", "integer", "real", "string"]
        weights = [
            float(getattr(params, "DIST_BOOLEAN", 0.0)),
            float(getattr(params, "DIST_INTEGER", 0.0)),
            float(getattr(params, "DIST_REAL", 0.0)),
            float(getattr(params, "DIST_STRING", 0.0)),
        ]

        if sum(weights) <= 0.0:
            return "boolean"

        return random.choices(attr_types, weights=weights, k=1)[0]

    for i in range(num_attributes):
        # Garantizamos attrs numéricos suficientes al principio
        if i < required_numeric_attrs:
            num_types = ["integer", "real"]
            num_weights = [
                float(getattr(params, "DIST_INTEGER", 0.0)),
                float(getattr(params, "DIST_REAL", 0.0)),
            ]
            attr_type = random.choices(num_types, weights=num_weights, k=1)[0]
            if available_features_for_numeric:
                feature = available_features_for_numeric.pop()
            else:
                feature = random.choice(features)
        else:
            feature = random.choice(features)
            attr_type = pick_random_attribute_type()

        attr_name = f"Attr{i}"

        if attr_type == "boolean":
            domain = Domain(ranges=None, elements=[True, False])
            default = random.choice([True, False])

        elif attr_type == "integer":
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = random.randint(min_val, max_val)

        elif attr_type == "real":
            min_val, max_val = random.randint(0, 50), random.randint(51, 100)
            domain = Domain(ranges=[Range(min_val, max_val)], elements=None)
            default = round(random.uniform(min_val, max_val), 2)

        else:
            min_len = 1
            max_len = 50
            domain = Domain(ranges=[Range(min_len, max_len)], elements=None)
            length = random.randint(min_len, max_len)
            letters = string.ascii_letters + string.digits
            default = "".join(random.choices(letters, k=length))

        attribute = Attribute(name=attr_name, domain=domain, default_value=default)
        setattr(attribute, "attribute_type", attr_type)
        attribute.set_parent(feature)
        feature.add_attribute(attribute)


def assign_manual_attributes(params: Params, features: list[Feature]) -> None:
    assert (
        params.MIN_ATTRIBUTES is None and params.MAX_ATTRIBUTES is None
    ), "MIN_ATTRIBUTES and MAX_ATTRIBUTES must be None when using manual attributes."
    attr_dicts = params.ATTRIBUTES_LIST

    for attr in attr_dicts:
        name = attr.get("name")
        type_ = attr.get("type", "").strip().lower()
        value = attr.get("value")
        min_value = attr.get("min_value")
        max_value = attr.get("max_value")
        # Por defecto 1.0 (seguro se añade)
        attach_prob = attr.get("attach_probability", 1.0)

        if type_ == "boolean":
            domain_values = value
            if not isinstance(domain_values, list):
                if domain_values in [True, False]:
                    domain_values = [domain_values]
                elif isinstance(domain_values, str):
                    v = domain_values.strip().lower()
                    if v == "true":
                        domain_values = [True]
                    elif v == "false":
                        domain_values = [False]
                    else:
                        domain_values = [True, False]
                else:
                    domain_values = [True, False]
            domain = Domain(ranges=None, elements=domain_values)

            def gen_default():
                return random.choice(domain_values)

        elif type_ == "integer":
            try:
                min_v = int(min_value)
            except Exception:
                min_v = 0
            try:
                max_v = int(max_value)
            except Exception:
                max_v = 10
            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)

            def gen_default():
                return random.randint(min_v, max_v)

        elif type_ == "real":
            try:
                min_v = float(min_value)
            except Exception:
                min_v = 0.0
            try:
                max_v = float(max_value)
            except Exception:
                max_v = 1.0
            domain = Domain(ranges=[Range(min_v, max_v)], elements=None)

            def gen_default():
                return round(random.uniform(min_v, max_v), 3)

        elif type_ == "string":
            try:
                min_len = int(min_value)
            except Exception:
                min_len = 1
            try:
                max_len = int(max_value)
            except Exception:
                max_len = 10
            domain = Domain(ranges=[Range(min_len, max_len)], elements=None)

            def gen_default():
                length = random.randint(min_len, max_len)
                letters = string.ascii_letters + string.digits
                return "".join(random.choices(letters, k=length))

        else:
            continue

        for feature in features:
            if random.random() < float(attach_prob):
                default = gen_default()
                attribute = Attribute(name=name, domain=domain, default_value=default)
                setattr(attribute, "attribute_type", type_)
                attribute.set_parent(feature)
                feature.add_attribute(attribute)
