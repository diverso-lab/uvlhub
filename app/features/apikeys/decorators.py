from functools import wraps

from flask import g, jsonify, request

from app.features.apikeys.services import ApiKeyService


def resolve_api_key(required_scope):
    """Validate the X-API-Key header for the given scope.

    On success returns (api_key, None) and leaves the key and its owner in
    flask.g (g.api_key / g.api_user) for the request handler. On failure
    returns (None, (response, status_code)) ready to be returned by the route.
    Useful for routes where the API key is one of several auth mechanisms.
    """
    key = request.headers.get("X-API-Key")
    if not key:
        return None, (jsonify({"error": "Missing API key"}), 401)

    service = ApiKeyService()
    api_key = service.get_valid_key(key)
    if api_key is None:
        return None, (jsonify({"error": "Invalid API key"}), 403)
    if required_scope not in api_key.scope_list:
        return None, (jsonify({"error": "Forbidden: scope not allowed"}), 403)

    service.mark_used(api_key)
    g.api_key = api_key
    g.api_user = api_key.user
    return api_key, None


def require_api_key(required_scope):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            _, error = resolve_api_key(required_scope)
            if error:
                return error
            return f(*args, **kwargs)

        return wrapper

    return decorator
