import os

from flask import Blueprint, jsonify
from sqlalchemy import text
from app import db

test_routes = Blueprint('test_routes', __name__)


@test_routes.route('/test')
def test_route():
    return 'Test route'


@test_routes.route('/env')
def show_env():
    env_vars = {key: value for key, value in os.environ.items()}
    return jsonify(env_vars)


@test_routes.route('/test_db')
def test_db():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'message': 'Connection to the database successful'})
    except Exception as e:
        return jsonify({'error': str(e)})
