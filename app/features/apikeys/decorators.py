from functools import wraps

from flask import jsonify, request

from app.features.apikeys.services import ApiKeyService


def require_api_key(required_scope):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.headers.get("X-API-Key")
            if not key:
                return jsonify({"error": "Missing API key"}), 401

            service = ApiKeyService()
            api_key = service.get_valid_key(key)
            if api_key is None:
                return jsonify({"error": "Invalid API key"}), 403
            if required_scope not in api_key.scope_list:
                return jsonify({"error": "Forbidden: scope not allowed"}), 403

            service.mark_used(api_key)
            return f(*args, **kwargs)

        return wrapper

    return decorator
