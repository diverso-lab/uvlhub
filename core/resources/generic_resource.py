from flask import request
from flask_restful import Resource
from datetime import datetime

from app import db


def convert_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class GenericResource(Resource):
    def __init__(self, model, serializer):
        self.model = model
        self.model_name = model.__name__
        self.serializer = serializer

    def get(self, id=None):
        if id:
            item = self.model.query.get(id)
            if not item:
                return {'message': f'{self.model_name} not found'}, 404
            return self.serializer.serialize(item), 200
        else:
            items = self.model.query.all()
            return {'items': [self.serializer.serialize(i) for i in items]}, 200

    def post(self):
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400

        if self.serializer.serialization_fields:
            filtered_data = {key: value for key, value in data.items() if key in self.serializer.serialization_fields}
            item = self.model(**filtered_data)
        else:
            item = self.model(**data)

        db.session.add(item)
        db.session.commit()
        return {'message': f'{self.model.__name__} created successfully', 'id': item.id}, 201

    def put(self, id):
        item = self.model.query.get(id)
        if not item:
            return {'message': f'{self.model_name} not found'}, 404
        data = request.get_json()
        for key, value in data.items():
            if key in self.serializer.serialization_fields:
                setattr(item, key, value)
        db.session.commit()
        return self.serializer.serialize(item), 200

    def delete(self, id):
        item = self.model.query.get(id)
        if not item:
            return {'message': f'{self.model_name} not found'}, 404
        db.session.delete(item)
        db.session.commit()
        return {'message': f'{self.model_name} deleted successfully'}, 204


def create_resource(model, serialization_fields=None):
    class Resource(GenericResource):
        def __init__(self):
            super().__init__(model, serialization_fields)
    return Resource
