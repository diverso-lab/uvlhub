from flamapy.metamodels.bdd_metamodel import operations as bdd_operations
from flamapy.metamodels.bdd_metamodel.transformations.fm_to_bdd import FmToBDD
from flamapy.metamodels.fm_metamodel import operations as fm_operations
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.pysat_metamodel import operations as sat_operations
from flamapy.metamodels.pysat_metamodel.transformations.fm_to_pysat import FmToPysat
from fm_characterization import FMProperties, FMPropertyMeasure

from .fm_utils import get_nof_configuration_as_str, get_ratio


class FMAnalysis:

    def __init__(self, model: FeatureModel):
        self.fm = model
        self.sat_model = FmToPysat(model).transform()
        try:
            self.bdd_model = FmToBDD(model).transform()
        except Exception as e:
            print(f"Warning: the feature model is too large to build the BDD model. (Exception: {e})")
            self.bdd_model = None

        # For performance purposes
        self._common_features = sat_operations.Glucose3CoreFeatures().execute(self.sat_model).get_result()
        self._dead_features = sat_operations.Glucose3DeadFeatures().execute(self.sat_model).get_result()

    def get_analysis(self) -> list[FMPropertyMeasure]:
        result = []
        result.append(self.fm_valid())
        result.append(self.fm_core_features())
        result.append(self.fm_dead_features())
        result.append(self.fm_variant_features())
        result.append(self.fm_false_optional_features())
        result.append(self.fm_configurations_number())
        return result

    def fm_valid(self) -> FMPropertyMeasure:
        _valid = sat_operations.Glucose3Valid().execute(self.sat_model).get_result()
        _result = "Yes" if _valid else "No"
        return FMPropertyMeasure(FMProperties.VALID.value, _result)

    def fm_core_features(self) -> FMPropertyMeasure:
        _core_features = self._common_features
        return FMPropertyMeasure(
            FMProperties.CORE_FEATURES.value,
            _core_features,
            len(_core_features),
            get_ratio(_core_features, self.fm.get_features()),
        )

    def fm_dead_features(self) -> FMPropertyMeasure:
        _dead_features = self._dead_features
        return FMPropertyMeasure(
            FMProperties.DEAD_FEATURES.value,
            _dead_features,
            len(_dead_features),
            get_ratio(_dead_features, self.fm.get_features()),
        )

    def fm_variant_features(self) -> FMPropertyMeasure:
        _variant_features = [
            f.name
            for f in self.fm.get_features()
            if f.name not in self._common_features and f.name not in self._dead_features
        ]
        return FMPropertyMeasure(
            FMProperties.VARIANT_FEATURES.value,
            _variant_features,
            len(_variant_features),
            get_ratio(_variant_features, self.fm.get_features()),
        )

    def fm_false_optional_features(self) -> FMPropertyMeasure:
        _false_optional_features = (
            sat_operations.Glucose3FalseOptionalFeatures(self.fm).execute(self.sat_model).get_result()
        )
        return FMPropertyMeasure(
            FMProperties.FALSE_OPTIONAL_FEATURES.value,
            _false_optional_features,
            len(_false_optional_features),
            get_ratio(_false_optional_features, self.fm.get_features()),
        )

    def fm_configurations_number(self) -> FMPropertyMeasure:
        if self.bdd_model is not None:
            _configurations = bdd_operations.BDDProductsNumber().execute(self.bdd_model).get_result()
            _approximation = False
        else:
            _configurations = fm_operations.FMEstimatedProductsNumber().execute(self.fm).get_result()
            _approximation = True
        _configurations = get_nof_configuration_as_str(_configurations, _approximation, len(self.fm.get_constraints()))
        return FMPropertyMeasure(FMProperties.CONFIGURATIONS.value, _configurations)
