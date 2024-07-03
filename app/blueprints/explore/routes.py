from flask import render_template, request, jsonify

from app.blueprints.explore import explore_bp
from app.blueprints.explore.forms import ExploreForm
from app.blueprints.dataset.services import DataSetService


@explore_bp.route('/explore', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        query = request.args.get('query', '')
        form = ExploreForm()
        return render_template('explore/index.html', form=form, query=query)

    if request.method == 'POST':
        criteria = request.get_json()
        datasets = DataSetService().filter(**criteria)
        return jsonify([dataset.to_dict() for dataset in datasets])
