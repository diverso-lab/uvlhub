from flask import render_template
from app.blueprints.zenodo import zenodo_bp


@zenodo_bp.route('/zenodo', methods=['GET'])
def index():
    return render_template('zenodo/index.html')
