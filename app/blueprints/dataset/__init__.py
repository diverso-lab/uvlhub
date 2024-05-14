from flask import Blueprint
from flask_restful import Api

from app.blueprints.dataset.api import init_blueprint_api

dataset_bp = Blueprint('dataset', __name__, template_folder='templates')

api = Api(dataset_bp)
init_blueprint_api(api)
