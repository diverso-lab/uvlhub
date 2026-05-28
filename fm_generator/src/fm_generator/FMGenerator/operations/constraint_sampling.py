import random

from flamapy.metamodels.fm_metamodel.models.feature_model import (
    Feature,
    Attribute,
)


# -----------------------------
# ECR es por FEATURE (no por key)
# key: "F12" o "F12.attr"
# feature_id = "F12"
# -----------------------------
def feature_id_from_key(key: str) -> str:
    return key.split(".", 1)[0]


def group_keys_by_feature(keys: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for k in keys:
        fid = feature_id_from_key(k)
        groups.setdefault(fid, []).append(k)
    return groups


def sample_keys_with_ecr(
    groups: dict[str, list[str]],
    target_occ: int,
    max_reps: int,
    max_features_param: int,
    feature_usage: dict[str, int] | None = None,
    selected_features: set[str] | None = None,
) -> list[str] | None:
    """
    Devuelve una lista de keys de longitud target_occ.
    Permite repetir keys, pero restringe por feature_id a max_reps apariciones.
    Además limita el número de features distintas usadas por MAX_FEATURES.
    """
    if target_occ < 1:
        return None

    feature_usage = {} if feature_usage is None else feature_usage
    selected_features = set() if selected_features is None else selected_features

    out: list[str] = []

    for _ in range(target_occ):
        allowed_fids = [
            fid
            for fid in groups
            if feature_usage.get(fid, 0) < max_reps
            and (fid in selected_features or len(selected_features) < max_features_param)
        ]

        if not allowed_fids:
            return None

        fid = random.choice(allowed_fids)
        out.append(random.choice(groups[fid]))
        feature_usage[fid] = feature_usage.get(fid, 0) + 1
        selected_features.add(fid)

    random.shuffle(out)
    return out


def filter_attrs_for_constraint(attr_pool: list[tuple[Feature, Attribute, float]]) -> list[tuple[Feature, Attribute]]:
    filtered: list[tuple[Feature, Attribute]] = []
    for feat, attr, prob in attr_pool:
        if random.random() < prob:
            filtered.append((feat, attr))
    return filtered


def ensure_non_empty_filtered_pool(
    filtered_pool: list[tuple[Feature, Attribute]], original_pool: list[tuple[Feature, Attribute, float]]
) -> list[tuple[Feature, Attribute]]:
    if filtered_pool or not original_pool:
        return filtered_pool

    # Si no ha entrado ninguno por probabilidad, damos una oportunidad
    # a que entre uno al menos, escogido ponderadamente por su
    # attach_probability.
    weights = [max(0.0, prob) for _, _, prob in original_pool]
    if sum(weights) <= 0.0:
        return []

    feat, attr, _ = random.choices(original_pool, weights=weights, k=1)[0]
    return [(feat, attr)]


def filter_len_groups_for_numeric_use(
    len_groups: dict[str, list[str]],
    len_prob: float,
) -> dict[str, list[str]]:
    filtered: dict[str, list[str]] = {}

    if len_prob <= 0.0:
        return filtered

    for fid, values in len_groups.items():
        selected_values = [value for value in values if random.random() < len_prob]
        if selected_values:
            filtered[fid] = selected_values

    return filtered


def distinct_feature_cap(groups, max_features_param):
    return min(len(groups), max_features_param)


def max_occurrences_possible(groups, max_features_param, max_reps):
    return distinct_feature_cap(groups, max_features_param) * max_reps
