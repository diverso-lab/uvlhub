# Statistics of Provided Variability Models

## Feature Models

For each provided variability model that was originally a feature model, we provide the following statistics:

* **Number of Features:** Number of features appearing in the feature model
* **Number of Leaf Features:** Number of features that have no child features
* **Number of Top Features:** Number of features that have a hierarchy level of one (i.e., are child features of the root feature)
* **Number of Constraints:** Number of cross-tree constraints appearing in the feature model (i.e., constraints that are not part of the tree hierarchy)
* **Average Constraint Size:** Average number of features appearing in the cross-tree constraint.
* **Cross-tree Constraint Density:** Ratio of number of cross-tree constraints to the number of features
* **Tree Depth:** Length of the largest path from the root feature to a leaf feature
* **Average Number of Children:** Average number of children each feature has
* **Number of Clauses:** Number of clauses after translating the model to CNF (using FeatureIDE's translation)
* **Number of Literals:** Number of literals after translating the model to CNF (using FeatureIDE's translation)
* **Clause Density:** Ratio of number of clauses to the number of variables/features (using FeatureIDE's translation)


## Decision Models

For each provided variability model that was originally a decision model, we provide the following statistics:

* **Number of Decisions:** Number of decisions appearing in the decision model
* **Number of Rules:** Number of rules appearing in the decision model
* **Number of Visibility Conditions:** Number of visibility constraints appearing in the decision model


## OVM Models

For each provided variability model that was originally an OVM model, we provide the following statistics:

* **Number of Variation Points:** Number of variation points appearing in the OVM model
* **Number of Variants:** Number of variants induced by the OVM model
* **Number of Constraints:** Number of constraints appearing in the OVM model
