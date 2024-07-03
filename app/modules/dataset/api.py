from app.modules.dataset.models import DataSet
from core.resources.generic_resource import create_resource
from core.serialisers.serializer import Serializer

file_fields = {
    'file_id': 'id',
    'file_name': 'name',
    'size': 'get_formatted_size'
}
file_serializer = Serializer(file_fields)

dataset_fields = {
    'dataset_id': 'id',
    'created': 'created_at',
    'name': 'name',
    'doi': 'get_uvlhub_doi',
    'files': 'files'
}

dataset_serializer = Serializer(dataset_fields, related_serializers={'files': file_serializer})

DataSetResource = create_resource(DataSet, dataset_serializer)


def init_blueprint_api(api):
    """ Function to register resources with the provided Flask-RESTful Api instance. """
    api.add_resource(DataSetResource, '/api/v1/datasets/', endpoint='datasets')
    api.add_resource(DataSetResource, '/api/v1/datasets/<int:id>', endpoint='dataset')
