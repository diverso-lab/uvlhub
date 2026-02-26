from datetime import datetime


def convert_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class Serializer:
    def __init__(self, serialization_fields, related_serializers=None):
        self.serialization_fields = serialization_fields
        self.related_serializers = related_serializers or {}

    def serialize(self, instance):
        serialized_data = {}
        for key, attr_name in self.serialization_fields.items():
            if key in self.related_serializers:
                related_data = getattr(instance, attr_name)()
                if isinstance(related_data, list):
                    serialized_data[key] = [
                        self.related_serializers[key].serialize(sub_instance) for sub_instance in related_data
                    ]
                else:
                    serialized_data[key] = self.related_serializers[key].serialize(related_data)
            else:
                attr = getattr(instance, attr_name, None)
                if callable(attr):
                    attr = attr()
                serialized_data[key] = convert_value(attr)
        return serialized_data
