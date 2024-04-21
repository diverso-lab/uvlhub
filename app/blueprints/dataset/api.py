from app.blueprints.dataset.models import DataSet
from core.resources.generic_resource import create_resource

# Define fields and create the resource class
fields = {
    'dataset_id': 'id',
    'created': 'created_at'
}
DataSetResource = create_resource(DataSet, serialization_fields=fields)


def init_blueprint_api(api):
    """ Function to register resources with the provided Flask-RESTful Api instance. """
    api.add_resource(DataSetResource, '/api/v1/datasets/', endpoint='datasets')
    api.add_resource(DataSetResource, '/api/v1/datasets/<int:id>', endpoint='dataset')
