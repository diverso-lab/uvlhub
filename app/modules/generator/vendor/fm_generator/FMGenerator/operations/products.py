from flamapy.core.operations import Products

from flamapy.metamodels.Fmgenerator_metamodel.models.models import FmgeneratorModel


class FmgeneratorProducts(Products):

    def __init__(self):
        self.products = []

    def execute(self, model: FmgeneratorModel) -> 'FmgeneratorProducts':
        # TODO: insert your model code here
        return self.products
