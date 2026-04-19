from flamapy.core.operations import Valid

from flamapy.metamodels.Fmgenerator_metamodel.models.models import FmgeneratorModel


class FmgeneratorValid(Valid):

    def __init__(self):
        self.result = False

    def execute(self, model: FmgeneratorModel) -> 'FmgeneratorValid':
        # TODO: insert your model code here
        return self.result
