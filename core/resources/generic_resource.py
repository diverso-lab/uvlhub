from flask import request
from flask_restful import Resource
from sqlalchemy.inspection import inspect
from datetime import datetime

from app import db


def convert_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class GenericResource(Resource):
    def __init__(self, model, serialization_fields=None):
        self.model = model
        self.model_name = model.__name__
        self.serialization_fields = serialization_fields

    def serialize(self, instance):
        if self.serialization_fields:
            serialized_data = {}
            for key, path in self.serialization_fields.items():
                target = instance
                for attr in path.split('.'):
                    target = getattr(target, attr, None)
                    if target is None:
                        break
                if isinstance(target, datetime):
                    target = target.isoformat()
                serialized_data[key] = target
            return serialized_data
        else:
            # Serialize all columns if serialization_fields is not provided
            return {attr.key: convert_value(getattr(instance, attr.key))
                    for attr in inspect(instance.__class__).mapper.column_attrs}

    def get(self, id=None):
        if id:
            item = self.model.query.get(id)
            if not item:
                return {'message': f'{self.model_name} not found'}, 404
            return self.serialize(item), 200
        items = self.model.query.all()
        return {'items': [self.serialize(i) for i in items]}, 200

    def post(self):
        data = request.get_json()
        if not data:
            return {'message': 'No input data provided'}, 400
        item = self.model(**{k: v for k, v in data.items() if
                             self.serialization_fields and k in self.serialization_fields}) if self.serialization_fields else self.model(
            **data)
        db.session.add(item)
        db.session.commit()
        return {'message': f'{self.model_name} created successfully', 'id': item.id}, 201

    def put(self, id):
        item = self.model.query.get(id)
        if not item:
            return {'message': f'{self.model_name} not found'}, 404
        data = request.get_json()
        fields_to_update = self.serialization_fields if self.serialization_fields else inspect(
            item.__class__).attrs.keys()
        for key in fields_to_update:
            if key in data:
                setattr(item, key, data[key])
        db.session.commit()
        return {'message': f'{self.model_name} updated successfully'}, 200

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
