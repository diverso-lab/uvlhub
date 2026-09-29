<div align="center">

  <a href="">[![Pytest Testing Suite](https://github.com/flamapy/flamapy/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/flamapy/flamapy/actions/workflows/tests.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/flamapy/flamapy/actions/workflows/commits.yml/badge.svg?branch=main)](https://github.com/flamapy/flamapy/actions/workflows/commits.yml)</a>
  <a href="">![PyPI](https://img.shields.io/pypi/v/flamapy?label=pypi%20package)
  <a href="">![PyPI - Downloads](https://img.shields.io/pypi/dm/flamapy)
</div>

# 

<div id="top"></div>
<br />
<div align="center">

  <h3 align="center">FLAMAPY</h3>

  <p align="center">
    A new and easy way to use FLAMA
    <br />
    <a href="https://github.com/flamapy/flamapy/issues">Report Bug</a>
    ·
    <a href="https://github.com/flamapy/flamapy/issues">Request Feature</a>
  </p>
</div>
<!-- ABOUT THE PROJECT -->

# About The Project
FLAMAPY Feature model distribution provides an easier way of using FLAMAPY when analysing feature models. It packs the most used plugins for analyis of feature models adding a layer of convenience to use the framework or integrate it. If some other operations are required please see in the [documentation](flamapy.github.io/docs) if its supported in the ecosystem though the Python interface. 

Feature Model Analysis has a crucial role in software product line engineering, enabling us to understand, design, and validate the complex relationships among features in a software product line. These feature models can often be complex and challenging to analyze due to their variability, making it difficult to identify conflicts, dead features, and potential optimizations. This is where this distribution comes in.

# Using the CMD
```bash
flamapy --help #This will show the commands available
flamapy satisfiable <path to file> to check if a model is valid
...
```
# Using the Python interface
This is simple, Flama FM dist in hosted in pypi, therefore simply add the package flama-fm-dist to your requirements file and call the API as follows:

```python
from flamapy.interfaces.python.flama_feature_model import FLAMAFeatureModel

fm = FLAMAFeatureModel("path/to/feature/model")
print(fm.valid())
```
# Operations available:
Currently this distribution offers a subset of the operations available in the ecosystem, in the case of the feature mdoel distribution, we provide those operations that are well tested and used by the community. Nonetheless, If other more complex operations are required you can rely on the python interface of the framework to execute them all. 

* atomic_sets: This operation is used to find the atomic sets in a model: It returns the atomic sets if they are found in the model. If the model does not follow the UVL specification, an exception is raised and the operation returns False.

* average_branching_factor:This refers to the average number of child features that a parent feature has in a feature model. It's calculated by dividing the total number of child features by the total number of parent features. A high average branching factor indicates a complex feature model with many options, while a low average branching factor indicates a simpler model.

* commonality: This is a measure of how often a feature appears in the products of a product line. It's usually expressed as a percentage. A feature with 100 per cent commonality is a core feature, as it appears in all products.

* configurations: These are the individual outcomes that can be produced from a feature model. Each product is a combination of features that satisfies all the constraints and dependencies in the feature model.

* configurations_number: This is the total number of different full configurations that can be produced from a feature model. It's calculated by considering all possible combinations of features, taking into account the constraints and dependencies between features.

* core_features: These are the features that are present in all products of a product line. In a feature model, they are the  features that are mandatory and not optional. Core features define the commonality among all products in a product line. This call requires sat to be called, however, there is an implementation within flamapy that does not requires sat, please use the framework in case of needing it.

* count_leafs: This operation counts the number of leaf features in a feature model. Leaf features are those that do not have any child features. They represent the most specific options in a product line.
* dead_features: These are features that, due to the constraints and dependencies in the feature model, cannot be included in any valid product. Dead features are usually a sign of an error in the feature model.

* estimated_number_of_configurations: This is an estimate of the total number of different products that can be produced from a feature model. It's calculated by considering all possible combinations of features. This can be a simple multiplication if all
features are independent, but in most cases, constraints and dependencies between features need to be taken into account.

* false_optional_features: These are features that appear to be optional in the feature model, but due to the constraints and dependencies, must be included in every valid product. Like dead features, false optional features are usually a sign of an error in the feature model.

* feature_ancestors: These are the features that are directly or indirectly the parent of a given feature in a feature model. Ancestors of a feature are found by traversing up the feature hierarchy. This information can be useful to understand the context and dependencies of a feature.

* filter: This operation selects a subset of the products of a product line based on certain criteria. For example, youmight filter the products to only include those that contain a certain feature.

* leaf_features: This operation is used to find leaf features in a model: It returns the leaf features if they are found in themodel. If the model does not follow the UVL specification, an exception is raised and the operation returns False.

* max_depth: This operation is used to find the max depth of the tree in a model: It returns the max depth of the tree. If the model does not follow the UVL specification, an exception is raised and the operation returns False.

* satisfiable: In the context of feature models, this usually refers to whether the feature model itself satisfies all the
constraints and dependencies. A a valid feature model is one that does encodes at least a single valid product.

* satisfiable_configuration: This is a product that is produced from a valid configuration of features. A valid product satisfies all the constraints and dependencies in the feature model.

