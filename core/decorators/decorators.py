from functools import wraps

from flask import abort


def pass_or_abort(condition):

    def decorator(f):

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not condition(**kwargs):
                abort(404)
            return f(*args, **kwargs)

        return decorated_function

    return decorator
