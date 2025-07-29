from datetime import datetime
from functools import wraps
from flask import request, jsonify
import pytz


def require_api_key(required_scope):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.headers.get("X-API-Key")
            if not key:
                return jsonify({"error": "Missing API key"}), 401

            from app.modules.apikeys.models import ApiKey
            from app import db

            api_key = ApiKey.query.filter_by(key=key).first()
            if not api_key:
                return jsonify({"error": "Invalid API key"}), 403

            if required_scope not in api_key.scopes.split(","):
                return jsonify({"error": "Forbidden: scope not allowed"}), 403

            api_key.last_used_at = datetime.now(pytz.utc)
            db.session.commit()
            return f(*args, **kwargs)

        return wrapper

    return decorator
